"""Async httpx wrapper around the FinMind v4 HTTP API."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any, Optional, Union

import httpx

from .errors import (
    AuthenticationError,
    BadRequestError,
    EmptyDataError,
    PaymentRequiredError,
    RateLimitError,
    UpstreamError,
)

BASE_URL = "https://api.finmindtrade.com/api"
DEFAULT_TIMEOUT = 30.0
# Whole-day parquet files run from a few MB to a few hundred MB.
DOWNLOAD_TIMEOUT = 600.0
# Keep quoted API error text short: a 422 enum error lists ~100 dataset names.
MAX_DETAIL_CHARS = 600

# FinMind answers "plan too low" with HTTP 400 and this message
# (`Your level is free. Please update your user level. ...`).
_TIER_PATTERN = re.compile(r"update your user level|your level is", re.IGNORECASE)
_RATE_LIMIT_PATTERN = re.compile(r"upper limit", re.IGNORECASE)
_TOKEN_PATTERN = re.compile(r"token is illegal", re.IGNORECASE)

ParamValue = Union[str, list[str]]


class FinMindClient:
    """Thin async client for FinMind /v4 endpoints.

    Token resolves from constructor arg, then `FINMIND_TOKEN` env var.
    """

    def __init__(
        self,
        token: Optional[str] = None,
        base_url: str = BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
    ):
        resolved = token if token is not None else os.environ.get("FINMIND_TOKEN")
        if not resolved:
            raise AuthenticationError("FINMIND_TOKEN not set")
        self.token: str = resolved
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    async def query_dataset(
        self,
        dataset: str,
        data_id: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        """Call `/api/v4/data` and return the rows list.

        Raises:
            AuthenticationError: 401 / illegal token
            PaymentRequiredError: plan too low
            RateLimitError: 402 / 429
            BadRequestError: other 4xx
            UpstreamError: 5xx / network failure
            EmptyDataError: 200 with `data: []`
        """
        params: dict[str, ParamValue] = {"dataset": dataset}
        if data_id:
            params["data_id"] = data_id
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date

        data = await self._get_json("/v4/data", params)
        rows = data.get("data", []) if isinstance(data, dict) else []
        if not rows:
            raise EmptyDataError(
                f"no data for {dataset} data_id={data_id} start_date={start_date}"
            )
        return rows

    async def query_trading_daily_report(
        self,
        date: str,
        data_id: Optional[str] = None,
        securities_trader_id: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        """Call the dedicated `/api/v4/taiwan_stock_trading_daily_report` endpoint.

        Takes a single `date` plus `data_id` (stock) and/or
        `securities_trader_id` (broker branch). Sponsor tier required.
        """
        params: dict[str, ParamValue] = {"date": date}
        if data_id:
            params["data_id"] = data_id
        if securities_trader_id:
            params["securities_trader_id"] = securities_trader_id
        result = await self.query_endpoint("taiwan_stock_trading_daily_report", params)
        return result  # type: ignore[return-value]

    async def query_endpoint(
        self, endpoint: str, params: dict[str, ParamValue]
    ) -> Union[list[dict[str, Any]], dict[str, Any], list[Any]]:
        """GET `/api/v4/{endpoint}` and return the response's `data` field.

        `data` is a list of row dicts for most endpoints, a list of strings for
        `datalist`, and a dict of parallel lists for `translation`. List values
        in `params` are sent as repeated query keys (`data_id=a&data_id=b`).
        """
        data = await self._get_json(f"/v4/{endpoint}", params)
        payload = data.get("data") if isinstance(data, dict) else None
        if not payload:
            shown = ", ".join(f"{k}={v}" for k, v in params.items())
            raise EmptyDataError(f"no data for {endpoint} {shown}")
        return payload

    async def storage_object_url(self, dataset: str, date: str) -> str:
        """Ask `/api/v4/storage_objects` for a signed URL (HTTP 307 Location).

        The signed URL is short-lived (minutes), so download it right away.
        """
        url = f"{self.base_url}/v4/storage_objects"
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    url,
                    params={"dataset": dataset, "date": date},
                    headers=self._headers(),
                    follow_redirects=False,
                )
        except (httpx.TimeoutException, httpx.ConnectError) as exc:
            raise UpstreamError(f"connection failure: {exc}") from exc
        if response.status_code in (301, 302, 303, 307, 308):
            location = response.headers.get("location")
            if location:
                return location
            raise UpstreamError("storage_objects redirect without Location header")
        self._raise_for_status(response)
        # 200 without redirect: either a JSON error envelope or something unexpected.
        self._raise_for_body(response)
        raise UpstreamError(
            f"unexpected storage_objects response HTTP {response.status_code}"
        )

    async def download(self, signed_url: str, dest: Path) -> int:
        """Stream `signed_url` into `dest` atomically; return bytes written.

        No Authorization header: the URL is pre-signed for object storage and an
        extra auth header would break the signature.
        """
        dest.parent.mkdir(parents=True, exist_ok=True)
        tmp = dest.with_name(dest.name + ".part")
        written = 0
        try:
            async with httpx.AsyncClient(timeout=DOWNLOAD_TIMEOUT) as client:
                async with client.stream("GET", signed_url) as response:
                    if response.status_code >= 400:
                        body = (await response.aread()).decode(errors="replace")
                        raise UpstreamError(
                            f"download failed HTTP {response.status_code}: {body[:300]}",
                            status=response.status_code,
                        )
                    with tmp.open("wb") as fh:
                        async for chunk in response.aiter_bytes(1 << 20):
                            fh.write(chunk)
                            written += len(chunk)
            os.replace(tmp, dest)
        except (httpx.TimeoutException, httpx.ConnectError, httpx.ReadError) as exc:
            raise UpstreamError(f"download failure: {exc}") from exc
        finally:
            if tmp.exists():
                tmp.unlink()
        return written

    # --- internals -----------------------------------------------------------

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.token}"} if self.token else {}

    async def _get_json(
        self, path: str, params: dict[str, ParamValue]
    ) -> dict[str, Any]:
        url = f"{self.base_url}{path}"
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, params=params, headers=self._headers())
        except (httpx.TimeoutException, httpx.ConnectError) as exc:
            raise UpstreamError(f"connection failure: {exc}") from exc

        self._raise_for_status(response)
        try:
            data = response.json()
        except ValueError as exc:
            raise UpstreamError(f"invalid JSON response: {exc}") from exc
        # Some errors arrive as HTTP 200 with `{"status": 4xx, "msg": ...}`.
        if isinstance(data, dict) and isinstance(data.get("status"), int):
            if data["status"] >= 400:
                self._classify(data["status"], _extract_detail(data))
        return data

    @staticmethod
    def _raise_for_body(response: httpx.Response) -> None:
        try:
            data = response.json()
        except ValueError:
            return
        if isinstance(data, dict) and isinstance(data.get("status"), int):
            if data["status"] >= 400:
                FinMindClient._classify(data["status"], _extract_detail(data))

    @staticmethod
    def _raise_for_status(response: httpx.Response) -> None:
        code = response.status_code
        if code < 400:
            return
        try:
            body: Any = response.json()
        except ValueError:
            body = response.text
        FinMindClient._classify(code, _extract_detail(body))

    @staticmethod
    def _classify(code: int, detail: str) -> None:
        """Raise the FinMindError subclass matching an error status + message.

        The message wins over the status: FinMind returns both "plan too low"
        and "illegal token" as HTTP 400, and "rate limit" as HTTP 402.
        """
        if code == 401 or _TOKEN_PATTERN.search(detail):
            raise AuthenticationError(detail, detail=detail, status=code)
        if _TIER_PATTERN.search(detail):
            raise PaymentRequiredError(detail, detail=detail, status=code)
        if code in (402, 429) or _RATE_LIMIT_PATTERN.search(detail):
            raise RateLimitError(detail, detail=detail, status=code)
        if code >= 500:
            raise UpstreamError(f"HTTP {code}: {detail}", detail=detail, status=code)
        raise BadRequestError(f"HTTP {code}: {detail}", detail=detail, status=code)


def _extract_detail(body: Any) -> str:
    """Pull the human-readable error text out of a FinMind error body.

    FinMind uses `{"msg": ...}` for its own exceptions and FastAPI's
    `{"detail": str | [{loc, msg, ...}]}` for validation errors.
    """
    text: str
    if isinstance(body, dict):
        detail = body.get("detail", body.get("msg"))
        if isinstance(detail, list):
            parts = []
            for item in detail:
                if isinstance(item, dict):
                    loc = ".".join(str(x) for x in item.get("loc", []) if x != "query")
                    msg = str(item.get("msg", ""))
                    parts.append(f"{loc}: {msg}" if loc else msg)
                else:
                    parts.append(str(item))
            text = "; ".join(parts)
        elif detail is not None:
            text = str(detail)
        else:
            text = str(body)
    else:
        text = str(body or "")
    text = text.strip()
    if len(text) > MAX_DETAIL_CHARS:
        text = text[:MAX_DETAIL_CHARS] + "…（已截斷）"
    return text
