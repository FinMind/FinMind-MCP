"""Tests for the dedicated-endpoint tool (`query_endpoint`), the whole-day
download tool (`download_storage_object`) and API error-detail passthrough.

All HTTP is mocked; live behaviour is covered by regression/runner.py.
"""

from __future__ import annotations

import builtins
from pathlib import Path

import httpx
import pyarrow as pa
import pyarrow.parquet as pq
import pytest
import respx

from finmind_mcp import endpoints, storage, tools
from finmind_mcp.client import FinMindClient, _extract_detail
from finmind_mcp.errors import (
    AuthenticationError,
    BadRequestError,
    EmptyDataError,
    PaymentRequiredError,
    RateLimitError,
)

API = "https://api.finmindtrade.com/api/v4"
TIER_MSG = (
    "Your level is free. Please update your user level. "
    "Detail information:https://finmindtrade.com/analysis/#/Sponsor/sponsor"
)


# --- client: query_endpoint ---------------------------------------------------


@respx.mock
async def test_query_endpoint_hits_dedicated_path_with_params():
    route = respx.get(f"{API}/taiwan_stock_trading_daily_report_secid_agg").mock(
        return_value=httpx.Response(
            200, json={"status": 200, "data": [{"stock_id": "2330"}]}
        )
    )
    client = FinMindClient(token="t")
    rows = await client.query_endpoint(
        "taiwan_stock_trading_daily_report_secid_agg",
        {
            "data_id": "2330",
            "securities_trader_id": "1020",
            "start_date": "2024-07-01",
            "end_date": "2024-07-05",
        },
    )
    assert rows == [{"stock_id": "2330"}]
    req = route.calls.last.request
    assert req.url.path == "/api/v4/taiwan_stock_trading_daily_report_secid_agg"
    assert dict(req.url.params)["securities_trader_id"] == "1020"
    assert req.headers["Authorization"] == "Bearer t"


@respx.mock
async def test_query_endpoint_list_param_is_repeated_key():
    route = respx.get(f"{API}/taiwan_stock_tick_snapshot").mock(
        return_value=httpx.Response(
            200, json={"status": 200, "data": [{"stock_id": "2330"}]}
        )
    )
    await FinMindClient(token="t").query_endpoint(
        "taiwan_stock_tick_snapshot", {"data_id": ["2330", "001"]}
    )
    assert route.calls.last.request.url.params.get_list("data_id") == ["2330", "001"]


@respx.mock
async def test_query_endpoint_400_detail_is_preserved():
    detail = "parameter securities_trader_id can't be none on TaiwanStockTradingDailyReportSecIdAgg dataset"
    respx.get(f"{API}/taiwan_stock_trading_daily_report_secid_agg").mock(
        return_value=httpx.Response(400, json={"detail": detail})
    )
    with pytest.raises(BadRequestError) as info:
        await FinMindClient(token="t").query_endpoint(
            "taiwan_stock_trading_daily_report_secid_agg", {"data_id": "2330"}
        )
    assert info.value.detail == detail
    assert info.value.status == 400


@respx.mock
async def test_query_endpoint_empty_raises_empty():
    respx.get(f"{API}/taiwan_futures_snapshot").mock(
        return_value=httpx.Response(200, json={"status": 200, "data": []})
    )
    with pytest.raises(EmptyDataError):
        await FinMindClient(token="t").query_endpoint(
            "taiwan_futures_snapshot", {"data_id": "XXX"}
        )


@pytest.mark.parametrize(
    "code, body, exc",
    [
        (400, {"msg": TIER_MSG, "status": 400}, PaymentRequiredError),
        (400, {"msg": "Token is illegal.", "status": 400}, AuthenticationError),
        (
            402,
            {"msg": "Requests reach the upper limit.", "status": 402},
            RateLimitError,
        ),
        (
            422,
            {"detail": [{"loc": ["query", "date"], "msg": "bad date"}]},
            BadRequestError,
        ),
        (
            404,
            {"detail": "Object not found: dataset=TaiwanStockKBar, date=2024-07-06"},
            BadRequestError,
        ),
    ],
)
@respx.mock
async def test_error_classification(code, body, exc):
    respx.get(f"{API}/taiwan_stock_tick_snapshot").mock(
        return_value=httpx.Response(code, json=body)
    )
    with pytest.raises(exc):
        await FinMindClient(token="t").query_endpoint("taiwan_stock_tick_snapshot", {})


