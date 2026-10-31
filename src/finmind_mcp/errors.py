"""Exception hierarchy for FinMind MCP server.

All errors raised by `client.py` derive from `FinMindError`. `tools.py`
catches these and converts them into user-facing 繁中 templates loaded
from `knowledge/errors.md`.

`detail` keeps the API's own error text (`detail` / `msg` field of the
response body) so the tool output can quote it verbatim to the LLM.
"""

from __future__ import annotations

from typing import Optional


class FinMindError(Exception):
    """Base class for all FinMind-related errors."""

    def __init__(
        self,
        message: str = "",
        *,
        detail: Optional[str] = None,
        status: Optional[int] = None,
    ):
        super().__init__(message)
        self.detail = detail if detail is not None else (message or None)
        self.status = status


class AuthenticationError(FinMindError):
    """HTTP 401, `Token is illegal.`, or `FINMIND_TOKEN` not set."""


class PaymentRequiredError(FinMindError):
    """方案權限不足（API 回 `Your level is ... Please update your user level`）。

    FinMind 以 HTTP 400 回這個錯誤；HTTP 402 是「請求數達上限」，歸 RateLimitError。
    """


class EmptyDataError(FinMindError):
    """API returned 200 with empty `data: []`."""


class RateLimitError(FinMindError):
    """HTTP 429，或 HTTP 402 `Requests reach the upper limit`（每小時請求數達上限）。"""


class BadRequestError(FinMindError):
    """HTTP 400 / 404 / 422 參數錯誤（缺參數、格式錯、不支援的 dataset、查無物件）。"""


class UpstreamError(FinMindError):
    """HTTP 5xx, timeout, or connection error from FinMind upstream."""


class DependencyMissingError(FinMindError):
    """選用套件（例如 pyarrow）沒有安裝。"""
