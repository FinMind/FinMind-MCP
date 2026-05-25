# FinMind Plugin — 範例問答對

> 涵蓋 MVP 17 個 dataset 的 few-shot 範例。
> 今日日期以 **2026-05-17** 為基準計算相對日期（例如「最近一週」= 2026-05-10 ~ 2026-05-17 含當日）。
> 所有回應預設繁中、預設 markdown 表格；用戶說「畫圖」/「圖表」時改用平台 code 環境。

---

### Q1: 個股近一週股價（TaiwanStockPrice）

**User:** 「台積電最近一週的股價」

**Tool call:**
- `query_dataset(dataset="TaiwanStockPrice", data_id="2330", start_date="2026-05-10", end_date="2026-05-17")`

**Response:**
> 台積電 (2330) 2026-05-10 ~ 2026-05-17 股價如下：
>
> | date | open | max | min | close | Trading_Volume |
> |------|------|-----|-----|-------|----------------|
> | 2026-05-12 | 985 | 992 | 980 | 990 | 25,400,000 |
> | 2026-05-13 | 990 | 998 | 988 | 995 | 22,100,000 |
> | 2026-05-14 | 995 | 1002 | 993 | 1000 | 28,300,000 |
>
> 一週累積上漲約 1.5%，量能溫和放大。

---

### Q2: 今年每月營收（TaiwanStockMonthRevenue）

**User:** 「台積電今年每月營收」

**Tool call:**
- `query_dataset(dataset="TaiwanStockMonthRevenue", data_id="2330", start_date="2026-01-01", end_date="2026-05-17")`

**Response:**
> 台積電 (2330) 2026 年至今月營收（單位：新台幣千元）：
>
> | date | revenue | revenue_year | revenue_month |
> |------|---------|--------------|---------------|
> | 2026-01-10 | 280,500,000 | 2026 | 1 |
> | 2026-02-10 | 265,300,000 | 2026 | 2 |
> | 2026-03-10 | 295,800,000 | 2026 | 3 |
>
> 1~3 月累計營收約 8,416 億，較去年同期成長約 28%。

---

### Q3: 近一年財報（TaiwanStockFinancialStatements）

**User:** 「鴻海最近一年的損益表」

**Tool call:**
- `query_dataset(dataset="TaiwanStockFinancialStatements", data_id="2317", start_date="2025-05-17", end_date="2026-05-17")`

**Response:**
> 鴻海 (2317) 最近一年季報摘要：
>
> | date | type | value |
> |------|------|-------|
> | 2025-06-30 | Revenue | 1,580,000,000 |
> | 2025-09-30 | EPS | 2.85 |
> | 2025-12-31 | GrossProfit | 95,200,000 |
>
> Q2~Q4 EPS 累計約 7.6 元，毛利率持續改善至 6.5% 左右。

---

### Q4: 股利政策（TaiwanStockDividend）

**User:** 「台積電過去三年的股利政策」

**Tool call:**
- `query_dataset(dataset="TaiwanStockDividend", data_id="2330", start_date="2023-01-01", end_date="2026-05-17")`

**Response:**
> 台積電 (2330) 2023~2025 股利政策：
>
> | date | CashEarningsDistribution | StockEarningsDistribution |
> |------|--------------------------|---------------------------|
> | 2024-06-13 | 13.5 | 0 |
> | 2024-09-12 | 14.0 | 0 |
> | 2025-06-12 | 14.5 | 0 |
>
> 近三年現金股利每股累計約 56 元，無配股。

---

### Q5: 除權息結果（TaiwanStockDividendResult）

**User:** 「2330 最近一次除權息填息了嗎」

**Tool call:**
- `query_dataset(dataset="TaiwanStockDividendResult", data_id="2330", start_date="2025-01-01", end_date="2026-05-17")`

**Response:**
> 台積電 (2330) 最近一次除權息結果：
>
> | date | before_price | after_price | stock_or_cache_dividend | max_price_today |
> |------|--------------|-------------|--------------------------|------------------|
> | 2025-09-12 | 1015 | 1001 | 14.0 | 1008 |
> | 2025-09-15 | 1001 | 1001 | 0 | 1010 |
> | 2025-09-22 | 1014 | 1014 | 0 | 1016 |
>
> 除息參考價 1001，於 2025-09-22 收盤 1014 完成填息（約 7 個交易日）。

