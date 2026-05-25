# FinMind Plugin Spec（ChatGPT + MCP）

- Status: Draft
- Owner: linsamtw
- Last updated: 2026-05-17
- Supersedes: `specs/custom-gpt.md`

## 1. 背景與目標

FinMind 目前在 Claude Code / Cursor / Windsurf / Gemini CLI / Codex 已透過
本機 agent skill（`finmind.md` / `AGENTS.md`）支援自然語言查詢。但這套機制：

- 只在「有 CLI / IDE」的場景生效
- 在 ChatGPT、Claude.ai web、Gemini App 上完全無法用
- 每個工具要各自維護 skill 檔，內容容易漂移

本 spec 定義 FinMind 官方 **Plugin**，以「**一份知識包 + 兩條 distribution**」覆蓋三大平台：

| Distribution | 涵蓋平台 | 機制 |
|---|---|---|
| A. ChatGPT Custom GPT | ChatGPT Plus / Pro / Team | OpenAPI Action |
| B. MCP Server | Claude.ai / Claude Code / Claude Desktop / Gemini CLI / Cursor / Windsurf / 其他 MCP host | Model Context Protocol |

### 目標
1. ChatGPT 用戶可在 GPT Store 搜到 "FinMind" 直接使用
2. Claude / Gemini / Cursor / Windsurf 用戶可一鍵安裝 FinMind MCP server 使用
3. 兩條 distribution 的回應品質、dataset 覆蓋、錯誤行為**一致**（來自同一份知識包）
4. 既有 `finmind.md` skill 不受影響、繼續維護

### 非目標
- 不做 ChatGPT Free 用戶支援（GPT Store 限付費版）
- 不取代既有 `finmind.md` / `AGENTS.md`
- 不在 plugin 內處理付費 / 訂閱
- MVP 不做 75+ dataset 全覆蓋，先 ~20 個

## 2. 使用者故事

| # | 角色 / 平台 | 我想要 | 為了 |
|---|---|---|---|
| US-1 | ChatGPT 散戶 | 問「台積電最近一個月股價」 | 不用自己組 API |
| US-2 | ChatGPT 散戶 | 請 GPT 畫「2330 近三個月 K 線圖」 | 快速看走勢 |
| US-3 | Claude.ai 研究者 | 在 Claude integrations 一鍵啟用 FinMind 比較兩檔股票 | 不用切到 IDE |
| US-4 | Cursor / Windsurf 開發者 | 在編輯器內查資料、寫策略 code | 開發策略不切視窗 |
| US-5 | Gemini CLI 用戶 | 在終端機問問題、拿表格 | 不裝其它 client |
| US-6 | 新用戶（任一平台） | 被引導去 finmindtrade.com 取得 Token | 降低上手門檻 |
| US-7 | Token 用完用戶 | 收到「請求數已達上限」並指引升級 | 不會卡住 |

## 3. 共用知識包（Single Source of Truth）

兩條 distribution 都從這份知識包生內容，不允許平台特定的 dataset 描述或錯誤腳本。

### 3.1 知識包檔案

放在 `knowledge/`：

| 檔案 | 內容 | 用途 |
|---|---|---|
| `datasets.md` | MVP ~20 個 dataset 的欄位 / 必填參數 / 範例 | GPT instructions、MCP tool description |
| `datasets-full.md` | 75+ dataset 全列表（phase 2）| Knowledge file / MCP resource |
| `instructions.md` | 角色定位、語言、回應格式、拒答規則 | GPT instructions / MCP server prompt |
| `examples.md` | 範例問答對（涵蓋每個 dataset 至少 1 題）| Few-shot / regression |
| `errors.md` | 401 / 402 / 空資料 / rate limit 錯誤回應腳本 | 兩端共用 |
| `token-guide.md` | Token 取得步驟（含截圖路徑）| 兩端首次互動時用 |
| `regression.md` | 10 題以上的 regression 題庫 + 期望輸出 | 上線前驗證 |

### 3.2 支援的 dataset（MVP）

依重要性，MVP 至少涵蓋（兩條 distribution 同步）：

**台股**
- `TaiwanStockPrice` — 個股日成交
- `TaiwanStockMonthRevenue` — 月營收
- `TaiwanStockFinancialStatements` — 三大財報
- `TaiwanStockDividend` / `TaiwanStockDividendResult` — 股利
- `TaiwanStockInstitutionalInvestorsBuySell` — 三大法人
- `TaiwanStockShareholding` — 外資持股
- `TaiwanStockMarginPurchaseShortSale` — 融資融券
- `TaiwanStockPER` — 本益比

