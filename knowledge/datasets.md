本文件列出 FinMind 支援的 dataset，涵蓋台股技術面 / 籌碼面 / 基本面 / 衍生性商品 / 即時資料 / 可轉債 / 國際市場 / 全球總經，共約 100 個。
ChatGPT Custom GPT 與 MCP server 共用此文件作為 single source of truth。
所有參數命名以 FinMind v4 API（`/api/v4/data`，少數 dedicated endpoint 另列）為準；日期格式一律 `YYYY-MM-DD`。

## Tier 說明

FinMind 會員方案由低到高為 **Free → Backer → Sponsor → Sponsor Pro**；高階方案涵蓋所有低階方案可存取的資料。下方每個 dataset 標示的是「可存取所需的最低方案」。

- **Free：** 不需 `data_id` 也能查（多為總覽 / 整體市場 / 列表型 dataset）
- **Free(w/ data_id)：** 帶 `data_id`（單一標的）為 Free；省略 `data_id` 想查全市場需 Backer 以上
- **Backer：** 需 Backer 方案以上
- **Sponsor：** 需 Sponsor 方案以上（Sponsor Pro 亦可存取）

「single day」字樣表示該 dataset 僅吃 `start_date`，不支援 `end_date` 區間。

## 台股 - 技術面

### TaiwanStockInfo
- **Endpoint:** `/api/v4/data`
- **Tier:** Free
- **Required:** `dataset=TaiwanStockInfo`
- **Optional:** （無，回傳全市場清單）
- **Key columns:** industry_category, stock_id, stock_name, type, date
- **描述:** 台股代號 / 中文名 / 產業別總覽

### TaiwanStockInfoWithWarrant
- **Endpoint:** `/api/v4/data`
- **Tier:** Free
- **Required:** `dataset=TaiwanStockInfoWithWarrant`
- **Optional:** （無）
- **Key columns:** industry_category, stock_id, stock_name, type, date
- **描述:** 台股總覽（含權證）

### TaiwanStockInfoWithWarrantSummary
- **Endpoint:** `/api/v4/data`
- **Tier:** Sponsor
- **Required:** `dataset=TaiwanStockInfoWithWarrantSummary`, `data_id`, `start_date`
- **Optional:** `end_date`
- **Key columns:** stock_id, date, close, target_stock_id, target_close, type, exercise_ratio, fulfillment_price
- **描述:** 台股權證標的對照表（含履約價、行使比例）；涵蓋上市 (TWSE) 與上櫃 (TPEX) 權證，可用母股代碼 `target_stock_id` 反查其對應權證（含已到期、代碼重用的歷史權證），上櫃對照歷史回溯至 2011-01-03

### TaiwanStockTradingDate
- **Endpoint:** `/api/v4/data`
- **Tier:** Free
- **Required:** `dataset=TaiwanStockTradingDate`
- **Optional:** （無，回傳所有交易日）
- **Key columns:** date
- **描述:** 台股交易日清單

### TaiwanStockPrice
- **Endpoint:** `/api/v4/data`
- **Tier:** Free(w/ data_id)
- **Required:** `dataset=TaiwanStockPrice`, `data_id` (股票代號，如 `2330`), `start_date`
- **Optional:** `end_date`
- **Key columns:** date, stock_id, Trading_Volume, Trading_money, open, max, min, close, spread, Trading_turnover
- **描述:** 個股日成交資料（開高低收、成交量、漲跌）

### TaiwanStockPriceAdj
- **Endpoint:** `/api/v4/data`
- **Tier:** Free(w/ data_id)
- **Required:** `dataset=TaiwanStockPriceAdj`, `data_id` (股票代號), `start_date`
- **Optional:** `end_date`
- **Key columns:** date, stock_id, Trading_Volume, Trading_money, open, max, min, close, spread, Trading_turnover
- **描述:** 還原股價（除權息調整後），算長期報酬率用這個而不是 TaiwanStockPrice

### TaiwanStockPriceTick
- **Endpoint:** `/api/v4/data`
- **Tier:** Backer
- **Required:** `dataset=TaiwanStockPriceTick`, `data_id` (股票代號), `start_date` (single day)
- **Optional:** （無）
- **Key columns:** date, stock_id, deal_price, volume, Time, TickType
- **描述:** 歷史逐筆成交（單日，含時間戳與委買委賣方向）
- **Bulk download (Sponsor Pro):** `GET /api/v4/storage_objects?dataset=TaiwanStockPriceTick&date=YYYY-MM-DD` 一次取整日全市場 parquet（signed URL，免逐檔查詢）；SDK `taiwan_stock_tick(date='YYYY-MM-DD', use_object=True)`。此整日下載限 **Sponsor Pro**（與上方逐檔查詢的 Backer tier 不同）

### TaiwanStockPER
- **Endpoint:** `/api/v4/data`
- **Tier:** Free
- **Required:** `dataset=TaiwanStockPER`, `data_id` (股票代號), `start_date`
- **Optional:** `end_date`
- **Key columns:** date, stock_id, dividend_yield, PER, PBR
- **描述:** 個股本益比、股價淨值比、殖利率

### TaiwanStockStatisticsOfOrderBookAndTrade
- **Endpoint:** `/api/v4/data`
- **Tier:** Free
- **Required:** `dataset=TaiwanStockStatisticsOfOrderBookAndTrade`, `start_date` (single day)
- **Optional:** （無）
- **Key columns:** Time, TotalBuyOrder, TotalBuyVolume, TotalSellOrder, TotalSellVolume, TotalDealVolume, TotalDealMoney, date
- **描述:** 每 5 秒委託 / 成交統計

### TaiwanVariousIndicators5Seconds
- **Endpoint:** `/api/v4/data`
- **Tier:** Free
- **Required:** `dataset=TaiwanVariousIndicators5Seconds`, `start_date` (single day)
- **Optional:** （無）
- **Key columns:** date, TAIEX
- **描述:** 台股加權指數（每 5 秒）

