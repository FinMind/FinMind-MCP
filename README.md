# FinMind-MCP

FinMind 官方 [Model Context Protocol](https://modelcontextprotocol.io) server。
讓 Claude、Gemini CLI、Cursor、Windsurf 等支援 MCP 的 AI 工具，能用自然語言查
[FinMind](https://finmindtrade.com) 75+ 種台股、期權、總經與全球金融資料。

倉庫同時收錄 [FinMind Custom GPT](chatgpt/) 的 OpenAPI Action schema 與
編譯 instructions 工具——MCP server 與 Custom GPT **共用一份知識包**
（[`knowledge/`](knowledge/)）。

## 快速開始

```bash
# 取 Token: https://finmindtrade.com/analysis/#/account/user
export FINMIND_TOKEN=your-token

# 一行裝
uvx finmind-mcp
# 或
pipx install finmind-mcp
```

## 在各 host 啟用

| Host | 安裝指引 |
|---|---|
| Claude Desktop | [install/claude-desktop.md](install/claude-desktop.md) |
| Claude Code | [install/claude-code.md](install/claude-code.md) |
| Claude.ai (Web) | [install/claude-ai.md](install/claude-ai.md) |
| Cursor | [install/cursor.md](install/cursor.md) |
| Windsurf | [install/windsurf.md](install/windsurf.md) |
| Gemini CLI | [install/gemini-cli.md](install/gemini-cli.md) |
| Codex CLI | [install/codex.md](install/codex.md) |

## 範例查詢

- 「台積電最近一個月股價」
- 「2330 三大法人近一週買賣」
- 「台積電今年每月營收」
- 「美元對台幣匯率近半年走勢」

完整範例見 [`knowledge/examples.md`](knowledge/examples.md)。

## 倉庫結構

```
FinMind-MCP/
├── src/finmind_mcp/      # MCP server source
├── tests/                # pytest 31 個測試
├── smoke.py              # stdio smoke test
├── knowledge/            # SSOT markdown（dataset、行為規則、錯誤腳本、Q&A）
├── chatgpt/              # Custom GPT artifacts（OpenAPI + build script）
├── install/              # 各 host 安裝指引
└── docs/                 # 設計 spec 與實作 plan
```

## 開發

```bash
uv venv --python 3.10
source .venv/bin/activate
uv pip install -e ".[dev]"
uv run pytest -v          # 31 tests
uv run python smoke.py    # stdio integration check
```

## 同步發佈

兩條 distribution（ChatGPT 與 MCP）共用一份 `knowledge/`，但發佈流程不同。

### Custom GPT（ChatGPT 線）

```bash
python chatgpt/build_instructions.py
# 產出：
# - chatgpt/instructions.txt      → 貼到 OpenAI Custom GPT instructions
# - chatgpt/knowledge_bundle.md   → 上傳到 Custom GPT Knowledge files
# - chatgpt/openapi.yaml          → 在 Custom GPT Action 匯入
```

### MCP server（Claude / Gemini / Cursor / Windsurf 線）

MCP server runtime 直接讀 `knowledge/`，**不用 compile** — `knowledge/` 改完後直接 bump version + 發版。`knowledge/` 會被 hatch 透過 `force-include` 打包進 wheel（搬到 `finmind_mcp/_knowledge/`），pip install 後 server 仍能讀到。

```bash
# 1. 改完 knowledge/，跑既有測試
uv run pytest -q

# 2. bump 版本（pyproject.toml [project].version）
# 3. 建 sdist + wheel
uv build
# 產出 dist/finmind-mcp-<ver>.tar.gz、dist/finmind_mcp-<ver>-py3-none-any.whl
# 兩者都已內含 knowledge/（wheel 路徑：finmind_mcp/_knowledge/*.md）

# 4. 發 PyPI
uv publish
# 之後用戶用 `uvx finmind-mcp` 或 `pipx install finmind-mcp` 就會抓到新版

# 5. 部署 remote endpoint mcp.finmindtrade.com（給 Claude.ai integrations）
# 走既有 service repo 的 docker compose + traefik 路徑
```

各 host 安裝方式見 [install/*.md](install/)；同一份 server code 在所有 MCP host 共用。

## License

[Apache License 2.0](LICENSE)。
