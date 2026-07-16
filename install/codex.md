# Codex CLI

在 OpenAI Codex CLI 啟用 FinMind MCP server（本機 stdio 模式），讓你在終端機用自然語言查 FinMind 金融資料。

## 安裝套件

先裝 [uv](https://docs.astral.sh/uv/)（提供 `uvx`）；`uvx` 會在啟動時從 PyPI 抓 `finmind-mcp`，不需另外安裝。

```bash
# 或常駐安裝（下方 command 改成 finmind-mcp）：
pipx install finmind-mcp
```

> **Windows 使用者**：`uv`/`pipx` 的安裝方式、token 設定與常見 PATH 問題，請先看 [Windows 安裝指引](windows.md)。

## 設定

一行指令（推薦）：

```bash
codex mcp add finmind --env FINMIND_TOKEN=your-token-here -- uvx finmind-mcp
```

格式為 `codex mcp add <名稱> --env K=V -- <stdio 啟動指令>`。

或手動編 `~/.codex/config.toml`（注意 Codex 的 `env` 是**獨立子表**，跟 Claude 的 JSON 不同）：

```toml
[mcp_servers.finmind]
command = "uvx"
args = ["finmind-mcp"]

[mcp_servers.finmind.env]
FINMIND_TOKEN = "your-token-here"
```

> 也可放專案層級 `.codex/config.toml`（僅限信任的專案）。

## 取得 Token

請先依 [token 取得指引](../knowledge/token-guide.md) 取得 FinMind Token，填入上方 `FINMIND_TOKEN`。

## 驗證

在 Codex TUI 輸入 `/mcp` 查看 `finmind` 是否連線；接著問「列出 FinMind 可用的 dataset」應回傳清單。
