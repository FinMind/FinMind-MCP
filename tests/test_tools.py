"""Tests for MCP tool implementations + markdown formatting + error mapping."""

import pytest

from finmind_mcp import tools
from finmind_mcp.errors import (
    AuthenticationError,
    EmptyDataError,
    PaymentRequiredError,
    RateLimitError,
    UpstreamError,
)


class FakeClient:
    """Test double for FinMindClient — records calls and yields canned responses."""

    def __init__(self, *, query_result=None, raise_exc=None,
                 trading_result=None):
        self.token = "fake-token"
        self.query_result = query_result if query_result is not None else []
        self.trading_result = trading_result if trading_result is not None else []
        self.raise_exc = raise_exc
        self.calls: list[tuple] = []

    async def query_dataset(self, dataset, data_id=None, start_date=None, end_date=None):
        self.calls.append(("query_dataset", dataset, data_id, start_date, end_date))
        if self.raise_exc is not None:
            raise self.raise_exc
        return list(self.query_result)

    async def query_trading_daily_report(self, data_id, date):
        self.calls.append((
            "query_trading_daily_report",
            data_id,
            date,
        ))
        if self.raise_exc is not None:
            raise self.raise_exc
        return list(self.trading_result)


@pytest.fixture
def install_fake_client(monkeypatch):
    """Install a FakeClient via the module-level factory hook."""

    def _install(**kwargs):
        client = FakeClient(**kwargs)
        monkeypatch.setattr(tools, "_make_client", lambda: client)
        return client

    return _install


def test_tool_definitions_returns_four_tools():
    defs = tools.tool_definitions()
    names = [d.name for d in defs]
    assert names == [
        "query_dataset",
        "list_datasets",
        "get_stock_info",
        "query_trading_daily_report",
    ]
    for d in defs:
        assert d.description
        assert d.input_schema is not None
        assert d.input_schema.get("type") == "object"


@pytest.mark.asyncio
async def test_dispatch_query_dataset_markdown(install_fake_client):
    client = install_fake_client(
        query_result=[
            {"date": "2026-05-10", "stock_id": "2330", "close": 1000.0},
            {"date": "2026-05-11", "stock_id": "2330", "close": 1010.5},
        ]
    )
    md = await tools.dispatch(
        "query_dataset",
        {
            "dataset": "TaiwanStockPrice",
            "data_id": "2330",
            "start_date": "2026-05-10",
            "end_date": "2026-05-11",
        },
    )
    # Forwarded to client.
    assert client.calls[0] == (
        "query_dataset",
        "TaiwanStockPrice",
        "2330",
        "2026-05-10",
        "2026-05-11",
    )
    # Markdown table.
    assert "| date" in md
    assert "stock_id" in md
    assert "2330" in md
    assert "1000.0" in md
    # Header separator.
    assert "---" in md


@pytest.mark.asyncio
async def test_dispatch_query_dataset_truncates_at_500(install_fake_client):
    big = [{"i": n} for n in range(800)]
    install_fake_client(query_result=big)
    md = await tools.dispatch(
        "query_dataset",
        {"dataset": "TaiwanStockPrice", "data_id": "2330", "start_date": "2020-01-01"},
    )
    # Header + separator + 500 rows -> 502 lines minimum.
    assert "truncated" in md.lower()
    assert "800" in md  # total row count surfaced
    body_lines = [
        line for line in md.splitlines() if line.startswith("|") and "---" not in line
    ]
    # 1 header + 500 data rows = 501 table lines
    assert len(body_lines) == 501


@pytest.mark.asyncio
async def test_dispatch_list_datasets_reads_knowledge_pack(install_fake_client):
    # list_datasets must NOT hit the API (FinMind has no list-all endpoint);
    # it reads the bundled datasets.md catalog instead.
    client = install_fake_client()
    md = await tools.dispatch("list_datasets", {})
    assert "TaiwanStockPrice" in md
    assert "TaiwanStockInfo" in md
    # 90 datasets shipped in knowledge/datasets.md
    assert "共" in md and "個" in md
    # No client call was made.
    assert client.calls == []


