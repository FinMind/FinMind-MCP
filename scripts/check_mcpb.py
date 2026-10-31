"""模擬 Claude Desktop 安裝並啟動 dist/finmind.mcpb，確認擴充套件真的能用。

步驟與 host 相同：解壓縮 → 讀 manifest 的 mcp_config → 代入 ${__dirname} 與
${user_config.*} → 啟動子行程 → 走 MCP 握手 → tools/list → 呼叫一個離線 tool。
需要 PATH 上有 uv（Claude Desktop 啟動 uv 類型擴充套件時同樣會用 uv）。

用法：
    python scripts/check_mcpb.py [dist/finmind.mcpb]
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_BUNDLE = ROOT / "dist" / "finmind.mcpb"
FAKE_TOKEN = "mcpb-check"


def substitute(value: str, dirname: Path, user_config: dict[str, str]) -> str:
    value = value.replace("${__dirname}", str(dirname))
    for key, val in user_config.items():
        value = value.replace("${user_config.%s}" % key, val)
    return value


def main() -> None:
    bundle = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_BUNDLE
    with tempfile.TemporaryDirectory() as tmp:
        ext_dir = Path(tmp) / "finmind"
        with zipfile.ZipFile(bundle) as zf:
            zf.extractall(ext_dir)

        manifest = json.loads((ext_dir / "manifest.json").read_text(encoding="utf-8"))
        assert manifest["server"]["type"] == "uv", manifest["server"]
        user_config = {key: FAKE_TOKEN for key in manifest.get("user_config", {})}
        cfg = manifest["server"]["mcp_config"]
        command = shutil.which(cfg["command"])
        if command is None:
            sys.exit(f"找不到 {cfg['command']}，請先安裝 uv")
        args = [substitute(a, ext_dir, user_config) for a in cfg.get("args", [])]
        env = {k: substitute(v, ext_dir, user_config) for k, v in cfg.get("env", {}).items()}
        assert env.get("FINMIND_TOKEN") == FAKE_TOKEN, "token 沒有從 user_config 傳進 env"

        proc = subprocess.Popen(
            [command, *args],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, encoding="utf-8", env={**os.environ, **env},
        )
        assert proc.stdin is not None and proc.stdout is not None

        def send(msg: dict) -> None:
            proc.stdin.write(json.dumps(msg) + "\n")
            proc.stdin.flush()

        def request(msg: dict) -> dict:
            # 跟真正的 host 一樣保持 stdin 開著，一問一答；略過 server 主動送的通知。
            send(msg)
            while True:
                line = proc.stdout.readline()
                if not line:
                    proc.kill()
                    sys.exit(f"server 提早結束（等待 {msg['method']}）\nstderr:\n{proc.stderr.read()}")
                resp = json.loads(line)
                if resp.get("id") == msg["id"]:
                    return resp

        try:
            init = request({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {
                "protocolVersion": "2024-11-05", "capabilities": {},
                "clientInfo": {"name": "check_mcpb", "version": "0"}}})
            assert "result" in init, init
            send({"jsonrpc": "2.0", "method": "notifications/initialized"})
            tools = request({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
            call = request({"jsonrpc": "2.0", "id": 3, "method": "tools/call",
                            "params": {"name": "list_datasets", "arguments": {}}})
        finally:
            proc.stdin.close()
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                proc.kill()

        tool_names = sorted(t["name"] for t in tools["result"]["tools"])
        declared = sorted(t["name"] for t in manifest.get("tools", []))
        assert tool_names == declared, f"manifest tools {declared} != server tools {tool_names}"
        result = call["result"]
        assert not result.get("isError") and result["content"], call
        print(f"OK finmind.mcpb {manifest['version']}: {len(tool_names)} tools {tool_names}")


if __name__ == "__main__":
    main()
