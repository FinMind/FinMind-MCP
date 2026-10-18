"""Local handling of `storage_objects` whole-day parquet files.

The files are far too large to hand to an LLM, so `download_storage_object`
saves them on disk and only returns a summary (path, size, row count, schema,
a few rows, or a small filtered slice).

Reading parquet needs pyarrow, which is an optional extra
(`pip install "finmind-mcp[parquet]"`) because its wheel is 29-54 MB.
Without it the file is still downloaded and its path returned.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any, Optional

from .errors import DependencyMissingError

INSTALL_HINT = (
    "讀取 parquet 需要選用套件 pyarrow，目前未安裝。檔案已下載，可用其他工具開啟；"
    "若要讓本工具回傳筆數、欄位、前幾列與過濾結果，請改用含 parquet extra 的安裝方式：\n"
    '- uvx：`uvx --from "finmind-mcp[parquet]" finmind-mcp`（MCP 設定的 args 改成 '
    '`["--from", "finmind-mcp[parquet]", "finmind-mcp"]`）\n'
    '- pip：`pip install "finmind-mcp[parquet]"`\n'
    "- Claude Desktop 擴充套件（.mcpb）已內含，不需另外安裝"
)


def download_dir() -> Path:
    """Directory for downloaded whole-day files.

    `FINMIND_DOWNLOAD_DIR` wins; otherwise the per-user cache dir
    (`%LOCALAPPDATA%` on Windows, `~/Library/Caches` on macOS,
    `$XDG_CACHE_HOME` or `~/.cache` elsewhere) + `finmind-mcp/storage_objects`.
    """
    override = os.environ.get("FINMIND_DOWNLOAD_DIR")
    if override:
        return Path(override).expanduser()
    if sys.platform == "win32":
        base = Path(os.environ.get("LOCALAPPDATA") or Path.home() / "AppData" / "Local")
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Caches"
    else:
        base = Path(os.environ.get("XDG_CACHE_HOME") or Path.home() / ".cache")
    return base / "finmind-mcp" / "storage_objects"


def object_path(dataset: str, date: str) -> Path:
    return download_dir() / dataset / f"{dataset}_{date}.parquet"


def _pyarrow():
    try:
        import pyarrow.parquet as pq
    except ImportError as exc:  # pragma: no cover - exercised via monkeypatch
        raise DependencyMissingError(INSTALL_HINT) from exc
    return pq


def summarize(
    path: Path,
    *,
    id_column: str,
    data_id: Optional[list[str]] = None,
    securities_trader_id: Optional[list[str]] = None,
    columns: Optional[list[str]] = None,
    limit: int = 20,
) -> dict[str, Any]:
    """Read metadata + a bounded slice of the parquet file at `path`.

    Returns {total_rows, schema: [(name, type)], matched_rows (None when no
    filter), rows: list[dict] (≤ limit), unknown_columns}.
    """
    pq = _pyarrow()

    pf = pq.ParquetFile(path)
    schema = pf.schema_arrow
    names = list(schema.names)
    total_rows = pf.metadata.num_rows

    unknown = [c for c in (columns or []) if c not in names]
    selected = [c for c in (columns or []) if c in names] or None

    filters: list[tuple[str, list[str]]] = []
    if data_id:
        filters.append((id_column, data_id))
    if securities_trader_id:
        filters.append(("securities_trader_id", securities_trader_id))
    filters = [(col, vals) for col, vals in filters if col in names]

    matched: Optional[int] = None
    if filters:
        read_cols = list(dict.fromkeys((selected or names) + [c for c, _ in filters]))
        table = pq.read_table(
            path,
            columns=read_cols,
            filters=[(col, "in", vals) for col, vals in filters],
        )
        matched = table.num_rows
        if selected:
            table = table.select(selected)
        rows = table.slice(0, limit).to_pylist()
    else:
        rows = []
        if limit > 0 and total_rows:
            batch = next(pf.iter_batches(batch_size=limit, columns=selected), None)
            rows = batch.to_pylist() if batch is not None else []
    return {
        "total_rows": total_rows,
        "schema": [(f.name, str(f.type)) for f in schema],
        "matched_rows": matched,
        "rows": rows,
        "unknown_columns": unknown,
    }
