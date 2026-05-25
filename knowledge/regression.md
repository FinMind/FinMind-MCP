# FinMind Plugin — Regression 題庫

> 兩條 distribution（ChatGPT Custom GPT / MCP server）上線前必須跑通。
> 每題期望輸出可機器檢查（tool name + params + response shape）。
> 今日日期 = **2026-05-17**，用來解析「最近一週」、「今年」等相對日期。
> 日期允許 ±1 day 容忍度（trading day rounding / time zone）。

---

### R1: 個股最近一週股價

**Query:** 「台積電最近一週的股價」

**Expected tool call:**
- tool: `query_dataset`
- params:
  - `dataset`: `TaiwanStockPrice`
  - `data_id`: `2330`
  - `start_date`: `2026-05-10` (±1 day allowed)
  - `end_date`: optional, may be `2026-05-17` or omitted

**Pass criteria:**
- Tool called: `query_dataset` ✓
- Param `dataset` == `TaiwanStockPrice` ✓
- Param `data_id` == `2330` ✓
- Param `start_date` within `[2026-05-09, 2026-05-11]` ✓
- Response contains markdown table with columns: `date`, `open`, `max`, `min`, `close` ✓
- Table has ≥5 rows ✓

---

### R2: 今年每月營收

**Query:** 「台積電今年每月營收」

**Expected tool call:**
- tool: `query_dataset`
- params:
  - `dataset`: `TaiwanStockMonthRevenue`
  - `data_id`: `2330`
  - `start_date`: `2026-01-01` (±1 day allowed)
  - `end_date`: optional

**Pass criteria:**
- Tool called: `query_dataset` ✓
- Param `dataset` == `TaiwanStockMonthRevenue` ✓
- Param `data_id` == `2330` ✓
- Param `start_date` within `[2025-12-31, 2026-01-02]` ✓
- Response markdown table contains columns: `date`, `revenue` ✓
- Table has ≥3 rows (3+ months of 2026) ✓

---

### R3: 季報財務數據

**Query:** 「鴻海最近一年的財報」

**Expected tool call:**
- tool: `query_dataset`
- params:
  - `dataset`: `TaiwanStockFinancialStatements`
  - `data_id`: `2317`
  - `start_date`: `2025-05-17` (±1 day allowed)
  - `end_date`: optional

**Pass criteria:**
- Tool called: `query_dataset` ✓
- Param `dataset` == `TaiwanStockFinancialStatements` ✓
- Param `data_id` == `2317` ✓
- Param `start_date` within `[2025-05-16, 2025-05-18]` ✓
- Response markdown table contains columns: `date`, `type`, `value` ✓
- Table has ≥3 rows ✓

---

### R4: 三大法人買賣超

**Query:** 「2330 三大法人近一週買賣超」

**Expected tool call:**
- tool: `query_dataset`
- params:
  - `dataset`: `TaiwanStockInstitutionalInvestorsBuySell`
  - `data_id`: `2330`
  - `start_date`: `2026-05-10` (±1 day allowed)
  - `end_date`: optional

**Pass criteria:**
- Tool called: `query_dataset` ✓
- Param `dataset` == `TaiwanStockInstitutionalInvestorsBuySell` ✓
- Param `data_id` == `2330` ✓
- Param `start_date` within `[2026-05-09, 2026-05-11]` ✓
- Response markdown table contains columns: `date`, `name`, `buy`, `sell` ✓
- Table has ≥3 rows ✓

---

### R5: 股利政策查詢

**Query:** 「台積電過去三年股利」

**Expected tool call:**
- tool: `query_dataset`
- params:
  - `dataset`: `TaiwanStockDividend`
  - `data_id`: `2330`
  - `start_date`: `2023-05-17` (±1 day allowed) 或 `2023-01-01`（year-bucket 也接受）
  - `end_date`: optional

**Pass criteria:**
- Tool called: `query_dataset` ✓
- Param `dataset` == `TaiwanStockDividend` ✓
- Param `data_id` == `2330` ✓
- Param `start_date` within `[2023-01-01, 2023-05-18]` ✓
- Response markdown table contains columns: `date`, `CashEarningsDistribution` ✓
- Table has ≥3 rows ✓

---

### R6: 期貨日成交

**Query:** 「台指期（TX）近一週收盤」

**Expected tool call:**
- tool: `query_dataset`
- params:
  - `dataset`: `TaiwanFuturesDaily`
  - `data_id`: `TX`（台指期代號為 `TX`，非 `TXF`）
  - `start_date`: `2026-05-10` (±1 day allowed)
  - `end_date`: optional

**Pass criteria:**
- Tool called: `query_dataset` ✓
- Param `dataset` == `TaiwanFuturesDaily` ✓
- Param `data_id` == `TX` ✓
- Param `start_date` within `[2026-05-09, 2026-05-11]` ✓
- Response markdown table contains columns: `date`, `open`, `max`, `min`, `close` ✓
- Table has ≥3 rows ✓

