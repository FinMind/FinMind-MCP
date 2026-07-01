"""MCP tool implementations and markdown formatting.

Four tools are exposed:

- `query_dataset`             — generic /api/v4/data query
- `list_datasets`             — bundled dataset catalog (knowledge/datasets.md)
- `get_stock_info`            — shorthand for TaiwanStockInfo
- `query_trading_daily_report` — dedicated /api/v4/taiwan_stock_trading_daily_report

Each tool returns a markdown string. `FinMindError` subclasses raised by
`FinMindClient` are caught and converted into the 繁中 templates from
`knowledge/errors.md`. Tools never raise.
"""

from __future__ import annotations

import asyncio
import os
import tempfile
from pathlib import Path
from typing import Any, Optional

from mcp.types import Tool

from . import knowledge
from .client import FinMindClient
from .errors import (
    AuthenticationError,
    EmptyDataError,
    FinMindError,
    PaymentRequiredError,
    RateLimitError,
    UpstreamError,
)
from .jobs import SQLiteJobStore

# Truncate row count for inline markdown rendering. Larger results should
# be processed via the host's code interpreter.
MAX_ROWS = 500


# --- Tool registry -----------------------------------------------------------


def _make_client() -> FinMindClient:
    """Factory hook — tests monkey-patch this to inject a FakeClient."""
    return FinMindClient()


def _make_job_store() -> SQLiteJobStore:
    """Factory hook for async handleId jobs."""
    db_path = os.environ.get("FINMIND_MCP_JOB_DB")
    if not db_path:
        db_path = str(Path(tempfile.gettempdir()) / "finmind_mcp_jobs.sqlite3")
    return SQLiteJobStore(db_path)


def tool_definitions() -> list[Tool]:
    """Return MCP Tool definitions in stable order."""
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
                "此 dataset 走專屬 endpoint 不在 /api/v4/data 通用路徑：必填股票代號 data_id"
                "與單一日期 date（非區間）。需要 Sponsor 等級。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "data_id": {
                        "type": "string",
                        "description": "股票代號，例如 2330",
                    },
                    "date": {
                        "type": "string",
                        "description": "查詢日期 YYYY-MM-DD（單日，非區間）",
                    },
                },
                "required": ["data_id", "date"],
            },
        ),
        Tool(
            name="start_query_dataset_job",
            description=(
                "啟動較慢的通用 FinMind dataset 查詢，立即回傳 handle_id，避免 MCP "
                "tool call 因外部 API 延遲而 timeout。之後用 check_query_dataset_job "
                "輪詢結果。"
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
                    "original_query": {
                        "type": "string",
                        "description": "原始使用者問題，用於 polling 回覆時保留上下文。",
                    },
                },
                "required": ["dataset"],
            },
        ),
        Tool(
            name="check_query_dataset_job",
            description=(
                "用 handle_id 查詢 start_query_dataset_job 的狀態。回覆會保留 original_query，"
                "避免長時間查詢完成後遺失對話上下文。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "handle_id": {
                        "type": "string",
                        "description": "start_query_dataset_job 回傳的 handle_id",
                    }
                },
                "required": ["handle_id"],
            },
        ),
    ]


# --- Dispatch ----------------------------------------------------------------


async def dispatch(name: str, arguments: dict[str, Any]) -> str:
    """Dispatch a tool call to the matching implementation.

    Returns a markdown string. Errors from the upstream client are caught
    and rendered as 繁中 user-facing messages.
    """
    handlers = {
        "query_dataset": _query_dataset,
        "list_datasets": _list_datasets,
        "get_stock_info": _get_stock_info,
        "query_trading_daily_report": _query_trading_daily_report,
        "start_query_dataset_job": _start_query_dataset_job,
        "check_query_dataset_job": _check_query_dataset_job,
    }
    handler = handlers.get(name)
    if handler is None:
        raise ValueError(f"unknown tool: {name}")
    client: FinMindClient | None = None
    if name not in {"list_datasets", "check_query_dataset_job"}:
        try:
            client = _make_client()
        except AuthenticationError:
            return _error_message(AuthenticationError("missing token"))
    try:
        return await handler(client, arguments or {})
    except FinMindError as exc:
        return _error_message(exc)


# --- Tool handlers -----------------------------------------------------------


