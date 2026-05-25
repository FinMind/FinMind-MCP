"""Pre-launch regression runner for the FinMind MCP server.

Spawns the `finmind-mcp` server over stdio (once), then for each canonical
query in `knowledge/regression.md` issues the *expected* `tools/call` with the
expected tool + params and asserts the live API response has the right shape
(required columns present, minimum row count, expected substrings).

What this DOES test (server-side contract):
    given the right tool + params, the live FinMind API returns
    correctly-shaped data that the server renders into the expected table.

What this does NOT test (LLM-side, validate manually on the real GPT/Claude):
    - whether the model picks the right tool / dataset / params from the
      natural-language query,
    - prose criteria like "mentions K線" (R9) or "comparison narrative" (R10).
Those are noted per-case below and excluded from the automated assertions.

`knowledge/regression.md` is the human-readable spec; the CASES list here is
its executable mirror. A startup sync-guard parses the `### Rn:` headers from
the markdown and refuses to run if the two drift (case added/removed/renamed).

Usage:
    FINMIND_TOKEN=<token> uv run python regression/runner.py
    uv run python regression/runner.py --min 10     # require 10/12 to pass
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
REGRESSION_MD = REPO_ROOT / "knowledge" / "regression.md"


# --- Case model --------------------------------------------------------------


@dataclass
class Call:
    tool: str
    params: dict


@dataclass
class Check:
    columns: tuple[str, ...] = ()       # every column must appear in some table
    any_columns: tuple[str, ...] = ()   # at least one must appear
    min_rows: int = 0                   # total data rows across all tables
    contains: tuple[str, ...] = ()      # every substring must appear in the text


@dataclass
class Case:
    id: str
    title: str
    calls: list[Call]
    check: Check
    note: str = ""                      # LLM-side criteria validated manually


# Mirror of knowledge/regression.md. Dates are the fixed values from the spec
# (today=2026-05-17 there); they sit in the past relative to now, so the live
# API has data and the run stays deterministic.
CASES: list[Case] = [
    Case(
        "R1", "個股最近一週股價",
        [Call("query_dataset", {"dataset": "TaiwanStockPrice", "data_id": "2330", "start_date": "2026-05-10"})],
        Check(columns=("date", "open", "max", "min", "close"), min_rows=5),
    ),
    Case(
        "R2", "今年每月營收",
        [Call("query_dataset", {"dataset": "TaiwanStockMonthRevenue", "data_id": "2330", "start_date": "2026-01-01"})],
        Check(columns=("date", "revenue"), min_rows=3),
    ),
    Case(
        "R3", "季報財務數據",
        [Call("query_dataset", {"dataset": "TaiwanStockFinancialStatements", "data_id": "2317", "start_date": "2025-05-17"})],
        Check(columns=("date", "type", "value"), min_rows=3),
    ),
    Case(
        "R4", "三大法人買賣超",
        [Call("query_dataset", {"dataset": "TaiwanStockInstitutionalInvestorsBuySell", "data_id": "2330", "start_date": "2026-05-10"})],
        Check(columns=("date", "name", "buy", "sell"), min_rows=3),
    ),
    Case(
        "R5", "股利政策查詢",
        [Call("query_dataset", {"dataset": "TaiwanStockDividend", "data_id": "2330", "start_date": "2023-01-01"})],
        Check(columns=("date", "CashEarningsDistribution"), min_rows=3),
    ),
    Case(
        "R6", "期貨日成交",
        [Call("query_dataset", {"dataset": "TaiwanFuturesDaily", "data_id": "TX", "start_date": "2026-05-10"})],
        Check(columns=("date", "open", "max", "min", "close"), min_rows=3),
    ),
    Case(
        "R7", "匯率走勢",
        [Call("query_dataset", {"dataset": "TaiwanExchangeRate", "data_id": "USD", "start_date": "2025-11-17"})],
        Check(columns=("date",), any_columns=("spot_buy", "cash_buy"), min_rows=10),
    ),
    Case(
        "R8", "美國利率",
        [Call("query_dataset", {"dataset": "InterestRate", "data_id": "FED", "start_date": "2025-05-17"})],
        Check(columns=("date", "interest_rate"), min_rows=3),
    ),
    Case(
        "R9", "畫圖請求（K 線圖）",
        [Call("query_dataset", {"dataset": "TaiwanStockPrice", "data_id": "2330", "start_date": "2026-02-17"})],
        Check(columns=("date", "open", "max", "min", "close"), min_rows=3),
        note="繪圖敘述（K線/圖、軸）由平台 code 環境產生，屬 LLM-side，需人工驗證。",
    ),
    Case(
        "R10", "跨股比較（多檔股票）",
        [
            Call("query_dataset", {"dataset": "TaiwanStockPrice", "data_id": "2330", "start_date": "2026-01-01"}),
            Call("query_dataset", {"dataset": "TaiwanStockPrice", "data_id": "2454", "start_date": "2026-01-01"}),
        ],
        Check(columns=("close",), contains=("2330", "2454"), min_rows=2),
        note="比較性敘述（漲幅/百分比）由模型產生，屬 LLM-side，需人工驗證。",
    ),
    Case(
        "R11", "本益比",
        [Call("query_dataset", {"dataset": "TaiwanStockPER", "data_id": "2330", "start_date": "2026-05-10"})],
        Check(columns=("date", "PER"), min_rows=1),
    ),
    Case(
        "R12", "股票代號查詢",
        [Call("get_stock_info", {"stock_id": "2330"})],
        Check(contains=("2330", "台積電")),
    ),
]


# --- Markdown table parsing --------------------------------------------------


def parse_tables(text: str) -> tuple[set[str], int]:
    """Return (union of all column names, total data-row count) across every
    markdown table in `text`. The truncation note and section headings break
    a table because they don't start with '|'."""
    columns: set[str] = set()
    total_rows = 0
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith("|"):
            header = [c.strip().strip("`") for c in line.strip("|").split("|")]
            columns.update(c for c in header if c)
            j = i + 1
            # Skip the |---|---| separator row if present.
            if j < len(lines) and "---" in lines[j]:
                j += 1
            while j < len(lines) and lines[j].strip().startswith("|"):
                total_rows += 1
                j += 1
            i = j
        else:
            i += 1
    return columns, total_rows


