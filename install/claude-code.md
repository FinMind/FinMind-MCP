# Claude Code

在 Claude Code CLI 啟用 FinMind MCP server（本機 stdio 模式），讓您在終端機開發時直接查詢 FinMind 金融資料。

## 安裝套件

請先安裝 `finmind-mcp`（擇一即可）：

```bash
pipx install finmind-mcp      # 推薦：長駐安裝
# 或
uvx finmind-mcp --help        # 用 uv 即時跑，不安裝
```

> **Windows 使用者**：`pipx`/`uvx` 的安裝方式、token 設定與常見 PATH 問題，請先看 [Windows 安裝指引](windows.md)。

## 設定

使用 `claude mcp add` 指令一鍵註冊（推薦）：

```bash
claude mcp add finmind --env FINMIND_TOKEN=your-token-here -- finmind-mcp
```

或者手動編輯 `~/.claude.json`，在 `mcpServers` 區塊加入：

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

重新啟動 Claude Code session（`claude` 或 `/exit` 再進來），輸入「列出 FinMind 可用的 dataset」，應該看到工具圖示出現並回傳 dataset 清單；亦可用 `/mcp` 指令查看 finmind server 連線狀態。

![](../../docs/images/install/claude-code.png)