**期權**
- `TaiwanFuturesDaily` / `TaiwanOptionDaily` — 期權日成交
- `TaiwanFuturesInstitutionalInvestors` — 期貨三大法人

**總經 / 全球**
- `TaiwanExchangeRate` — 匯率
- `InterestRate` — 美國利率
- `GoldPrice` — 黃金
- `USStockPrice` — 美股

**索引 / 代號**
- `TaiwanStockInfo` — 股票清單

剩餘 dataset 在 phase 2 透過 `datasets-full.md` 動態載入。

### 3.3 共用行為規則

兩條 distribution 必須一致實現：

- **Token 處理**：未設定 / 401 時用 `token-guide.md` 引導
- **意圖解析**：「最近一週」、「今年」轉成 `start_date` / `end_date`（含當日）
- **Dataset 選擇**：根據問句選對 dataset，不確定時列選項給用戶
- **資料呈現**：預設 markdown 表格；用戶說「畫圖」改用平台 code 環境
- **錯誤處理**：依 `errors.md` 腳本
  - 402 Payment Required → 提示升級
  - 401 Unauthorized → 提示 Token 無效
  - 空資料 → 確認日期 / 股票代號
- **資料量保護**：預估 > ~500 列時先給摘要、提議用 code 環境處理
- **拒答**：個人投資建議、預測未來價格

## 4. Distribution A：ChatGPT Custom GPT

### 4.1 架構

```
ChatGPT 用戶
    │  自然語言
    ▼
Custom GPT (instructions = 知識包編譯結果)
    │  Function call (OpenAPI Action)
    ▼
api.finmindtrade.com
    │  JSON
    ▼
Custom GPT → markdown / Code Interpreter 畫圖
```

### 4.2 Actions schema

只暴露最少 endpoint，避開 ChatGPT 8K token OpenAPI 上限。

| Path | Method | 用途 |
|---|---|---|
| `/api/v4/data` | GET | 通用資料查詢 |
| `/api/v4/datalist` | GET | 列可用 dataset |
| `/api/v4/taiwan_stock_trading_daily_report` | GET | dedicated endpoint dataset（如必要）|

Auth：Bearer token（HTTP `Authorization: Bearer <token>` header）。

完整 schema：`chatgpt/openapi.yaml`。

### 4.3 Instructions

從知識包**編譯**而成，不手寫第二份：

```
chatgpt/instructions.md  ← build 產出
    ├── knowledge/instructions.md
    ├── knowledge/datasets.md（精簡版）
    ├── knowledge/errors.md
    └── knowledge/token-guide.md
```

Build 指令：`make plugin-chatgpt`（後續工作項）。

### 4.4 Knowledge files（GPT 上傳）

- `datasets-full.md`：phase 2 上傳
- `examples.md`：MVP 可上傳

### 4.5 Code Interpreter

啟用，用於：K 線圖（mplfinance）、折線圖、報酬率計算、大量資料 pandas。

### 4.6 Web Browsing

**關閉**。所有資料只從 Action 拿。

### 4.7 公開設定

- Visibility: Public（先 "Anyone with the link"，審核通過後 GPT Store）
- Privacy policy URL: `https://finmindtrade.com/analysis/#/privacy`（**需確認頁面存在**）
- Logo: FinMind 既有 logo（512x512）
- Conversation starters：
  - 「台積電最近一個月股價」
  - 「2330 三大法人近一週買賣」
  - 「台積電今年每月營收」
  - 「美元對台幣匯率近半年走勢圖」

## 5. Distribution B：MCP Server

### 5.1 架構

```
Claude.ai / Code / Desktop          Gemini CLI / Cursor / Windsurf
                        \          /
                         ▼        ▼
                   FinMind MCP Server
                   ├── stdio mode（本機安裝）
                   └── HTTP/SSE mode（remote, 官方 host）
                              │
                              ▼
                   api.finmindtrade.com
```

### 5.2 部署模式

| 模式 | Host | 適用 |
|---|---|---|
| **Remote (官方)** | `mcp.finmindtrade.com` | Claude.ai integrations、新手用戶 |
| **Local stdio** | 用戶端 `npx finmind-mcp` / `uvx finmind-mcp` | Cursor / Windsurf / Claude Desktop / Gemini CLI |