### TaiwanStockDayTrading
- **Endpoint:** `/api/v4/data`
- **Tier:** Free(w/ data_id)
- **Required:** `dataset=TaiwanStockDayTrading`, `data_id` (股票代號), `start_date`
- **Optional:** `end_date`
- **Key columns:** stock_id, date, BuyAfterSale, Volume, BuyAmount, SellAmount
- **描述:** 當沖交易量 / 金額（2014-01-01 起）

### TaiwanStockTotalReturnIndex
- **Endpoint:** `/api/v4/data`
- **Tier:** Free
- **Required:** `dataset=TaiwanStockTotalReturnIndex`, `data_id` (`TAIEX` 或 `TPEx`), `start_date`
- **Optional:** `end_date`
- **Key columns:** price, stock_id, date
- **描述:** 加權報酬指數（含息）

### TaiwanStock10Year
- **Endpoint:** `/api/v4/data`
- **Tier:** Backer
- **Required:** `dataset=TaiwanStock10Year`, `data_id` (股票代號), `start_date`
- **Optional:** `end_date`
- **Key columns:** date, stock_id, close
- **描述:** 個股十年線（長期均線）

### TaiwanStockKBar
- **Endpoint:** `/api/v4/data`
- **Tier:** Sponsor
- **Required:** `dataset=TaiwanStockKBar`, `data_id` (股票代號), `start_date` (single day)
- **Optional:** （無）
- **Key columns:** date, minute, stock_id, open, high, low, close, volume
- **描述:** 分鐘 K 線（單日，1 分鐘粒度）
- **Bulk download (Sponsor Pro):** `GET /api/v4/storage_objects?dataset=TaiwanStockKBar&date=YYYY-MM-DD` 一次取整日全市場 parquet（signed URL，免逐檔查詢）；SDK `taiwan_stock_kbar(date='YYYY-MM-DD', use_object=True)`。逐交易日提供、無歷史回補。此整日下載限 **Sponsor Pro**

### TaiwanStockWeekPrice
- **Endpoint:** `/api/v4/data`
- **Tier:** Backer
- **Required:** `dataset=TaiwanStockWeekPrice`, `data_id` (股票代號), `start_date`
- **Optional:** `end_date`
- **Key columns:** stock_id, yweek, max, min, trading_volume, trading_money, date, close, open, spread
- **描述:** 週 K 線

### TaiwanStockMonthPrice
- **Endpoint:** `/api/v4/data`
- **Tier:** Backer
- **Required:** `dataset=TaiwanStockMonthPrice`, `data_id` (股票代號), `start_date`
- **Optional:** `end_date`
- **Key columns:** stock_id, ymonth, max, min, trading_volume, trading_money, date, close, open, spread
- **描述:** 月 K 線

### TaiwanStockEvery5SecondsIndex
- **Endpoint:** `/api/v4/data`
- **Tier:** Backer
- **Required:** `dataset=TaiwanStockEvery5SecondsIndex`, `start_date` (single day)
- **Optional:** （無）
- **Key columns:** date, time, stock_id, price, kind
- **描述:** 每 5 秒分類指數

### TaiwanStockSuspended
- **Endpoint:** `/api/v4/data`
- **Tier:** Backer
- **Required:** `dataset=TaiwanStockSuspended`, `start_date`
- **Optional:** `end_date`
- **Key columns:** stock_id, date, suspension_time, resumption_date
- **描述:** 暫停交易公告

### TaiwanStockDayTradingSuspension
- **Endpoint:** `/api/v4/data`
- **Tier:** Backer
- **Required:** `dataset=TaiwanStockDayTradingSuspension`, `start_date`
- **Optional:** `end_date`
- **Key columns:** stock_id, date, end_date, reason
- **描述:** 暫停先賣後買當沖

### TaiwanStockPriceLimit
- **Endpoint:** `/api/v4/data`
- **Tier:** Free(w/ data_id)
- **Required:** `dataset=TaiwanStockPriceLimit`, `data_id` (股票代號), `start_date`
- **Optional:** （無）
- **Key columns:** date, stock_id, reference_price, limit_up, limit_down
- **描述:** 每日漲跌停價（2000-01-01 起）

## 台股 - 籌碼面

### TaiwanStockMarginPurchaseShortSale
- **Endpoint:** `/api/v4/data`
- **Tier:** Free(w/ data_id)
- **Required:** `dataset=TaiwanStockMarginPurchaseShortSale`, `data_id` (股票代號), `start_date`
- **Optional:** `end_date`
- **Key columns:** date, stock_id, MarginPurchaseBuy, MarginPurchaseSell, MarginPurchaseTodayBalance, ShortSaleBuy, ShortSaleSell, ShortSaleTodayBalance
- **描述:** 個股融資融券（買賣與餘額）

### TaiwanStockTotalMarginPurchaseShortSale
- **Endpoint:** `/api/v4/data`
- **Tier:** Free
- **Required:** `dataset=TaiwanStockTotalMarginPurchaseShortSale`, `start_date`
- **Optional:** `end_date`
- **Key columns:** TodayBalance, YesBalance, buy, date, name, Return, sell
- **描述:** 整體市場融資融券

### TaiwanStockInstitutionalInvestorsBuySell
- **Endpoint:** `/api/v4/data`
- **Tier:** Free(w/ data_id)
- **Required:** `dataset=TaiwanStockInstitutionalInvestorsBuySell`, `data_id` (股票代號), `start_date`
- **Optional:** `end_date`
- **Key columns:** date, stock_id, buy, name, sell
- **描述:** 個股三大法人買賣超

