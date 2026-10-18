"""MCP tool implementations and markdown formatting.

Seven tools are exposed:

- `query_dataset`             — generic /api/v4/data query
- `list_datasets`             — bundled dataset catalog (knowledge/datasets.md)
- `get_stock_info`            — shorthand for TaiwanStockInfo
- `query_trading_daily_report` — dedicated /api/v4/taiwan_stock_trading_daily_report
- `get_pricing`               — bundled plan pricing (knowledge/pricing.md)
- `query_endpoint`            — every other dedicated /api/v4/<endpoint>
                                 (allowlist in endpoints.py)
- `download_storage_object`   — /api/v4/storage_objects whole-day parquet,
                                 saved locally; returns a summary only

Each tool returns a markdown string. `FinMindError` subclasses raised by
`FinMindClient` are caught and converted into the 繁中 templates from
`knowledge/errors.md`. Tools never raise.
"""

from __future__ import annotations

import re
from typing import Any, Optional

from mcp.types import Tool

from . import knowledge, storage
from .client import FinMindClient
from .endpoints import (
    DEDICATED_ONLY_DATASETS,
    ENDPOINTS,
    PARAM_NAMES,
    STORAGE_OBJECT_BROKER_DATASETS,
    STORAGE_OBJECT_DATASETS,
    STORAGE_OBJECT_TIER,
    validate_params,
)
from .errors import (
    AuthenticationError,
    BadRequestError,
    DependencyMissingError,
    EmptyDataError,
    FinMindError,
    PaymentRequiredError,
    RateLimitError,
    UpstreamError,
)

# Truncate row count for inline markdown rendering. Larger results should
# be processed via the host's code interpreter.
MAX_ROWS = 500
# download_storage_object returns at most this many rows inline.
STORAGE_DEFAULT_LIMIT = 20
STORAGE_MAX_LIMIT = 500

PRICING_URL = "https://finmindtrade.com/analysis/#/Sponsor/sponsor"
_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


# --- Tool registry -----------------------------------------------------------


def _make_client() -> FinMindClient:
    """Factory hook — tests monkey-patch this to inject a FakeClient."""
    return FinMindClient()


def tool_definitions() -> list[Tool]:
    """Return MCP Tool definitions for all seven tools in stable order."""
    return [
        Tool(
            name="query_dataset",
            description=(
                "通用 FinMind 資料查詢（呼叫 /api/v4/data）。輸入 dataset 名稱"
                "（如 TaiwanStockPrice、TaiwanStockMonthRevenue）、股票代號 data_id 與"
                " start_date（YYYY-MM-DD），回傳 markdown 表格。超過 500 列會截斷"
                "並標註總列數。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "dataset": {
                        "type": "string",
                        "description": "FinMind dataset 名稱，例如 TaiwanStockPrice",
                    },
                    "data_id": {
                        "type": "string",
                        "description": "股票 / 期貨 / 選擇權代號（如 2330、TX、TXO）",
                    },
                    "start_date": {
                        "type": "string",
                        "description": "查詢起始日 YYYY-MM-DD",
                    },
                    "end_date": {
                        "type": "string",
                        "description": "查詢結束日 YYYY-MM-DD（可選）",
                    },
                },
                "required": ["dataset"],
            },
        ),
        Tool(
            name="list_datasets",
            description=(
                "列出 FinMind 支援的所有 dataset（讀取內建知識庫，不需連線）。"
                "依分類回傳 dataset 名稱、會員層級與說明的 markdown 條列。"
            ),
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="get_stock_info",
            description=(
                "查詢台股代號 / 中文名 / 產業別總覽（呼叫 TaiwanStockInfo）。"
                "可選 stock_id 指定單一標的；未提供時回傳全市場清單（會截斷）。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "stock_id": {
                        "type": "string",
                        "description": "股票代號，如 2330。省略則回傳全市場清單。",
                    }
                },
            },
        ),
        Tool(
            name="query_trading_daily_report",
            description=(
                "查詢券商分點進出（呼叫 /api/v4/taiwan_stock_trading_daily_report）。"
                "必填單一日期 date（非區間），並帶股票代號 data_id 或券商分點代號"
                " securities_trader_id（擇一或都帶）。需要 Sponsor 等級。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "data_id": {
                        "type": "string",
                        "description": "股票代號，例如 2330（與 securities_trader_id 擇一）",
                    },
                    "securities_trader_id": {
                        "type": "string",
                        "description": "券商分點代號，例如 1020（查該分點當日所有個股）",
                    },
                    "date": {
                        "type": "string",
                        "description": "查詢日期 YYYY-MM-DD（單日，非區間）",
                    },
                },
                "required": ["date"],
            },
        ),
        Tool(
            name="get_pricing",
            description=(
                "查詢 FinMind 會員方案價格（讀取內建知識庫，不需連線、不需 token）。"
                "回傳 Free / Backer / Sponsor / Sponsor Pro 的月繳／年繳價格（新台幣）、"
                "API 每小時上限、各方案新增資料集、商業授權規則與購買連結。"
                "使用者問價格、費用、方案差異、升級或商業用途時使用。"
            ),
            inputSchema={"type": "object", "properties": {}},
        ),
        _query_endpoint_tool(),
        _download_storage_object_tool(),
    ]