def test_extract_detail_formats_and_truncates_validation_list():
    body = {
        "detail": [
            {"loc": ["query", "dataset"], "msg": "Input should be " + "'X', " * 300}
        ]
    }
    text = _extract_detail(body)
    assert text.startswith("dataset: Input should be")
    assert text.endswith("（已截斷）")
    assert len(text) < 700


# --- client: storage_objects -------------------------------------------------


@respx.mock
async def test_storage_object_url_returns_redirect_location():
    route = respx.get(f"{API}/storage_objects").mock(
        return_value=httpx.Response(
            307, headers={"location": "https://obj.example/x.parquet?sig=1"}
        )
    )
    url = await FinMindClient(token="t").storage_object_url(
        "TaiwanStockKBar", "2026-10-16"
    )
    assert url == "https://obj.example/x.parquet?sig=1"
    assert dict(route.calls.last.request.url.params) == {
        "dataset": "TaiwanStockKBar",
        "date": "2026-10-16",
    }


@respx.mock
async def test_storage_object_url_tier_error():
    respx.get(f"{API}/storage_objects").mock(
        return_value=httpx.Response(400, json={"msg": TIER_MSG, "status": 400})
    )
    with pytest.raises(PaymentRequiredError):
        await FinMindClient(token="t").storage_object_url(
            "TaiwanStockKBar", "2026-10-16"
        )


@respx.mock
async def test_download_streams_without_auth_header(tmp_path):
    route = respx.get("https://obj.example/x.parquet").mock(
        return_value=httpx.Response(200, content=b"PAR1data")
    )
    dest = tmp_path / "sub" / "x.parquet"
    n = await FinMindClient(token="t").download("https://obj.example/x.parquet", dest)
    assert n == 8 and dest.read_bytes() == b"PAR1data"
    assert not dest.with_name("x.parquet.part").exists()
    # A signed URL must not carry the FinMind bearer token.
    assert "Authorization" not in route.calls.last.request.headers


# --- tools: query_endpoint ----------------------------------------------------


class EndpointFake:
    def __init__(self, result=None, raise_exc=None):
        self.result = result
        self.raise_exc = raise_exc
        self.calls: list = []

    async def query_endpoint(self, endpoint, params):
        self.calls.append((endpoint, params))
        if self.raise_exc:
            raise self.raise_exc
        return self.result

    async def storage_object_url(self, dataset, date):
        self.calls.append(("url", dataset, date))
        if self.raise_exc:
            raise self.raise_exc
        return "https://obj.example/signed"

    async def download(self, url, dest: Path):
        self.calls.append(("download", url))
        dest.parent.mkdir(parents=True, exist_ok=True)
        _write_sample(dest)
        return dest.stat().st_size


def _install(monkeypatch, **kwargs):
    fake = EndpointFake(**kwargs)
    monkeypatch.setattr(tools, "_make_client", lambda: fake)
    return fake


def test_every_endpoint_is_in_tool_enum():
    tool = next(t for t in tools.tool_definitions() if t.name == "query_endpoint")
    assert tool.input_schema["properties"]["endpoint"]["enum"] == list(
        endpoints.ENDPOINTS
    )
    for name in endpoints.ENDPOINTS:
        assert name in tool.description


async def test_query_endpoint_secid_agg(monkeypatch):
    fake = _install(monkeypatch, result=[{"stock_id": "2330", "buy_volume": 12157}])
    md = await tools.dispatch(
        "query_endpoint",
        {
            "endpoint": "taiwan_stock_trading_daily_report_secid_agg",
            "data_id": "2330",
            "securities_trader_id": "1020",
            "start_date": "2024-07-01",
            "end_date": "2024-07-05",
        },
    )
    assert fake.calls[0][0] == "taiwan_stock_trading_daily_report_secid_agg"
    assert "12157" in md


async def test_query_endpoint_missing_param_never_calls_api(monkeypatch):
    fake = _install(monkeypatch, result=[])
    md = await tools.dispatch(
        "query_endpoint",
        {
            "endpoint": "taiwan_stock_trading_daily_report_secid_agg",
            "data_id": "2330",
            "start_date": "2024-07-01",
            "end_date": "2024-07-05",
        },
    )
    assert "securities_trader_id" in md and "缺少必填" in md
    assert fake.calls == []


