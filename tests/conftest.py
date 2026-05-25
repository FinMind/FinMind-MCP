"""Shared pytest fixtures for finmind-mcp tests."""

import os

import pytest


@pytest.fixture(autouse=True)
def _set_finmind_token(monkeypatch):
    """Default FINMIND_TOKEN so client construction does not fail."""
    monkeypatch.setenv("FINMIND_TOKEN", os.environ.get("FINMIND_TOKEN", "test-token"))
