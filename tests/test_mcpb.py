"""Tests for the Claude Desktop extension bundle (mcpb/) and its build script."""

import importlib.util
import json
from pathlib import Path

import pytest

from finmind_mcp import tools

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = json.loads((ROOT / "mcpb" / "manifest.json").read_text(encoding="utf-8"))


def _load_build_script():
    spec = importlib.util.spec_from_file_location("build_mcpb", ROOT / "scripts" / "build_mcpb.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_manifest_tools_match_server():
    # Claude Desktop 安裝畫面顯示的是 manifest 的 tools；新增 tool 時要一起補。
    declared = sorted(t["name"] for t in MANIFEST["tools"])
    assert declared == sorted(t.name for t in tools.tool_definitions())


def test_manifest_uses_uv_runtime_and_passes_token():
    server = MANIFEST["server"]
    assert server["type"] == "uv"
    assert (ROOT / "mcpb" / server["entry_point"]).is_file()
    assert server["mcp_config"]["env"]["FINMIND_TOKEN"] == "${user_config.finmind_token}"
    token = MANIFEST["user_config"]["finmind_token"]
    assert token["required"] is True and token["sensitive"] is True


def test_manifest_does_not_require_system_python():
    # 宣告 runtimes.python 會讓 Claude Desktop 檢查系統 Python，沒裝就拒絕安裝；
    # uv 類型由 host 自己準備 Python，不該宣告。
    assert "runtimes" not in MANIFEST.get("compatibility", {})


def test_stamp_pins_release_version(tmp_path):
    build = _load_build_script()
    for name in ("manifest.json", "pyproject.toml"):
        (tmp_path / name).write_text((ROOT / "mcpb" / name).read_text(encoding="utf-8"), encoding="utf-8")

    build.stamp(tmp_path, "1.2.3", "finmind-mcp==1.2.3")

    assert json.loads((tmp_path / "manifest.json").read_text(encoding="utf-8"))["version"] == "1.2.3"
    pyproject = (tmp_path / "pyproject.toml").read_text(encoding="utf-8")
    assert '"finmind-mcp==1.2.3"' in pyproject
    assert 'version = "1.2.3"' in pyproject


@pytest.mark.parametrize(
    "args, env, expected",
    [(["0.0.11"], "", "0.0.11"), ([], "v0.1.0", "0.1.0"), ([], "0.2.0", "0.2.0")],
)
def test_resolve_version(monkeypatch, args, env, expected):
    monkeypatch.setenv("GITHUB_REF_NAME", env)
    assert _load_build_script().resolve_version(args) == expected


def test_resolve_version_rejects_non_release(monkeypatch):
    monkeypatch.setenv("GITHUB_REF_NAME", "master")
    with pytest.raises(SystemExit):
        _load_build_script().resolve_version([])
