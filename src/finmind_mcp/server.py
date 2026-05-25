"""FinMind MCP server entry point (stdio transport).

Registers four tools and a small set of markdown resources from the
shared knowledge pack. Designed to be launched by an MCP host such as
Claude Desktop, Claude Code, Cursor, Windsurf, or Gemini CLI.

Run via:
    finmind-mcp
or:
    python -m finmind_mcp.server
"""

from __future__ import annotations

import asyncio
import logging

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Resource, TextContent, Tool

from . import knowledge, tools

logger = logging.getLogger(__name__)
app: Server = Server("finmind")


@app.list_tools()
async def list_tools() -> list[Tool]:
    return tools.tool_definitions()


@app.call_tool()
async def call_tool(name: str, arguments: dict | None) -> list[TextContent]:
    result = await tools.dispatch(name, arguments or {})
    return [TextContent(type="text", text=result)]


@app.list_resources()
async def list_resources() -> list[Resource]:
    return knowledge.resource_definitions()


@app.read_resource()
async def read_resource(uri) -> str:
    # `uri` is a pydantic AnyUrl in current MCP SDK; convert to string.
    return knowledge.read(str(uri))


async def _run() -> None:
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    asyncio.run(_run())


if __name__ == "__main__":
    main()