兩者共用同一份 server code，差別只在 transport。

### 5.3 Tools

對外暴露的 MCP tools（schema 從知識包生）：

| Tool | 描述 | 對應 endpoint |
|---|---|---|
| `query_dataset` | 通用查詢，必填 `dataset` / `data_id` / `start_date` | `/api/v4/data` |
| `list_datasets` | 列可用 dataset 與層級 | `/api/v4/datalist` |
| `query_trading_daily_report` | dedicated dataset，必填 `data_id` + 單日 `date` | `/api/v4/taiwan_stock_trading_daily_report` |
| `get_stock_info` | 股票代號 ↔ 中文名查詢 | `/api/v4/data?dataset=TaiwanStockInfo` |

每個 tool 的 description 從 `knowledge/datasets.md` 對應段落讀。

### 5.4 Resources

MCP `resources` 暴露：

- `finmind://datasets` → 完整 dataset 清單（給 host 端做 RAG）
- `finmind://examples` → 範例問答對

### 5.5 Auth

- **Local stdio**：環境變數 `FINMIND_TOKEN`（安裝時引導設）
- **Remote HTTP**：MCP OAuth flow（或 header-based API key）

Token 未設 / 401 時 server 回 MCP error，host 端按 `errors.md` 顯示引導。

### 5.6 安裝引導

每個 host 一段 README 區塊，由 build script 從 `knowledge/install/*.md` 生：

- `install/claude-ai.md` — Claude.ai → Settings → Integrations → Add MCP server
- `install/claude-desktop.md` — `claude_desktop_config.json` 範例
- `install/claude-code.md` — `claude mcp add` 指令
- `install/cursor.md` — `.cursor/mcp.json` 範例
- `install/windsurf.md` — 設定路徑
- `install/gemini-cli.md` — `gemini mcp add` 指令

### 5.7 倉庫與發佈

- 程式碼：`src/finmind_mcp/ (+ tests/, smoke.py)`（Python，配合既有 FinMind SDK）
- 套件名：`finmind-mcp`（PyPI）/ `@finmind/mcp`（npm wrapper 給 stdio 用 npx）
- Remote host：`mcp.finmindtrade.com`（docker 部署，沿用既有 service repo traefik 路徑）

### 5.8 Claude Code `/plugin` 一鍵安裝（plugin marketplace）

讓使用者在 Claude Code 內 `/plugin` 直接裝，免手動編 `.mcp.json`。

**關鍵觀念：`/plugin` refer 的是 GitHub repo，不是 PyPI。** Claude Code 不瀏覽 PyPI；它 clone 本 repo、讀 `.claude-plugin/` 下的 manifest。PyPI 只是「執行時 `uvx` 抓套件來跑」的地方（在使用者機器上、MCP server 啟動那一刻才碰）。

**repo root 需新增兩檔：**

`.claude-plugin/plugin.json`（plugin 定義，內含 MCP server）：

```json
{
  "name": "finmind-mcp",
  "description": "FinMind 台股／期權／總經／全球金融資料 MCP server",
  "version": "0.1.0",
  "author": { "name": "FinMind", "email": "finmind.tw@gmail.com" },
  "homepage": "https://github.com/FinMind/FinMind-MCP",
  "license": "Apache-2.0",
  "mcpServers": {
    "finmind": {
      "command": "uvx",
      "args": ["finmind-mcp"],
      "env": { "FINMIND_TOKEN": "${FINMIND_TOKEN}" }
    }
  }
}
```

`.claude-plugin/marketplace.json`（catalog，指回同 repo）：

```json
{
  "name": "finmind-official",
  "owner": { "name": "FinMind", "email": "finmind.tw@gmail.com" },
  "plugins": [
    { "name": "finmind-mcp",
      "source": { "source": "github", "repo": "FinMind/FinMind-MCP" },
      "description": "FinMind financial data MCP server" }
  ]
}
```

**使用者指令：**

```
/plugin marketplace add FinMind/FinMind-MCP
/plugin install finmind-mcp@finmind-official
/reload-plugins      # /mcp 看 server 連線狀態
```

**Token：** `/plugin` 不會於安裝時 prompt；`${FINMIND_TOKEN}` 讀使用者環境變數，需啟動 Claude 前 `export FINMIND_TOKEN=...`（與 GitHub/Jira 等需 token 的 MCP 一致）。README 安裝段須寫明。

