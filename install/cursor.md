# Cursor

在 Cursor IDE 啟用 FinMind MCP server（本機 stdio 模式），讓 Cursor Composer / Chat 直接呼叫 FinMind 金融資料。

## 安裝套件

請先安裝 `finmind-mcp`（擇一即可）：

```bash
pipx install finmind-mcp      # 推薦：長駐安裝
# 或
uvx finmind-mcp --help        # 用 uv 即時跑，不安裝
```

## 設定

依使用範圍選擇設定檔位置：

| 範圍 | 設定檔路徑 |
|---|---|
| 單一專案 | 專案根目錄 `.cursor/mcp.json` |
| 全域（所有專案） | `~/.cursor/mcp.json` |

加入以下內容（若檔案已有其他 server，合併到同一個 `mcpServers` 物件即可）：

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

重啟 Cursor，打開 Composer / Chat 並輸入「列出 FinMind 可用的 dataset」，應該看到工具圖示出現並回傳 dataset 清單；亦可到 **Settings → MCP** 查看 finmind server 是否顯示為 connected。

![](../../docs/images/install/cursor.png)
