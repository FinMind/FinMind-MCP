# Claude Desktop

在 Claude Desktop 桌面應用程式啟用 FinMind MCP server，讓 Claude 直接呼叫 FinMind 金融資料。

先依 [token 取得指引](../knowledge/token-guide.md) 取得 FinMind Token，再選擇以下任一方式安裝。

## 方式一：一鍵安裝擴充套件（推薦）

不需要安裝 Python、不需要編輯設定檔，Windows / macOS 步驟相同：

1. 下載 **[finmind.mcpb](https://github.com/FinMind/FinMind-MCP/releases/latest/download/finmind.mcpb)**
2. 在下載的檔案上**點兩下**，Claude Desktop 會跳出安裝視窗（若沒有反應：開啟 Claude Desktop →「設定」→「擴充功能（Extensions）」，把檔案拖進視窗）
3. 按「安裝」，在「FinMind Token」欄位貼上 token，確認啟用

第一次使用時 Claude Desktop 會自動下載執行環境，約需數十秒。

> 更新版本：重新下載上面的連結再安裝一次即可。

## 方式二：手動編輯設定檔

適合想自行管理套件版本的使用者。

### 安裝套件

```bash
pipx install finmind-mcp      # 推薦：長駐安裝
# 或
uvx finmind-mcp --help        # 用 uv 即時跑，不安裝
```

> **Windows 使用者**：`pipx`/`uvx` 的安裝方式、token 設定與常見 PATH 問題，請先看 [Windows 安裝指引](windows.md)。

### 設定

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

## 驗證

（方式二需先完全結束並重開 Claude Desktop）在對話框輸入「列出 FinMind 可用的 dataset」，應該看到工具圖示出現並回傳 dataset 清單。

![](../../docs/images/install/claude-desktop.png)

## 常見問題

### 擴充套件顯示無法連線

1. 確認 token 有貼對：「設定」→「擴充功能」→ FinMind →「設定」重新貼上。
2. 第一次啟動需要下載執行環境，網路較慢時可能逾時；等一分鐘後關閉再開啟擴充套件。
3. 仍失敗時，安裝 [uv](https://docs.astral.sh/uv/getting-started/installation/)（Windows：PowerShell 執行 `winget install --id astral-sh.uv -e`），然後從系統匣（工作列右下角）圖示按右鍵**結束** Claude Desktop 再重開。
