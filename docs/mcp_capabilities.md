# MCP Server — Capabilities and examples

This document describes in detail the tools exposed by the MCP server, their
parameters, example calls, and expected behavior.

## Overview

The MCP server exposes tools to control Apache Airflow via HTTP. Main features:

- DAG management (list, trigger, pause/unpause)
- Task management (list instances, retry)
- Log retrieval
- Connection management
- Tool discovery

## Endpoints

- `POST /tool/{tool_name}` — Main route to invoke a tool. Body: `{ "params": {...} }`.
- `POST /tool` — Fallback that accepts `{ "tool_name": "...", "params": {...} }`.
- `GET /health` — Liveness endpoint for the MCP API process.
- `GET /ready` — Readiness endpoint validating Airflow connectivity.
- Interactive documentation (OpenAPI / Swagger): `GET /docs`.

All responses return a `ToolResponse`:

```
{ "success": true|false, "data": <result>|null, "error": <str>|null }
```

## Available tools (examples and payloads)

1) `airflow_dag_list`

- Description: returns the list of DAGs (supports different Airflow response formats).
- Payload: `{ "params": { "limit": 100, "offset": 0 } }`
- Example curl:

```bash
curl -s -X POST http://localhost:8000/tool/airflow_dag_list \
  -H 'Content-Type: application/json' \
  -d '{"params": {"limit": 100, "offset": 0}}' | jq .
```

2) `airflow_dag_trigger`

- Description: triggers a DAG and returns the `dag_run_id`.
- Payload: `{ "params": { "dag_id": "example_bash_operator", "conf": {} } }`
- Example:

```bash
curl -s -X POST http://localhost:8000/tool/airflow_dag_trigger \
  -H 'Content-Type: application/json' \
  -d '{"params": {"dag_id": "example_bash_operator", "conf": {}}}' | jq .
```

3) `airflow_task_list_instances`

- Description: list task instances for a given `dag_id` and `run_id`.
- Payload: `{ "params": { "dag_id": "my_dag", "run_id": "my_run" } }`

4) `airflow_task_retry`

- Description: requests a retry for a task. The client first tries the legacy
  `setState` endpoint and falls back to Airflow 3 `clearTaskInstances` when
  needed.
- Payload: `{ "params": { "dag_id": "my_dag", "run_id": "my_run", "task_id": "my_task" } }`

5) `airflow_task_logs`

- Description: fetches logs for a task.
- Payload: `{ "params": { "dag_id": "my_dag", "run_id": "my_run", "task_id": "my_task", "try_number": 1 } }`

6) `airflow_connection_create`

- Description: creates or updates an Airflow connection via the REST API.
- Payload: `{ "params": { "conn_id": "my_conn", "type": "http", "host": "example.com", "login": "u", "password": "p", "port": 123 } }`

7) `airflow_dag_pause` / `airflow_dag_unpause`

- Payload: `{ "params": { "dag_id": "my_dag" } }`

8) `airflow_health_check`

- Description: health endpoint returning `{"status":"ok"}`.
- Payload: `{ "params": {} }`

9) `airflow_tools_list` (discovery)

- Description: returns a list of exposed tools with useful metadata
  (`tool_name`, `module`, `category`, `read_only`, `description`,
  `input_schema`, `examples`).
- Example curl:

```bash
curl -s -X POST http://localhost:8000/tool/airflow_tools_list \
  -H 'Content-Type: application/json' -d '{"params": {}}' | jq .
```

## Behavior and compatibility

- The Airflow client targets Airflow 3.x exclusively via `/api/v2`.
- `get_health()` probes `/api/v2/monitor/health` and falls back to `/api/v2/health`.
- The client applies a retry/backoff strategy and converts HTTP errors
  into specific exceptions (`AirflowAuthError`, `AirflowConnectionError`, ...).
- `MCP_TRANSPORT` controls protocol exposure: `stdio`, `http`, or `both`.

## Environment variables

- `AIRFLOW_BASE_URL` (e.g. `http://localhost:8080`)
- `AIRFLOW_USERNAME`, `AIRFLOW_PASSWORD` (BasicAuth — optional)
- `AIRFLOW_API_TOKEN` (Bearer token — optional, takes precedence over BasicAuth)
- `MCP_REQUIRE_AUTH` (default `true`, protects `/tool*` and `/mcp`)
- `MCP_AUTH_TOKEN` (optional token for non-local clients when auth is enabled)
- `MCP_ENABLE_ADMIN_ENDPOINTS` (default `false`, controls admin/config surfaces)
- `MCP_READ_ONLY` (default `false`, hides mutating tools)

## Security behavior

- Sensitive values are masked in variable and connection handler responses.
- Admin configuration capabilities are disabled by default.
- Read-only mode excludes mutating tools from discovery and invocation.

## Tests

- Integration tests require a reachable real Airflow instance by default.
- Mock fallback (`httpx.MockTransport`) is opt-in via
  `AIRFLOW_INTEGRATION_ALLOW_MOCK_FALLBACK=true`.

## Useful links

- Quickstart guide: `README.md`.
- Architecture: `docs/architecture.md`.
- Code: `airflow_mcp_server/handlers`, `airflow_mcp_server/airflow_client.py`, `airflow_mcp_server/server.py`.