def _query_endpoint_tool() -> Tool:
    lines = [
        "呼叫 FinMind 專屬 endpoint（不走 /api/v4/data 的資料）。endpoint 只能是下列其一，"
        "各自的參數規則：",
    ]
    for name, spec in ENDPOINTS.items():
        lines.append(f"- {name}（{spec['tier']}）：{spec['summary']}")
    lines.append(
        "參數不符時工具會直接說明缺什麼，不會打 API。方案不足會回傳所需方案與升級連結。"
        "超過 500 列會截斷。"
    )
    return Tool(
        name="query_endpoint",
        description="\n".join(lines),
        inputSchema={
            "type": "object",
            "properties": {
                "endpoint": {
                    "type": "string",
                    "enum": list(ENDPOINTS),
                    "description": "專屬 endpoint 名稱（即 /api/v4/ 後面的路徑）",
                },
                "data_id": {
                    "description": (
                        "標的代號（股票 / 權證 / 期貨 / 選擇權系列）。snapshot 類可傳陣列一次查多檔"
                    ),
                    "anyOf": [
                        {"type": "string"},
                        {"type": "array", "items": {"type": "string"}},
                    ],
                },
                "securities_trader_id": {
                    "type": "string",
                    "description": "券商分點代號，例如 1020",
                },
                "date": {"type": "string", "description": "單日 YYYY-MM-DD"},
                "start_date": {"type": "string", "description": "起始日 YYYY-MM-DD"},
                "end_date": {"type": "string", "description": "結束日 YYYY-MM-DD"},
                "dataset": {
                    "type": "string",
                    "description": "datalist / translation 要查的 dataset 名稱",
                },
            },
            "required": ["endpoint"],
        },
    )


def _download_storage_object_tool() -> Tool:
    return Tool(
        name="download_storage_object",
        description=(
            "下載 FinMind 整日全市場檔案（/api/v4/storage_objects，parquet，需 Sponsor Pro）"
            "到本機，只回傳檔案路徑、總筆數、欄位與前幾列；可用 data_id（股票/期貨/選擇權代號）"
            "或 securities_trader_id 過濾後回傳小量資料（最多 500 列）。整日檔可能數十 MB，"
            "完整資料請用程式讀取回傳的本機路徑。一次一個 dataset、一個交易日；"
            "同一檔已下載過會直接用本機快取。"
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "dataset": {
                    "type": "string",
                    "enum": list(STORAGE_OBJECT_DATASETS),
                    "description": "整日檔 dataset 名稱",
                },
                "date": {"type": "string", "description": "交易日 YYYY-MM-DD"},
                "data_id": {
                    "description": (
                        "只回傳這些代號的列（股票類過濾 stock_id、期貨 futures_id、"
                        "選擇權 option_id）"
                    ),
                    "anyOf": [
                        {"type": "string"},
                        {"type": "array", "items": {"type": "string"}},
                    ],
                },
                "securities_trader_id": {
                    "description": "只回傳這些券商分點（僅分點類 dataset）",
                    "anyOf": [
                        {"type": "string"},
                        {"type": "array", "items": {"type": "string"}},
                    ],
                },
                "columns": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "只回傳這些欄位（省略則全部）",
                },
                "limit": {
                    "type": "integer",
                    "minimum": 0,
                    "maximum": STORAGE_MAX_LIMIT,
                    "description": f"回傳列數上限（預設 {STORAGE_DEFAULT_LIMIT}，最多 {STORAGE_MAX_LIMIT}）",
                },
                "refresh": {
                    "type": "boolean",
                    "description": "true 時忽略本機快取重新下載",
                },
            },
            "required": ["dataset", "date"],
        },
    )


# --- Dispatch ----------------------------------------------------------------


