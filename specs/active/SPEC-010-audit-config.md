---
id: SPEC-010
title: "Audit, Config & Monitoring — Event Logs, Config, Version, DAG Warnings"
status: draft
domain: "handlers/event_logs, handlers/config, airflow_client"
created: 2026-04-13
updated: 2026-04-13
branch: feature/SPEC-010-audit-config
---

# SPEC-010: Audit, Config & Monitoring

## Context

Agents debugging production issues need to know: who triggered what and when (event logs),
what the Airflow configuration looks like (scheduler intervals, parallelism, etc.), and
which DAGs have SLA misses or configuration warnings. None of these are currently available
through the MCP server.

## Goal

Provide full audit trail and configuration introspection for monitoring, compliance,
and debugging workflows.

## Acceptance criteria

- [ ] `airflow_event_log_list` — list Airflow audit logs with filters
- [ ] `airflow_event_log_get` — get a single audit event by ID
- [ ] `airflow_config_get` — retrieve Airflow configuration
- [ ] `airflow_version_get` — get Airflow version and metadata
- [ ] `airflow_dag_warning_list` — list DAG warnings (SLA misses, import warnings)
- [ ] Unit tests for all tools

## Technical approach

### New Client Methods (`airflow_mcp_server/airflow_client.py`)

```python
async def list_event_logs(self, limit: int = 100, dag_id: Optional[str] = None,
                           event: Optional[str] = None) -> Any:
    """GET /eventLogs — Airflow audit trail."""
    params = {"limit": limit}
    if dag_id: params["dag_id"] = dag_id
    if event: params["event"] = event
    return await self._request_with_fallback("GET", f"{self.api_prefix}/eventLogs", params=params)

async def get_event_log(self, event_log_id: int) -> Any:
    """GET /eventLogs/{event_log_id}"""

async def get_config(self) -> Any:
    """GET /config — Airflow configuration (may require admin permissions)."""

async def get_version(self) -> Any:
    """GET /version — Airflow version metadata."""

async def list_dag_warnings(self, dag_id: Optional[str] = None, limit: int = 100) -> Any:
    """GET /dagWarnings"""
```

### New Handler File (`airflow_mcp_server/handlers/event_logs.py`)

```python
TOOLS = {
    "airflow_event_log_list": list_event_logs,
    "airflow_event_log_get": get_event_log,
}
```

### New Handler File (`airflow_mcp_server/handlers/config.py`)

```python
TOOLS = {
    "airflow_config_get": get_config,
    "airflow_version_get": get_version,
}
```

### In `handlers/import_errors.py` — add (or new handler)

```python
TOOLS.update({"airflow_dag_warning_list": list_dag_warnings})
```

### New Schemas (`airflow_mcp_server/schemas.py`)

```python
class ListEventLogsParams(BaseModel):
    limit: int = Field(100, ge=1, description="Maximum number of events to return")
    dag_id: Optional[str] = Field(None, description="Filter by DAG ID")
    event: Optional[str] = Field(None, description="Filter by event type (e.g. 'trigger', 'pause')")

class EventLogIdParams(BaseModel):
    event_log_id: int = Field(..., description="Numeric ID of the audit event")

class ListDagWarningsParams(BaseModel):
    dag_id: Optional[str] = Field(None, description="Filter by DAG ID (None = all DAGs)")
    limit: int = Field(100, ge=1, description="Maximum number of warnings to return")

class GetConfigParams(BaseModel):
    section: Optional[str] = Field(None, description="Config section to filter (e.g. 'core', 'scheduler')")
```

### Tests

- `tests/unit/test_event_logs.py`:
  - `test_list_event_logs_success`
  - `test_list_event_logs_filtered_by_dag`
  - `test_list_event_logs_filtered_by_event`
  - `test_get_event_log_success`
  - `test_get_event_log_not_found`
  - `test_*_connection_error`
  - `test_*_auth_error`

- `tests/unit/test_config.py`:
  - `test_get_config_success`
  - `test_get_version_success`
  - `test_get_config_forbidden` (may require admin — map to 403)
  - `test_list_dag_warnings_success`

## Event types (reference for agents)

Common Airflow event types returned by `eventLogs`:
- `trigger` — DAG was triggered
- `pause` / `unpause` — DAG pause state changed
- `success` / `failed` — task state change
- `set_variable` — variable was updated
- `delete_variable` — variable was deleted
- `connection.create` / `connection.edit` / `connection.delete`

## MCP tools affected

### New tools (5)
- `airflow_event_log_list` — audit trail (filtered by DAG, event type)
- `airflow_event_log_get` — single audit event
- `airflow_config_get` — Airflow configuration (read-only)
- `airflow_version_get` — Airflow version info
- `airflow_dag_warning_list` — SLA misses and config warnings

All tools are read-only (no addition to `WRITE_ONLY_TOOLS`).

## Related

- SPEC-006: Observability (import_errors already implemented)
- SPEC-007: Agent Tools (system_health could incorporate dag_warnings in future)