---

### Q6: 三大法人買賣超（TaiwanStockInstitutionalInvestorsBuySell）

**User:** 「2330 三大法人近一週買賣超」

**Tool call:**
- `query_dataset(dataset="TaiwanStockInstitutionalInvestorsBuySell", data_id="2330", start_date="2026-05-10", end_date="2026-05-17")`

**Response:**
> 台積電 (2330) 2026-05-10 ~ 2026-05-17 三大法人買賣超（單位：股）：
>
> | date | name | buy | sell |
> |------|------|-----|------|
> | 2026-05-12 | Foreign_Investor | 18,500,000 | 12,300,000 |
> | 2026-05-13 | Investment_Trust | 1,200,000 | 800,000 |
> | 2026-05-14 | Dealer_self | 350,000 | 420,000 |
>
> 一週外資累計買超約 2,800 萬股，投信小幅買超，自營商小賣。

---

### Q7: 外資持股比例（TaiwanStockShareholding）

**User:** 「台積電外資持股比例現在多少」

**Tool call:**
- `query_dataset(dataset="TaiwanStockShareholding", data_id="2330", start_date="2026-04-17", end_date="2026-05-17")`

**Response:**
> 台積電 (2330) 近一個月外資持股比例：
>
> | date | ForeignInvestmentSharesRatio | ForeignInvestmentSharesRatio_Limit |
> |------|------------------------------|------------------------------------|
> | 2026-05-15 | 73.85 | 100.00 |
> | 2026-05-16 | 73.92 | 100.00 |
> | 2026-05-17 | 74.05 | 100.00 |
>
> 外資持股比例 74.05%，距上限 100% 仍有空間，近一月微升 0.6%。

---

### Q8: 融資融券餘額（TaiwanStockMarginPurchaseShortSale）

**User:** 「鴻海最近一週融資融券」

**Tool call:**
- `query_dataset(dataset="TaiwanStockMarginPurchaseShortSale", data_id="2317", start_date="2026-05-10", end_date="2026-05-17")`

**Response:**
> 鴻海 (2317) 2026-05-10 ~ 2026-05-17 融資融券餘額（單位：張）：
>
> | date | MarginPurchaseTodayBalance | ShortSaleTodayBalance |
> |------|------------------------------|------------------------|
> | 2026-05-12 | 185,300 | 12,400 |
> | 2026-05-13 | 186,100 | 12,150 |
> | 2026-05-14 | 184,800 | 12,820 |
>
> 融資餘額穩定在 18.5 萬張上下，券資比約 6.6%。

---

### Q9: 本益比查詢（TaiwanStockPER）

**User:** 「台積電的本益比」

**Tool call:**
- `query_dataset(dataset="TaiwanStockPER", data_id="2330", start_date="2026-05-10", end_date="2026-05-17")`

**Response:**
> 台積電 (2330) 近一週本益比與股價淨值比：
>
> | date | PER | PBR | dividend_yield |
> |------|-----|-----|----------------|
> | 2026-05-15 | 26.42 | 7.85 | 1.45 |
> | 2026-05-16 | 26.58 | 7.90 | 1.44 |
> | 2026-05-17 | 26.65 | 7.92 | 1.44 |
>
> 目前 PER 約 26.6，PBR 7.9，殖利率 1.44%。

---

### Q10: 期貨日成交（TaiwanFuturesDaily）

**User:** 「台指期近一週收盤」

**Tool call:**
- `query_dataset(dataset="TaiwanFuturesDaily", data_id="TX", start_date="2026-05-10", end_date="2026-05-17")`（台指期代號為 `TX`）

**Response:**
> 台指期貨 (TX) 近一週日成交：
>
> | date | futures_id | contract_date | open | max | min | close |
> |------|-----------|---------------|------|-----|-----|-------|
> | 2026-05-12 | TX | 202605 | 21500 | 21680 | 21450 | 21620 |
> | 2026-05-13 | TX | 202605 | 21620 | 21750 | 21580 | 21700 |
> | 2026-05-14 | TX | 202605 | 21700 | 21820 | 21650 | 21790 |
>
> 一週上漲 290 點（約 1.3%），多方氣勢延續。

---

### Q11: 選擇權日成交（TaiwanOptionDaily）

**User:** 「TXO 選擇權 21500 call 近一週價格」