### TaiwanStockInstitutionalInvestorsBuySellWide
- **Endpoint:** `/api/v4/data`
- **Tier:** Free(w/ data_id)
- **Required:** `dataset=TaiwanStockInstitutionalInvestorsBuySellWide`, `data_id` (股票代號), `start_date`
- **Optional:** `end_date`
- **Key columns:** date, stock_id, Foreign_Investor_buy, Foreign_Investor_sell, Foreign_Dealer_Self_buy, Foreign_Dealer_Self_sell, Investment_Trust_buy, Investment_Trust_sell, Dealer_buy, Dealer_sell, Dealer_self_buy, Dealer_self_sell, Dealer_Hedging_buy, Dealer_Hedging_sell
- **描述:** 個股三大法人買賣（寬表）；與 TaiwanStockInstitutionalInvestorsBuySell 同資料，改為每交易日一列、各法人別買賣攤平成獨立欄位（免自行轉置），欄位涵蓋所有歷史分類、尚未存在的年代為 0

### TaiwanStockTotalInstitutionalInvestors
- **Endpoint:** `/api/v4/data`
- **Tier:** Free
- **Required:** `dataset=TaiwanStockTotalInstitutionalInvestors`, `start_date`
- **Optional:** `end_date`
- **Key columns:** buy, date, name, sell
- **描述:** 整體市場三大法人買賣超

### TaiwanStockShareholding
- **Endpoint:** `/api/v4/data`
- **Tier:** Free(w/ data_id)
- **Required:** `dataset=TaiwanStockShareholding`, `data_id` (股票代號), `start_date`
- **Optional:** `end_date`
- **Key columns:** date, stock_id, ForeignInvestmentShares, ForeignInvestmentSharesRatio, ForeignInvestmentRemainRatio, ForeignInvestmentUpperLimitRatio
- **描述:** 外資持股（股數、比例、上限）

### TaiwanStockHoldingSharesPer
- **Endpoint:** `/api/v4/data`
- **Tier:** Backer
- **Required:** `dataset=TaiwanStockHoldingSharesPer`, `data_id` (股票代號), `start_date`
- **Optional:** `end_date`
- **Key columns:** date, stock_id, HoldingSharesLevel, people, percent, unit
- **描述:** 股權持股分級（各持股級距的人數 / 比例）

### TaiwanStockSecuritiesLending
- **Endpoint:** `/api/v4/data`
- **Tier:** Free(w/ data_id)
- **Required:** `dataset=TaiwanStockSecuritiesLending`, `data_id` (股票代號), `start_date`
- **Optional:** `end_date`
- **Key columns:** date, stock_id, transaction_type, volume, fee_rate, close
- **描述:** 借券成交（含借券費率）

### TaiwanStockMarginShortSaleSuspension
- **Endpoint:** `/api/v4/data`
- **Tier:** Free(w/ data_id)
- **Required:** `dataset=TaiwanStockMarginShortSaleSuspension`, `data_id` (股票代號), `start_date`
- **Optional:** `end_date`
- **Key columns:** stock_id, date, end_date, reason
- **描述:** 暫停融券賣出公告

### TaiwanDailyShortSaleBalances
- **Endpoint:** `/api/v4/data`
- **Tier:** Free(w/ data_id)
- **Required:** `dataset=TaiwanDailyShortSaleBalances`, `data_id` (股票代號), `start_date`
- **Optional:** `end_date`
- **Key columns:** stock_id, MarginShortSalesPreviousBalance, MarginShortSalesShortSales, MarginShortSalesShortCovering, MarginShortSalesStockReturns, MarginShortSalesCurrentDayBalance, SBLShortSalesPreviousBalance, SBLShortSalesShortSales, SBLShortSalesReturns, SBLShortSalesAdjustments, SBLShortSalesCurrentDayBalance, SBLShortSalesQuota, SBLShortSalesShortCovering, date
- **描述:** 信用額度總量管制餘額（融券 + 借券賣出）

### TaiwanSecuritiesTraderInfo
- **Endpoint:** `/api/v4/data`
- **Tier:** Free
- **Required:** `dataset=TaiwanSecuritiesTraderInfo`
- **Optional:** （無，回傳全市場券商清單）
- **Key columns:** securities_trader_id, securities_trader, date, address, phone
- **描述:** 證券商代號與基本資訊

### TaiwanStockTradingDailyReport
- **Endpoint:** `/api/v4/taiwan_stock_trading_daily_report`（dedicated）
- **Tier:** Sponsor
- **Required:** `data_id` (股票代號), `date` (注意是 `date`，不是 `start_date`)
- **Optional:** （無）
- **Key columns:** securities_trader, price, buy, sell, securities_trader_id, stock_id, date
- **描述:** 分點進出（單日，按券商分點列出買賣）
- **Bulk download (Sponsor Pro):** `GET /api/v4/storage_objects?dataset=TaiwanStockTradingDailyReport&date=YYYY-MM-DD` 一次取整日全市場分點 parquet（signed URL，免逐檔查詢）；SDK `taiwan_stock_trading_daily_report(date='YYYY-MM-DD', use_object=True)`。此整日下載限 **Sponsor Pro**

### TaiwanStockWarrantTradingDailyReport
- **Endpoint:** `/api/v4/taiwan_stock_warrant_trading_daily_report`（dedicated）
- **Tier:** Sponsor
- **Required:** `data_id` (權證代號), `date`
- **Optional:** （無）
- **Key columns:** securities_trader, price, buy, sell, securities_trader_id, stock_id, date
- **描述:** 權證分點進出（單日）

### TaiwanStockGovernmentBankBuySell
- **Endpoint:** `/api/v4/data`
- **Tier:** Sponsor
- **Required:** `dataset=TaiwanStockGovernmentBankBuySell`, `data_id` (股票代號), `start_date`
- **Optional:** `end_date`
- **Key columns:** date, stock_id, buy_amount, sell_amount, buy, sell, bank_name
- **描述:** 八大行庫買賣

### TaiwanTotalExchangeMarginMaintenance
- **Endpoint:** `/api/v4/data`
- **Tier:** Backer
- **Required:** `dataset=TaiwanTotalExchangeMarginMaintenance`, `start_date`
- **Optional:** `end_date`
- **Key columns:** date, TotalExchangeMarginMaintenance
- **描述:** 大盤融資維持率

