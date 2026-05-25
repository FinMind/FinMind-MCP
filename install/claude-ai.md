# Claude.ai（Web）

在 Claude.ai 網頁版透過 remote MCP integration 連接 FinMind 官方 server，免本機安裝即可使用。

## 安裝套件

Claude.ai 為 remote 模式，**不需要**在本機安裝任何套件，全部由官方 host `https://mcp.finmindtrade.com` 提供。

> 目前 remote endpoint 尚在部署中（coming soon）。在正式上線前，Claude.ai 用戶建議改用 [Claude Desktop](./claude-desktop.md) 走本機 stdio 模式。

## 設定

待 `mcp.finmindtrade.com` 部署上線後，設定步驟如下：

1. 打開 Claude.ai → 右上角頭像 → **Settings**
2. 進入 **Integrations** 分頁
3. 點 **Add custom integration**
4. 在 URL 欄位填入：

   ```
   https://mcp.finmindtrade.com/sse
   ```

5. 按 **Connect**，瀏覽器會跳到 finmindtrade.com OAuth 授權頁，用既有帳號登入並按「允許」即可完成註冊。

## 取得 Token

請先依 [token 取得指引](../knowledge/token-guide.md) 取得 FinMind Token。

> Remote 模式採 OAuth flow：首次連線會引導完成 FinMind Token 授權，授權後 token 由 Claude.ai 端管理，您**不需要**手動貼 token 到對話框。要撤銷授權請到 finmindtrade.com 會員中心 → 已授權應用 → 移除。

## 驗證

回到 Claude.ai 任一對話視窗，輸入「列出 FinMind 可用的 dataset」，應該看到工具圖示出現並回傳 dataset 清單；亦可到 **Settings → Integrations** 確認 FinMind 顯示為 **Connected**。

![](../../docs/images/install/claude-ai.png)