**套件來源：** `finmind-mcp` 已發佈於 PyPI，manifest 用 `args: ["finmind-mcp"]`（`uvx` 從 PyPI 取得穩定版）。

> 若要測尚未發版的開發版，可暫時改 `args: ["--from", "git+https://github.com/FinMind/FinMind-MCP", "finmind-mcp"]` 直接跑 GitHub HEAD。

**兩個前提（缺一不可）：**
1. GitHub repo 要 commit + push `.claude-plugin/`（+ 套件原始碼）→ `/plugin` 才讀得到 catalog。
2. 套件取得來源就緒：PyPI 發布 `finmind-mcp`，或用上方 `git+https://...` 版（免 PyPI）。

> 只發 PyPI 但 GitHub 沒 `.claude-plugin/` → `/plugin` 找不到 plugin；只放 manifest 但無套件來源 → 裝得起來但 server 起不來。

### 5.9 Gemini CLI extension 一鍵安裝

Gemini CLI 的對應物是 **extension**（git 安裝、可內含 MCP server），等同 Claude 的 plugin。repo root 放 `gemini-extension.json`：

```json
{
  "name": "finmind-mcp",
  "version": "0.1.0",
  "mcpServers": {
    "finmind": {
      "command": "uvx",
      "args": ["finmind-mcp"],
      "env": { "FINMIND_TOKEN": "${FINMIND_TOKEN}" }
    }
  },
  "contextFileName": "GEMINI.md"
}
```

使用者：

```
gemini extensions install https://github.com/FinMind/FinMind-MCP
```

- 同 Claude：extension manifest 來自 GitHub repo，但 `uvx finmind-mcp` 從 PyPI 抓套件（開發版可用 `--from git+https://github.com/FinMind/FinMind-MCP`）。
- Token 一樣走 `${FINMIND_TOKEN}` 環境變數。
- 基本路徑（不做 extension）：`gemini mcp add`（見 5.6 `install/gemini-cli.md`）。

### 5.10 各 host 一鍵安裝對照

| Host | 一鍵方式 | 載體 | MCP 形態 | Token |
|---|---|---|---|---|
| Claude Code | `/plugin marketplace add` + install | plugin（`.claude-plugin/`） | stdio（uvx） | env `FINMIND_TOKEN` |
| Gemini CLI | `gemini extensions install <github>` | extension（`gemini-extension.json`） | stdio（uvx） | env `FINMIND_TOKEN` |
| ChatGPT | 發佈 **Custom GPT**（§4），非 MCP | Custom GPT（Actions + 知識包） | 無（用 OpenAPI Action） | Action 內帶 |

**ChatGPT 補充：** 消費端 ChatGPT 的「安裝」＝打開已發佈的 Custom GPT（GPT Store / 連結），用 OpenAPI Action + 知識包，**不是 MCP** —— FinMind 的 stdio `finmind-mcp` 套件對 ChatGPT 不適用。ChatGPT 若要接 MCP，只吃 **remote（HTTPS）MCP**，且需在 **Developer Mode / Apps**（付費方案 Plus/Pro/Team/Enterprise；Free 不支援）；要進 app catalog 還需 Apps SDK + 審核。真要做就接已規劃的 remote 端點 `mcp.finmindtrade.com`（§5.2），而非 stdio 套件。

## 6. 安全與隱私

- **Token**：兩條 distribution 都不入訓練資料（Custom GPT Actions / MCP env），instructions 中不含任何 Token
- **後端**：FinMind backend 只看到 dataset / 參數，不知道來源平台或用戶身份
- **Rate limit**：沿用 FinMind 既有 per-token rate limit
- **濫用防範**：`instructions.md` 內建拒答規則（投資建議、價格預測）
- **MCP remote 特有**：HTTP/SSE 端點需有 access log、abuse detection（沿用既有 traefik middleware）

## 7. 風險與未解問題