**Tool call:**
- `query_dataset(dataset="TaiwanOptionDaily", data_id="TXO", start_date="2026-05-10", end_date="2026-05-17")`

**Response:**
> TXO 選擇權近一週成交資料（節錄 21500 Call）：
>
> | date | strike_price | call_put | open | close | volume |
> |------|--------------|----------|------|-------|--------|
> | 2026-05-12 | 21500 | call | 185 | 215 | 12,400 |
> | 2026-05-13 | 21500 | call | 215 | 245 | 14,800 |
> | 2026-05-14 | 21500 | call | 245 | 290 | 18,200 |
>
> 21500 Call 一週由 185 漲到 290，內含價值跟著加權升高。

---

### Q12: 期貨三大法人（TaiwanFuturesInstitutionalInvestors）

**User:** 「台指期三大法人近一週淨部位」

**Tool call:**
- `query_dataset(dataset="TaiwanFuturesInstitutionalInvestors", data_id="TX", start_date="2026-05-10", end_date="2026-05-17")`

**Response:**
> 台指期 (TX) 近一週三大法人淨部位（口數）：
>
> | date | name | long_open_interest_balance_volume | short_open_interest_balance_volume |
> |------|------|-----------------------------------|------------------------------------|
> | 2026-05-14 | 外資 | 58,200 | 32,500 |
> | 2026-05-14 | 投信 | 8,400 | 6,200 |
> | 2026-05-14 | 自營商 | 14,200 | 18,300 |
>
> 外資多單淨額約 25,700 口，自營偏空，投信小多。

---

### Q13: 匯率走勢（TaiwanExchangeRate）

**User:** 「美元對台幣最近半年走勢」

**Tool call:**
- `query_dataset(dataset="TaiwanExchangeRate", data_id="USD", start_date="2025-11-17", end_date="2026-05-17")`

**Response:**
> 美元對台幣 (USD) 近半年匯率（節錄）：
>
> | date | cash_buy | cash_sell | spot_buy | spot_sell |
> |------|----------|-----------|----------|-----------|
> | 2025-12-15 | 32.45 | 33.07 | 32.75 | 32.85 |
> | 2026-02-28 | 32.10 | 32.72 | 32.40 | 32.50 |
> | 2026-05-15 | 30.85 | 31.47 | 31.15 | 31.25 |
>
> 半年來新台幣升值約 4.9%，從 32.8 升到 31.2 附近。

---

### Q14: 美國利率（InterestRate）

**User:** 「美國基準利率最近一年變化」

**Tool call:**
- `query_dataset(dataset="InterestRate", data_id="FED", start_date="2025-05-17", end_date="2026-05-17")`（此 dataset 必填 `data_id`，美國 → `FED`）

**Response:**
> 美國聯邦基準利率 (Fed Funds Rate) 近一年變化：
>
> | country | date | interest_rate |
> |---------|------|---------------|
> | FED | 2025-06-18 | 4.50 |
> | FED | 2025-12-15 | 4.25 |
> | FED | 2026-05-01 | 3.75 |
>
> Fed 過去一年累計降息 150 bps，目前位於 3.75%。

---

### Q15: 黃金價格（GoldPrice）

**User:** 「黃金價格最近三個月走勢」

**Tool call:**
- `query_dataset(dataset="GoldPrice", start_date="2026-02-17", end_date="2026-05-17")`

**Response:**
> 黃金價格近三個月走勢（USD / 盎司）：
>
> | date | gold_price |
> |------|------------|
> | 2026-02-20 | 2,850 |
> | 2026-04-15 | 3,020 |
> | 2026-05-15 | 3,180 |
>
> 三個月累計上漲約 11.6%，避險買盤推升至歷史新高區間。

---

### Q16: 美股查詢（USStockPrice）

**User:** 「Apple 最近一週股價」

**Tool call:**
- `query_dataset(dataset="USStockPrice", data_id="AAPL", start_date="2026-05-10", end_date="2026-05-17")`

**Response:**
> Apple (AAPL) 近一週股價（USD）：
>
> | date | Open | High | Low | Close | Volume |
> |------|------|------|-----|-------|--------|
> | 2026-05-12 | 245.80 | 248.20 | 244.50 | 247.60 | 48,200,000 |
> | 2026-05-13 | 247.80 | 250.40 | 247.20 | 249.85 | 52,100,000 |
> | 2026-05-14 | 250.00 | 252.30 | 249.50 | 251.70 | 49,800,000 |
>
> 一週累積上漲約 2.4%，量能穩定。

