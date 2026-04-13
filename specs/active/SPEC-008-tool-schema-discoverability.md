---
id: SPEC-008
title: "Tool Schema & Discoverability — JSON Schema, Descriptions, Categories"
status: draft
domain: "schemas, handlers, discovery"
created: 2026-04-13
updated: 2026-04-13
branch: feature/SPEC-008-tool-schema-discoverability
---

# SPEC-008: Tool Schema & Discoverability

## Context

All LLMs (Claude, OpenAI, Gemini, Grok) rely on structured tool definitions to understand
what parameters to pass. Currently `airflow_tools_list` returns Python signatures and raw
docstrings — no JSON Schema, no field-level descriptions, no categories. An LLM calling
`airflow_tools_list` cannot synthesize valid `params` payloads without guessing.

Additionally, 60% of handler functions have no docstring, and no `Field(description=...)`
is set in any Pydantic model — so even the FastAPI OpenAPI schema is useless for agents.

## Goal

Make every tool self-describing so that **any LLM can discover and call it correctly**
without consulting external documentation.

## Acceptance criteria

- [ ] Every Pydantic field in `schemas.py` has a `description=` in its `Field()` call
- [ ] Every handler function has a Google-style docstring (Args, Returns, Raises)
- [ ] `airflow_tools_list` returns `input_schema` (JSON Schema object) per tool
- [ ] `airflow_tools_list` returns `read_only: bool` per tool
- [ ] `airflow_tools_list` returns `category: str` per tool (e.g., "dag", "task", "monitoring")
- [ ] `airflow_tools_list` returns `examples: list` per tool (at least 1 example invocation)
- [ ] New tool `airflow_tool_get` — fetch schema for a single tool by name
- [ ] Unit tests for discovery response shape and field completeness

## Technical approach

### Schemas (`airflow_mcp_server/schemas.py`)

Add `description=` to every `Field(...)`. Examples:

```python
class DagIdParams(BaseModel):
    dag_id: str = Field(..., description="The unique identifier of the DAG (e.g. 'my_etl_dag')")

class TriggerDagParams(BaseModel):
    dag_id: str = Field(..., description="DAG to trigger")
    conf: Optional[Dict] = Field(None, description="Optional run configuration JSON")

class FetchLogsParams(BaseModel):
    dag_id: str = Field(..., description="DAG identifier")
    run_id: str = Field(..., description="DAG run identifier (e.g. 'manual__2026-01-01T00:00:00+00:00')")
    task_id: str = Field(..., description="Task identifier within the DAG")
    try_number: int = Field(1, ge=1, description="Attempt number (1 = first try, 2 = first retry, etc.)")
```

### Handlers — Docstrings (all missing handlers)

Add Google-style docstrings to: `list_dags`, `get_dag`, `trigger_dag`, `list_dag_runs`,
`pause_dag`, `unpause_dag` (dags.py); all functions in tasks.py, logs.py, connections.py,
pools.py, health.py.

Pattern to follow (from variables.py, which is already complete):

```python
async def list_dags(params: dict) -> ToolResponse:
    """List all available DAGs.

    Args:
        params: Dictionary containing:
            - limit (int, optional): Max results. Default 100.
            - offset (int, optional): Pagination offset. Default 0.

    Returns:
        {"success": True, "data": [{"dag_id": str, "is_paused": bool, ...}], "error": None}

    Raises:
        AirflowConnectionError: If Airflow is unreachable.
        AirflowAuthError: If credentials are invalid.
    """
```

### Discovery (`airflow_mcp_server/handlers/discovery.py`)

Enhance `list_tools()` to return per tool:

```python
{
    "tool_name": "airflow_dag_trigger",
    "module": "dags",
    "category": "dag",                       # NEW
    "read_only": False,                      # NEW — from WRITE_ONLY_TOOLS
    "description": "Trigger a DAG run...",   # NEW — from __doc__ first line
    "input_schema": {                        # NEW — model.model_json_schema()
        "type": "object",
        "properties": {
            "dag_id": {"type": "string", "description": "..."},
            "conf":   {"type": "object", "description": "..."}
        },
        "required": ["dag_id"]
    },
    "examples": [                            # NEW — from metadata dict
        {"dag_id": "my_etl_dag", "conf": {}}
    ]
}
```

**Category mapping** (`TOOL_CATEGORIES` dict in `server.py` or `discovery.py`):
```python
TOOL_CATEGORIES = {
    "dags": "dag",
    "tasks": "task",
    "logs": "log",
    "connections": "connection",
    "variables": "variable",
    "pools": "pool",
    "xcoms": "xcom",
    "datasets": "dataset",
    "providers": "system",
    "import_errors": "monitoring",
    "agent_tools": "agent",
    "health": "monitoring",
    "discovery": "meta",
}
```

**Tool examples** — add a `TOOL_EXAMPLES` dict in each handler module:
```python
# dags.py
TOOL_EXAMPLES = {
    "airflow_dag_list": {"limit": 10, "offset": 0},
    "airflow_dag_trigger": {"dag_id": "my_etl_dag", "conf": {}},
    ...
}
```

**New tool** — `airflow_tool_get(tool_name: str)`:
Returns full schema + description for one tool. Faster than parsing all of `list_tools`.

### Tests

- `tests/unit/test_server_and_handlers.py` — extend with:
  - `test_list_tools_has_input_schema` — every tool in list has `input_schema`
  - `test_list_tools_has_category` — every tool has `category`
  - `test_list_tools_read_only_flag` — write tools have `read_only=True`
  - `test_tool_get_returns_full_schema` — single tool fetch
- `tests/unit/test_discovery.py` — new file, explicit tests for discovery handler

## MCP tools affected

- `airflow_tools_list` — enriched response: `input_schema`, `category`, `read_only`, `examples`
- `airflow_tool_get` — new: single-tool schema lookup

## Related

- SPEC-011: True MCP Protocol (consumes these schemas for proper MCP `tools/list`)
- SPEC-007: Agent Tools (agent_tools category)
