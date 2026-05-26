# finmind-mcp

Official FinMind MCP server. Exposes the FinMind v4 API to MCP-compatible
AI tools (Claude Desktop / Code, Gemini CLI, Cursor, Windsurf, Codex).

## Tools

| Tool | Endpoint | Required args |
| --- | --- | --- |
| `query_dataset` | `/api/v4/data` | `dataset` |
| `list_datasets` | `/api/v4/datalist` | — |
| `get_stock_info` | `/api/v4/data?dataset=TaiwanStockInfo` | — |
| `query_trading_daily_report` | `/api/v4/taiwan_stock_trading_daily_report` | `data_id`, `date` |

Each tool returns a markdown table; results over 500 rows are truncated
with a note pointing to the host's code interpreter.

## Resources

Knowledge pack is served as MCP resources:

- `finmind://datasets`
- `finmind://examples`
- `finmind://errors`
- `finmind://instructions`
- `finmind://token-guide`
- `finmind://regression`

## Install & run

```bash
cd plugin/mcp
uv venv --python 3.10
source .venv/bin/activate
uv pip install -e ".[dev]"
FINMIND_TOKEN=your-token finmind-mcp
```

The server speaks MCP over stdio. Host config examples are in
`../install/`.

## Auth

Token resolves from constructor arg → `FINMIND_TOKEN` env var. If neither
is set, the server returns the 401 繁中 template from
`plugin/knowledge/errors.md`.

## Tests

```bash
uv run pytest tests/ -v
uv run python smoke.py   # subprocess smoke test
```
