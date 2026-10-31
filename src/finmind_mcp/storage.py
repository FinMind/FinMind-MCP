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


# --- TaiwanStockFinancialReportFile（財報／年報 PDF） --------------------------

# 一次回傳的文字上限，避免整份財報（動輒 6–10 萬字）塞爆對話。
REPORT_TEXT_LIMIT = 30_000


def report_dir(data_id: str, report_category: str) -> Path:
    return download_dir().parent / "financial_report_file" / report_category / data_id


def report_path(data_id: str, year: int, quarter: int, report_category: str, ext: str) -> Path:
    period = f"{year}" if report_category == "annual_report" else f"{year}Q{quarter}"
    return report_dir(data_id, report_category) / f"{data_id}_{period}.{ext}"


def sniff_extension(path: Path) -> str:
    """`pdf` or `doc` from the file's magic bytes (少數公司上傳 Word 檔)."""
    with path.open("rb") as fh:
        head = fh.read(8)
    if head.startswith(b"%PDF"):
        return "pdf"
    if head.startswith(b"\xd0\xcf\x11\xe0"):
        return "doc"
    return "bin"


def _is_garbled(text: str) -> bool:
    """文字層損壞的頁面（字型對應表壞掉）抽出來是一堆非中文符號。

    中文財報的非 ASCII 字元絕大多數是 CJK 漢字或全形標點；若兩者占比不到一半，
    視為亂碼，不把它當內容回傳。
    """
    non_ascii = [c for c in text if ord(c) > 0x7F and not c.isspace()]
    if len(non_ascii) < 20:
        return False
    cjk = sum(
        1
        for c in non_ascii
        if 0x4E00 <= ord(c) <= 0x9FFF or 0x3000 <= ord(c) <= 0x303F or 0xFF00 <= ord(c) <= 0xFFEF
    )
    return cjk / len(non_ascii) < 0.5


def parse_pages(spec: str, total: int) -> list[int]:
    """'5' / '3-8' / '1,4,10-12' → sorted 1-based page numbers within 1..total."""
    pages: set[int] = set()
    for part in str(spec).split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            lo, hi = part.split("-", 1)
            start, end = int(lo), int(hi)
        else:
            start = end = int(part)
        pages.update(range(max(1, start), min(total, end) + 1))
    return sorted(pages)


def read_report(
    path: Path,
    *,
    pages: Optional[str] = None,
    keyword: Optional[str] = None,
    limit: int = REPORT_TEXT_LIMIT,
) -> dict[str, Any]:
    """Extract text from a report PDF.

    - `pages`: only those pages
    - `keyword`: pages whose text contains it (空白不計，PDF 斷行常把詞切開)
    - neither: the first 2 pages (封面＋目錄), to decide what to read next

    Returns {total_pages, pages: [(page_no, text)], no_text_pages,
    garbled_pages, truncated}. Pages without a text layer (多為掃描影像，例如
    部分公司的主要報表頁) go to `no_text_pages`; pages whose text layer is
    corrupted (亂碼，部分年報整份如此) go to `garbled_pages` — neither returns text.
    """
    from pypdf import PdfReader

    reader = PdfReader(str(path))
    total = len(reader.pages)
    if pages:
        wanted = parse_pages(pages, total)
    elif keyword:
        wanted = list(range(1, total + 1))
    else:
        wanted = list(range(1, min(total, 2) + 1))

    needle = "".join(keyword.split()) if keyword else None
    out: list[tuple[int, str]] = []
    no_text: list[int] = []
    garbled: list[int] = []
    used = 0
    truncated = False
    for no in wanted:
        text = (reader.pages[no - 1].extract_text() or "").strip()
        if needle and needle not in "".join(text.split()):
            continue
        if not text:
            no_text.append(no)
            continue
        if _is_garbled(text):
            garbled.append(no)
            continue
        if used + len(text) > limit:
            truncated = True
            break
        out.append((no, text))
        used += len(text)
    return {
        "total_pages": total,
        "pages": out,
        "no_text_pages": no_text,
        "garbled_pages": garbled,
        "truncated": truncated,
    }
