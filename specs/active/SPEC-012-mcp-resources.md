---
id: SPEC-012
title: "MCP Resources — airflow:// URI Scheme for Read-only Content"
status: draft
domain: "server.py, handlers/resources.py"
created: 2026-04-13
updated: 2026-04-13
branch: feature/SPEC-012-mcp-resources
---

# SPEC-012: MCP Resources

## Context

MCP Resources are the idiomatic way to expose read-only named content to LLMs without
requiring a tool invocation. In the current server, every piece of information (DAG source,
config, version) requires an explicit tool call — even for static/slow-changing data.

Resources allow an MCP host to pre-load content into context automatically, reducing
round-trips and enabling richer agent context without explicit tool calls.

**Requires SPEC-011 (MCP SDK) to be completed first.**

## Goal

Expose key Airflow content as `airflow://` resources that any MCP client can list and read.

## Acceptance criteria

- [ ] `airflow://version` — Airflow version and metadata
- [ ] `airflow://config` — Airflow configuration (read-only)
- [ ] `airflow://dag/{dag_id}` — DAG metadata as structured JSON
- [ ] `airflow://dag/{dag_id}/source` — DAG Python source code
- [ ] `airflow://dag/{dag_id}/run/{run_id}/log/{task_id}` — task log as text
- [ ] `airflow://variable/{key}` — variable value (masked sensitive values)
- [ ] `airflow://providers` — list of installed providers
- [ ] Resources registered via `@mcp.resource()` decorators
- [ ] Resource template URIs use `{param}` syntax for dynamic resources
- [ ] Unit tests for resource handler functions
- [ ] Integration test via MCP `resources/list` + `resources/read`

## Technical approach

### New File (`airflow_mcp_server/handlers/resources.py`)

```python
from mcp.server.fastmcp import FastMCP
# mcp instance imported from server.py or passed in

@mcp.resource("airflow://version")
async def get_version_resource() -> str:
    """Current Airflow version and metadata."""
    version = await airflow_client.get_version()
    return json.dumps(version, indent=2)

@mcp.resource("airflow://config")
async def get_config_resource() -> str:
    """Airflow configuration. May require admin permissions."""
    config = await airflow_client.get_config()
    return json.dumps(config, indent=2)

@mcp.resource("airflow://dag/{dag_id}")
async def get_dag_resource(dag_id: str) -> str:
    """DAG metadata: schedule, owner, tags, is_paused, etc."""
    dag = await airflow_client.get_dag(dag_id)
    return json.dumps(dag, indent=2)

@mcp.resource("airflow://dag/{dag_id}/source")
async def get_dag_source_resource(dag_id: str) -> str:
    """Python source code of the DAG file."""
    dag = await airflow_client.get_dag(dag_id)
    file_token = dag.get("file_token")
    if not file_token:
        return "# Source not available for this DAG"
    source = await airflow_client.get_dag_source(file_token)
    return source if isinstance(source, str) else json.dumps(source, indent=2)

@mcp.resource("airflow://dag/{dag_id}/run/{run_id}/log/{task_id}")
async def get_task_log_resource(dag_id: str, run_id: str, task_id: str) -> str:
    """Task execution log (most recent attempt)."""
    logs = await airflow_client.get_task_logs(dag_id, run_id, task_id, try_number=1)
    return logs if isinstance(logs, str) else json.dumps(logs, indent=2)

@mcp.resource("airflow://variable/{key}")
async def get_variable_resource(key: str) -> str:
    """Variable value. Sensitive variables are masked."""
    var = await airflow_client.get_variable(key)
    # Mask values with 'password', 'secret', 'token', 'key' in name
    if any(s in key.lower() for s in ["password", "secret", "token", "api_key"]):
        if isinstance(var, dict) and "value" in var:
            var = {**var, "value": "***MASKED***"}
    return json.dumps(var, indent=2)

@mcp.resource("airflow://providers")
async def get_providers_resource() -> str:
    """List of installed Airflow providers."""
    providers = await airflow_client.list_providers()
    return json.dumps(providers, indent=2)
```

### Integration with server.py

`create_app()` in `server.py` calls `register_resources()` after `register_tools_with_mcp()`:

```python
from airflow_mcp_server.handlers import resources as _resources_module
_resources_module.register_all(mcp, airflow_client)
```

### Resource MIME types

| Resource | MIME type |
| --- | --- |
| `airflow://dag/{dag_id}/source` | `text/x-python` |
| `airflow://dag/{dag_id}/run/{run_id}/log/{task_id}` | `text/plain` |
| All others | `application/json` |

### Tests

`tests/unit/test_resources.py`:
- `test_version_resource_returns_json`
- `test_dag_resource_returns_metadata`
- `test_dag_source_resource_no_file_token` (graceful fallback)
- `test_variable_resource_masks_sensitive_keys`
- `test_task_log_resource_returns_text`

## Agent UX benefit

With MCP resources, an agent workflow can be:
```
1. Client auto-loads airflow://version into context → agent knows Airflow 2.9
2. Agent queries airflow://dag/my_etl_dag → gets metadata without a tool call
3. Agent uses airflow_dag_run_clear tool to re-run the failing job
4. Client loads airflow://dag/my_etl_dag/run/manual__xxx/log/task_1 into context
```

Instead of 4 tool calls, 2 are replaced by resource reads (free, no round-trip).

## Related

- SPEC-010: Audit & Config (version/config endpoints used by resources)
- SPEC-011: MCP Protocol (prerequisite — resources need MCP SDK infrastructure)
- SPEC-013: MCP Prompts (prompts reference resources by URI)
