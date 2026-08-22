"""Launches the FinMind MCP server as a subprocess, sends initialize +
tools/list over stdio, and asserts the expected tools are registered.

Usage:
    uv run python smoke.py
"""

import asyncio
import json
import os
import sys


EXPECTED_TOOLS = [
    "query_dataset",
    "list_datasets",
    "get_stock_info",
    "query_trading_daily_report",
    "start_query_dataset_job",
    "check_query_dataset_job",
]


async def main() -> None:
    proc = await asyncio.create_subprocess_exec(
        sys.executable,
        "-m",
        "finmind_mcp.server",
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        env={**os.environ, "FINMIND_TOKEN": "smoke-test"},
    )
    assert proc.stdin is not None and proc.stdout is not None

    async def send(msg: dict) -> None:
        proc.stdin.write((json.dumps(msg) + "\n").encode())
        await proc.stdin.drain()

    async def recv() -> dict:
        line = await proc.stdout.readline()
        if not line:
            stderr = await proc.stderr.read()
            raise RuntimeError(
                f"server closed stdout. stderr=\n{stderr.decode(errors='replace')}"
            )
        return json.loads(line)

    await send(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "smoke", "version": "0"},
            },
        }
    )
    init_resp = await recv()
    assert "result" in init_resp, init_resp

    await send({"jsonrpc": "2.0", "method": "notifications/initialized"})
    await send({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
    tools_resp = await recv()
    tools_list = tools_resp["result"]["tools"]
    names = [t["name"] for t in tools_list]
    print("tools:", names)
    assert names == EXPECTED_TOOLS, f"expected {EXPECTED_TOOLS}, got {names}"

    proc.terminate()
    await proc.wait()
    print("SMOKE OK")


asyncio.run(main())
