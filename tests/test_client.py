"""Tests for FinMindClient (httpx async wrapper)."""

import httpx
import pytest
import respx

from finmind_mcp.client import FinMindClient
from finmind_mcp.errors import (
    AuthenticationError,
    EmptyDataError,
    PaymentRequiredError,
    RateLimitError,
    UpstreamError,
)


@pytest.mark.asyncio
@respx.mock
async def test_query_dataset_returns_rows():
    respx.get("https://api.finmindtrade.com/api/v4/data").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": [
                    {"date": "2026-05-10", "stock_id": "2330", "close": 1000.0}
                ],
                "status": 200,
            },
        )
    )
    client = FinMindClient(token="t")
    rows = await client.query_dataset(
        dataset="TaiwanStockPrice",
        data_id="2330",
        start_date="2026-05-10",
    )
    assert len(rows) == 1
    assert rows[0]["stock_id"] == "2330"


@pytest.mark.asyncio
@respx.mock
async def test_query_dataset_sends_token_and_params():
    route = respx.get("https://api.finmindtrade.com/api/v4/data").mock(
        return_value=httpx.Response(
            200,
            json={"data": [{"date": "2026-05-10"}], "status": 200},
        )
    )
    client = FinMindClient(token="abc123")
    await client.query_dataset(
        dataset="TaiwanStockPrice",
        data_id="2330",
        start_date="2026-05-01",
        end_date="2026-05-10",
    )
    assert route.called
    request = route.calls.last.request
    params = dict(request.url.params)
    assert params["dataset"] == "TaiwanStockPrice"
    assert params["data_id"] == "2330"
    assert params["start_date"] == "2026-05-01"
    assert params["end_date"] == "2026-05-10"
    # Auth is sent as a Bearer header, not a query param.
    assert "token" not in params
    assert request.headers["Authorization"] == "Bearer abc123"


@pytest.mark.asyncio
@respx.mock
async def test_query_dataset_401_raises_auth_error():
    respx.get("https://api.finmindtrade.com/api/v4/data").mock(
        return_value=httpx.Response(
            401, json={"status": 401, "msg": "invalid token"}
        )
    )
    client = FinMindClient(token="bad")
    with pytest.raises(AuthenticationError):
        await client.query_dataset(
            dataset="TaiwanStockPrice",
            data_id="2330",
            start_date="2026-05-10",
        )


@pytest.mark.asyncio
@respx.mock
async def test_query_dataset_402_raises_payment_error():
    respx.get("https://api.finmindtrade.com/api/v4/data").mock(
        return_value=httpx.Response(
            402, json={"status": 402, "msg": "sponsor required"}
        )
    )
    client = FinMindClient(token="t")
    with pytest.raises(PaymentRequiredError):
        await client.query_dataset(
            dataset="TaiwanStockBlockTrade",
            data_id="2330",
            start_date="2026-05-10",
        )


@pytest.mark.asyncio
@respx.mock
async def test_query_dataset_429_raises_rate_limit_error():
    respx.get("https://api.finmindtrade.com/api/v4/data").mock(
        return_value=httpx.Response(429, json={"status": 429, "msg": "rate limit"})
    )
    client = FinMindClient(token="t")
    with pytest.raises(RateLimitError):
        await client.query_dataset(
            dataset="TaiwanStockPrice",
            data_id="2330",
            start_date="2026-05-10",
        )


@pytest.mark.asyncio
@respx.mock
async def test_query_dataset_500_raises_upstream_error():
    respx.get("https://api.finmindtrade.com/api/v4/data").mock(
        return_value=httpx.Response(503, text="upstream down")
    )
    client = FinMindClient(token="t")
    with pytest.raises(UpstreamError):
        await client.query_dataset(
            dataset="TaiwanStockPrice",
            data_id="2330",
            start_date="2026-05-10",
        )


@pytest.mark.asyncio
@respx.mock
async def test_query_dataset_empty_raises_empty_error():
    respx.get("https://api.finmindtrade.com/api/v4/data").mock(
        return_value=httpx.Response(200, json={"data": [], "status": 200})
    )
    client = FinMindClient(token="t")
    with pytest.raises(EmptyDataError):
        await client.query_dataset(
            dataset="TaiwanStockPrice",
            data_id="9999",
            start_date="2026-05-10",
        )


@pytest.mark.asyncio
@respx.mock
async def test_token_from_env(monkeypatch):
    monkeypatch.setenv("FINMIND_TOKEN", "env-token")
    respx.get("https://api.finmindtrade.com/api/v4/data").mock(
        return_value=httpx.Response(
            200, json={"data": [{"stock_id": "2330", "close": 1000.0}]}
        )
    )
    client = FinMindClient()  # no token arg
    assert client.token == "env-token"
    rows = await client.query_dataset(
        dataset="TaiwanStockPrice", data_id="2330", start_date="2026-05-10"
    )
    assert rows[0]["stock_id"] == "2330"


def test_missing_token_raises_auth_error(monkeypatch):
    monkeypatch.delenv("FINMIND_TOKEN", raising=False)
    with pytest.raises(AuthenticationError):
        FinMindClient()


@pytest.mark.asyncio
@respx.mock
async def test_query_trading_daily_report():
    route = respx.get(
        "https://api.finmindtrade.com/api/v4/taiwan_stock_trading_daily_report"
    ).mock(
        return_value=httpx.Response(
            200,
            json={
                "data": [
                    {"date": "2026-05-10", "stock_id": "2330", "buy": 100},
                ],
                "status": 200,
            },
        )
    )
    client = FinMindClient(token="t")
    rows = await client.query_trading_daily_report(
        data_id="2330",
        date="2026-05-10",
    )
    assert len(rows) == 1
    assert rows[0]["stock_id"] == "2330"
    params = dict(route.calls.last.request.url.params)
    assert params["data_id"] == "2330"
    assert params["date"] == "2026-05-10"