async def test_query_endpoint_rejects_unknown_param_and_endpoint(monkeypatch):
    fake = _install(monkeypatch, result=[])
    md = await tools.dispatch(
        "query_endpoint", {"endpoint": "taiwan_futures_snapshot", "date": "2024-07-01"}
    )
    assert "不接受參數 `date`" in md
    md = await tools.dispatch("query_endpoint", {"endpoint": "user_info"})
    assert "不支援的 endpoint" in md
    assert fake.calls == []


async def test_query_endpoint_one_of(monkeypatch):
    _install(monkeypatch, result=[])
    md = await tools.dispatch(
        "query_endpoint",
        {"endpoint": "taiwan_stock_warrant_trading_daily_report", "date": "2023-06-21"},
    )
    assert "`data_id` 或 `securities_trader_id`" in md


async def test_query_endpoint_snapshot_multi_ids(monkeypatch):
    fake = _install(monkeypatch, result=[{"stock_id": "2330"}, {"stock_id": "001"}])
    await tools.dispatch(
        "query_endpoint",
        {"endpoint": "taiwan_stock_tick_snapshot", "data_id": ["2330", "001"]},
    )
    assert fake.calls[0] == ("taiwan_stock_tick_snapshot", {"data_id": ["2330", "001"]})


async def test_query_endpoint_datalist_and_translation_render(monkeypatch):
    _install(monkeypatch, result=["Japan", "Taiwan"])
    md = await tools.dispatch(
        "query_endpoint", {"endpoint": "datalist", "dataset": "ExchangeRate"}
    )
    assert "| data_id |" in md and "Taiwan" in md
    _install(monkeypatch, result={"name": ["應付帳款"], "english": ["AccountsPayable"]})
    md = await tools.dispatch(
        "query_endpoint",
        {"endpoint": "translation", "dataset": "TaiwanStockBalanceSheet"},
    )
    assert "| name | english |" in md and "AccountsPayable" in md


async def test_query_endpoint_tier_error_names_plan(monkeypatch):
    _install(
        monkeypatch,
        raise_exc=PaymentRequiredError(TIER_MSG, detail=TIER_MSG, status=400),
    )
    md = await tools.dispatch(
        "query_endpoint", {"endpoint": "taiwan_options_snapshot", "data_id": "TXO"}
    )
    assert "`taiwan_options_snapshot` 需要 **Sponsor** 以上方案" in md
    assert TIER_MSG in md
    assert "https://finmindtrade.com/analysis/#/Sponsor/sponsor" in md
    assert "get_pricing" in md


async def test_query_endpoint_bad_request_quotes_detail(monkeypatch):
    detail = "parameter securities_trader_id can't be none"
    _install(monkeypatch, raise_exc=BadRequestError(detail, detail=detail, status=400))
    md = await tools.dispatch(
        "query_endpoint",
        {
            "endpoint": "taiwan_stock_trading_daily_report",
            "data_id": "2330",
            "date": "2024-07-01",
        },
    )
    assert detail in md and "參數錯誤" in md


async def test_query_dataset_points_dedicated_only_to_query_endpoint(monkeypatch):
    fake = _install(monkeypatch, result=[])
    md = await tools.dispatch(
        "query_dataset",
        {"dataset": "TaiwanStockTradingDailyReportSecIdAgg", "data_id": "2330"},
    )
    assert (
        "query_endpoint" in md and "taiwan_stock_trading_daily_report_secid_agg" in md
    )
    assert fake.calls == []


def test_required_tier_lookup():
    assert tools.required_tier("storage_objects:TaiwanStockKBar") == "Sponsor Pro"
    assert tools.required_tier("taiwan_stock_tick_snapshot") == "Sponsor"
    assert tools.required_tier("TaiwanStockPriceTick") == "Backer"
    assert tools.required_tier("TaiwanStockPrice").startswith("Backer（不帶 data_id")
    assert tools.required_tier("NoSuchDataset") is None


# --- tools: download_storage_object -----------------------------------------


def _write_sample(path: Path) -> None:
    table = pa.table(
        {
            "date": ["2026-10-16"] * 6,
            "stock_id": ["2330", "2330", "2317", "2317", "0050", "2330"],
            "securities_trader_id": ["1020", "9200", "1020", "9200", "1020", "1020"],
            "buy": [1, 2, 3, 4, 5, 6],
        }
    )
    pq.write_table(table, path, row_group_size=2)


@pytest.fixture
def download_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("FINMIND_DOWNLOAD_DIR", str(tmp_path))
    return tmp_path