---

### R7: 匯率走勢

**Query:** 「美元對台幣最近半年匯率」

**Expected tool call:**
- tool: `query_dataset`
- params:
  - `dataset`: `TaiwanExchangeRate`
  - `data_id`: `USD`
  - `start_date`: `2025-11-17` (±1 day allowed)
  - `end_date`: optional

**Pass criteria:**
- Tool called: `query_dataset` ✓
- Param `dataset` == `TaiwanExchangeRate` ✓
- Param `data_id` == `USD` ✓
- Param `start_date` within `[2025-11-16, 2025-11-18]` ✓
- Response markdown table contains columns: `date`, `spot_buy` 或 `cash_buy` ✓
- Table has ≥10 rows (近半年至少 100 個交易日，輸出可截斷) ✓

---

### R8: 美國利率

**Query:** 「美國基準利率最近一年」

**Expected tool call:**
- tool: `query_dataset`
- params:
  - `dataset`: `InterestRate`
  - `data_id`: `FED`（美國 → `FED`；此 dataset **必填** data_id，央行代號如 `FED`/`ECB`/`BOJ`）
  - `start_date`: `2025-05-17` (±1 day allowed)
  - `end_date`: optional

**Pass criteria:**
- Tool called: `query_dataset` ✓
- Param `dataset` == `InterestRate` ✓
- Param `data_id` == `FED` ✓
- Param `start_date` within `[2025-05-16, 2025-05-18]` ✓
- Response markdown table contains columns: `date`, `interest_rate` ✓
- Table has ≥3 rows ✓

---

### R9: 畫圖請求（K 線圖）

**Query:** 「畫一張台積電近三個月 K 線圖」

**Expected tool call:**
- tool: `query_dataset`
- params:
  - `dataset`: `TaiwanStockPrice`
  - `data_id`: `2330`
  - `start_date`: `2026-02-17` (±1 day allowed)
  - `end_date`: optional
- 接著呼叫平台 code 環境（ChatGPT Code Interpreter / Claude analysis）執行 mplfinance / matplotlib

**Pass criteria:**
- Tool called: `query_dataset` ✓
- Param `dataset` == `TaiwanStockPrice` ✓
- Param `data_id` == `2330` ✓
- Param `start_date` within `[2026-02-16, 2026-02-18]` ✓
- Response 包含圖表敘述（檔名、圖類型 candle/K線、X/Y 軸）或實際 inline 圖檔 ✓
- 回應中不是只給表格、必須提到「K 線」或「圖」字樣 ✓

---

### R10: 跨股比較（多檔股票）

**Query:** 「比較台積電和聯發科今年股價表現」

**Expected tool call:** （兩次連續呼叫）
- Call 1:
  - tool: `query_dataset`
  - params: `dataset=TaiwanStockPrice`, `data_id=2330`, `start_date=2026-01-01` (±1 day allowed)
- Call 2:
  - tool: `query_dataset`
  - params: `dataset=TaiwanStockPrice`, `data_id=2454`, `start_date=2026-01-01` (±1 day allowed)

**Pass criteria:**
- Tool `query_dataset` 被呼叫 ≥2 次 ✓
- 兩次 `dataset` 皆 == `TaiwanStockPrice` ✓
- `data_id` 集合 == `{"2330", "2454"}` ✓
- 兩次 `start_date` 皆 within `[2025-12-31, 2026-01-02]` ✓
- 回應 markdown 表格同時包含 2330 與 2454 的 close 資料（合併欄位或併排兩表）✓
- 回應有比較性敘述（例如「漲幅」、「表現」、百分比）✓

---

### R11: 本益比

**Query:** 「台積電目前的本益比」

**Expected tool call:**
- tool: `query_dataset`
- params:
  - `dataset`: `TaiwanStockPER`
  - `data_id`: `2330`
  - `start_date`: 近期日期，例如 `2026-05-10` (±7 day allowed，因為「目前」可以是最近一週)
  - `end_date`: optional

**Pass criteria:**
- Tool called: `query_dataset` ✓
- Param `dataset` == `TaiwanStockPER` ✓
- Param `data_id` == `2330` ✓
- Param `start_date` within `[2026-05-03, 2026-05-17]` ✓
- Response markdown table contains columns: `date`, `PER` ✓
- Table has ≥1 row ✓

---

### R12: 股票代號查詢

**Query:** 「台積電的股票代號是多少」

**Expected tool call:**
- tool: `get_stock_info` 或 `query_dataset` with `dataset=TaiwanStockInfo`
- params:
  - `dataset`: `TaiwanStockInfo`（若使用 query_dataset）
  - `data_id`: optional `2330` 或不填整張表

**Pass criteria:**
- Tool called: `get_stock_info` 或 `query_dataset` ✓
- 若 `query_dataset`，`dataset` == `TaiwanStockInfo` ✓
- Response 文字內容包含「2330」字串 ✓
- Response 文字內容包含「台積電」字串 ✓