### TaiwanStockTradingDailyReportSecIdAgg
- **Endpoint:** `/api/v4/taiwan_stock_trading_daily_report_secid_agg`（dedicated）
- **Tier:** Sponsor
- **Required:** `data_id` (股票代號), `start_date`
- **Optional:** `end_date`
- **Key columns:** securities_trader, securities_trader_id, stock_id, date, buy_volume, sell_volume, buy_price, sell_price
- **描述:** 券商分點統計（區間 aggregation；2021-06-30 起）

### TaiwanStockDispositionSecuritiesPeriod
- **Endpoint:** `/api/v4/data`
- **Tier:** Backer
- **Required:** `dataset=TaiwanStockDispositionSecuritiesPeriod`, `start_date`
- **Optional:** `end_date`
- **Key columns:** date, stock_id, stock_name, disposition_cnt, condition, measure, period_start, period_end
- **描述:** 處置有價證券（含處置原因與期間）

### TaiwanStockBlockTrade
- **Endpoint:** `/api/v4/data`
- **Tier:** Sponsor
- **Required:** `dataset=TaiwanStockBlockTrade`, `data_id` (股票代號), `start_date`
- **Optional:** `end_date`
- **Key columns:** date, stock_id, trade_type, price, volume, trading_money
- **描述:** 鉅額交易日成交資訊（逐筆，含交易別、成交價量金額）；資料區間 2005-04-04 ~ now

### TaiwanStockBlockTradingDailyReport
- **Endpoint:** `/api/v4/data`
- **Tier:** Sponsor
- **Required:** `dataset=TaiwanStockBlockTradingDailyReport`, `start_date`
- **Optional:** `data_id` (股票代號), `end_date`
- **Key columns:** date, stock_id, securities_trader, securities_trader_id, price, buy, sell, trade_type
- **描述:** 鉅額交易買賣日報表（含券商別）；資料區間 2026-04-28 ~ now

### TaiwanStockDayTradingBorrowingFeeRate
- **Endpoint:** `/api/v4/data`
- **Tier:** Backer
- **Required:** `dataset=TaiwanStockDayTradingBorrowingFeeRate`, `start_date`
- **Optional:** `data_id` (股票代號), `end_date`
- **Key columns:** date, stock_id, stock_name, InvestorBorrowedShares, InvestorBorrowingFeeRate
- **描述:** 現股當日沖銷券差借券費率（借券股數、借券費率）；資料區間 2015-06-01 ~ now

### TaiwanStockLoanCollateralBalance
- **Endpoint:** `/api/v4/data`
- **Tier:** Sponsor
- **Required:** `dataset=TaiwanStockLoanCollateralBalance`, `data_id` (股票代號), `start_date`
- **Optional:** `end_date`
- **Key columns:** date, stock_id, market, MarginCurrentDayBalance, SecuritiesFirmLoanCurrentDayBalance, UnrestrictedLoanCurrentDayBalance（融資/證券商借貸/不限用途借貸各前日餘額、買進、賣出、現償、更換、今日餘額、次日限額，共 37 欄）
- **描述:** 借貸款項擔保品餘額表（集中市場 / 櫃買中心，融資與證券商借貸款項各項餘額）；資料區間 2006-10-02 ~ now

### TaiwanStockActiveETFInfo
- **Endpoint:** `/api/v4/data`
- **Tier:** Free
- **Required:** `dataset=TaiwanStockActiveETFInfo`
- **Optional:** （無，回傳完整清單）
- **Key columns:** date, stock_id, stock_name, category, type
- **描述:** 台灣掛牌主動式ETF清單（上市 + 上櫃）；category=ETF 分類（domestic 國內投資 / foreign 跨國投資）、type=市場別（twse / tpex）

### TaiwanStockActiveETFHolding
- **Endpoint:** `/api/v4/data`
- **Tier:** Sponsor
- **Required:** `dataset=TaiwanStockActiveETFHolding`, `start_date`
- **Optional:** `data_id` (ETF 代號，如 00980A；省略則查當日全部主動式ETF), `end_date`
- **Key columns:** date, stock_id (ETF 代號), component_stock_id (成份標的代號), component_stock_name, asset_type, shares, weight, market_value, currency
- **描述:** 主動式ETF每日持股明細；資料區間 2025-05-05 ~ now（各檔起始日依掛牌日不同）。shares 為整數；空方部位（賣出選擇權 / 期貨）與負債科目的 shares / market_value 可為負；market_value 僅部分 ETF 揭露、未揭露為 0；asset_type 可篩選 stock / bond / futures / option / cash / etf / repo / other

### TaiwanStockActiveETFHoldingChange
- **Endpoint:** `/api/v4/data`
- **Tier:** Sponsor
- **Required:** `dataset=TaiwanStockActiveETFHoldingChange`, `start_date`
- **Optional:** `data_id` (ETF 代號，如 00980A；省略則查當日全部主動式ETF), `end_date`
- **Key columns:** date, stock_id (ETF 代號), component_stock_id (成份標的代號), component_stock_name, buy, sell
- **描述:** 主動式ETF每日持股異動（買賣）；由持股明細相鄰交易日差分而得，資料區間 2025-05-05 ~ now。buy / sell 為整數股數、每列僅其一非 0；申購 / 贖回造成的等比例增減亦計入，非經理人主動買賣純額

## 台股 - 基本面

### TaiwanStockFinancialStatements
- **Endpoint:** `/api/v4/data`
- **Tier:** Free(w/ data_id)
- **Required:** `dataset=TaiwanStockFinancialStatements`, `data_id` (股票代號), `start_date` (季底，如 `2024-03-31`)
- **Optional:** `end_date`
- **Key columns:** date, stock_id, type, value, origin_name
- **描述:** 綜合損益表（季 / 年報，含 EPS）

