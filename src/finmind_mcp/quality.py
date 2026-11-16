"""`get_data_quality` — FinMind 公開資料品質報告摘要。

讀取 FinMind-Doc 發佈的機器可讀摘要 `summary.json`（每月更新），回傳單一
dataset 或總覽的檢測日期、結果、官方一致率與報告頁連結。summary.json 是
公開靜態檔，不需要 FinMind token。

讀不到（網路錯誤、格式不符）時回傳說明文字與總覽頁連結，不丟例外。
"""

from __future__ import annotations

import difflib
from typing import Any, Optional

import httpx

SUMMARY_URL = "https://finmind.github.io/DataQuality/summary.json"
SITE = "https://finmind.github.io"
OVERVIEW_URL = {"zh": f"{SITE}/DataQuality/", "en": f"{SITE}/en/DataQuality/"}
METHODOLOGY_URL = {
    "zh": f"{SITE}/DataQuality/Methodology/",
    "en": f"{SITE}/en/DataQuality/Methodology/",
}
TIMEOUT = 15.0

# summary.json 的檢測代碼 → 顯示名稱（順序同各資料集報告頁）。
CHECKS: dict[str, dict[str, str]] = {
    "D9": {"zh": "資料更新時效", "en": "Freshness"},
    "D2cal": {"zh": "交易日涵蓋率", "en": "Trading-day coverage"},
    "D2sat": {"zh": "補行交易日涵蓋", "en": "Make-up trading-day coverage"},
    "OFF": {"zh": "與官方來源一致率", "en": "Official-source match rate"},
    "XCHK": {"zh": "跨資料集一致性", "en": "Cross-dataset consistency"},
    "D6": {"zh": "查詢方式一致性", "en": "Query consistency"},
    "D5": {"zh": "欄位格式一致性", "en": "Field format consistency"},
    "D8": {"zh": "數值與主鍵一致性", "en": "Value & key consistency"},
    "D3": {"zh": "每日內容獨立性", "en": "Daily content independence"},
}
STATUS: dict[str, dict[str, str]] = {
    "pass": {"zh": "通過", "en": "Pass"},
    "note": {"zh": "資料特性說明", "en": "Data characteristic noted"},
    "na": {"zh": "不適用", "en": "N/A"},
    "planned": {"zh": "規劃中", "en": "Planned"},
}
OVERALL: dict[str, dict[str, str]] = {
    "validated": {"zh": "已驗證", "en": "Validated"},
    "validated_notes": {
        "zh": "已驗證・附資料特性說明",
        "en": "Validated, with data notes",
    },
}


async def fetch_summary(url: str = SUMMARY_URL, timeout: float = TIMEOUT) -> dict[str, Any]:
    """Download and minimally validate summary.json. Raises on any failure."""
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as http:
        resp = await http.get(url)
        resp.raise_for_status()
        data = resp.json()
    if not isinstance(data, dict) or not isinstance(data.get("datasets"), list):
        raise ValueError("unexpected summary.json format")
    return data


def report_url(dataset: str, lang: str = "zh") -> str:
    prefix = f"{SITE}/en" if lang == "en" else SITE
    return f"{prefix}/DataQuality/{dataset}/"


def _label(table: dict[str, dict[str, str]], key: Any) -> str:
    # 輸出一律繁中；lang 只決定報告頁連結的語言版本。
    entry = table.get(str(key))
    return entry["zh"] if entry else str(key)


def _rate(value: Any) -> str:
    if isinstance(value, (int, float)):
        return f"{value * 100:.2f}%"
    return "—"


def unavailable_message(lang: str = "zh") -> str:
    return (
        "目前無法取得資料品質摘要，請稍後再試，或直接查看資料品質總覽："
        f"{OVERVIEW_URL[lang]}（檢測方法：{METHODOLOGY_URL[lang]}）"
    )


