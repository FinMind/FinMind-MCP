# Claude Desktop

在 Claude Desktop 桌面應用程式啟用 FinMind MCP server（本機 stdio 模式），讓 Claude 直接呼叫 FinMind 金融資料。

## 安裝套件

請先安裝 `finmind-mcp`（擇一即可）：

```bash
pipx install finmind-mcp      # 推薦：長駐安裝
# 或
uvx finmind-mcp --help        # 用 uv 即時跑，不安裝
```

> **Windows 使用者**：`pipx`/`uvx` 的安裝方式、token 設定與常見 PATH 問題，請先看 [Windows 安裝指引](windows.md)。

## 設定

依您的作業系統，編輯對應的設定檔：

| 作業系統 | 設定檔路徑 |
|---|---|
| macOS | `~/Library/Application Support/Claude/claude_desktop_config.json` |
| Windows | `%APPDATA%\Claude\claude_desktop_config.json` |
| Linux | `~/.config/Claude/claude_desktop_config.json` |

加入以下 `mcpServers` 區塊（若檔案已有其他 server，合併到同一個 `mcpServers` 物件即可）：

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

重啟 Claude Desktop，在對話框輸入「列出 FinMind 可用的 dataset」，應該看到工具圖示出現並回傳 dataset 清單。

![](../../docs/images/install/claude-desktop.png)