@pytest.mark.asyncio
async def test_dispatch_get_stock_info_calls_taiwanstockinfo(install_fake_client):
    client = install_fake_client(
        query_result=[
            {
                "date": "2026-05-10",
                "stock_id": "2330",
                "stock_name": "台積電",
                "industry_category": "半導體",
                "type": "twse",
            }
        ]
    )
    md = await tools.dispatch("get_stock_info", {"stock_id": "2330"})
    assert client.calls[0][0] == "query_dataset"
    assert client.calls[0][1] == "TaiwanStockInfo"
    assert client.calls[0][2] == "2330"
    assert "2330" in md
    assert "台積電" in md


@pytest.mark.asyncio
async def test_dispatch_get_stock_info_no_arg(install_fake_client):
    client = install_fake_client(
        query_result=[{"date": "2026-05-10", "stock_id": "1101"}]
    )
    await tools.dispatch("get_stock_info", {})
    # No data_id should be passed when stock_id omitted.
    assert client.calls[0] == (
        "query_dataset",
        "TaiwanStockInfo",
        None,
        None,
        None,
    )


@pytest.mark.asyncio
async def test_dispatch_query_trading_daily_report(install_fake_client):
    client = install_fake_client(
        trading_result=[
            {
                "date": "2026-05-10",
                "stock_id": "2330",
                "securities_trader": "元大-台北",
                "buy": 100,
                "sell": 50,
            }
        ]
    )
    md = await tools.dispatch(
        "query_trading_daily_report",
        {
            "data_id": "2330",
            "date": "2026-05-10",
        },
    )
    assert client.calls[0] == (
        "query_trading_daily_report",
        "2330",
        "2026-05-10",
    )
    assert "2330" in md


@pytest.mark.asyncio
async def test_auth_error_returns_user_facing_message(install_fake_client):
    install_fake_client(raise_exc=AuthenticationError("invalid"))
    md = await tools.dispatch(
        "query_dataset",
        {"dataset": "TaiwanStockPrice", "data_id": "2330", "start_date": "2026-05-10"},
    )
    # 401 verbatim 繁中 phrasing from errors.md
    assert "Token" in md
    assert "無法驗證" in md
    assert "finmindtrade.com" in md


@pytest.mark.asyncio
async def test_payment_required_returns_user_facing_message(install_fake_client):
    install_fake_client(raise_exc=PaymentRequiredError("sponsor"))
    md = await tools.dispatch(
        "query_dataset",
        {"dataset": "TaiwanStockBlockTrade", "data_id": "2330", "start_date": "2026-05-10"},
    )
    assert "Sponsor" in md
    assert "pricing" in md


@pytest.mark.asyncio
async def test_empty_data_returns_user_facing_message(install_fake_client):
    install_fake_client(raise_exc=EmptyDataError("no data"))
    md = await tools.dispatch(
        "query_dataset",
        {"dataset": "TaiwanStockPrice", "data_id": "9999", "start_date": "2026-05-10"},
    )
    assert "查無資料" in md


@pytest.mark.asyncio
async def test_rate_limit_returns_user_facing_message(install_fake_client):
    install_fake_client(raise_exc=RateLimitError("429"))
    md = await tools.dispatch(
        "query_dataset",
        {"dataset": "TaiwanStockPrice", "data_id": "2330", "start_date": "2026-05-10"},
    )
    assert "上限" in md


@pytest.mark.asyncio
async def test_upstream_error_returns_user_facing_message(install_fake_client):
    install_fake_client(raise_exc=UpstreamError("503"))
    md = await tools.dispatch(
        "query_dataset",
        {"dataset": "TaiwanStockPrice", "data_id": "2330", "start_date": "2026-05-10"},
    )
    assert "無法連線" in md or "暫時" in md


@pytest.mark.asyncio
async def test_unknown_tool_name_raises():
    with pytest.raises(ValueError):
        await tools.dispatch("does_not_exist", {})
