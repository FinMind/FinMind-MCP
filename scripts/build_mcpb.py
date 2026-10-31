"""打包 Claude Desktop 擴充套件 dist/finmind.mcpb。

把 mcpb/ 複製到暫存目錄，將 manifest.json 與 pyproject.toml 的版本改成 VERSION，
再用官方 CLI（@anthropic-ai/mcpb）驗證並打包。需要 Node.js（npx）。

用法：
    python scripts/build_mcpb.py 0.0.11       # 指定版本
    python scripts/build_mcpb.py              # 沒給版本 → 讀環境變數 GITHUB_REF_NAME（發版 tag）
    python scripts/build_mcpb.py --dev        # CI 用：相依改指向本 repo 原始碼，測尚未發版的改動

finmind-mcp 會被釘在同一個版本，所以該版本必須已經在 PyPI 上
（publish.yml 先上 PyPI 再打包，順序已保證）。
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "mcpb"
OUT = ROOT / "dist" / "finmind.mcpb"
MCPB_CLI = "@anthropic-ai/mcpb@2"
VERSION_RE = re.compile(r"^\d+\.\d+\.\d+$")


def resolve_version(args: list[str]) -> str:
    raw = args[0] if args else os.environ.get("GITHUB_REF_NAME", "")
    version = raw.removeprefix("v")
    if not VERSION_RE.match(version):
        sys.exit(f"版本需為 X.Y.Z（可帶 v 前綴），收到：{raw!r}")
    return version


def stamp(build_dir: Path, version: str, requirement: str) -> None:
    manifest_path = build_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["version"] = version
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    pyproject_path = build_dir / "pyproject.toml"
    text = pyproject_path.read_text(encoding="utf-8")
    text, n_pin = re.subn(r'"finmind-mcp==[^"]*"', f'"{requirement}"', text)
    text, n_ver = re.subn(r'(?m)^version = "[^"]*"$', f'version = "{version}"', text)
    if n_pin != 1 or n_ver != 1:
        sys.exit("mcpb/pyproject.toml 格式不符，找不到 finmind-mcp 釘版或 version 欄位")
    pyproject_path.write_text(text, encoding="utf-8")


def main() -> None:
    args = sys.argv[1:]
    dev = "--dev" in args
    if dev:
        version, requirement = "0.0.0", f"finmind-mcp @ {ROOT.as_uri()}"
    else:
        version = resolve_version(args)
        requirement = f"finmind-mcp=={version}"
    npx = shutil.which("npx")
    if npx is None:
        sys.exit("找不到 npx，請先安裝 Node.js")

    with tempfile.TemporaryDirectory() as tmp:
        build_dir = Path(tmp) / "finmind"
        shutil.copytree(SRC, build_dir, ignore=shutil.ignore_patterns(".venv", "uv.lock", "__pycache__"))
        stamp(build_dir, version, requirement)
        OUT.parent.mkdir(exist_ok=True)
        subprocess.run([npx, "-y", MCPB_CLI, "validate", str(build_dir)], check=True)
        subprocess.run([npx, "-y", MCPB_CLI, "pack", str(build_dir), str(OUT)], check=True)

    print(f"built {OUT.relative_to(ROOT)} ({requirement})")


if __name__ == "__main__":
    main()
