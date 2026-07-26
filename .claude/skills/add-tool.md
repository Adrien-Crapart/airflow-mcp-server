---
name: add-tool
description: Skill for adding a new MCP tool end-to-end — handler, Pydantic schema, client method, tests, documentation.
---

# Skill: Add a new MCP tool

## Steps in order

### 1. Handler (`airflow_mcp_server/handlers/<domain>.py`)

Create or extend the domain file:

```python
async def airflow_<domain>_<action>(params: dict) -> dict:
    """..."""
    result = await airflow_client.<method>(params["<param>"])
    return {"success": True, "data": result, "error": None}

TOOLS = {
    "airflow_<domain>_<action>": airflow_<domain>_<action>,
}
```

### 2. Pydantic schema (`airflow_mcp_server/schemas.py`)

```python
class <Domain><Action>Params(BaseModel):
    <param>: str = Field(..., description="...")

TOOL_INPUT_MODELS["airflow_<domain>_<action>"] = <Domain><Action>Params
```

### 3. Client method (`airflow_mcp_server/airflow_client.py`)

If the Airflow endpoint is not yet wrapped:

```python
async def <method>(self, <param>: str) -> dict:
    return await self._request_with_fallback("GET", f"{self.api_prefix}/<endpoint>/{<param>}")
```

### 4. Tests (`tests/unit/test_<domain>.py`)

At minimum: success, missing parameter, `AirflowNotFoundError`.

### 5. Documentation (`docs/MCP_TOOLS.md`)

Add an entry with: name, description, inputs, outputs, curl example.

## Final verification

```bash
just test           # Unit tests pass
just lint           # No ruff errors
uv run mypy airflow_mcp_server/  # No type errors

# Manual test
curl -X POST http://localhost:8000/tool/airflow_<domain>_<action> \
  -H "Content-Type: application/json" \
  -d '{"params": {"<param>": "value"}}'
```
