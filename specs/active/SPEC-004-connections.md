---
id: SPEC-004
title: "Connection Management — Full CRUD Operations"
status: active
domain: "handlers/connections"
created: 2026-04-13
updated: 2026-04-13
branch: feature/SPEC-004-connections
---

# SPEC-004: Connection Management

## Context

Connections store credentials and connection parameters for external services (databases,
APIs, etc.). Users need to create, list, retrieve, and delete connections for DAG configuration.

## Goal

Provide full CRUD operations for Airflow connection management.

## Acceptance criteria

- [x] `airflow_connection_list` — list all connections
- [x] `airflow_connection_get` — fetch a single connection by ID
- [x] `airflow_connection_create` — create a new connection
- [x] `airflow_connection_delete` — delete a connection
- [x] Unit tests for all 4 operations with edge cases (missing params, not found, auth errors)

## Technical approach

### Handler (`airflow_mcp_server/handlers/connections.py`)

- `list_connections(params)` — GET `/connections`
- `get_connection(params)` — GET `/connections/{conn_id}`
- `create_connection(params)` — POST `/connections` with connection details
- `delete_connection(params)` — DELETE `/connections/{conn_id}`

### Schema

- `ListConnectionsParams(limit=100)`
- `ConnectionIdParams(conn_id: str)`
- `CreateConnectionParams(conn_id, type, host?, login?, password?, port?, extra?)`

### Tests

- `tests/unit/test_connections_crud.py` — 12 test cases covering all 4 tools

## Integration tests

- `tests/integration/test_integration_more.py::test_create_connection` already covers create

## MCP tools affected

- `airflow_connection_list` — paginated connection listing
- `airflow_connection_get` — fetch connection by ID
- `airflow_connection_create` — create connection (write)
- `airflow_connection_delete` — delete connection (write)

## Related

- SPEC-001: Core Infrastructure
