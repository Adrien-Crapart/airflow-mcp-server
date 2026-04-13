---
id: SPEC-002
title: "DAG Management — List, Get, Trigger, Pause, Unpause, Run List, Source"
status: done
domain: "handlers/dags"
created: 2026-04-13
updated: 2026-04-13
branch: feature/SPEC-002-dag-management
---

# SPEC-002: DAG Management

## Context

DAGs (Directed Acyclic Graphs) are the core unit of work in Airflow. Users need to list
available DAGs, inspect their details, trigger runs, manage pause/unpause state, view
run history, and access source code for debugging.

## Goal

Provide comprehensive DAG management tools covering lifecycle operations and introspection.

## Acceptance criteria

- [x] `airflow_dag_list` — list all DAGs with pagination
- [x] `airflow_dag_get` — fetch DAG metadata (status, schedule, owner, etc.)
- [x] `airflow_dag_trigger` — trigger a DAG run with optional config
- [x] `airflow_dag_pause` — pause a DAG (no new runs)
- [x] `airflow_dag_unpause` — unpause a DAG (resume scheduling)
- [x] `airflow_dag_run_list` — list runs for a specific DAG
- [x] `airflow_dag_source` — retrieve DAG source code (for debugging/inspection)
- [x] Unit tests covering all 7 tools with 22 test cases

## Technical approach

### Handler (`airflow_mcp_server/handlers/dags.py`)

- `list_dags(params)` — GET `/dags`, respects limit + offset pagination
- `get_dag(params)` — GET `/dags/{dag_id}`, returns metadata
- `trigger_dag(params)` — POST `/dags/{dag_id}/dagRuns`, accepts optional conf dict
- `pause_dag(params)` — PATCH `/dags/{dag_id}` with `{is_paused: true}`
- `unpause_dag(params)` — PATCH `/dags/{dag_id}` with `{is_paused: false}`
- `list_dag_runs(params)` — GET `/dags/{dag_id}/dagRuns`, returns run history
- `get_dag_source(params)` — chains `get_dag()` to fetch file_token, then GET `/dagSources/{file_token}`

### Schema

Models in `schemas.py`:
- `ListDagsParams(limit=100, offset=0)`
- `DagIdParams(dag_id: str)` — reused for get, trigger, pause, unpause, source
- `TriggerDagParams(dag_id: str, conf: Optional[Dict])`
- `DagRunListParams(dag_id: str, limit=100)`

### Tests

- `tests/unit/test_dags.py` — basic list_dags, trigger_dag_missing_id scenarios
- `tests/unit/test_dags_extended.py` — comprehensive tests for all 7 tools:
  - Success cases with real-like responses
  - Missing required params (ValueError)
  - `AirflowNotFoundError` (404 DAG not found)
  - `AirflowConnectionError` (Airflow unreachable)
  - `AirflowAuthError` (401 auth failure)
  - Pagination (respects limit parameter)

## Integration tests

- `tests/integration/test_integration_airflow.py::test_trigger_dag_against_airflow` already covers list_dags + trigger

## MCP tools affected

### New tools (7)
- `airflow_dag_list` — paginated DAG listing
- `airflow_dag_get` — DAG metadata retrieval
- `airflow_dag_trigger` — trigger a run
- `airflow_dag_pause` — pause scheduling
- `airflow_dag_unpause` — resume scheduling
- `airflow_dag_run_list` — DAG run history
- `airflow_dag_source` — retrieve source code

## Related

- SPEC-001: Core Infrastructure (AirflowClient foundation)
- Integration: test_integration_airflow.py covers basic DAG operations
