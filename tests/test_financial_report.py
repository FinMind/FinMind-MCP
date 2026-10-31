"""Tests for `download_financial_report` (財報／年報 PDF via storage_objects).

All HTTP is mocked; live behaviour is covered by regression/runner.py.
"""

from __future__ import annotations

from pathlib import Path

import httpx
import pytest
import respx

from finmind_mcp import storage, tools
from finmind_mcp.client import FinMindClient
from finmind_mcp.errors import BadRequestError, PaymentRequiredError

API = "https://api.finmindtrade.com/api/v4"


def _pdf(pages: list[str]) -> bytes:
    """Minimal valid PDF, one Helvetica text line per page ('' = no text layer)."""
    n = len(pages)
    font_id = 3 + 2 * n
    objs = [
        "<< /Type /Catalog /Pages 2 0 R >>",
        "<< /Type /Pages /Kids [%s] /Count %d >>"
        % (" ".join(f"{3 + 2 * i} 0 R" for i in range(n)), n),
    ]
    for i, text in enumerate(pages):
        objs.append(
            "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 300 300] "
            f"/Resources << /Font << /F1 {font_id} 0 R >> >> /Contents {4 + 2 * i} 0 R >>"
        )
        stream = f"BT /F1 12 Tf 20 150 Td ({text}) Tj ET" if text else ""
        objs.append(f"<< /Length {len(stream)} >>\nstream\n{stream}\nendstream")
    objs.append("<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
    out = b"%PDF-1.4\n"
    offsets = []
    for i, body in enumerate(objs, start=1):
        offsets.append(len(out))
        out += f"{i} 0 obj\n{body}\nendobj\n".encode("latin-1")
    xref = len(out)
    out += f"xref\n0 {len(objs) + 1}\n0000000000 65535 f \n".encode()
    out += b"".join(f"{o:010d} 00000 n \n".encode() for o in offsets)
    out += f"trailer\n<< /Size {len(objs) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()
    return out


SAMPLE = _pdf(["Cover 2330", "Contents notes p3", "", "Inventory WIP 2839", "Revenue HPC"])


class ReportFake:
    def __init__(self, content: bytes = SAMPLE, raise_exc=None):
        self.content = content
        self.raise_exc = raise_exc
        self.calls: list = []

    async def financial_report_url(self, data_id, year, quarter, report_category):
        self.calls.append(("url", data_id, year, quarter, report_category))
        if self.raise_exc:
            raise self.raise_exc
        return "https://obj.example/signed"

    async def download(self, url, dest: Path):
        self.calls.append(("download", url))
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(self.content)
        return len(self.content)


@pytest.fixture
def fake(monkeypatch, tmp_path):
    monkeypatch.setenv("FINMIND_DOWNLOAD_DIR", str(tmp_path / "storage_objects"))

    def _install(**kwargs):
        client = ReportFake(**kwargs)
        monkeypatch.setattr(tools, "_make_client", lambda: client)
        return client

    return _install


# --- client ------------------------------------------------------------------


@respx.mock
async def test_financial_report_url_sends_period_params():
    route = respx.get(f"{API}/storage_objects").mock(
        return_value=httpx.Response(307, headers={"location": "https://obj.example/r.pdf?sig=1"})
    )
    url = await FinMindClient(token="t").financial_report_url("2330", 2026, 2, "financial_report")
    assert url == "https://obj.example/r.pdf?sig=1"
    assert dict(route.calls.last.request.url.params) == {
        "dataset": "TaiwanStockFinancialReportFile",
        "data_id": "2330",
        "year": "2026",
        "quarter": "2",
        "report_category": "financial_report",
    }


# --- storage helpers ---------------------------------------------------------


def test_parse_pages_clamps_and_merges():
    assert storage.parse_pages("3,1-2,9-12", 10) == [1, 2, 3, 9, 10]
    with pytest.raises(ValueError):
        storage.parse_pages("a-b", 10)


def test_garbled_detection():
    assert storage._is_garbled("ʮ̡ᐼ௅ʿ౺෥ɤɚAᅀ 300-096 อ϶߅ኪ෤ਜɢБʬ༩8໮ ཥ ༑ ʮ̡ᐼ௅ʿ౺෥")
    assert not storage._is_garbled("十二、存貨 115年6月30日 製成品 在製品 原料 物料及零件（單位：仟元）")
    assert not storage._is_garbled("Inventory WIP 2839")


def test_sniff_extension(tmp_path):
    pdf, doc = tmp_path / "a", tmp_path / "b"
    pdf.write_bytes(SAMPLE)
    doc.write_bytes(b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1rest")
    assert storage.sniff_extension(pdf) == "pdf"
    assert storage.sniff_extension(doc) == "doc"


# --- tool --------------------------------------------------------------------


async def test_default_returns_cover_and_contents(fake, tmp_path):
    client = fake()
    md = await tools.dispatch(
        "download_financial_report", {"data_id": "2330", "year": 2026, "quarter": 2}
    )
    path = tmp_path / "financial_report_file" / "financial_report" / "2330" / "2330_2026Q2.pdf"
    assert path.is_file() and str(path) in md
    assert "總頁數：5" in md
    assert "Cover 2330" in md and "Contents notes p3" in md
    assert "Inventory" not in md
    assert "目錄" in md
    assert client.calls[0] == ("url", "2330", 2026, 2, "financial_report")


async def test_keyword_returns_matching_pages_only(fake):
    fake()
    md = await tools.dispatch(
        "download_financial_report",
        {"data_id": "2330", "year": 2026, "quarter": 2, "keyword": "Inventory"},
    )
    assert "含「Inventory」的頁面：[4]" in md
    assert "#### 第 4 頁" in md and "Revenue" not in md


async def test_pages_reports_image_only_pages(fake):
    fake()
    md = await tools.dispatch(
        "download_financial_report",
        {"data_id": "2330", "year": 2026, "quarter": 2, "pages": "3-4"},
    )
    assert "第 [3] 頁沒有文字層" in md
    assert "Inventory WIP 2839" in md


async def test_bad_pages_format(fake):
    fake()
    md = await tools.dispatch(
        "download_financial_report",
        {"data_id": "2330", "year": 2026, "quarter": 2, "pages": "x"},
    )
    assert "`pages` 格式錯誤" in md


async def test_annual_report_forces_q4(fake, tmp_path):
    client = fake()
    await tools.dispatch(
        "download_financial_report",
        {"data_id": "2330", "year": 2025, "quarter": 1, "report_category": "annual_report"},
    )
    assert client.calls[0] == ("url", "2330", 2025, 4, "annual_report")
    assert (tmp_path / "financial_report_file" / "annual_report" / "2330" / "2330_2025.pdf").is_file()


async def test_uses_cache_unless_refresh(fake):
    client = fake()
    args = {"data_id": "2330", "year": 2026, "quarter": 2}
    await tools.dispatch("download_financial_report", args)
    md = await tools.dispatch("download_financial_report", args)
    assert "本機快取" in md
    assert [c[0] for c in client.calls] == ["url", "download"]
    await tools.dispatch("download_financial_report", {**args, "refresh": True})
    assert [c[0] for c in client.calls] == ["url", "download", "url", "download"]


async def test_word_document_is_saved_without_text(fake, tmp_path):
    fake(content=b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1rest")
    md = await tools.dispatch(
        "download_financial_report", {"data_id": "1101", "year": 2014, "quarter": 4}
    )
    assert (tmp_path / "financial_report_file" / "financial_report" / "1101" / "1101_2014Q4.doc").is_file()
    assert "Word 檔" in md


@pytest.mark.parametrize(
    "args, expected",
    [
        ({"year": 2026, "quarter": 2}, "data_id"),
        ({"data_id": "../x", "year": 2026, "quarter": 2}, "data_id"),
        ({"data_id": "2330", "year": 2026}, "quarter"),
        ({"data_id": "2330", "year": "abc", "quarter": 2}, "西元年"),
        ({"data_id": "2330", "year": 2026, "quarter": 2, "report_category": "x"}, "report_category"),
    ],
)
async def test_validates_inputs_without_calling_api(fake, args, expected):
    client = fake()
    md = await tools.dispatch("download_financial_report", args)
    assert expected in md
    assert client.calls == []


async def test_not_found_message(fake):
    fake(raise_exc=BadRequestError("Object not found", status=404, detail="Object not found"))
    md = await tools.dispatch(
        "download_financial_report", {"data_id": "2330", "year": 2030, "quarter": 1}
    )
    assert "查無這份財報" in md


async def test_tier_message_names_sponsor_pro(fake):
    fake(raise_exc=PaymentRequiredError("tier", detail="Your level is free."))
    md = await tools.dispatch(
        "download_financial_report", {"data_id": "2330", "year": 2026, "quarter": 2}
    )
    assert "財報 PDF" in md and "Sponsor Pro" in md
