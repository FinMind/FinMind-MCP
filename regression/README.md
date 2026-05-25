# Regression — 上線前驗證

兩條 distribution（MCP server / ChatGPT Custom GPT）共用 `knowledge/` 知識包。
這個 runner 是上線前的**伺服器端契約測試**：對 `knowledge/regression.md` 裡的每一題
canonical query，用「期望的 tool + params」實際打 **live FinMind API**，驗證回傳資料
形狀正確（欄位、列數、關鍵字串）。

## 跑法

```bash
FINMIND_TOKEN=<your-token> uv run python regression/runner.py
uv run python regression/runner.py --min 10     # 自訂通過門檻（預設 9/12）
```

成功時 exit code 0，未達門檻時為 1（方便接 CI）。

```
[1/12] PASS — R1 個股最近一週股價
...
12/12 passed（門檻 9）
```

## 它測什麼、不測什麼

**會測（server-side 契約）：** 給定正確的 tool + params，live API 是否回傳形狀正確的資料，
並由 server 正確渲染成表格。這能抓到「endpoint 路徑錯」「dataset 名稱/欄位變了」「canonical
範例的 data_id 寫錯」等問題——例如本套件初版就靠它抓到所有 endpoint 漏了 `/api` 前綴。

**不會測（LLM-side，需人工在真實 GPT/Claude 上驗）：**
- 模型是否能從自然語言**選對** tool / dataset / params（runner 直接餵正確 params，不經過模型）
- 純敘述型 pass criteria，例如 R9「要提到 K 線/圖」、R10「要有比較性敘述」

這些題目在 runner 內標了 `note`，只驗其中 server-side 可檢的部分（資料形狀），輸出末尾會列出
需人工驗證的項目。

## SSOT 與同步保護

`knowledge/regression.md` 是**人類可讀的題庫 SSOT**；`runner.py` 的 `CASES` 是它的可執行鏡像
（params 取自 spec，欄位/列數斷言寫在程式碼裡，因為散文 pass-criteria 無法穩定 parse）。

啟動時 runner 會 parse `regression.md` 的 `### Rn:` 標題，若與 `CASES` 的案例集合不一致
（新增/刪除/改名）會直接報錯拒跑，避免兩邊默默 drift。改題庫時請兩邊一起改。

## 注意

- 會真的消耗 API quota（12 題、約 13 次呼叫）。
- 使用 spec 內的固定日期（today=2026-05-17），都落在過去，故 live API 有資料、結果穩定。
- 部分 dataset 需較高會員等級；若 token 等級不足可能個別失敗（門檻預設 9/12 留有餘裕）。
