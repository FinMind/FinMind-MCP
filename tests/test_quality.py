"""Tests for get_data_quality (summary.json is mocked with respx)."""

import httpx
import pytest
import respx

from finmind_mcp import quality, tools

SUMMARY = {
    "schema": 1,
    "edition": "2026-11",
    "run_date": "2026-11-15",
    "report_url": {
        "zh": "https://finmind.github.io/DataQuality/",
        "en": "https://finmind.github.io/en/DataQuality/",
    },
    "groups": {
        "stock": {"zh": "台股", "en": "Taiwan stocks"},
        "macro": {"zh": "總經、匯率與原物料", "en": "Macro, FX & commodities"},
    },
    "datasets": [
        {
            "dataset": "TaiwanStockPrice",
            "group": "stock",
            "overall": "validated_notes",
            "checks": {
                "D9": "pass", "D2cal": "pass", "D2sat": "pass", "OFF": "pass",
                "XCHK": "pass", "D6": "pass", "D5": "pass", "D8": "note", "D3": "pass",
            },
            "official_match_rate": 1.0,
            "cross_dataset_match_rate": 1.0,
            "first_date": "1999-01-05",
            "last_date": "2026-11-13",
            "run_date": "2026-11-14",
        },
        {
            "dataset": "GoldPrice",
            "group": "macro",
            "overall": "validated",
            "checks": {
                "D9": "pass", "D2cal": "pass", "D2sat": "na", "OFF": "pass",
                "XCHK": "planned", "D6": "pass", "D5": "pass", "D8": "pass", "D3": "na",
            },
            "official_match_rate": 1.0,
            "cross_dataset_match_rate": None,
            "first_date": "2000-01-03",
            "last_date": "2026-11-13",
            "run_date": "2026-11-14",
        },
    ],
}


def _mock(**kwargs):
    return respx.get(quality.SUMMARY_URL).mock(return_value=httpx.Response(200, **kwargs))


@pytest.mark.asyncio
@respx.mock
async def test_single_dataset_report():
    _mock(json=SUMMARY)
    md = await tools.dispatch("get_data_quality", {"dataset": "TaiwanStockPrice"})
    assert "### TaiwanStockPrice 資料品質報告（2026-11）" in md
    assert "已驗證・附資料特性說明" in md
    assert "檢測日期：2026-11-14" in md
    assert "與官方來源一致率：100.00%" in md
    assert "跨資料集一致率：100.00%" in md
    assert "https://finmind.github.io/DataQuality/TaiwanStockPrice/" in md
    assert "| 數值與主鍵一致性 | 資料特性說明 |" in md
    assert "| 資料更新時效 | 通過 |" in md
    # All nine checks are rendered.
    assert md.count("| 通過 |") + md.count("| 資料特性說明 |") == 9


@pytest.mark.asyncio
@respx.mock
async def test_dataset_lookup_is_case_insensitive_and_supports_en_links():
    _mock(json=SUMMARY)
    md = await tools.dispatch("get_data_quality", {"dataset": "goldprice", "lang": "en"})
    assert "### GoldPrice 資料品質報告" in md
    assert "https://finmind.github.io/en/DataQuality/GoldPrice/" in md
    assert "| 跨資料集一致性 | 規劃中 |" in md
    assert "| 補行交易日涵蓋 | 不適用 |" in md
    # No cross-dataset rate line when the value is null.
    assert "跨資料集一致率" not in md


@pytest.mark.asyncio
@respx.mock
async def test_overview_without_dataset():
    _mock(json=SUMMARY)
    md = await tools.dispatch("get_data_quality", {})
    assert "### FinMind 資料品質總覽（2026-11）" in md
    assert "檢測日期：2026-11-15" in md
    assert "2 個資料集，已驗證 2 個" in md
    assert "| 台股 | TaiwanStockPrice | 已驗證・附資料特性說明 | 100.00% |" in md
    assert "| 總經、匯率與原物料 | GoldPrice | 已驗證 | 100.00% |" in md
    assert "https://finmind.github.io/DataQuality/" in md
    assert "https://finmind.github.io/DataQuality/Methodology/" in md


@pytest.mark.asyncio
@respx.mock
async def test_unknown_dataset_points_to_overview_and_close_matches():
    _mock(json=SUMMARY)
    md = await tools.dispatch("get_data_quality", {"dataset": "TaiwanStockPrices"})
    assert "https://finmind.github.io/DataQuality/" in md
    assert "https://finmind.github.io/DataQuality/TaiwanStockPrice/" in md


@pytest.mark.asyncio
@respx.mock
async def test_http_error_returns_message_not_exception():
    respx.get(quality.SUMMARY_URL).mock(return_value=httpx.Response(503))
    md = await tools.dispatch("get_data_quality", {"dataset": "TaiwanStockPrice"})
    assert "目前無法取得資料品質摘要" in md
    assert "https://finmind.github.io/DataQuality/" in md


@pytest.mark.asyncio
@respx.mock
async def test_network_error_returns_message_not_exception():
    respx.get(quality.SUMMARY_URL).mock(side_effect=httpx.ConnectTimeout("timeout"))
    md = await tools.dispatch("get_data_quality", {})
    assert "目前無法取得資料品質摘要" in md


@pytest.mark.asyncio
@respx.mock
async def test_malformed_json_returns_message_not_exception():
    _mock(text="<html>not json</html>")
    md = await tools.dispatch("get_data_quality", {})
    assert "目前無法取得資料品質摘要" in md
    _mock(json={"unexpected": True})
    md = await tools.dispatch("get_data_quality", {})
    assert "目前無法取得資料品質摘要" in md


@pytest.mark.asyncio
@respx.mock
async def test_works_without_finmind_token(monkeypatch):
    monkeypatch.delenv("FINMIND_TOKEN", raising=False)
    _mock(json=SUMMARY)
    md = await tools.dispatch("get_data_quality", {"dataset": "TaiwanStockPrice"})
    assert "TaiwanStockPrice 資料品質報告" in md


def test_data_quality_resource_is_registered():
    from finmind_mcp import knowledge

    uris = [str(r.uri) for r in knowledge.resource_definitions()]
    assert "finmind://data-quality" in uris
    md = knowledge.read("finmind://data-quality")
    assert "https://finmind.github.io/DataQuality/" in md
    assert "get_data_quality" in md
