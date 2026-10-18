"""Registry of the FinMind v4 dedicated endpoints exposed via `query_endpoint`.

`/api/v4/data` covers most datasets, but a few are served only by their own
path with their own parameter set. Every entry here is publicly documented in
FinMind-Doc (`docs/llms.txt` / tutor) and was verified against the live API.
Adding an endpoint = adding one entry; the `query_endpoint` tool schema,
description, parameter validation and the tier hint all derive from this dict.

Deliberately NOT exposed:
- `/login`（需帳號密碼；MCP 一律用 token）
- `/health`（維運用）、`/websocket`（串流，不適合一問一答的 tool）
- `storage_objects` 走獨立工具 `download_storage_object`（回檔案，不回 JSON）
- `storage_objects?dataset=TaiwanStockFinancialReportFile`（FinMind-Doc 未公開記載）
"""

from __future__ import annotations

from typing import Any

# Parameters a caller may pass to `query_endpoint` (union over all endpoints).
PARAM_NAMES = (
    "data_id",
    "securities_trader_id",
    "date",
    "start_date",
    "end_date",
    "dataset",
)

DATALIST_DATASETS = (
    "CrudeOilPrices",
    "CurrencyCirculation",
    "ExchangeRate",
    "GovernmentBonds",
    "GovernmentBondsYield",
    "InterestRate",
    "TaiwanExchangeRate",
)

TRANSLATION_DATASETS = (
    "RawMaterialFuturesPrices",
    "TaiwanFutures",
    "TaiwanOption",
    "TaiwanStockBalanceSheet",
    "TaiwanStockCashFlowsStatement",
    "TaiwanStockDividend",
    "TaiwanStockFinancialStatements",
    "TaiwanStockInstitutionalInvestorsBuySell",
    "TaiwanStockMarginPurchaseShortSale",
    "TaiwanStockShareholding",
    "TaiwanStockTotalMarginPurchaseShortSale",
    "USStockPrice",
)

# required:   every param must be present
# one_of:     at least one of these must be present
# optional:   allowed but not required
# multi:      params that accept a list (sent as repeated query keys)
ENDPOINTS: dict[str, dict[str, Any]] = {
    "taiwan_stock_trading_daily_report": {
        "dataset": "TaiwanStockTradingDailyReport",
        "tier": "Sponsor",
        "required": ("date",),
        "one_of": ("data_id", "securities_trader_id"),
        "optional": (),
        "multi": (),
        "summary": (
            "分點進出（單日）：data_id=股票代號 或 securities_trader_id=券商分點代號"
            "（擇一或都帶），date=單日"
        ),
    },
    "taiwan_stock_warrant_trading_daily_report": {
        "dataset": "TaiwanStockWarrantTradingDailyReport",
        "tier": "Sponsor",
        "required": ("date",),
        "one_of": ("data_id", "securities_trader_id"),
        "optional": (),
        "multi": (),
        "summary": (
            "權證分點進出（單日，2023-06-21 起）：data_id=權證代號 或 "
            "securities_trader_id=券商分點代號，date=單日"
        ),
    },
    "taiwan_stock_trading_daily_report_secid_agg": {
        "dataset": "TaiwanStockTradingDailyReportSecIdAgg",
        "tier": "Sponsor",
        "required": ("data_id", "securities_trader_id", "start_date", "end_date"),
        "one_of": (),
        "optional": (),
        "multi": (),
        "summary": (
            "券商分點統計（每日每股每分點買賣股數與均價，2021-06-30 起）："
            "data_id、securities_trader_id、start_date、end_date 皆必填"
        ),
    },
    "taiwan_stock_tick_snapshot": {
        "dataset": "taiwan_stock_tick_snapshot",
        "tier": "Sponsor",
        "required": (),
        "one_of": (),
        "optional": ("data_id",),
        "multi": ("data_id",),
        "summary": (
            "台股即時報價快照：data_id=股票代號或 3 碼指數代號（如 001 加權指數），"
            "可傳陣列一次取多檔；省略則回全市場"
        ),
    },
    "taiwan_futures_snapshot": {
        "dataset": "taiwan_futures_snapshot",
        "tier": "Sponsor",
        "required": (),
        "one_of": (),
        "optional": ("data_id",),
        "multi": ("data_id",),
        "summary": "期貨即時報價快照：data_id=期貨代號（如 TXF），省略則回全部",
    },
    "taiwan_options_snapshot": {
        "dataset": "taiwan_options_snapshot",
        "tier": "Sponsor",
        "required": (),
        "one_of": (),
        "optional": ("data_id",),
        "multi": ("data_id",),
        "summary": (
            "選擇權即時報價快照：data_id=契約系列（TXO 月選、TX1~TX5 週三週選、"
            "TXU/TXV/TXX/TXY/TXZ 週五週選），省略則回全部（約 2000 列）"
        ),
    },
    "datalist": {
        "dataset": None,
        "tier": "Free",
        "required": ("dataset",),
        "one_of": (),
        "optional": (),
        "multi": (),
        "summary": (
            "列出某 dataset 可用的 data_id 值；dataset 只接受 "
            + "、".join(DATALIST_DATASETS)
        ),
    },
    "translation": {
        "dataset": None,
        "tier": "Free",
        "required": ("dataset",),
        "one_of": (),
        "optional": (),
        "multi": (),
        "summary": (
            "欄位中英對照（財報 type 等）；dataset 只接受 "
            + "、".join(TRANSLATION_DATASETS)
        ),
    },
}