def evaluate(check: Check, text: str) -> list[str]:
    """Return a list of failure reasons (empty list == pass)."""
    failures: list[str] = []
    columns, rows = parse_tables(text)

    for col in check.columns:
        if col not in columns:
            failures.append(f"缺少欄位 `{col}`")
    if check.any_columns and not any(c in columns for c in check.any_columns):
        failures.append("缺少任一欄位 " + " / ".join(f"`{c}`" for c in check.any_columns))
    if rows < check.min_rows:
        failures.append(f"列數 {rows} < 期望 {check.min_rows}")
    for sub in check.contains:
        if sub not in text:
            failures.append(f"回應未包含「{sub}」")
    return failures


# --- Sync guard --------------------------------------------------------------


def md_case_headers() -> dict[str, str]:
    """Parse `### Rn: title` headers from regression.md → {id: title}."""
    out: dict[str, str] = {}
    for line in REGRESSION_MD.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^###\s+(R\d+):\s+(.+?)\s*$", line)
        if m:
            out[m.group(1)] = m.group(2)
    return out


def assert_in_sync() -> None:
    md = md_case_headers()
    code = {c.id: c.title for c in CASES}
    if set(md) != set(code):
        only_md = sorted(set(md) - set(code))
        only_code = sorted(set(code) - set(md))
        raise SystemExit(
            "runner.py 與 regression.md 不同步：\n"
            f"  只在 regression.md：{only_md}\n"
            f"  只在 runner.py：{only_code}\n"
            "請同步兩邊的測試案例後再跑。"
        )
    drift = [f"  {cid}: md「{md[cid]}」≠ code「{code[cid]}」" for cid in md if md[cid] != code[cid]]
    if drift:
        print("⚠ 標題與 regression.md 不一致（不擋執行）：", file=sys.stderr)
        print("\n".join(drift), file=sys.stderr)


# --- stdio JSON-RPC client ---------------------------------------------------


class MCPProcess:
    def __init__(self) -> None:
        self._id = 0

    async def __aenter__(self) -> "MCPProcess":
        self.proc = await asyncio.create_subprocess_exec(
            sys.executable, "-m", "finmind_mcp.server",
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env={**os.environ},
        )
        await self._send({
            "jsonrpc": "2.0", "id": self._next(), "method": "initialize",
            "params": {"protocolVersion": "2024-11-05", "capabilities": {},
                       "clientInfo": {"name": "regression", "version": "0"}},
        })
        init = await self._recv()
        assert "result" in init, init
        await self._send({"jsonrpc": "2.0", "method": "notifications/initialized"})
        return self

    async def __aexit__(self, *exc) -> None:
        self.proc.terminate()
        await self.proc.wait()

    def _next(self) -> int:
        self._id += 1
        return self._id

    async def _send(self, msg: dict) -> None:
        self.proc.stdin.write((json.dumps(msg) + "\n").encode())
        await self.proc.stdin.drain()

    async def _recv(self) -> dict:
        line = await self.proc.stdout.readline()
        if not line:
            stderr = (await self.proc.stderr.read()).decode(errors="replace")
            raise RuntimeError(f"server closed stdout. stderr=\n{stderr}")
        return json.loads(line)

    async def call_tool(self, name: str, arguments: dict) -> str:
        await self._send({
            "jsonrpc": "2.0", "id": self._next(), "method": "tools/call",
            "params": {"name": name, "arguments": arguments},
        })
        resp = await self._recv()
        if "error" in resp:
            return f"[RPC error] {resp['error']}"
        content = resp.get("result", {}).get("content", [])
        return "\n".join(c.get("text", "") for c in content if c.get("type") == "text")


# --- Main --------------------------------------------------------------------


async def run(min_pass: int) -> int:
    assert_in_sync()
    if not os.environ.get("FINMIND_TOKEN"):
        raise SystemExit("FINMIND_TOKEN 未設定 — 此 runner 會打 live API，請先設 token。")

    passed = 0
    total = len(CASES)
    async with MCPProcess() as mcp:
        for idx, case in enumerate(CASES, 1):
            texts = []
            for call in case.calls:
                texts.append(await mcp.call_tool(call.tool, call.params))
            failures = evaluate(case.check, "\n".join(texts))
            if failures:
                print(f"[{idx}/{total}] FAIL — {case.id} {case.title}")
                for f in failures:
                    print(f"           ✗ {f}")
            else:
                passed += 1
                tag = "  (含人工項)" if case.note else ""
                print(f"[{idx}/{total}] PASS — {case.id} {case.title}{tag}")

    print()
    print(f"{passed}/{total} passed（門檻 {min_pass}）")
    manual = [c for c in CASES if c.note]
    if manual:
        print("\n需人工驗證的 LLM-side 項目（不在自動判定內）：")
        for c in manual:
            print(f"  - {c.id} {c.title}：{c.note}")
    return 0 if passed >= min_pass else 1


def main() -> None:
    ap = argparse.ArgumentParser(description="FinMind MCP 上線前 regression runner")
    ap.add_argument("--min", type=int, default=9, help="通過門檻（預設 9/12）")
    args = ap.parse_args()
    sys.exit(asyncio.run(run(args.min)))


if __name__ == "__main__":
    main()
