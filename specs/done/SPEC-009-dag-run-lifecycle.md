---
id: SPEC-009
title: "DAG Run Lifecycle — Clear, Cancel, State, Task Definitions"
status: done
domain: "handlers/dags, handlers/tasks, airflow_client"
created: 2026-04-13
updated: 2026-04-13
branch: feature/SPEC-009-dag-run-lifecycle
---

# SPEC-009: DAG Run Lifecycle

## Context

Clearing a failed DAG run (re-running it from scratch or from a specific task) is the
most common Airflow operator action. Currently impossible via the MCP server.
Similarly, cancelling a running DAG, setting a run's state manually, and listing
task definitions (structure, not instances) are all absent — yet are needed to build
any meaningful automation workflow.

## Goal

Complete the DAG run and task management lifecycle so agents can fully control
Airflow workflow execution without needing the Airflow UI.

## Acceptance criteria

- [x] `airflow_dag_run_get` — fetch a single DAG run by run_id
- [x] `airflow_dag_run_clear` — clear/re-run a DAG run (POST /dagRuns/{id}/clear)
- [x] `airflow_dag_run_cancel` — cancel/delete a running DAG run
- [x] `airflow_dag_run_set_state` — update DAG run state (mark success/failed)
- [x] `airflow_task_list` — list task definitions for a DAG (not instances)
- [x] `airflow_task_get` — get a single task definition
- [x] `airflow_task_set_state` — set a task instance state (clear, success, failed, skipped)
- [x] `airflow_task_clear` — clear a task instance to force re-run
- [x] Unit tests for all new tools (success, missing params, not found, connection error)
- [x] READ_ONLY_TOOLS updated in discovery.py for new mutating tools

## Technical approach

### New Client Methods (`airflow_mcp_server/airflow_client.py`)

```python
async def get_dag_run(self, dag_id: str, run_id: str) -> Any:
    """GET /dags/{dag_id}/dagRuns/{dag_run_id}"""

async def clear_dag_run(self, dag_id: str, run_id: str, only_failed: bool = True) -> Any:
    """POST /dags/{dag_id}/dagRuns/{dag_run_id}/clear"""
    # Body: {"dry_run": false, "only_failed": true, "reset_dag_runs": true}

async def delete_dag_run(self, dag_id: str, run_id: str) -> Any:
    """DELETE /dags/{dag_id}/dagRuns/{dag_run_id}"""

async def update_dag_run_state(self, dag_id: str, run_id: str, state: str) -> Any:
    """PATCH /dags/{dag_id}/dagRuns/{dag_run_id}"""
    # Body: {"state": state}  (success | failed | queued | running)

async def list_tasks(self, dag_id: str) -> Any:
    """GET /dags/{dag_id}/tasks"""

async def get_task(self, dag_id: str, task_id: str) -> Any:
    """GET /dags/{dag_id}/tasks/{task_id}"""

async def set_task_instance_state(self, dag_id: str, run_id: str, task_id: str, state: str) -> Any:
    """PATCH /dags/{dag_id}/dagRuns/{dag_run_id}/taskInstances/{task_id}"""
    # Body: {"state": state, "include_upstream": false, "include_downstream": false}

async def clear_task_instance(self, dag_id: str, run_id: str, task_id: str) -> Any:
    """POST /dags/{dag_id}/dagRuns/{dag_run_id}/taskInstances/{task_id}/clear"""
```

### New Schemas (`airflow_mcp_server/schemas.py`)

```python
class DagRunIdParams(BaseModel):
    dag_id: str = Field(..., description="DAG identifier")
    run_id: str = Field(..., description="DAG run identifier")

class ClearDagRunParams(BaseModel):
    dag_id: str = Field(..., description="DAG identifier")
    run_id: str = Field(..., description="DAG run to clear")
    only_failed: bool = Field(True, description="Only clear failed tasks (default: True)")

class SetDagRunStateParams(BaseModel):
    dag_id: str = Field(..., description="DAG identifier")
    run_id: str = Field(..., description="DAG run identifier")
    state: str = Field(..., description="Target state: 'success', 'failed', 'queued'")

class TaskIdParams(BaseModel):
    dag_id: str = Field(..., description="DAG identifier")
    task_id: str = Field(..., description="Task identifier within the DAG")

class SetTaskStateParams(BaseModel):
    dag_id: str = Field(..., description="DAG identifier")
    run_id: str = Field(..., description="DAG run identifier")
    task_id: str = Field(..., description="Task identifier")
    state: str = Field(..., description="Target state: 'success', 'failed', 'skipped', 'up_for_retry'")
```

### Handlers

**In `handlers/dags.py`** — add:
- `get_dag_run(params)` — delegates to `airflow_client.get_dag_run()`
- `clear_dag_run(params)` — delegates to `airflow_client.clear_dag_run()`
- `cancel_dag_run(params)` — delegates to `airflow_client.delete_dag_run()`
- `set_dag_run_state(params)` — delegates to `airflow_client.update_dag_run_state()`

**In `handlers/tasks.py`** — add:
- `list_tasks(params)` — delegates to `airflow_client.list_tasks()`
- `get_task(params)` — delegates to `airflow_client.get_task()`
- `set_task_state(params)` — delegates to `airflow_client.set_task_instance_state()`
- `clear_task(params)` — delegates to `airflow_client.clear_task_instance()`

### Write tools to add to `WRITE_ONLY_TOOLS` (server.py)

```python
"airflow_dag_run_clear",
"airflow_dag_run_cancel",
"airflow_dag_run_set_state",
"airflow_task_set_state",
"airflow_task_clear",
```

### Tests

New file `tests/unit/test_dag_run_lifecycle.py`:
- `test_get_dag_run_success`
- `test_clear_dag_run_success`
- `test_clear_dag_run_missing_params`
- `test_cancel_dag_run_success`
- `test_set_dag_run_state_success`
- `test_set_dag_run_state_invalid_state`
- `test_list_tasks_success`
- `test_get_task_success`
- `test_set_task_state_success`
- `test_clear_task_success`
- `test_*_not_found` (for each tool)
- `test_*_connection_error` (for each tool)

## MCP tools affected

### New tools (8)
- `airflow_dag_run_get` — fetch single DAG run
- `airflow_dag_run_clear` — clear/re-run (write)
- `airflow_dag_run_cancel` — cancel/delete run (write)
- `airflow_dag_run_set_state` — mark success/failed (write)
- `airflow_task_list` — list task definitions (DAG structure)
- `airflow_task_get` — single task definition
- `airflow_task_set_state` — set task state (write)
- `airflow_task_clear` — force re-run task (write)

## Related

- SPEC-002: DAG Management (list_dag_runs, list_task_instances already implemented)
- SPEC-003: Task Management (retry_task already implemented)
- SPEC-007: Agent Tools (diagnose uses task instances)
