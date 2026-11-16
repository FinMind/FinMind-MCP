# 資料品質保證

FinMind 每月對資料集進行一次全面品質驗證，並把結果公開在「資料品質保證」頁面。用戶問「資料可不可靠」「怎麼驗證」「某個 dataset 的品質如何」時，依本頁引導。

## 連結

| 頁面 | 中文 | English |
|---|---|---|
| 資料品質總覽 | https://finmind.github.io/DataQuality/ | https://finmind.github.io/en/DataQuality/ |
| 檢測方法 | https://finmind.github.io/DataQuality/Methodology/ | https://finmind.github.io/en/DataQuality/Methodology/ |
| 單一 dataset 報告 | `https://finmind.github.io/DataQuality/{Dataset}/` | `https://finmind.github.io/en/DataQuality/{Dataset}/` |
| 機器可讀摘要 | https://finmind.github.io/DataQuality/summary.json | 同左 |

`{Dataset}` 為 dataset 名稱，例如 https://finmind.github.io/DataQuality/TaiwanStockPrice/ 。

## 檢測方式

- **與官方來源交叉核對：** 抽樣代表性代號與期間，把 FinMind 的數字與官方公開資料的同一數字逐筆核對，計算一致比例；國際股價等由資料來源提供的資料，則與資料來源的原始值逐筆核對。
- **每月全面檢測：** 每月上旬對每個資料集執行 9 項自動檢測，全程只透過公開 API 進行，完成後更新總覽與各資料集報告（頁首標示本期月份與檢測日期）。
- **依官方來源更新：** 官方來源有更新或補充時同步更新資料，並在更新公告（https://finmind.github.io/WhatIsNew/ ）說明。

9 項檢測：

| 檢測項目 | 內容 |
|---|---|
| 資料更新時效 | 最新資料日與最近交易日（或應有期別）同步 |
| 交易日涵蓋率 | 依官方交易日曆抽樣，每個交易日都有資料且筆數合理 |
| 補行交易日涵蓋 | 週六補行交易日的資料完整 |
| 與官方來源一致率 | 與官方公開資料逐筆核對的一致比例 |
| 跨資料集一致性 | 相關資料集互相勾稽（例如日成交量與逐筆成交加總） |
| 查詢方式一致性 | 單日、區間、指定代號查詢結果一致 |
| 欄位格式一致性 | 各年度數值欄位的小數位數與型別一致 |
| 數值與主鍵一致性 | 數量金額非負、最高價不低於最低價、主鍵完整不重複等 |
| 每日內容獨立性 | 不同日期的內容各自獨立 |

結果標示：**已驗證**（所有適用項目皆通過）、**通過**、**資料特性說明**（結果反映資料本身特性，例如官方來源開始提供的日期、市場交易制度，報告附說明）、**不適用**、**規劃中**（將於後續納入，目前用於跨資料集一致性）。

## 回答方式

1. MCP host 先呼叫 `get_data_quality`：帶 `dataset` 取得該資料集的檢測日期、結果、官方一致率與報告連結；不帶則回傳總覽。ChatGPT 直接提供上方連結。
2. 回覆時附上該 dataset 的報告頁連結與總覽連結，簡述檢測方式（9 項檢測、與官方公開資料逐筆比對、每月更新）。
3. 報告頁附有「可重現查詢」參數，用戶可用自己的 token 呼叫 API 自行驗證。
4. 只引述報告內容；檢測採抽樣，結論適用於本期抽樣範圍。用戶對特定數值有疑問時，請對方提供 dataset、代號與日期，並引導到 https://finmind.github.io/Contact/ 聯繫。
