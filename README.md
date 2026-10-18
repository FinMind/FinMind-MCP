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
| Claude Desktop | **一鍵安裝**：下載 [finmind.mcpb](https://github.com/FinMind/FinMind-MCP/releases/latest/download/finmind.mcpb) 點兩下 → 詳見 [install/claude-desktop.md](install/claude-desktop.md) |
| Claude Code | [install/claude-code.md](install/claude-code.md) |
| Cursor | [install/cursor.md](install/cursor.md) |
| Windsurf | [install/windsurf.md](install/windsurf.md) |
| Gemini CLI | [install/gemini-cli.md](install/gemini-cli.md) |
| Codex CLI | [install/codex.md](install/codex.md) |

> **Windows 使用者**：請先看 [install/windows.md](install/windows.md) —— 含 `uv`/`pipx` 安裝、PowerShell 環境變數、各 host 設定檔的 Windows 路徑，以及「host 找不到 `finmind-mcp` 指令」等常見問題。

## Tools

| Tool | 用途 | 對應 API |
|---|---|---|
| `query_dataset` | 通用查詢（`dataset` + `data_id` + 日期） | `/api/v4/data` |
| `list_datasets` | 列出所有 dataset、所需方案與說明（離線） | 內建 `knowledge/datasets.md` |
| `get_stock_info` | 台股代號／名稱／產業 | `/api/v4/data?dataset=TaiwanStockInfo` |
| `query_trading_daily_report` | 單日分點進出（依個股 `data_id` 或券商 `securities_trader_id`） | `/api/v4/taiwan_stock_trading_daily_report` |
| `get_pricing` | 方案價格與授權（離線、不需 token） | 內建 `knowledge/pricing.md` |
| `query_endpoint` | 其他專屬 endpoint：分點統計 SecIdAgg、權證分點、股／期／選即時快照、`datalist`、`translation` | `/api/v4/<endpoint>`（allowlist） |
| `download_storage_object` | 整日全市場 parquet（Sponsor Pro）下載到本機，回傳路徑、筆數、欄位、前幾列，可依代號／分點過濾 | `/api/v4/storage_objects` |

權限不足時，工具會說明該 dataset／endpoint 需要哪個方案（Backer / Sponsor / Sponsor Pro）、附上 API 回應原文與升級連結；參數錯誤時同樣附上 API 原文。

### 整日檔下載（`download_storage_object`）

- 檔案存到 `FINMIND_DOWNLOAD_DIR`；沒設時預設為使用者快取目錄下的 `finmind-mcp/storage_objects/`（Linux `~/.cache/…`、macOS `~/Library/Caches/…`、Windows `%LOCALAPPDATA%\…`）。同一天同一 dataset 再查會直接用本機檔，`refresh: true` 才重抓。
- 整日檔動輒數十 MB，工具**只回摘要**（最多 500 列），完整資料請用程式讀本機檔（`pandas.read_parquet(path)`）。
- 讀 parquet 需要 `pyarrow`（wheel 約 29–54 MB），是選用 extra，預設不裝；沒裝時仍會下載並回傳路徑，並提示安裝方式：

  ```bash
  uvx --from "finmind-mcp[parquet]" finmind-mcp      # host 設定的 args 改成 ["--from", "finmind-mcp[parquet]", "finmind-mcp"]
  pipx install "finmind-mcp[parquet]"
  ```

  Claude Desktop 擴充套件（`.mcpb`）已內含 pyarrow，不需另外處理。

## 範例查詢

- 「台積電最近一個月股價」
- 「2330 三大法人近一週買賣」
- 「台積電今年每月營收」
- 「美元對台幣匯率近半年走勢」
- 「合庫（1020）7/1~7/5 每天買賣台積電多少張」（分點統計）
- 「台積電跟加權指數現在多少」（即時快照）
- 「下載 10/16 全市場分 K 整日檔，給我台積電的部分」（整日檔，Sponsor Pro）

完整範例見 [`knowledge/examples.md`](knowledge/examples.md)。

## 倉庫結構

```
FinMind-MCP/
├── src/finmind_mcp/      # MCP server source
├── tests/                # pytest 單元測試（全 mock）
├── smoke.py              # stdio smoke test
├── knowledge/            # SSOT markdown（dataset、行為規則、錯誤腳本、Q&A）
├── chatgpt/              # Custom GPT artifacts（OpenAPI + build script）
├── install/              # 各 host 安裝指引
├── mcpb/                 # Claude Desktop 擴充套件（.mcpb）的 manifest 與進入點
└── docs/                 # 設計 spec 與實作 plan
```

## 開發

```bash
uv venv --python 3.10
source .venv/bin/activate
uv pip install -e ".[dev]"   # dev extra 含 respx 與 pyarrow
uv run pytest -v
FINMIND_TOKEN=... uv run python regression/runner.py   # 打 live API 的契約測試
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

PyPI 發佈成功後，同一個 workflow 會打包 Claude Desktop 擴充套件 `finmind.mcpb`（`finmind-mcp` 釘在同一版本）並附加到該 tag 的 GitHub Release，下載連結 `releases/latest/download/finmind.mcpb` 會自動指向最新版。本機打包測試：

```bash
python3 scripts/build_mcpb.py --dev   # 需要 Node.js；--dev 用本機原始碼
python3 scripts/check_mcpb.py         # 模擬 Claude Desktop 解壓、啟動、MCP 握手
```

新增 tool 時記得同步 `mcpb/manifest.json` 的 `tools`（`tests/test_mcpb.py` 會擋）。

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
