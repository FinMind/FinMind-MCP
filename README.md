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

## 發佈

兩條 distribution（MCP 與 ChatGPT）共用一份 `knowledge/`，但發佈方式不同。

### MCP server（Claude / Gemini / Cursor / Windsurf 線）— 推 tag 全自動

改完 `knowledge/` 或程式碼後，**推一個版本 tag 就好**：GitHub Actions（[`.github/workflows/publish.yml`](.github/workflows/publish.yml)）會自動 `uv build` → `twine check` → 用 PyPI Trusted Publishing（OIDC）發 PyPI。版本號由 tag 經 `hatch-vcs` 決定，**不用改 `pyproject.toml`**。

```bash
uv run pytest -q          # 先確認測試過（CI 也會再跑一次）
git tag v0.1.0
git push origin v0.1.0    # → CI 自動 build + 發 PyPI
```

`knowledge/` 由 hatch `force-include` 打包進 wheel（`finmind_mcp/_knowledge/`），server runtime 直接讀、不用 compile；發版後用戶 `uvx finmind-mcp` / `pipx install finmind-mcp` 即抓到新版。

> 首次需在 PyPI 設好 trusted publisher（project `finmind-mcp` / repo `FinMind/FinMind-MCP` / workflow `publish.yml` / env `pypi`）。

### Custom GPT（ChatGPT 線）— 產物自動 build、建 GPT 手動

GPT 的輸入由 `chatgpt/build_instructions.py` 編出來，CI 每次 push/PR 都會驗證它能 build 且 instructions 在 8000 字上限內。但 **OpenAI 沒有公開 API 可程式化建立／更新 Custom GPT**，最後一步要手動在 ChatGPT builder 完成：

```bash
python chatgpt/build_instructions.py
# 產出（gitignored，每次重生）：
# - chatgpt/instructions.txt      → 貼到 Custom GPT 的 instructions
# - chatgpt/knowledge_bundle.md   → 上傳到 Custom GPT 的 Knowledge files
# - chatgpt/openapi.yaml          → 在 Custom GPT Action 匯入（Bearer auth）
```

`knowledge/` 改版後重跑上面指令、把三個檔重貼／重傳到 GPT 即可。各 host 的 MCP 安裝方式見 [install/*.md](install/)。

## License

[Apache License 2.0](LICENSE)。
