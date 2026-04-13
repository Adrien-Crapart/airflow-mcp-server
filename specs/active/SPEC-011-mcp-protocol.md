---
id: SPEC-011
title: "True MCP Protocol Compliance — SDK Migration, stdio/SSE Transports"
status: draft
domain: "server.py, main.py, pyproject.toml"
created: 2026-04-13
updated: 2026-04-13
branch: feature/SPEC-011-mcp-protocol
---

# SPEC-011: True MCP Protocol Compliance

## Context

The current server is a **plain FastAPI HTTP API**, not a real MCP server. It cannot be
connected to Claude Desktop, Cursor, or any MCP host that speaks the standard MCP protocol
(stdio or SSE). Any agent using this server requires a custom HTTP client.

The MCP specification defines:
- `tools/list` — enumerate tools with `inputSchema` (JSON Schema)
- `tools/call` — invoke a tool by name
- `resources/list` + `resources/read` — read-only named content
- `prompts/list` + `prompts/get` — workflow templates

None of these are implemented. The server needs migrating to the official MCP Python SDK
to be usable by any LLM tool-use ecosystem (Claude, OpenAI function calling bridge, etc.).

## Goal

Migrate to the official `mcp` Python SDK while **keeping backward-compatible HTTP endpoints**
for existing integrations. Support both stdio (Claude Desktop) and Streamable HTTP transports.

## Acceptance criteria

- [ ] `mcp` SDK added to dependencies (`pyproject.toml`)
- [ ] MCP server initialized with `FastMCP("Airflow MCP Server")`
- [ ] All 31+ tools registered via `@mcp.tool()` with their `inputSchema` from Pydantic models
- [ ] Tool `description` sourced from handler docstrings (first line = tool description)
- [ ] stdio transport supported (for Claude Desktop, CLI usage)
- [ ] Streamable HTTP transport at `/mcp` supported (for web integrations)
- [ ] Legacy FastAPI HTTP `/tool/{tool_name}` route kept (backward compat)
- [ ] `MCP_TRANSPORT` env var selects transport: `stdio` | `http` | `both` (default: `both`)
- [ ] Unit tests for tool registration and schema exposure
- [ ] Integration test: verify `tools/list` response has `inputSchema` per tool

## Technical approach

### Dependency (`pyproject.toml`)

```toml
dependencies = [
  "uvicorn[standard]>=0.22.0",
  "httpx>=0.24.0",
  "fastapi>=0.95.0",
  "pydantic>=2.0.0",
  "mcp[cli]>=1.0.0",          # NEW — official MCP Python SDK
]
```

### New server architecture (`airflow_mcp_server/server.py`)

```python
from mcp.server.fastmcp import FastMCP
from fastapi import FastAPI

mcp = FastMCP("Airflow MCP Server")

def register_tools_with_mcp(tools: dict, tool_input_models: dict):
    """Register all discovered tools with the MCP server."""
    for tool_name, handler in tools.items():
        model = tool_input_models.get(tool_name)
        description = (handler.__doc__ or "").split("\n")[0].strip()

        if model:
            # Use the Pydantic model for typed registration
            @mcp.tool(name=tool_name, description=description)
            async def _wrapped(**kwargs):
                params = model(**kwargs).model_dump()
                result = await handler(params)
                return result
        else:
            @mcp.tool(name=tool_name, description=description)
            async def _wrapped_no_schema():
                result = await handler({})
                return result

def create_app() -> FastAPI:
    """Create dual-mode app: MCP protocol + legacy HTTP."""
    tools = load_tools()
    register_tools_with_mcp(tools, TOOL_INPUT_MODELS)

    # Mount MCP at /mcp for Streamable HTTP transport
    app = FastAPI(title="Airflow MCP Server")
    app.mount("/mcp", mcp.streamable_http_app())

    # Keep legacy /tool/{tool_name} routes for backward compat
    _register_legacy_routes(app, tools)

    return app

def create_stdio_server():
    """Entry point for stdio transport (Claude Desktop)."""
    tools = load_tools()
    register_tools_with_mcp(tools, TOOL_INPUT_MODELS)
    return mcp
```

### Config (`airflow_mcp_server/config.py`)

```python
MCP_TRANSPORT: str = os.getenv("MCP_TRANSPORT", "both")
# "stdio"  — pure stdio, no HTTP server
# "http"   — Streamable HTTP only
# "both"   — HTTP server + stdio available
```

### Entry point (`airflow_mcp_server/main.py`)

```python
import sys
from airflow_mcp_server.config import cfg

if cfg.MCP_TRANSPORT == "stdio":
    # Run as stdio MCP server (for Claude Desktop / mcp CLI)
    from airflow_mcp_server.server import create_stdio_server
    mcp_server = create_stdio_server()
    mcp_server.run()
else:
    # Run as HTTP server (Streamable HTTP + legacy routes)
    import uvicorn
    from airflow_mcp_server.server import create_app
    uvicorn.run(create_app(), host=cfg.MCP_SERVER_HOST, port=cfg.MCP_SERVER_PORT)
```

### Claude Desktop integration (`claude_desktop_config.json` example)

```json
{
  "mcpServers": {
    "airflow": {
      "command": "uv",
      "args": ["run", "python", "-m", "airflow_mcp_server.main"],
      "env": {
        "AIRFLOW_BASE_URL": "http://localhost:8080",
        "AIRFLOW_USERNAME": "airflow",
        "AIRFLOW_PASSWORD": "airflow",
        "MCP_TRANSPORT": "stdio"
      }
    }
  }
}
```

Add example to `README.md` and `.env.example`.

### Tests

- `tests/unit/test_mcp_registration.py`:
  - `test_all_tools_registered` — mcp.list_tools() returns all tools
  - `test_tool_has_input_schema` — each tool has non-null inputSchema
  - `test_tool_description_not_empty` — each tool has a description
  - `test_read_only_mode_filters_write_tools` — 22 tools (not 31) in read-only

- `tests/integration/test_integration_mcp.py`:
  - `test_mcp_tools_list_via_http` — GET /mcp/tools returns list
  - `test_mcp_tool_call_via_http` — POST /mcp/call with dag_list succeeds

## MCP protocol compatibility

| MCP Client | Transport | Config |
| --- | --- | --- |
| Claude Desktop | stdio | `MCP_TRANSPORT=stdio` |
| Cursor | stdio | `MCP_TRANSPORT=stdio` |
| OpenAI function bridge | Streamable HTTP | `MCP_TRANSPORT=http` at `/mcp` |
| Custom HTTP client | Legacy HTTP | `POST /tool/{name}` (unchanged) |

## Related

- SPEC-008: Tool Schema (inputSchema and descriptions — prerequisite)
- SPEC-012: MCP Resources (requires this MCP infrastructure)
- SPEC-013: MCP Prompts (requires this MCP infrastructure)