async def test_download_returns_summary_not_whole_file(monkeypatch, download_dir):
    fake = _install(monkeypatch)
    md = await tools.dispatch(
        "download_storage_object",
        {"dataset": "TaiwanStockTradingDailyReport", "date": "2026-10-16", "limit": 2},
    )
    path = (
        download_dir
        / "TaiwanStockTradingDailyReport"
        / "TaiwanStockTradingDailyReport_2026-10-16.parquet"
    )
    assert path.is_file()
    assert str(path) in md
    assert "總筆數：6" in md
    assert "stock_id (string)" in md
    assert "前 2 筆" in md
    assert fake.calls[0] == ("url", "TaiwanStockTradingDailyReport", "2026-10-16")


async def test_download_filters_by_data_id_and_broker(monkeypatch, download_dir):
    _install(monkeypatch)
    md = await tools.dispatch(
        "download_storage_object",
        {
            "dataset": "TaiwanStockTradingDailyReport",
            "date": "2026-10-16",
            "data_id": "2330",
            "securities_trader_id": ["1020"],
            "columns": ["stock_id", "buy", "nope"],
        },
    )
    assert "符合 2 筆" in md
    assert "| stock_id | buy |" in md
    assert "忽略不存在的欄位：nope" in md


async def test_download_uses_cache_unless_refresh(monkeypatch, download_dir):
    fake = _install(monkeypatch)
    args = {"dataset": "TaiwanStockKBar", "date": "2026-10-16"}
    await tools.dispatch("download_storage_object", args)
    md = await tools.dispatch("download_storage_object", args)
    assert "本機快取" in md
    assert [c[0] for c in fake.calls] == ["url", "download"]
    await tools.dispatch("download_storage_object", {**args, "refresh": True})
    assert [c[0] for c in fake.calls] == ["url", "download", "url", "download"]


async def test_download_validates_inputs(monkeypatch, download_dir):
    fake = _install(monkeypatch)
    md = await tools.dispatch(
        "download_storage_object", {"dataset": "TaiwanStockPrice", "date": "2026-10-16"}
    )
    assert "不支援的整日檔" in md
    md = await tools.dispatch(
        "download_storage_object", {"dataset": "TaiwanStockKBar", "date": "../../etc"}
    )
    assert "YYYY-MM-DD" in md
    md = await tools.dispatch(
        "download_storage_object",
        {
            "dataset": "TaiwanFuturesTick",
            "date": "2026-10-16",
            "securities_trader_id": "1020",
        },
    )
    assert "securities_trader_id" in md
    assert fake.calls == []


async def test_download_tier_error_says_sponsor_pro(monkeypatch, download_dir):
    _install(
        monkeypatch,
        raise_exc=PaymentRequiredError(TIER_MSG, detail=TIER_MSG, status=400),
    )
    md = await tools.dispatch(
        "download_storage_object",
        {"dataset": "TaiwanStockPriceTick", "date": "2026-10-16"},
    )
    assert "**Sponsor Pro** 以上方案" in md
    assert "storage_objects 整日檔 TaiwanStockPriceTick" in md
    assert TIER_MSG in md and "get_pricing" in md


async def test_download_404_explains_missing_day(monkeypatch, download_dir):
    detail = "Object not found: dataset=TaiwanStockKBar, date=2026-10-17"
    _install(monkeypatch, raise_exc=BadRequestError(detail, detail=detail, status=404))
    md = await tools.dispatch(
        "download_storage_object", {"dataset": "TaiwanStockKBar", "date": "2026-10-17"}
    )
    assert "非交易日" in md and detail in md


async def test_download_without_pyarrow_still_returns_path(monkeypatch, download_dir):
    _install(monkeypatch)
    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name.startswith("pyarrow"):
            raise ImportError("no pyarrow")
        return real_import(name, *args, **kwargs)

    # Pre-create the file so the fake download (which needs pyarrow) is skipped.
    path = storage.object_path("TaiwanStockKBar", "2026-10-16")
    path.parent.mkdir(parents=True)
    _write_sample(path)
    monkeypatch.setattr(builtins, "__import__", fake_import)
    md = await tools.dispatch(
        "download_storage_object", {"dataset": "TaiwanStockKBar", "date": "2026-10-16"}
    )
    assert str(path) in md
    assert "finmind-mcp[parquet]" in md


def test_default_download_dir_is_user_cache(monkeypatch):
    monkeypatch.delenv("FINMIND_DOWNLOAD_DIR", raising=False)
    path = storage.download_dir()
    assert path.parts[-2:] == ("finmind-mcp", "storage_objects")