### TaiwanStockBalanceSheet
- **Endpoint:** `/api/v4/data`
- **Tier:** Free(w/ data_id)
- **Required:** `dataset=TaiwanStockBalanceSheet`, `data_id` (股票代號), `start_date`
- **Optional:** `end_date`
- **Key columns:** date, stock_id, type, value, origin_name
- **描述:** 資產負債表

### TaiwanStockCashFlowsStatement
- **Endpoint:** `/api/v4/data`
- **Tier:** Free(w/ data_id)
- **Required:** `dataset=TaiwanStockCashFlowsStatement`, `data_id` (股票代號), `start_date`
- **Optional:** `end_date`
- **Key columns:** date, stock_id, type, value, origin_name
- **描述:** 現金流量表

### TaiwanStockDividend
- **Endpoint:** `/api/v4/data`
- **Tier:** Free(w/ data_id)
- **Required:** `dataset=TaiwanStockDividend`, `data_id` (股票代號), `start_date`
- **Optional:** `end_date`
- **Key columns:** date, stock_id, year, CashEarningsDistribution, StockEarningsDistribution, CashExDividendTradingDate, CashDividendPaymentDate
- **描述:** 股利政策（現金 / 股票股利、除息日）

### TaiwanStockDividendResult
- **Endpoint:** `/api/v4/data`
- **Tier:** Free(w/ data_id)
- **Required:** `dataset=TaiwanStockDividendResult`, `data_id` (股票代號), `start_date`
- **Optional:** `end_date`
- **Key columns:** date, stock_id, before_price, after_price, stock_and_cache_dividend, reference_price
- **描述:** 除權除息結果（除權息前後股價、權息值）

### TaiwanStockMonthRevenue
- **Endpoint:** `/api/v4/data`
- **Tier:** Free(w/ data_id)
- **Required:** `dataset=TaiwanStockMonthRevenue`, `data_id` (股票代號), `start_date`
- **Optional:** `end_date`
- **Key columns:** date, stock_id, revenue, revenue_month, revenue_year
- **描述:** 個股月營收

### TaiwanStockCapitalReductionReferencePrice
- **Endpoint:** `/api/v4/data`
- **Tier:** Free
- **Required:** `dataset=TaiwanStockCapitalReductionReferencePrice`, `start_date`
- **Optional:** `end_date`
- **Key columns:** date, stock_id, ClosingPriceonTheLastTradingDay, PostReductionReferencePrice, LimitUp, LimitDown, OpeningReferencePrice, ExrightReferencePrice, ReasonforCapitalReduction
- **描述:** 減資恢復買賣參考價

### TaiwanStockMarketValue
- **Endpoint:** `/api/v4/data`
- **Tier:** Backer
- **Required:** `dataset=TaiwanStockMarketValue`, `data_id` (股票代號), `start_date`
- **Optional:** `end_date`
- **Key columns:** date, stock_id, market_value
- **描述:** 個股股價市值

### TaiwanStockDelisting
- **Endpoint:** `/api/v4/data`
- **Tier:** Free
- **Required:** `dataset=TaiwanStockDelisting`, `start_date`
- **Optional:** `end_date`
- **Key columns:** date, stock_id, stock_name
- **描述:** 下市櫃公告

### TaiwanStockMarketValueWeight
- **Endpoint:** `/api/v4/data`
- **Tier:** Backer
- **Required:** `dataset=TaiwanStockMarketValueWeight`, `start_date`
- **Optional:** `end_date`
- **Key columns:** rank, stock_id, stock_name, weight_per, date, type
- **描述:** 個股市值比重（加權指數成分）

### TaiwanStockSplitPrice
- **Endpoint:** `/api/v4/data`
- **Tier:** Free
- **Required:** `dataset=TaiwanStockSplitPrice`, `start_date`
- **Optional:** `end_date`
- **Key columns:** date, stock_id, type, before_price, after_price
- **描述:** 股票分割後參考價

### TaiwanStockParValueChange
- **Endpoint:** `/api/v4/data`
- **Tier:** Free
- **Required:** `dataset=TaiwanStockParValueChange`, `start_date`
- **Optional:** `end_date`
- **Key columns:** date, stock_id, stock_name, before_close, after_ref_close
- **描述:** 變更面額恢復買賣參考價

## 台股 - 衍生性金融商品

### TaiwanFutOptDailyInfo
- **Endpoint:** `/api/v4/data`
- **Tier:** Free
- **Required:** `dataset=TaiwanFutOptDailyInfo`
- **Optional:** （無）
- **Key columns:** code, type, name
- **描述:** 期貨選擇權代號總覽

### TaiwanFuturesDaily
- **Endpoint:** `/api/v4/data`
- **Tier:** Free(w/ data_id)
- **Required:** `dataset=TaiwanFuturesDaily`, `data_id` (期貨代號，如 `TX`), `start_date`
- **Optional:** `end_date`
- **Key columns:** date, futures_id, contract_date, open, max, min, close, volume, settlement_price, open_interest
- **描述:** 期貨日成交（含結算價、未平倉）

### TaiwanOptionDaily
- **Endpoint:** `/api/v4/data`
- **Tier:** Free(w/ data_id)
- **Required:** `dataset=TaiwanOptionDaily`, `data_id` (選擇權代號，如 `TXO`), `start_date`
- **Optional:** `end_date`
- **Key columns:** date, option_id, contract_date, strike_price, call_put, open, max, min, close, volume
- **描述:** 選擇權日成交（履約價、買賣權）

### TaiwanFuturesTick
- **Endpoint:** `/api/v4/data`
- **Tier:** Backer
- **Required:** `dataset=TaiwanFuturesTick`, `data_id` (期貨代號), `start_date` (single day)
- **Optional:** （無）
- **Key columns:** contract_date, date, futures_id, price, volume
- **描述:** 期貨逐筆交易明細
- **Bulk download (Sponsor Pro):** `GET /api/v4/storage_objects?dataset=TaiwanFuturesTick&date=YYYY-MM-DD` 一次取整日全市場 parquet（signed URL，免逐檔查詢）；SDK `taiwan_futures_tick(date='YYYY-MM-DD', use_object=True)`。逐交易日提供、無歷史回補。此整日下載限 **Sponsor Pro**（與上方逐檔查詢的 Backer tier 不同）