async def _query_dataset(client: FinMindClient, args: dict[str, Any]) -> str:
    dataset = args.get("dataset")
    if not dataset:
        return "缺少必填參數 `dataset`。請指定要查詢的資料集名稱。"
    rows = await client.query_dataset(
        dataset=dataset,
        data_id=args.get("data_id"),
        start_date=args.get("start_date"),
        end_date=args.get("end_date"),
    )
    return _format_markdown_table(rows, title=dataset)


async def _list_datasets(_client: FinMindClient, _args: dict[str, Any]) -> str:
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
    date = args.get("date")
    if not data_id:
        return "缺少必填參數 `data_id`。請指定股票代號（例如 2330）。"
    if not date:
        return "缺少必填參數 `date`。請指定查詢日期（YYYY-MM-DD，單日）。"
    rows = await client.query_trading_daily_report(data_id=data_id, date=date)
    return _format_markdown_table(rows, title="TradingDailyReport")


async def _start_query_dataset_job(
    client: FinMindClient, args: dict[str, Any]
) -> str:
    dataset = args.get("dataset")
    if not dataset:
        return "缺少必填參數 `dataset`。請指定要查詢的資料集名稱。"

    job_args = {
        "dataset": dataset,
        "data_id": args.get("data_id"),
        "start_date": args.get("start_date"),
        "end_date": args.get("end_date"),
    }
    original_query = args.get("original_query") or _job_query_context(job_args)
    record = _make_job_store().create(
        tool_name="query_dataset",
        arguments=job_args,
        original_query=original_query,
    )
    asyncio.create_task(_run_query_dataset_job(record.handle_id, client, job_args))
    return (
        f"PROCESSING: Job started. handle_id: `{record.handle_id}`\n\n"
        f"Use `check_query_dataset_job` with this handle_id to poll results.\n\n"
        f"original_query: {original_query}"
    )


async def _run_query_dataset_job(
    handle_id: str,
    client: FinMindClient,
    args: dict[str, Any],
) -> None:
    store = _make_job_store()
    try:
        rows = await client.query_dataset(
            dataset=args["dataset"],
            data_id=args.get("data_id"),
            start_date=args.get("start_date"),
            end_date=args.get("end_date"),
        )
        store.complete(handle_id, _format_markdown_table(rows, title=args["dataset"]))
    except FinMindError as exc:
        store.fail(handle_id, _error_message(exc))
    except Exception as exc:  # Defensive guard: tools should not leak exceptions.
        store.fail(handle_id, f"FinMind 查詢失敗：{exc}")


async def _check_query_dataset_job(
    _client: FinMindClient | None,
    args: dict[str, Any],
) -> str:
    handle_id = args.get("handle_id")
    if not handle_id:
        return "缺少必填參數 `handle_id`。請提供 start_query_dataset_job 回傳的 handle_id。"

    record = _make_job_store().get(handle_id)
    if record is None:
        return f"NOT_FOUND: Job `{handle_id}` not found."
    if record.status == "completed":
        return (
            f"COMPLETED: Job `{handle_id}` completed.\n\n"
            f"original_query: {record.original_query}\n\n"
            f"{record.result or ''}"
        )
    if record.status == "failed":
        return (
            f"FAILED: Job `{handle_id}` failed.\n\n"
            f"original_query: {record.original_query}\n\n"
            f"{record.error or 'unknown error'}"
        )
    return (
        f"PROCESSING: Job `{handle_id}` still running.\n\n"
        f"original_query: {record.original_query}"
    )


def _job_query_context(args: dict[str, Any]) -> str:
    parts = [str(args.get("dataset") or "dataset")]
    if args.get("data_id"):
        parts.append(str(args["data_id"]))
    if args.get("start_date"):
        parts.append(str(args["start_date"]))
    if args.get("end_date"):
        parts.append(str(args["end_date"]))
    return " ".join(parts)


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
    UpstreamError: "upstream",
}


def _error_message(exc: FinMindError) -> str:
    """Render a FinMindError as the matching 繁中 template from errors.md."""
    kind = _ERROR_KIND.get(type(exc))
    if kind is None:
        # Fallback for the base FinMindError.
        return f"FinMind 查詢失敗：{exc}"
    template = knowledge.get_error_template(kind)
    if template:
        return template
    return f"FinMind 查詢失敗：{exc}"