# Datasets that `/api/v4/data` rejects (422) — they only live on a dedicated
# endpoint. `query_dataset` answers these with a pointer instead of a doomed call.
DEDICATED_ONLY_DATASETS: dict[str, str] = {
    "TaiwanStockTradingDailyReportSecIdAgg": "taiwan_stock_trading_daily_report_secid_agg",
    "taiwan_stock_tick_snapshot": "taiwan_stock_tick_snapshot",
    "taiwan_futures_snapshot": "taiwan_futures_snapshot",
    "taiwan_options_snapshot": "taiwan_options_snapshot",
}


# --- storage_objects ---------------------------------------------------------

# Whole-day parquet datasets (Sponsor Pro). Value = column that `data_id`
# filters on. Column names verified against real files (2026-10-16).
STORAGE_OBJECT_DATASETS: dict[str, str] = {
    "TaiwanStockPriceTick": "stock_id",
    "TaiwanStockKBar": "stock_id",
    "TaiwanStockTradingDailyReport": "stock_id",
    "TaiwanStockWarrantTradingDailyReport": "stock_id",
    "TaiwanStockTradingDailyReportSecIdAgg": "stock_id",
    "TaiwanFuturesTick": "futures_id",
    "TaiwanFuturesKBar": "futures_id",
    "TaiwanOptionTick": "option_id",
}

STORAGE_OBJECT_TIER = "Sponsor Pro"

# Datasets whose whole-day file carries a `securities_trader_id` column.
STORAGE_OBJECT_BROKER_DATASETS = frozenset(
    {
        "TaiwanStockTradingDailyReport",
        "TaiwanStockWarrantTradingDailyReport",
        "TaiwanStockTradingDailyReportSecIdAgg",
    }
)


def validate_params(endpoint: str, params: dict[str, Any]) -> str | None:
    """Return a 繁中 error message if `params` don't fit `endpoint`, else None."""
    spec = ENDPOINTS[endpoint]
    allowed = set(spec["required"]) | set(spec["one_of"]) | set(spec["optional"])
    extra = sorted(k for k in params if k not in allowed)
    if extra:
        return (
            f"`{endpoint}` 不接受參數 {', '.join(f'`{k}`' for k in extra)}。"
            f"可用參數：{_fmt_allowed(spec)}。"
        )
    missing = [k for k in spec["required"] if not params.get(k)]
    if missing:
        return (
            f"`{endpoint}` 缺少必填參數 {', '.join(f'`{k}`' for k in missing)}。"
            f"可用參數：{_fmt_allowed(spec)}。"
        )
    if spec["one_of"] and not any(params.get(k) for k in spec["one_of"]):
        return (
            f"`{endpoint}` 需要 {' 或 '.join(f'`{k}`' for k in spec['one_of'])}"
            "（至少帶一個）。"
        )
    for key, value in params.items():
        if isinstance(value, list) and key not in spec["multi"]:
            return f"`{endpoint}` 的 `{key}` 只接受單一值，不接受陣列。"
    return None


def _fmt_allowed(spec: dict[str, Any]) -> str:
    parts = []
    if spec["required"]:
        parts.append("必填 " + "、".join(spec["required"]))
    if spec["one_of"]:
        parts.append("擇一 " + "/".join(spec["one_of"]))
    if spec["optional"]:
        parts.append("選填 " + "、".join(spec["optional"]))
    return "；".join(parts) or "（無）"