async def dispatch(name: str, arguments: dict[str, Any]) -> str:
    """Dispatch a tool call to the matching implementation.

    Returns a markdown string. Errors from the upstream client are caught
    and rendered as 繁中 user-facing messages.
    """
    # Offline tools read the bundled knowledge pack and need no token.
    offline = {
        "list_datasets": _list_datasets,
        "get_pricing": _get_pricing,
    }
    if name in offline:
        return offline[name]()
    handlers = {
        "query_dataset": _query_dataset,
        "get_stock_info": _get_stock_info,
        "query_trading_daily_report": _query_trading_daily_report,
        "query_endpoint": _query_endpoint,
        "download_storage_object": _download_storage_object,
    }
    handler = handlers.get(name)
    if handler is None:
        raise ValueError(f"unknown tool: {name}")
    arguments = arguments or {}
    try:
        client = _make_client()
    except AuthenticationError:
        return _error_message(AuthenticationError("missing token"))
    try:
        return await handler(client, arguments)
    except FinMindError as exc:
        return _error_message(exc, target=_error_target(name, arguments))


# --- Tool handlers -----------------------------------------------------------


async def _query_dataset(client: FinMindClient, args: dict[str, Any]) -> str:
    dataset = args.get("dataset")
    if not dataset:
        return "缺少必填參數 `dataset`。請指定要查詢的資料集名稱。"
    if dataset in DEDICATED_ONLY_DATASETS:
        endpoint = DEDICATED_ONLY_DATASETS[dataset]
        return (
            f"`{dataset}` 不走 /api/v4/data（會回 422），請改用 `query_endpoint`，"
            f"endpoint=`{endpoint}`。參數規則：{ENDPOINTS[endpoint]['summary']}。"
        )
    rows = await client.query_dataset(
        dataset=dataset,
        data_id=args.get("data_id"),
        start_date=args.get("start_date"),
        end_date=args.get("end_date"),
    )
    return _format_markdown_table(rows, title=dataset)


def _list_datasets() -> str:
    # FinMind has no "list all datasets" endpoint; read the bundled catalog
    # (datasets.md) — the same SSOT as the Custom GPT knowledge bundle.
    catalog = knowledge.dataset_catalog()
    if not catalog:
        return "目前沒有可用的 dataset。"
    lines = [f"### FinMind 可用 dataset（共 {len(catalog)} 個）"]
    current_cat: Optional[str] = None
    for rec in catalog:
        if rec["category"] != current_cat:
            current_cat = rec["category"]
            lines.append(f"\n**{current_cat}**")
        tier = f"（{rec['tier']}）" if rec["tier"] else ""
        desc = f" — {rec['desc']}" if rec["desc"] else ""
        lines.append(f"- `{rec['name']}`{tier}{desc}")
    return "\n".join(lines)


def _get_pricing() -> str:
    try:
        return knowledge.read("finmind://pricing")
    except (KeyError, ValueError, OSError):
        return "方案價格請見：https://finmindtrade.com/analysis/#/Sponsor/sponsor"


async def _get_stock_info(client: FinMindClient, args: dict[str, Any]) -> str:
    stock_id = args.get("stock_id")
    rows = await client.query_dataset(
        dataset="TaiwanStockInfo",
        data_id=stock_id,
    )
    title = f"TaiwanStockInfo {stock_id}" if stock_id else "TaiwanStockInfo"
    return _format_markdown_table(rows, title=title)


async def _query_trading_daily_report(
    client: FinMindClient, args: dict[str, Any]
) -> str:
    data_id = args.get("data_id")
    securities_trader_id = args.get("securities_trader_id")
    date = args.get("date")
    if not data_id and not securities_trader_id:
        return (
            "缺少必填參數 `data_id` 或 `securities_trader_id`。請指定股票代號（例如 2330）"
            "或券商分點代號（例如 1020）。"
        )
    if not date:
        return "缺少必填參數 `date`。請指定查詢日期（YYYY-MM-DD，單日）。"
    rows = await client.query_trading_daily_report(
        date=date, data_id=data_id, securities_trader_id=securities_trader_id
    )
    return _format_markdown_table(rows, title="TradingDailyReport")


