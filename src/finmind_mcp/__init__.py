"""FinMind MCP server."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("finmind-mcp")
except PackageNotFoundError:  # running from a source tree that isn't installed
    __version__ = "0.0.0+unknown"