---

### Q17: 股票代號查詢（TaiwanStockInfo）

**User:** 「台積電股票代號是多少？順便給我一些半導體股」

**Tool call:**
- `get_stock_info()` 或 `query_dataset(dataset="TaiwanStockInfo")`

**Response:**
> 台積電股票代號為 **2330**。半導體相關常見代號：
>
> | stock_id | stock_name | industry_category |
> |----------|------------|---------------------|
> | 2330 | 台積電 | 半導體業 |
> | 2454 | 聯發科 | 半導體業 |
> | 2303 | 聯電 | 半導體業 |
>
> 完整清單可以接著查 TaiwanStockInfo dataset。

---

### Q18: 跨股比較（多檔 TaiwanStockPrice 合併）

**User:** 「比較台積電和聯發科今年股價表現」

**Tool call:**
- `query_dataset(dataset="TaiwanStockPrice", data_id="2330", start_date="2026-01-01", end_date="2026-05-17")`
- `query_dataset(dataset="TaiwanStockPrice", data_id="2454", start_date="2026-01-01", end_date="2026-05-17")`

**Response:**
> 2330 vs 2454 2026 年至今股價（節錄）：
>
> | date | 2330_close | 2454_close |
> |------|------------|------------|
> | 2026-01-02 | 1050 | 1320 |
> | 2026-03-31 | 980 | 1280 |
> | 2026-05-17 | 1000 | 1410 |
>
> 年初至今台積電 -4.8%，聯發科 +6.8%，聯發科表現較強。

---

### Q19: 畫圖請求（K 線圖）

**User:** 「畫一張台積電近三個月 K 線圖」

**Tool call:**
- `query_dataset(dataset="TaiwanStockPrice", data_id="2330", start_date="2026-02-17", end_date="2026-05-17")`
- 接著呼叫 ChatGPT Code Interpreter / Claude analysis 環境用 `mplfinance` 畫 K 線

**Response:**
> 已抓取台積電 (2330) 2026-02-17 ~ 2026-05-17 的 60 個交易日 OHLC 並繪製 K 線圖（含成交量副圖）：
>
> - 圖表類型：日 K 線 + 成交量
> - X 軸：日期；Y 軸：股價（NTD）
> - 期間區間：970 ~ 1010；當前收盤 1000
> - 中文字型已套用 `wqy-zenhei.ttc`
>
> [chart: 2330_kline_2026-02-17_to_2026-05-17.png]

---

### Q20: 折線圖請求（匯率走勢）

**User:** 「美元台幣匯率近半年走勢，畫折線圖」

**Tool call:**
- `query_dataset(dataset="TaiwanExchangeRate", data_id="USD", start_date="2025-11-17", end_date="2026-05-17")`
- 接著用 matplotlib `plot()` 畫 spot_buy 折線

**Response:**
> 已抓取 USD/TWD 近半年即期買入價並繪製折線圖：
>
> - 圖表類型：折線圖
> - X 軸：日期；Y 軸：spot_buy (NTD)
> - 區間：30.8 ~ 33.0；半年最低 30.85 出現於 2026-05-15
> - 中文標題、軸標籤皆使用 `wqy-zenhei.ttc` 字型
>
> [chart: usdtwd_line_2025-11-17_to_2026-05-17.png]

---

### Q21: 相對日期解讀（「最近三個月」）

**User:** 「鴻海最近三個月的股價」

**Tool call:**
- `query_dataset(dataset="TaiwanStockPrice", data_id="2317", start_date="2026-02-17", end_date="2026-05-17")`

**Response:**
> 鴻海 (2317) 2026-02-17 ~ 2026-05-17 股價（節錄）：
>
> | date | open | max | min | close | Trading_Volume |
> |------|------|-----|-----|-------|----------------|
> | 2026-02-18 | 195 | 198 | 194 | 196 | 32,400,000 |
> | 2026-04-15 | 210 | 212 | 208 | 211 | 28,100,000 |
> | 2026-05-15 | 218 | 221 | 217 | 220 | 35,800,000 |
>
> 三個月累計上漲約 12.2%，趨勢偏多。