async def _query_endpoint(client: FinMindClient, args: dict[str, Any]) -> str:
    endpoint = args.get("endpoint")
    if endpoint not in ENDPOINTS:
        return (
            f"不支援的 endpoint `{endpoint}`。可用：{', '.join(ENDPOINTS)}。"
            "一般 dataset 請用 `query_dataset`；整日檔請用 `download_storage_object`。"
        )
    params: dict[str, Any] = {}
    for key in PARAM_NAMES:
        value = args.get(key)
        if isinstance(value, list):
            value = [str(v) for v in value if str(v)]
            if len(value) == 1:
                value = value[0]
        if value not in (None, "", []):
            params[key] = value
    problem = validate_params(endpoint, params)
    if problem:
        return problem
    data = await client.query_endpoint(endpoint, params)
    title = f"{endpoint}"
    if isinstance(data, dict):
        # translation: {"name": [...], "english": [...]} parallel lists → rows.
        return _format_markdown_table(_columns_to_rows(data), title=title)
    if data and not isinstance(data[0], dict):
        # datalist: plain list of values.
        return _format_markdown_table([{"data_id": v} for v in data], title=title)
    return _format_markdown_table(data, title=title)


def _columns_to_rows(data: dict[str, Any]) -> list[dict[str, Any]]:
    keys = [k for k, v in data.items() if isinstance(v, list)]
    if not keys:
        return [data]
    length = max(len(data[k]) for k in keys)
    return [
        {k: (data[k][i] if i < len(data[k]) else None) for k in keys}
        for i in range(length)
    ]


def _as_list(value: Any) -> Optional[list[str]]:
    if value in (None, "", []):
        return None
    if isinstance(value, list):
        out = [str(v).strip() for v in value if str(v).strip()]
    else:
        out = [v.strip() for v in str(value).split(",") if v.strip()]
    return out or None


async def _download_storage_object(client: FinMindClient, args: dict[str, Any]) -> str:
    dataset = args.get("dataset")
    date = args.get("date")
    if dataset not in STORAGE_OBJECT_DATASETS:
        return (
            f"不支援的整日檔 dataset `{dataset}`。可用：{', '.join(STORAGE_OBJECT_DATASETS)}。"
        )
    if not date or not _DATE_RE.match(str(date)):
        return "缺少或格式錯誤的 `date`，請給單一交易日 YYYY-MM-DD。"
    data_id = _as_list(args.get("data_id"))
    trader = _as_list(args.get("securities_trader_id"))
    if trader and dataset not in STORAGE_OBJECT_BROKER_DATASETS:
        return f"`{dataset}` 沒有 securities_trader_id 欄位，不能用分點過濾。"
    columns = _as_list(args.get("columns"))
    try:
        limit = int(args.get("limit", STORAGE_DEFAULT_LIMIT))
    except (TypeError, ValueError):
        limit = STORAGE_DEFAULT_LIMIT
    limit = max(0, min(limit, STORAGE_MAX_LIMIT))

    path = storage.object_path(dataset, date)
    cached = path.is_file() and path.stat().st_size > 0 and not args.get("refresh")
    if not cached:
        signed_url = await client.storage_object_url(dataset, date)
        await client.download(signed_url, path)
    size_mb = path.stat().st_size / 1_000_000

    lines = [f"### {dataset} {date} 整日檔"]
    lines.append(
        f"- 本機檔案：`{path}`（{size_mb:.1f} MB，"
        f"{'使用先前下載的本機快取' if cached else '剛下載'}）"
    )
    try:
        info = storage.summarize(
            path,
            id_column=STORAGE_OBJECT_DATASETS[dataset],
            data_id=data_id,
            securities_trader_id=trader,
            columns=columns,
            limit=limit,
        )
    except DependencyMissingError as exc:
        lines.append("")
        lines.append(str(exc))
        return "\n".join(lines)

    lines.append(f"- 總筆數：{info['total_rows']:,}")
    lines.append(
        "- 欄位：" + ", ".join(f"{name} ({typ})" for name, typ in info["schema"])
    )
    if info["unknown_columns"]:
        lines.append(f"- 忽略不存在的欄位：{', '.join(info['unknown_columns'])}")
    rows = info["rows"]
    if info["matched_rows"] is not None:
        conds = []
        if data_id:
            conds.append(f"{STORAGE_OBJECT_DATASETS[dataset]} ∈ {data_id}")
        if trader:
            conds.append(f"securities_trader_id ∈ {trader}")
        lines.append(
            f"- 過濾 {'、'.join(conds)}：符合 {info['matched_rows']:,} 筆，"
            f"以下顯示前 {len(rows)} 筆"
        )
    else:
        lines.append(f"- 以下為檔案前 {len(rows)} 筆")
    lines.append("")
    lines.append(_format_markdown_table(rows) if rows else "（無符合的列）")
    lines.append(
        "\n_完整資料請用程式讀取上方本機檔案（例如 `pandas.read_parquet(path)`）；"
        f"本工具一次最多回傳 {STORAGE_MAX_LIMIT} 列。_"
    )
    return "\n".join(lines)


