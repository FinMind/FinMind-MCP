# FinMind Token 取得與設定

FinMind 所有 API 請求都需要 token；本文件說明如何取得，並在 ChatGPT Custom GPT
與各種 MCP host（Claude Desktop / Claude Code / Cursor / Windsurf / Gemini CLI / Claude.ai）
完成設定。

## 1. 取得 Token

1. 開啟會員中心：https://finmindtrade.com/analysis/#/account/user
   （未登入會自動導向登入 / 註冊頁；首次使用請先註冊並完成信箱驗證）
2. 進入會員中心後 → **API Token** 分頁 → 點「複製」
3. 將 token 妥善保存（之後設定都會用到）；token 等同帳號密碼，請勿公開貼到 GitHub / 截圖

> 免費（Free）方案即可使用大多數基本 dataset；分點、八大行庫、即時 tick、可轉債、
> 部分衍生性商品等進階 dataset 需要 Backer / Sponsor 方案，可在會員中心升級。

## 2. 在 ChatGPT 設定（FinMind Custom GPT）

FinMind Custom GPT 透過 OpenAPI Action 呼叫 `api.finmindtrade.com`，token 以 HTTP
`Authorization: Bearer <token>` header 帶入，由 ChatGPT 端代為附加（Action 認證類型選
**API Key → Auth Type: Bearer**）。

設定步驟：

1. 開啟 FinMind Custom GPT（GPT Store 連結公佈後補上）
2. 第一次發問並觸發 Action（例：「台積電最近一週股價」）時，ChatGPT 會彈出
   「Sign in with API Key」對話框
3. 在欄位中貼上步驟 1 取得的 token，按 **Save** 或 **Confirm**
4. 之後同一 conversation 不會再問，token 由 ChatGPT 帳號管理；
   如要更新，請到 ChatGPT → Settings → Connectors / Builder profile → FinMind → 重新登入

注意事項：

- ChatGPT Action 設定畫面中**不要**把 token 寫進 GPT instructions；ChatGPT 已提供
  per-user API key 機制，多人使用時各自輸入各自的 token
- 若回覆出現 `401 Unauthorized`，先到 finmindtrade.com 確認 token 還在有效期，再重新
  在 ChatGPT 端輸入一次

## 3. 在 MCP host 設定

FinMind MCP server 有兩種 transport，token 設定方式不同。

### stdio 模式（Claude Desktop / Claude Code / Cursor / Windsurf / Gemini CLI）

stdio 模式由 host 在本機啟動 `finmind-mcp` process，token 透過環境變數
`FINMIND_TOKEN` 傳入。各 host 的設定檔位置：

| Host | 設定檔路徑 | 設定方式 |
|---|---|---|
| Claude Desktop | macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`<br>Windows: `%APPDATA%\Claude\claude_desktop_config.json` | 編輯 JSON，在 `mcpServers.finmind.env.FINMIND_TOKEN` 填入 token |
| Claude Code | 由 CLI 管理 | `claude mcp add finmind --env FINMIND_TOKEN=<your-token> -- finmind-mcp` |
| Cursor | `~/.cursor/mcp.json`（global）或專案內 `.cursor/mcp.json` | 同 Claude Desktop 的 JSON 結構 |
| Windsurf | `~/.codeium/windsurf/mcp_config.json` | 同上 |
| Gemini CLI | 由 CLI 管理 | `gemini mcp add finmind --env FINMIND_TOKEN=<your-token> -- finmind-mcp` |

通用 JSON 範例（Claude Desktop / Cursor / Windsurf 適用，欄位名稱一致）：

```json
{
  "mcpServers": {
    "finmind": {
      "command": "finmind-mcp",
      "env": {
        "FINMIND_TOKEN": "貼上你的_token"
      }
    }
  }
}
```

若尚未安裝 `finmind-mcp`，先執行其中一種：

```bash
pipx install finmind-mcp      # 推薦
# 或
uvx finmind-mcp --help        # 用 uv 即時跑，不長駐安裝
```

驗證：重啟 host，輸入「列出 FinMind 可用的 dataset」，應出現 MCP 工具圖示並回覆
dataset 清單；若得到 `AuthenticationError`，請檢查環境變數是否正確設定且未含
多餘空白 / 引號。

### Remote 模式（Claude.ai integrations）

Remote 模式由官方 host `https://mcp.finmindtrade.com`（部署後啟用）提供，
Claude.ai 透過 HTTP / SSE 連線，使用 MCP 標準的 OAuth flow 取得授權：

1. Claude.ai → **Settings → Integrations → Add MCP server**
2. URL 填 `https://mcp.finmindtrade.com`（部署上線後提供，目前 placeholder）
3. 按 **Connect**，瀏覽器會跳到 finmindtrade.com OAuth 授權頁
4. 用既有帳號登入並按「允許」
5. Claude.ai 收到 access token 後完成註冊，之後直接在對話中觸發 FinMind 工具

Remote 模式下用戶**不需要**手動貼 token；授權後 token 由 Claude.ai 端管理，
撤銷請到 finmindtrade.com 會員中心 → 已授權應用 → 移除。

> 注意：remote endpoint 仍在部署中，正式 URL 上線後本檔案會同步更新。
> 在那之前，Claude.ai 用戶可改用 Claude Desktop 走 stdio 模式。
