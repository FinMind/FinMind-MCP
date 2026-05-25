# Windsurf

在 Windsurf IDE 啟用 FinMind MCP server（本機 stdio 模式），讓 Cascade 直接呼叫 FinMind 金融資料。

## 安裝套件

請先安裝 `finmind-mcp`（擇一即可）：

```bash
pipx install finmind-mcp      # 推薦：長駐安裝
# 或
uvx finmind-mcp --help        # 用 uv 即時跑，不安裝
```

## 設定

編輯設定檔 `~/.codeium/windsurf/mcp_config.json`（檔案不存在請自行建立），加入以下內容（若已有其他 server，合併到同一個 `mcpServers` 物件即可）：

```json
{
  "mcpServers": {
    "finmind": {
      "command": "finmind-mcp",
      "env": {
        "FINMIND_TOKEN": "your-token-here"
      }
    }
  }
}
```

## 取得 Token

請先依 [token 取得指引](../knowledge/token-guide.md) 取得 FinMind Token，並設定環境變數 `FINMIND_TOKEN`（或填入上方設定）。

## 驗證

重啟 Windsurf，在 Cascade 對話框輸入「列出 FinMind 可用的 dataset」，應該看到工具圖示出現並回傳 dataset 清單；亦可到 **Settings → Cascade → MCP servers** 確認 finmind 是否顯示為已連線。

![](../../docs/images/install/windsurf.png)