| # | 風險 / 問題 | 影響 | 對策 |
|---|---|---|---|
| R-1 | OpenAI GPT Store 審核失敗 | ChatGPT 線無法公開 | 先 "Anyone with link" 推廣 |
| R-2 | MCP 規格仍在演進，host 實作差異 | MCP 線部分 host 行為怪 | 鎖定主要 host（Claude / Gemini CLI / Cursor）測試 |
| R-3 | Token 設定步驟卡新用戶 | 流失 | 兩條 distribution 都打磨首次互動引導 |
| R-4 | Dataset 增加要重發 GPT（ChatGPT 線）| 維運成本 | MCP 線可熱更新；ChatGPT phase 2 用 Knowledge file |
| R-5 | 用戶要求預測 / 投資建議 | 法律 | Instructions 拒答並推回教育內容 |
| R-6 | ChatGPT / Claude / Gemini 模型升級導致行為飄移 | 品質 | regression 題庫每月跑兩條 distribution |
| R-7 | Remote MCP host 流量 / 成本 | 營運 | 監控 + per-token rate limit + 可改推 local stdio |
| Q-1 | builder 帳號歸屬（FinMind 公司 vs 創辦人）| 帳號 | 待決定（ChatGPT / OpenAI dev account / PyPI / npm 都要決）|
| Q-2 | 免費 vs sponsor dataset 引導 | 商業 | `instructions.md` 補「此 dataset 需 sponsor」提示 |

## 8. 驗收標準

MVP 上線前必須通過：

### 共用
- [ ] `knowledge/` 目錄齊全（datasets / instructions / errors / examples / token-guide / regression）
- [ ] 10 題 regression 在兩條 distribution 都過（含股價、營收、財報、三大法人、股利、期權、匯率、利率、畫圖、跨股比較）
- [ ] Token 未設定引導訊息清楚
- [ ] 401 / 402 / 空資料三種錯誤情境正確
- [ ] AgentSkill.md 新增 ChatGPT + MCP 兩個 tab，含安裝步驟與截圖

### ChatGPT 線
- [ ] `openapi.yaml` 通過 OpenAI Action 匯入
- [ ] Code Interpreter 畫出 K 線、折線各一張可下載
- [ ] Privacy policy URL 可開啟
- [ ] Logo / 名稱 / 描述符合 GPT Store 規範

### MCP 線
- [ ] Claude.ai integrations 可加入 remote server 並查詢成功
- [ ] Claude Desktop / Claude Code / Cursor / Windsurf / Gemini CLI 各跑通至少 3 題
- [ ] stdio 模式 `uvx finmind-mcp` 一行裝起
- [ ] Remote `mcp.finmindtrade.com` 健康檢查通過、有 access log

### 後端
- [ ] FinMind access log 確認兩條 distribution 流量歸屬正確
- [ ] Per-token rate limit 正常運作

## 9. 里程碑

| 階段 | 產出 | 預估 |
|---|---|---|
| M1 — Spec 定案 | 本文件 + 利害關係人 review | 0.5d |
| M2 — 知識包 | `knowledge/*` 全部 | 1d |
| M3a — ChatGPT 線 | `openapi.yaml` + build script + Custom GPT 內部測試 | 1d |
| M3b — MCP server | `src/finmind_mcp/ (+ tests/, smoke.py)` server code + local stdio 可跑 | 1.5d |
| M4 — MCP remote 部署 | `mcp.finmindtrade.com` 上線、Claude.ai 可連 | 0.5d |
| M5 — Regression 雙線通過 | 10 題在兩條 distribution 過 | 0.5d |
| M6 — 文件 + 上架 | AgentSkill.md 更新、PyPI / npm 發佈、GPT Store submit | 1d |

**工作天合計：6d**（不含 GPT Store 審核 1~3d wall clock）

> M3a 與 M3b 可並行（不同檔案），實際 wall clock 可壓到 ~5d。

## 10. Phase 2（MVP 後）

- 補齊剩餘 dataset 至 75+ 全覆蓋（兩條都透過 `datasets-full.md`）
- 多語系：英文版 instructions
- Backtesting helper（內建 pandas / mplfinance snippet）
- Sponsor 方案聯動：Token 為 sponsor 時自動啟用進階 dataset
- MCP server 加 `tools/prompts`（pre-built 策略模板）

## 11. 相關文件

- 既有 agent skill：`FinMind/.claude/commands/finmind.md`
- 公開教學頁：`FinMind-Doc/docs/tutor/AgentSkill.md`
- FinMind API reference：`FinMind-Doc/docs/`
- OpenAI Actions：https://platform.openai.com/docs/actions
- Model Context Protocol：https://modelcontextprotocol.io
- Claude.ai Integrations：https://docs.anthropic.com/en/docs/claude-code/mcp
- Gemini CLI MCP：https://github.com/google-gemini/gemini-cli
