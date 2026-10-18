## 401 Unauthorized（Token 無效）

**觸發條件：** HTTP 401、回應 `Token is illegal.`，或 Token 未設定（ChatGPT Action 未填 API Key；MCP 端 `FINMIND_TOKEN` 不存在）。

**回應模板：**
> 您的 FinMind Token 無法驗證。請確認：
> 1. Token 是否完整複製（前後無空白、換行）
> 2. 是否已完成信箱驗證
> 3. 是否為最新 Token（重設後舊 Token 失效）
>
> 取得 Token：https://finmindtrade.com/analysis/#/account/user

**下一步建議：** ChatGPT 到 GPT 設定「Authentication」重填；MCP host 改 `env.FINMIND_TOKEN` 後重啟。

## 方案權限不足（Tier 不足）

**觸發條件：** 回應訊息為 `Your level is ... Please update your user level`（FinMind 以 HTTP 400 回）。MCP 工具會在模板前標出所需方案（Backer / Sponsor / Sponsor Pro）與 API 回應原文。

**回應模板：**
> 您查詢的資料需要 **[所需方案]** 以上方案，目前方案無法存取。
> API 回應原文：`[回應原文]`
>
> 升級方案：https://finmindtrade.com/analysis/#/Sponsor/sponsor（升級後 Token 不需更換，立即生效）

**下一步建議：** 用 pricing（MCP `get_pricing`）列出方案價格與差異；需要時建議同主題的較低方案 dataset。不要嘗試其他繞過方式。

## 參數錯誤（400 / 404 / 422）

**觸發條件：** 缺必填參數、日期格式錯、dataset 不在該 endpoint 支援清單，或整日檔該日不存在（404）。

**回應模板：**
> 查詢參數有誤：`[API 回應原文]`。我會依原因調整參數後再查一次。

**下一步建議：** 依原文修正後重試一次；dataset 走專屬 endpoint 時改用正確的 endpoint；404 整日檔通常是非交易日。

## 空資料（`data: []`）

**觸發條件：** HTTP 200 但 `data` 為空。常見原因：代號錯誤、區間內無交易日、超出資料起始日、未來日期。

**回應模板：**
> 在指定條件下查無資料。可能原因：代號錯誤、區間內皆非交易日、早於資料起始日，或日期超過今日。請確認後再試，或告訴我想查的標的與時間。

**下一步建議：** 用 `TaiwanStockInfo` 驗證代號；擴大日期區間重試。

## HTTP Timeout / 5xx（暫時連線異常）

**觸發條件：** 連線逾時、無法連線，或 HTTP 5xx。

**回應模板：**
> FinMind 服務暫時無法連線，請 1 - 2 分鐘後再試。若持續失敗，可至 https://finmindtrade.com 確認服務狀態。

**下一步建議：** 不要連續重試三次以上；改查較小區間。

## Rate Limit（402 / 429 請求數達上限）

**觸發條件：** HTTP 402（`Requests reach the upper limit`）或 429。

**回應模板：**
> 已達本小時請求上限（Free 600、Backer 1,600、Sponsor 6,000、Sponsor Pro 20,000 次／小時）。等 1 小時重置，或升級方案：https://finmindtrade.com/analysis/#/Sponsor/sponsor

**下一步建議：** 合併查詢區間以減少請求次數（一次查一年比逐日查好）。