def format_dataset(summary: dict[str, Any], dataset: str, lang: str = "zh") -> str:
    records = {
        str(r.get("dataset")): r for r in summary.get("datasets", []) if isinstance(r, dict)
    }
    rec = records.get(dataset)
    if rec is None:
        # Case-insensitive fallback (e.g. "taiwanstockprice").
        lowered = {name.lower(): name for name in records}
        if dataset.lower() in lowered:
            rec = records[lowered[dataset.lower()]]
    if rec is None:
        close = difflib.get_close_matches(dataset, list(records), n=3, cutoff=0.6)
        lines = [f"資料品質報告依 dataset 名稱查詢，`{dataset}` 請直接參考資料品質總覽：{OVERVIEW_URL[lang]}"]
        if close:
            lines.append("名稱相近的 dataset 報告：")
            lines.extend(f"- `{n}`：{report_url(n, lang)}" for n in close)
        lines.append(f"檢測方法：{METHODOLOGY_URL[lang]}")
        return "\n".join(lines)

    name = str(rec.get("dataset"))
    lines = [f"### {name} 資料品質報告（{summary.get('edition', '')}）"]
    lines.append(f"- 驗證結果：**{_label(OVERALL, rec.get('overall'))}**")
    lines.append(f"- 檢測日期：{rec.get('run_date') or summary.get('run_date', '')}")
    if rec.get("first_date") and rec.get("last_date"):
        lines.append(f"- 資料期間：{rec['first_date']} ～ {rec['last_date']}")
    lines.append(f"- 與官方來源一致率：{_rate(rec.get('official_match_rate'))}")
    if rec.get("cross_dataset_match_rate") is not None:
        lines.append(f"- 跨資料集一致率：{_rate(rec.get('cross_dataset_match_rate'))}")
    lines.append(f"- 完整報告（含資料特性說明與可重現查詢）：{report_url(name, lang)}")
    lines.append("")
    lines.append("| 檢測項目 | 結果 |")
    lines.append("| --- | --- |")
    checks = rec.get("checks") or {}
    for code in [c for c in CHECKS if c in checks] + [c for c in checks if c not in CHECKS]:
        lines.append(f"| {_label(CHECKS, code)} | {_label(STATUS, checks[code])} |")
    lines.append("")
    lines.append(
        "_每月對資料集執行 9 項檢測，與官方公開資料（或資料來源原始值）逐筆比對；"
        f"採抽樣驗證，結論適用於本期抽樣範圍。總覽：{OVERVIEW_URL[lang]}；"
        f"檢測方法：{METHODOLOGY_URL[lang]}_"
    )
    return "\n".join(lines)


def format_overview(summary: dict[str, Any], lang: str = "zh") -> str:
    records = [r for r in summary.get("datasets", []) if isinstance(r, dict)]
    groups = summary.get("groups") or {}
    validated = sum(1 for r in records if str(r.get("overall", "")).startswith("validated"))
    with_official = sum(1 for r in records if r.get("official_match_rate") is not None)
    lines = [f"### FinMind 資料品質總覽（{summary.get('edition', '')}）"]
    lines.append(f"- 檢測日期：{summary.get('run_date', '')}")
    lines.append(f"- 公開驗證報告：{len(records)} 個資料集，已驗證 {validated} 個")
    lines.append(f"- 與官方公開資料或資料來源原始值逐筆比對：{with_official} 個資料集")
    lines.append(
        "- 檢測方式：每月執行 9 項檢測（更新時效、交易日涵蓋、補行交易日、與官方來源一致率、"
        "跨資料集一致性、查詢方式／欄位格式／數值與主鍵一致性、每日內容獨立性）"
    )
    lines.append(f"- 總覽頁：{OVERVIEW_URL[lang]}")
    lines.append(f"- 檢測方法：{METHODOLOGY_URL[lang]}")
    lines.append("")
    lines.append("| 分類 | Dataset | 結果 | 官方一致率 |")
    lines.append("| --- | --- | --- | --- |")
    order = list(groups) + sorted({str(r.get("group")) for r in records} - set(groups))
    for group in order:
        label = groups[group].get("zh") if isinstance(groups.get(group), dict) else None
        for r in sorted(
            (r for r in records if str(r.get("group")) == group),
            key=lambda r: str(r.get("dataset")),
        ):
            lines.append(
                f"| {label or group} | {r.get('dataset')} | "
                f"{_label(OVERALL, r.get('overall'))} | {_rate(r.get('official_match_rate'))} |"
            )
    lines.append("")
    lines.append(
        "_單一資料集的 9 項檢測結果與報告連結：帶 `dataset` 參數再查一次，"
        f"或開啟 {report_url('{Dataset}', lang)}。_"
    )
    return "\n".join(lines)


async def get_data_quality(dataset: Optional[str] = None, lang: str = "zh") -> str:
    lang = "en" if str(lang).lower().startswith("en") else "zh"
    try:
        summary = await fetch_summary()
    except Exception:  # noqa: BLE001 — network / HTTP / JSON errors all degrade the same way
        return unavailable_message(lang)
    dataset = (dataset or "").strip()
    if dataset:
        return format_dataset(summary, dataset, lang)
    return format_overview(summary, lang)
