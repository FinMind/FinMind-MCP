# Windows 安裝指引

各 host 的安裝文件（[Claude Desktop](claude-desktop.md)、[Cursor](cursor.md) 等）中的指令以 macOS / Linux 為例。Windows 使用者請先照本頁完成「安裝套件」與「設定 Token」，再回到對應 host 的文件貼設定；本頁最後整理了 Windows 常見問題（尤其是 host 顯示找不到 `finmind-mcp` 指令的狀況）。

以下指令都在 **PowerShell** 執行（開始功能表搜尋「PowerShell」開啟即可，不需系統管理員權限）。

## 1. 安裝套件

擇一即可：

### 方式 A：uv（推薦，不需先安裝 Python）

[uv](https://docs.astral.sh/uv/) 會自動下載並管理 Python，適合電腦上沒有 Python 的使用者：

```powershell
winget install --id astral-sh.uv -e
# 或（沒有 winget 時）
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

裝完後**關閉 PowerShell 再開一個新視窗**（讓 PATH 生效），驗證：

```powershell
uvx finmind-mcp --help
```

之後各 host 設定中的 `command` 填 `uvx`、`args` 填 `["finmind-mcp"]`（首次啟動會自動從 PyPI 下載 `finmind-mcp`，不需另外安裝）。

### 方式 B：pipx（已有 Python 3.10+ 的使用者）

```powershell
python -m pip install --user pipx
python -m pipx ensurepath
```

關閉 PowerShell 再開新視窗，然後：

```powershell
pipx install finmind-mcp
finmind-mcp --help
```

之後各 host 設定中的 `command` 直接填 `finmind-mcp`。

> 還沒有 Python？可用 `winget install --id Python.Python.3.12 -e` 安裝，或到 [python.org](https://www.python.org/downloads/windows/) 下載安裝檔（安裝時記得勾選 **Add python.exe to PATH**）；或直接改用方式 A。

## 2. 設定 Token

先依 [token 取得指引](../knowledge/token-guide.md) 取得 FinMind Token。**最推薦的做法**是直接把 token 填進各 host 設定檔的 `env` 區塊（各 host 文件的設定範例都有 `FINMIND_TOKEN` 欄位），不必動系統環境變數。

若想改設成 Windows 環境變數：

```powershell
# 只在目前這個 PowerShell 視窗有效（適合先測試）
$env:FINMIND_TOKEN = "your-token-here"

# 永久寫入使用者環境變數
setx FINMIND_TOKEN "your-token-here"
```

注意 `setx` 只對**之後新開啟**的程式生效——已經開著的終端機、Claude Desktop 等應用程式都要完全關閉重開才讀得到。

## 3. Windows 設定檔路徑對照

各 host 文件中 `~` 開頭的路徑，在 Windows 對應如下（`%APPDATA%`、`%USERPROFILE%` 可直接貼進檔案總管的網址列開啟）：

| Host | Windows 設定檔路徑 |
|---|---|
| Claude Desktop | `%APPDATA%\Claude\claude_desktop_config.json` |
| Claude Code | `%USERPROFILE%\.claude.json` |
| Cursor（全域） | `%USERPROFILE%\.cursor\mcp.json` |
| Windsurf | `%USERPROFILE%\.codeium\windsurf\mcp_config.json` |
| Gemini CLI | `%USERPROFILE%\.gemini\settings.json` |
| Codex CLI | `%USERPROFILE%\.codex\config.toml` |

## 4. 常見問題

### host 啟動 server 失敗（找不到指令 / `ENOENT`）

最常見的 Windows 問題：`finmind-mcp` 或 `uvx` 在 PowerShell 跑得動，但 Claude Desktop 這類**圖形介面應用程式讀到的 PATH 和終端機不同**，導致 MCP server 顯示連線失敗。解法是把設定裡的 `command` 改成執行檔的**完整路徑**。先在 PowerShell 查實際位置：

```powershell
where.exe uvx           # 方式 A
where.exe finmind-mcp   # 方式 B
```

通常會是 `C:\Users\<你的帳號>\.local\bin\uvx.exe`（或 `finmind-mcp.exe`）。填進 JSON 時**反斜線要寫成 `\\`**，例如 Claude Desktop：

```json
{
  "mcpServers": {
    "finmind": {
      "command": "C:\\Users\\<你的帳號>\\.local\\bin\\uvx.exe",
      "args": ["finmind-mcp"],
      "env": {
        "FINMIND_TOKEN": "your-token-here"
      }
    }
  }
}
```

### 改了設定卻沒有生效

Claude Desktop 關閉視窗後仍會在系統匣（工作列右下角）常駐——要在系統匣圖示上按右鍵選 **Quit / 結束** 完全關閉再重開，新設定才會載入。

### `winget` 不存在

較舊的 Windows 10 可能沒有內建 `winget`。改用方式 A 的第二行 PowerShell 安裝指令，或先從 Microsoft Store 安裝「應用程式安裝程式（App Installer）」。
