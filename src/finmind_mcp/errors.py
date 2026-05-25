"""Exception hierarchy for FinMind MCP server.

All errors raised by `client.py` derive from `FinMindError`. `tools.py`
catches these and converts them into user-facing 繁中 templates loaded
from `plugin/knowledge/errors.md`.
"""


class FinMindError(Exception):
    """Base class for all FinMind-related errors."""


class AuthenticationError(FinMindError):
    """HTTP 401, or `FINMIND_TOKEN` not set."""


class PaymentRequiredError(FinMindError):
    """HTTP 402 — dataset requires sponsor tier."""


class EmptyDataError(FinMindError):
    """API returned 200 with empty `data: []`."""


class RateLimitError(FinMindError):
    """HTTP 429 — per-token rate limit hit."""


class UpstreamError(FinMindError):
    """HTTP 5xx, timeout, or connection error from FinMind upstream."""
