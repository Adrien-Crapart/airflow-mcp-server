# Architecture

## Overview

This project exposes an MCP (Model Context Protocol) server to manage Apache
Airflow via an HTTP API.

- HTTP server: FastAPI (factory `airflow_mcp_server.server:create_app`).
- Handlers: `airflow_mcp_server/handlers/*` — domains: dags, tasks, connections, logs, health.
- Airflow client: `airflow_mcp_server/airflow_client.py` (httpx async, retries, basic auth).

## Main components

- **MCP API** — main entry points: `/tool` (PUT/POST) and `/tool/{tool_name}`.
- **Handlers** — async functions implementing MCP tools and returning `{success, data, error}`.
- **AirflowClient** — encapsulates REST calls to Airflow (versioning, API prefix, authentication).

## Running in development

PowerShell:

```powershell
uv run uvicorn airflow_mcp_server.server:create_app --factory --reload --host 127.0.0.1 --port 8000
```

Linux/macOS:

```bash
uv run uvicorn airflow_mcp_server.server:create_app --factory --reload --host 127.0.0.1 --port 8000
```

## Exposed endpoints (summary)

- `POST /tool` — execute an MCP tool (body: {"tool_name": "...", "params": {...}}).
- `POST /tool/{tool_name}` — shortcut to call a tool.
- `GET /health` — service health.

## OpenAPI

The OpenAPI schema is generated automatically by FastAPI. CI also produces an
`openapi.json` artifact (job `openapi`).

See also: `mcp_tools.md` for the list and schemas of tools, `integration.md` for running integration tests.
