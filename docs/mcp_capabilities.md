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

- Description: requests a retry for a task (sets state to `queued` via setState).
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
  (`tool_name`, `module`, `has_input_model`, `doc`, `signature`).
- Example curl:

```bash
curl -s -X POST http://localhost:8000/tool/airflow_tools_list \
  -H 'Content-Type: application/json' -d '{"params": {}}' | jq .
```

## Behavior and compatibility

- The Airflow client supports `/api/v1` and `/api/v2`. Default `AIRFLOW_VERSION` = `2`.
- The client applies a retry/backoff strategy and converts HTTP errors
  into specific exceptions (`AirflowAuthError`, `AirflowConnectionError`, ...).

## Environment variables

- `AIRFLOW_BASE_URL` (e.g. `http://localhost:8080`)
- `AIRFLOW_USERNAME`, `AIRFLOW_PASSWORD` (BasicAuth — optional)
- `AIRFLOW_VERSION` (`2` or `3`)

## Tests

- Integration tests include a fallback: if Airflow is unreachable,
  an `httpx.MockTransport` simulates common endpoints to allow tests to
  run in isolated environments.

## Useful links

- Quickstart guide: `README.md`.
- Architecture: `docs/architecture.md`.
- Code: `airflow_mcp_server/handlers`, `airflow_mcp_server/airflow_client.py`, `airflow_mcp_server/server.py`.