# --- Formatting --------------------------------------------------------------


def _format_markdown_table(rows: list[dict[str, Any]], title: Optional[str] = None) -> str:
    """Render a list of dict rows as a GitHub-flavored markdown table."""
    if not rows:
        return "查無資料。"

    columns: list[str] = []
    for row in rows:
        for key in row.keys():
            if key not in columns:
                columns.append(key)

    total = len(rows)
    truncated = total > MAX_ROWS
    visible = rows[:MAX_ROWS] if truncated else rows

    header = "| " + " | ".join(columns) + " |"
    separator = "| " + " | ".join("---" for _ in columns) + " |"
    body_lines = []
    for row in visible:
        cells = [_format_cell(row.get(col, "")) for col in columns]
        body_lines.append("| " + " | ".join(cells) + " |")

    parts = []
    if title:
        parts.append(f"### {title}")
    parts.append(header)
    parts.append(separator)
    parts.extend(body_lines)
    if truncated:
        parts.append(
            f"\n_(truncated, total {total} rows — use code interpreter for full data)_"
        )
    return "\n".join(parts)


def _format_cell(value: Any) -> str:
    if value is None:
        return ""
    text = str(value)
    # Escape pipe characters so they don't break the table layout.
    return text.replace("|", "\\|").replace("\n", " ")


# --- Error → user-facing message --------------------------------------------


_ERROR_KIND: dict[type, str] = {
    AuthenticationError: "auth",
    PaymentRequiredError: "payment",
    EmptyDataError: "empty",
    RateLimitError: "rate_limit",
    BadRequestError: "bad_request",
    UpstreamError: "upstream",
}


def _error_target(tool: str, args: dict[str, Any]) -> Optional[str]:
    """What the failed call was for (dataset / endpoint name), for messages."""
    if tool == "query_dataset":
        return args.get("dataset")
    if tool == "get_stock_info":
        return "TaiwanStockInfo"
    if tool == "query_trading_daily_report":
        return "taiwan_stock_trading_daily_report"
    if tool == "query_endpoint":
        return args.get("endpoint")
    if tool == "download_storage_object":
        return f"storage_objects:{args.get('dataset')}"
    return None


def required_tier(target: Optional[str]) -> Optional[str]:
    """Lowest plan that can access `target` (dataset, endpoint, or storage_objects)."""
    if not target:
        return None
    if target.startswith("storage_objects"):
        return STORAGE_OBJECT_TIER
    if target in ENDPOINTS:
        return ENDPOINTS[target]["tier"]
    for rec in knowledge.dataset_catalog():
        if rec["name"] == target and rec["tier"]:
            tier = rec["tier"]
            if tier.startswith("Free(w/"):
                return "Backer（不帶 data_id 查全市場時）"
            return tier
    return None


def _error_message(exc: FinMindError, target: Optional[str] = None) -> str:
    """Render a FinMindError as the matching 繁中 template from errors.md.

    The API's own error text (`exc.detail`) is always quoted so the LLM sees
    exactly what FinMind said; tier errors also name the plan that's needed.
    """
    kind = _ERROR_KIND.get(type(exc))
    detail = getattr(exc, "detail", None)
    head: list[str] = []
    if kind == "payment":
        tier = required_tier(target)
        what = f"`{target.replace('storage_objects:', 'storage_objects 整日檔 ')}`" if target else "此資料"
        need = f"**{tier}** 以上方案" if tier else "更高等級的方案"
        head.append(f"**方案權限不足：** {what} 需要 {need}，您目前的方案無法存取。")
        head.append(f"請升級方案後再試：{PRICING_URL}（可呼叫 `get_pricing` 查看各方案價格與差異）")
    elif kind == "bad_request" and target and target.startswith("storage_objects") and getattr(exc, "status", None) == 404:
        head.append(
            "**查無整日檔：** 該日沒有檔案，通常是非交易日、早於該 dataset 的資料起始日，"
            "或當日檔案尚未產生（盤後才會產生）。"
        )
    if detail and kind != "empty" and str(detail) != "missing token":
        head.append(f"**API 回應原文：** `{detail}`")
    template = knowledge.get_error_template(kind) if kind else None
    body = template or f"FinMind 查詢失敗：{exc}"
    return "\n\n".join(head + [body]) if head else body