### TaiwanOptionTick
- **Endpoint:** `/api/v4/data`
- **Tier:** Backer
- **Required:** `dataset=TaiwanOptionTick`, `data_id` (選擇權代號), `start_date` (single day)
- **Optional:** （無）
- **Key columns:** ExercisePrice, PutCall, contract_date, date, option_id, price, volume
- **描述:** 選擇權逐筆交易明細
- **Bulk download (Sponsor Pro):** `GET /api/v4/storage_objects?dataset=TaiwanOptionTick&date=YYYY-MM-DD` 一次取整日全市場 parquet（signed URL，免逐檔查詢）；SDK `taiwan_option_tick(date='YYYY-MM-DD', use_object=True)`。逐交易日提供、無歷史回補。此整日下載限 **Sponsor Pro**（與上方逐檔查詢的 Backer tier 不同）

### TaiwanFuturesInstitutionalInvestors
- **Endpoint:** `/api/v4/data`
- **Tier:** Free(w/ data_id)
- **Required:** `dataset=TaiwanFuturesInstitutionalInvestors`, `data_id` (期貨代號), `start_date`
- **Optional:** `end_date`
- **Key columns:** name, date, institutional_investors, long_deal_volume, long_deal_amount, short_deal_volume, short_deal_amount, long_open_interest_balance_volume, short_open_interest_balance_volume
- **描述:** 期貨三大法人多空口數與未平倉

### TaiwanOptionInstitutionalInvestors
- **Endpoint:** `/api/v4/data`
- **Tier:** Free(w/ data_id)
- **Required:** `dataset=TaiwanOptionInstitutionalInvestors`, `data_id` (選擇權代號), `start_date`
- **Optional:** `end_date`
- **Key columns:** name, date, call_put, institutional_investors, long_deal_volume, long_deal_amount, short_deal_volume, short_deal_amount, long_open_interest_balance_volume, short_open_interest_balance_volume
- **描述:** 選擇權三大法人

### TaiwanFuturesInstitutionalInvestorsAfterHours
- **Endpoint:** `/api/v4/data`
- **Tier:** Backer
- **Required:** `dataset=TaiwanFuturesInstitutionalInvestorsAfterHours`, `data_id` (期貨代號), `start_date`
- **Optional:** `end_date`
- **Key columns:** futures_id, date, institutional_investors, long_deal_volume, long_deal_amount, short_deal_volume, short_deal_amount
- **描述:** 期貨夜盤三大法人

### TaiwanOptionInstitutionalInvestorsAfterHours
- **Endpoint:** `/api/v4/data`
- **Tier:** Backer
- **Required:** `dataset=TaiwanOptionInstitutionalInvestorsAfterHours`, `data_id` (選擇權代號), `start_date`
- **Optional:** `end_date`
- **Key columns:** option_id, date, call_put, institutional_investors, long_deal_volume, long_deal_amount, short_deal_volume, short_deal_amount
- **描述:** 選擇權夜盤三大法人

### TaiwanFuturesDealerTradingVolumeDaily
- **Endpoint:** `/api/v4/data`
- **Tier:** Free
- **Required:** `dataset=TaiwanFuturesDealerTradingVolumeDaily`, `start_date`
- **Optional:** `end_date`
- **Key columns:** date, dealer_code, dealer_name, futures_id, volume
- **描述:** 期貨各券商每日交易量

### TaiwanOptionDealerTradingVolumeDaily
- **Endpoint:** `/api/v4/data`
- **Tier:** Free
- **Required:** `dataset=TaiwanOptionDealerTradingVolumeDaily`, `start_date`
- **Optional:** `end_date`
- **Key columns:** date, dealer_code, dealer_name, option_id, volume
- **描述:** 選擇權各券商每日交易量

### TaiwanFuturesOpenInterestLargeTraders
- **Endpoint:** `/api/v4/data`
- **Tier:** Backer
- **Required:** `dataset=TaiwanFuturesOpenInterestLargeTraders`, `data_id` (期貨代號), `start_date`
- **Optional:** `end_date`
- **Key columns:** name, futures_id, buy_top5_trader_open_interest, sell_top5_trader_open_interest, buy_top10_trader_open_interest, sell_top10_trader_open_interest, date
- **描述:** 期貨大額交易人未沖銷部位（前 5 / 前 10）

### TaiwanOptionOpenInterestLargeTraders
- **Endpoint:** `/api/v4/data`
- **Tier:** Backer
- **Required:** `dataset=TaiwanOptionOpenInterestLargeTraders`, `data_id` (選擇權代號), `start_date`
- **Optional:** `end_date`
- **Key columns:** name, option_id, put_call, buy_top5_trader_open_interest, sell_top5_trader_open_interest, buy_top10_trader_open_interest, sell_top10_trader_open_interest, date
- **描述:** 選擇權大額交易人未沖銷部位

### TaiwanFuturesSpreadTrading
- **Endpoint:** `/api/v4/data`
- **Tier:** Backer
- **Required:** `dataset=TaiwanFuturesSpreadTrading`, `data_id` (期貨代號), `start_date`
- **Optional:** `end_date`
- **Key columns:** date, futures_id, contract_date, open, max, min, close
- **描述:** 期貨價差行情（跨月價差）

### TaiwanFuturesFinalSettlementPrice
- **Endpoint:** `/api/v4/data`
- **Tier:** Backer
- **Required:** `dataset=TaiwanFuturesFinalSettlementPrice`, `start_date`
- **Optional:** `end_date`
- **Key columns:** date, contract_month, futures_id, settlement_price
- **描述:** 期貨最後結算價

