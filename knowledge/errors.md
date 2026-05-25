## 401 Unauthorized（Token 無效）

**觸發條件：** FinMind API 回應 HTTP 401，或 Token 未設定（ChatGPT 端 Action 未填 API Key；MCP 端 `FINMIND_TOKEN` 環境變數不存在）。

**回應模板：**
> 您的 FinMind Token 無法驗證。請確認下列三點：
> 1. Token 是否正確複製（前後無多餘空白、無換行）
> 2. 是否已完成註冊信箱驗證
> 3. 是否使用最新 Token（重設密碼後舊 Token 會失效）
>
> 取得或重新產生 Token：https://finmindtrade.com/analysis/#/account/user
>
> 設定完成後請再試一次，或告訴我哪一步驟卡住了。

**下一步建議：**
- ChatGPT：請使用者到 GPT 設定頁的「Authentication」面板重新填入 Token。
- MCP host：請使用者編輯 MCP server 設定檔的 `env.FINMIND_TOKEN`，並重啟 host。

## 402 Payment Required（需 sponsor 方案）

**觸發條件：** FinMind API 回應 HTTP 402，或回傳 JSON `status: 402`。代表此 dataset 屬於 sponsor 等級，免費 / backer 方案無權限存取。

**回應模板：**
> 您查詢的資料集需要 **Sponsor 會員**權限才能存取。
>
> 此資料集屬於進階資料（例如分點進出、即時報價、鉅額交易、借貸款項擔保品餘額等），免費與 Backer 方案無法存取。
>
> 升級 Sponsor 方案：https://finmindtrade.com/analysis/#/account/pricing
>
> 升級後 Token 不需更換，立即生效。

**下一步建議：**
- 若使用者只是想試水溫，可建議改查同主題的免費 dataset（例如 sponsor 的 `TaiwanStockTradingDailyReport` 改用免費的 `TaiwanStockInstitutionalInvestorsBuySell`）。
- 列出 FinMind 各方案差異，協助使用者判斷。

## 空資料（`data: []`）

**觸發條件：** FinMind API 回應 HTTP 200 但 `data` 為空陣列。常見原因：股票代號錯誤、日期區間內無交易日、dataset 尚未涵蓋該標的、未來日期。

**回應模板：**
> 在指定條件下查無資料。可能原因：
> 1. 股票代號錯誤（例：`2330` 為台積電，請確認代號）
> 2. 日期區間內全為假日 / 非交易日
> 3. 此資料集尚未涵蓋該標的，或起始日期早於資料庫最早日
> 4. 日期超過今日（無未來資料）
>
> 請確認後再試，或告訴我您想查詢的標的與大致時間，我可以協助您調整。

**下一步建議：**
- 主動以 `TaiwanStockInfo` 驗證代號是否存在。
- 將日期區間擴大（例如從「最近一週」改為「最近一個月」）後重試。
- 若是新上市 / 新編資料集，提醒使用者可能還沒回補歷史資料。

## HTTP Timeout / 5xx（暫時連線異常）

**觸發條件：** httpx 拋出 `TimeoutException`、`ConnectError`，或 FinMind API 回應 HTTP 500 / 502 / 503 / 504。

**回應模板：**
> FinMind 服務目前回應較慢或暫時無法連線，這通常是短暫狀況。
>
> 請稍候 1 - 2 分鐘後再試一次。若連續失敗超過 10 分鐘，可至 FinMind 官網確認服務狀態：https://finmindtrade.com
>
> 若情況持續，您可以將本次查詢條件回報給我，我會記錄下來。

**下一步建議：**
- 不要立即重試三次以上，避免加重上游負載。
- 若使用者連續多次遇到同一錯誤，建議改查較小區間或縮減 dataset。

## Rate Limit（429 或請求數達上限）

**觸發條件：** FinMind API 回應 HTTP 429，或回傳訊息提示請求數達上限。各方案上限：Free 600 req/hr、Backer 1,600 req/hr、Sponsor 6,000 req/hr、SponsorPro 20,000 req/hr。

**回應模板：**
> 您目前的請求數已達 FinMind 方案上限。
>
> 各方案每小時請求數：
> - Free：600 次
> - Backer：1,600 次
> - Sponsor：6,000 次
> - SponsorPro：20,000 次
>
> 解法：
> 1. 等待 1 小時後配額會重置
> 2. 升級方案以提高上限：https://finmindtrade.com/analysis/#/account/pricing
>
> 升級後 Token 不需更換，立即生效。

**下一步建議：**
- 提示使用者可合併查詢區間，減少請求次數（例如一次查一年比一次查一天好）。
- 若是 MCP 端密集呼叫，建議在 host 端加入快取或調整查詢頻率。
