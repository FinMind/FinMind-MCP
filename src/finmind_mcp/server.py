"""FinMind MCP server entry point (stdio transport).

Registers four tools and a small set of markdown resources from the
shared knowledge pack. Designed to be launched by an MCP host such as
Claude Desktop, Claude Code, Cursor, Windsurf, or Gemini CLI.

Handlers are passed to the `Server` constructor: mcp 2.0 removed the 1.x
`@app.list_tools()` decorators in favour of `on_*` keyword arguments, and
handlers now take `(ctx, params)` and return full result models.

Run via:
    finmind-mcp
or:
    python -m finmind_mcp.server
"""

from __future__ import annotations

import asyncio
import logging

import mcp.types as types
from mcp.server import Server
from mcp.server.stdio import stdio_server

from . import knowledge, tools

logger = logging.getLogger(__name__)


async def on_list_tools(ctx, params) -> types.ListToolsResult:
    return types.ListToolsResult(tools=tools.tool_definitions())


async def on_call_tool(ctx, params) -> types.CallToolResult:
    # mcp 1.x turned a raising handler into `isError`; mcp 2.0 lets the
    # exception become a JSON-RPC protocol error, which hosts report as a
    # server failure instead of showing the model something it can act on.
    try:
        result = await tools.dispatch(params.name, params.arguments or {})
    except Exception as exc:  # noqa: BLE001 — surfaced to the model, not swallowed
        logger.exception("tool %s failed", getattr(params, "name", "?"))
        return types.CallToolResult(
            content=[types.TextContent(type="text", text=str(exc))],
            is_error=True,
        )
    return types.CallToolResult(
        content=[types.TextContent(type="text", text=result)]
    )


async def on_list_resources(ctx, params) -> types.ListResourcesResult:
    return types.ListResourcesResult(resources=knowledge.resource_definitions())


async def on_read_resource(ctx, params) -> types.ReadResourceResult:
    # `params.uri` is a pydantic AnyUrl; knowledge.read wants a plain string.
    uri = str(params.uri)
    return types.ReadResourceResult(
        contents=[
            types.TextResourceContents(
                uri=uri,
                mime_type="text/markdown",
                text=knowledge.read(uri),
            )
        ]
    )


app: Server = Server(
    "finmind",
    on_list_tools=on_list_tools,
    on_call_tool=on_call_tool,
    on_list_resources=on_list_resources,
    on_read_resource=on_read_resource,
)


async def _run() -> None:
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    asyncio.run(_run())


if __name__ == "__main__":
    main()