### TaiwanOptionFinalSettlementPrice
- **Endpoint:** `/api/v4/data`
- **Tier:** Backer
- **Required:** `dataset=TaiwanOptionFinalSettlementPrice`, `start_date`
- **Optional:** `end_date`
- **Key columns:** date, contract_month, option_id, settlement_price
- **描述:** 選擇權最後結算價

### TaiwanFuturesSpreadTick
- **Endpoint:** `/api/v4/data`
- **Tier:** Sponsor
- **Required:** `dataset=TaiwanFuturesSpreadTick`, `data_id` (期貨代號，如 `CAF`), `start_date` (single day)
- **Optional:** （無）
- **Key columns:** date, time, futures_id, contract_date, price, volume, near_price, far_price, spread_to_spread
- **描述:** 期貨價差（近月/遠月）每筆成交；單次請求只提供一天資料，自 2026-04-27 起逐交易日累積（暫不含更早歷史回補）

### TaiwanOptionVix
- **Endpoint:** `/api/v4/data`
- **Tier:** Backer
- **Required:** `dataset=TaiwanOptionVix`, `start_date`
- **Optional:** `end_date`
- **Key columns:** date, time, vix
- **描述:** 臺指選擇權波動率指數（VIX）；含日期、時間、波動率指數，資料區間 2026-03-01 ~ now

## 台股 - 即時資料

> 此分類所有 dataset 都需要 **Sponsor** 方案。

### taiwan_stock_tick_snapshot
- **Endpoint:** `/api/v4/data`
- **Tier:** Sponsor
- **Required:** `dataset=taiwan_stock_tick_snapshot`, `data_id` (股票代號)
- **Optional:** （無）
- **Key columns:** close, high, low, open, volume, total_volume, change_price, change_rate, date, stock_id
- **描述:** 台股即時報價（快照）

### TaiwanFutOptTickInfo
- **Endpoint:** `/api/v4/data`
- **Tier:** Sponsor
- **Required:** `dataset=TaiwanFutOptTickInfo`
- **Optional:** （無）
- **Key columns:** code, callput, date, name
- **描述:** 期貨選擇權即時總覽

### taiwan_futures_snapshot
- **Endpoint:** `/api/v4/data`
- **Tier:** Sponsor
- **Required:** `dataset=taiwan_futures_snapshot`, `data_id` (期貨代號)
- **Optional:** （無）
- **Key columns:** open, high, low, close, volume, total_volume, change_price, change_rate, date, futures_id
- **描述:** 期貨即時報價（快照）

### taiwan_options_snapshot
- **Endpoint:** `/api/v4/data`
- **Tier:** Sponsor
- **Required:** `dataset=taiwan_options_snapshot`, `data_id` (選擇權代號)
- **Optional:** （無）
- **Key columns:** open, high, low, close, volume, total_volume, change_price, change_rate, date, options_id
- **描述:** 選擇權即時報價（快照）

## 台股 - 可轉債

> 此分類所有 dataset 都需要 **Backer** 或 **Sponsor** 方案。

### TaiwanStockConvertibleBondInfo
- **Endpoint:** `/api/v4/data`
- **Tier:** Backer
- **Required:** `dataset=TaiwanStockConvertibleBondInfo`
- **Optional:** （無）
- **Key columns:** cb_id, cb_name, InitialDateOfConversion, DueDateOfConversion
- **描述:** 可轉債總覽（含可轉債起 / 迄日）

### TaiwanStockConvertibleBondDaily
- **Endpoint:** `/api/v4/data`
- **Tier:** Backer
- **Required:** `dataset=TaiwanStockConvertibleBondDaily`, `data_id` (可轉債代號), `start_date`
- **Optional:** `end_date`
- **Key columns:** cb_id, cb_name, close, open, max, min, volume, date
- **描述:** 可轉債日成交

### TaiwanStockConvertibleBondInstitutionalInvestors
- **Endpoint:** `/api/v4/data`
- **Tier:** Backer
- **Required:** `dataset=TaiwanStockConvertibleBondInstitutionalInvestors`, `data_id` (可轉債代號), `start_date`
- **Optional:** `end_date`
- **Key columns:** cb_id, date, Foreign_Investment_Buy, Foreign_Investment_Sell, Investment_Trust_Buy, Investment_Trust_Sell, Dealer_Buy, Dealer_Sell
- **描述:** 可轉債三大法人

### TaiwanStockConvertibleBondDailyOverview
- **Endpoint:** `/api/v4/data`
- **Tier:** Backer
- **Required:** `dataset=TaiwanStockConvertibleBondDailyOverview`, `data_id` (可轉債代號), `start_date`
- **Optional:** `end_date`
- **Key columns:** cb_id, ConversionPrice, IssuanceAmount, OutstandingAmount, date
- **描述:** 可轉債每日總覽（轉換價、發行 / 流通在外金額）

### TaiwanStockConvertibleBondMonthlyAnalysis
- **Endpoint:** `/api/v4/data`
- **Tier:** Backer
- **Required:** `dataset=TaiwanStockConvertibleBondMonthlyAnalysis`, `start_date`
- **Optional:** `data_id` (可轉債代號), `end_date`
- **Key columns:** date, cb_id, cb_name, cb_name_en, custody_balance, last_month_balance, change, change_percent, issued_units, custody_accounts, pledged_units
- **描述:** 可轉換公司債月份分析表（每月保管餘額、上月餘額、增減、發行單位數、保管戶數、設質單位數）；資料區間 2026-05-01 ~ now

## 台股 - 其他

### TaiwanStockNews
- **Endpoint:** `/api/v4/data`
- **Tier:** Free
- **Required:** `dataset=TaiwanStockNews`, `data_id` (股票代號), `start_date`
- **Optional:** `end_date`
- **Key columns:** date, stock_id, description, link, source, title
- **描述:** 個股相關新聞（標題、連結、摘要）

### TaiwanBusinessIndicator
- **Endpoint:** `/api/v4/data`
- **Tier:** Backer
- **Required:** `dataset=TaiwanBusinessIndicator`, `start_date`
- **Optional:** `end_date`
- **Key columns:** date, leading, coincident, lagging, monitoring, monitoring_color
- **描述:** 景氣對策信號（領先 / 同時 / 落後指標 + 燈號）

