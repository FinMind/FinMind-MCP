"""Tests for the MCP protocol handlers in server.py.

Since the mcp 2.0 migration the handlers are plain async functions registered
on the `Server` constructor, so they can be called directly — no subprocess,
no transport. `smoke.py` and `regression/runner.py` still cover the real
stdio handshake end to end.
"""

import mcp.types as types
import pytest

from finmind_mcp import server, tools


class _Params:
    """Stand-in for the pydantic params models the runner passes in.

    The handlers only read attributes off params, so a namespace is enough.
    """

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


async def test_list_tools_returns_the_four_tools():
    result = await server.on_list_tools(None, None)

    assert isinstance(result, types.ListToolsResult)
    assert [t.name for t in result.tools] == [
        "query_dataset",
        "list_datasets",
        "get_stock_info",
        "query_trading_daily_report",
    ]


async def test_call_tool_wraps_dispatch_output_as_text_content(monkeypatch):
    async def fake_dispatch(name, arguments):
        return f"dispatched {name} {arguments}"

    monkeypatch.setattr(tools, "dispatch", fake_dispatch)

    result = await server.on_call_tool(
        None, _Params(name="query_dataset", arguments={"dataset": "TaiwanStockPrice"})
    )

    assert isinstance(result, types.CallToolResult)
    assert not result.is_error
    assert result.content[0].text == (
        "dispatched query_dataset {'dataset': 'TaiwanStockPrice'}"
    )


async def test_call_tool_handles_omitted_arguments(monkeypatch):
    seen = {}

    async def fake_dispatch(name, arguments):
        seen["arguments"] = arguments
        return "ok"

    monkeypatch.setattr(tools, "dispatch", fake_dispatch)

    await server.on_call_tool(None, _Params(name="list_datasets", arguments=None))

    assert seen["arguments"] == {}


async def test_call_tool_reports_errors_as_tool_results_not_protocol_errors():
    """A raising dispatch must come back as isError, not as an exception.

    mcp 1.x wrapped call_tool handlers and turned exceptions into
    `CallToolResult(isError=True)`; mcp 2.0 lets them escape and become
    JSON-RPC protocol errors, which hosts surface as a server failure rather
    than feeding back to the model. server.py restores the old behaviour, and
    this test is what keeps it restored.
    """
    result = await server.on_call_tool(None, _Params(name="no_such_tool", arguments={}))

    assert isinstance(result, types.CallToolResult)
    assert result.is_error
    assert "no_such_tool" in result.content[0].text


async def test_list_resources_exposes_the_knowledge_pack():
    result = await server.on_list_resources(None, None)

    assert isinstance(result, types.ListResourcesResult)
    assert result.resources, "expected at least one bundled knowledge resource"
    assert all(str(r.uri).startswith("finmind://") for r in result.resources)


async def test_read_resource_returns_markdown_contents():
    uri = str((await server.on_list_resources(None, None)).resources[0].uri)

    result = await server.on_read_resource(None, _Params(uri=uri))

    assert isinstance(result, types.ReadResourceResult)
    contents = result.contents[0]
    assert contents.mime_type == "text/markdown"
    assert contents.text.strip()


async def test_read_resource_rejects_unknown_uri():
    with pytest.raises(ValueError):
        await server.on_read_resource(None, _Params(uri="finmind://nope"))
