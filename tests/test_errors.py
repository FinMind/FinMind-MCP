"""Tests for the FinMind exception hierarchy."""

import pytest

from finmind_mcp.errors import (
    AuthenticationError,
    EmptyDataError,
    FinMindError,
    PaymentRequiredError,
    RateLimitError,
    UpstreamError,
)


def test_finmind_error_base():
    assert issubclass(FinMindError, Exception)
    err = FinMindError("boom")
    assert str(err) == "boom"


@pytest.mark.parametrize(
    "cls",
    [
        AuthenticationError,
        PaymentRequiredError,
        EmptyDataError,
        RateLimitError,
        UpstreamError,
    ],
)
def test_subclasses_of_finmind_error(cls):
    assert issubclass(cls, FinMindError)
    instance = cls("msg")
    assert isinstance(instance, FinMindError)
    assert str(instance) == "msg"


def test_subclasses_are_distinct():
    classes = [
        AuthenticationError,
        PaymentRequiredError,
        EmptyDataError,
        RateLimitError,
        UpstreamError,
    ]
    # No two share identity.
    assert len({c for c in classes}) == len(classes)