### TaiwanStockIndustryChain
- **Endpoint:** `/api/v4/data`
- **Tier:** Backer
- **Required:** `dataset=TaiwanStockIndustryChain`, `data_id` (股票代號)
- **Optional:** `start_date`
- **Key columns:** stock_id, industry, sub_industry, date
- **描述:** 產業鏈分類（上中下游）

## 國際市場

### USStockInfo
- **Endpoint:** `/api/v4/data`
- **Tier:** Free
- **Required:** `dataset=USStockInfo`
- **Optional:** （無）
- **Key columns:** date, stock_id, Country, MarketCap, stock_name
- **描述:** 美股代號總覽

### USStockPrice
- **Endpoint:** `/api/v4/data`
- **Tier:** Free
- **Required:** `dataset=USStockPrice`, `data_id` (美股代號，如 `AAPL`), `start_date`
- **Optional:** `end_date`
- **Key columns:** date, stock_id, Open, High, Low, Close, Adj_Close, Volume
- **描述:** 美股日成交（含調整收盤價）

### USStockPriceMinute
- **Endpoint:** `/api/v4/data`
- **Tier:** Backer
- **Required:** `dataset=USStockPriceMinute`, `data_id` (美股代號), `start_date`
- **Optional:** `end_date`
- **Key columns:** date, stock_id, open, high, low, close, volume
- **描述:** 美股分鐘 K

### UKStockInfo
- **Endpoint:** `/api/v4/data`
- **Tier:** Free
- **Required:** `dataset=UKStockInfo`
- **Optional:** （無）
- **Key columns:** date, stock_id, Country, stock_name
- **描述:** 英股代號總覽

### UKStockPrice
- **Endpoint:** `/api/v4/data`
- **Tier:** Free
- **Required:** `dataset=UKStockPrice`, `data_id` (英股代號), `start_date`
- **Optional:** `end_date`
- **Key columns:** date, stock_id, Open, High, Low, Close, Adj_Close, Volume
- **描述:** 英股日成交

### EuropeStockInfo
- **Endpoint:** `/api/v4/data`
- **Tier:** Free
- **Required:** `dataset=EuropeStockInfo`
- **Optional:** （無）
- **Key columns:** date, stock_id, Market, stock_name
- **描述:** 歐股代號總覽

### EuropeStockPrice
- **Endpoint:** `/api/v4/data`
- **Tier:** Free
- **Required:** `dataset=EuropeStockPrice`, `data_id` (歐股代號), `start_date`
- **Optional:** `end_date`
- **Key columns:** date, stock_id, Open, High, Low, Close, Adj_Close, Volume
- **描述:** 歐股日成交

### JapanStockInfo
- **Endpoint:** `/api/v4/data`
- **Tier:** Free
- **Required:** `dataset=JapanStockInfo`
- **Optional:** （無）
- **Key columns:** date, stock_id, Exchange, Sector, stock_name
- **描述:** 日股代號總覽

### JapanStockPrice
- **Endpoint:** `/api/v4/data`
- **Tier:** Free
- **Required:** `dataset=JapanStockPrice`, `data_id` (日股代號), `start_date`
- **Optional:** `end_date`
- **Key columns:** date, stock_id, Open, High, Low, Close, Adj_Close, Volume
- **描述:** 日股日成交

## 全球總經

### TaiwanExchangeRate
- **Endpoint:** `/api/v4/data`
- **Tier:** Free
- **Required:** `dataset=TaiwanExchangeRate`, `start_date`
- **Optional:** `data_id` (幣別，如 `USD`、`JPY`、`EUR`、`GBP`、`CNY`、`HKD`、`AUD`、`CAD`、`CHF`、`IDR`、`KRW`、`MYR`、`NZD`、`PHP`、`SEK`、`SGD`、`THB`、`VND`、`ZAR`), `end_date`
- **Key columns:** date, currency, cash_buy, cash_sell, spot_buy, spot_sell
- **描述:** 台灣銀行牌告匯率（現金 / 即期買賣）

### InterestRate
- **Endpoint:** `/api/v4/data`
- **Tier:** Free
- **Required:** `dataset=InterestRate`, `data_id` (央行代號，如 `FED`、`ECB`、`BOJ`、`BOE`、`RBA`、`PBOC`、`BOC`、`RBNZ`、`RBI`、`CBR`、`BCB`、`SNB`), `start_date`
- **Optional:** `end_date`
- **Key columns:** country, date, interest_rate
- **描述:** 各國央行政策利率

### GoldPrice
- **Endpoint:** `/api/v4/data`
- **Tier:** Free
- **Required:** `dataset=GoldPrice`, `start_date`
- **Optional:** `end_date`
- **Key columns:** Price, date
- **描述:** 國際黃金現貨價格

### CrudeOilPrices
- **Endpoint:** `/api/v4/data`
- **Tier:** Free
- **Required:** `dataset=CrudeOilPrices`, `data_id` (`WTI` 或 `Brent`), `start_date`
- **Optional:** `end_date`
- **Key columns:** date, name, price
- **描述:** 原油價格（WTI / Brent）

### GovernmentBondsYield
- **Endpoint:** `/api/v4/data`
- **Tier:** Free
- **Required:** `dataset=GovernmentBondsYield`, `data_id` (美債年期，如 `"United States 10-Year"`，可選 1-Month ~ 30-Year), `start_date`
- **Optional:** `end_date`
- **Key columns:** date, name, value
- **描述:** 美國國債殖利率

### CnnFearGreedIndex
- **Endpoint:** `/api/v4/data`
- **Tier:** Backer
- **Required:** `dataset=CnnFearGreedIndex`, `start_date`
- **Optional:** `end_date`
- **Key columns:** date, fear_greed, fear_greed_emotion
- **描述:** CNN 恐懼貪婪指數
