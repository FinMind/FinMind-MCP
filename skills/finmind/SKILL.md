---
name: finmind
description: Use when the user asks about Taiwan or global financial data — 股價/開高低收, 月營收, 三大法人買賣超, 融資融券, 股利/配息, 本益比 PER, 期貨/選擇權, 匯率, 央行利率, 美股 — or to resolve a Taiwan stock 名稱↔代號. Pairs with the bundled FinMind MCP server.
---

# FinMind 金融資料助手

用本 plugin 內含的 **`finmind` MCP server tools** 回答台股／全球金融資料問題，
**不要自己組 HTTP 請求**。可用 tools：

- `query_dataset` — 通用查詢（`dataset` + `data_id` + `start_date`/`end_date`）
- `get_stock_info` — 台股代號／中文名／產業查詢（TaiwanStockInfo）
- `list_datasets` — 列出所有可用 dataset；不確定用哪個時先查
- `query_trading_daily_report` — 券商分點進出（Sponsor 等級，必填 `data_id` + 單日 `date`）

需要 `FINMIND_TOKEN`（會員中心 <https://finmindtrade.com/analysis/#/account/user> 取得）。
未設定或 401 時，引導使用者去該頁取得 Token 並設成環境變數。

## 流程

1. 解析意圖 → 對到 dataset（見下表）；不確定就先呼叫 `list_datasets`。
2. 使用者給公司名而非代號 → 先 `get_stock_info` 轉成代號。
3. 日期規則：「最近一週」= 今天−7 天含當日；「今年」= 當年 1/1 至今日；沒指定預設近三個月。
4. 呼叫 `query_dataset`，結果整理成 markdown 表格；時間序列／比較再加圖。
5. 多步驟問題（比較多檔、篩選）連續呼叫、合併後再分析。

## 常見意圖 → dataset

| 意圖 | dataset |
|---|---|
| 股價、開高低收、成交量 | `TaiwanStockPrice` |
| 還原股價（除權息調整）| `TaiwanStockPriceAdj` |
| 本益比 / 股價淨值比 | `TaiwanStockPER` |
| 月營收 | `TaiwanStockMonthRevenue` |
| 損益表 / EPS / 財報 | `TaiwanStockFinancialStatements` |
| 股利 / 配息 | `TaiwanStockDividend` |
| 三大法人買賣超 | `TaiwanStockInstitutionalInvestorsBuySell` |
| 融資融券 | `TaiwanStockMarginPurchaseShortSale` |
| 外資持股比例 | `TaiwanStockShareholding` |
| 期貨日成交 | `TaiwanFuturesDaily`（台指期 `data_id=TX`，**不是 TXF**）|
| 選擇權日成交 | `TaiwanOptionDaily` |
| 匯率 | `TaiwanExchangeRate`（美元 `data_id=USD`）|
| 央行利率 | `InterestRate`（**必填 `data_id`**，美國=`FED`、歐洲=`ECB`、日本=`BOJ`）|
| 美股股價 | `USStockPrice` |
| 查股票代號 / 中文名 | `get_stock_info`（或 `TaiwanStockInfo`）|

常用代號：2330 台積電、2317 鴻海、2454 聯發科、2882 國泰金、0050 元大台灣50。
完整 dataset 清單與欄位細節：用 `list_datasets`，或讀 MCP resource（knowledge `datasets.md`）。

## 畫圖

時間序列 / 比較 / 分布適合配圖。圖表的 **title、軸標籤、圖例一律用英文**，避免中文字型缺字。

## 不做

個人化投資建議、預測未來價格 — 只提供資料與客觀整理。
