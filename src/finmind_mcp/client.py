"""Async httpx wrapper around the FinMind v4 HTTP API."""

from __future__ import annotations

import os
from typing import Any, Optional

import httpx

from .errors import (
    AuthenticationError,
    EmptyDataError,
    PaymentRequiredError,
    RateLimitError,
    UpstreamError,
)

BASE_URL = "https://api.finmindtrade.com/api"
DEFAULT_TIMEOUT = 30.0


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
            AuthenticationError: 401
            PaymentRequiredError: 402
            RateLimitError: 429
            UpstreamError: 5xx / network failure
            EmptyDataError: 200 with `data: []`
        """
        params: dict[str, str] = {"dataset": dataset}
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

    async def list_datasets(self) -> list[str]:
        """Call `/api/v4/datalist` and return the available dataset names."""
        data = await self._get_json("/v4/datalist", {})
        result = data.get("data", []) if isinstance(data, dict) else []
        return list(result)

    async def query_trading_daily_report(
        self,
        data_id: str,
        date: str,
    ) -> list[dict[str, Any]]:
        """Call the dedicated `/api/v4/taiwan_stock_trading_daily_report` endpoint.

        Unlike `/api/v4/data`, this endpoint requires `data_id` (a stock id) and
        takes a single `date` (not a start/end range). Sponsor tier required.
        """
        params: dict[str, str] = {
            "data_id": data_id,
            "date": date,
        }
        data = await self._get_json("/v4/taiwan_stock_trading_daily_report", params)
        rows = data.get("data", []) if isinstance(data, dict) else []
        if not rows:
            raise EmptyDataError(
                f"no trading daily report data data_id={data_id} date={date}"
            )
        return rows

    async def _get_json(self, path: str, params: dict[str, str]) -> dict[str, Any]:
        url = f"{self.base_url}{path}"
        headers = {"Authorization": f"Bearer {self.token}"}
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, params=params, headers=headers)
        except (httpx.TimeoutException, httpx.ConnectError) as exc:
            raise UpstreamError(f"connection failure: {exc}") from exc

        self._raise_for_status(response)
        try:
            return response.json()
        except ValueError as exc:
            raise UpstreamError(f"invalid JSON response: {exc}") from exc

    @staticmethod
    def _raise_for_status(response: httpx.Response) -> None:
        code = response.status_code
        if code == 401:
            raise AuthenticationError(response.text)
        if code == 402:
            raise PaymentRequiredError(response.text)
        if code == 429:
            raise RateLimitError(response.text)
        if code >= 500:
            raise UpstreamError(f"HTTP {code}: {response.text}")
        if code >= 400:
            # Catch-all 4xx that didn't match the specific cases above.
            raise UpstreamError(f"HTTP {code}: {response.text}")
