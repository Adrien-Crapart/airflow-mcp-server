---
id: SPEC-003
title: "Task & Log Management — List Instances, Retry, Fetch Logs"
status: active
domain: "handlers/tasks, handlers/logs"
created: 2026-04-13
updated: 2026-04-13
branch: feature/SPEC-003-task-logs
---

# SPEC-003: Task & Log Management

## Context

Task instances represent individual executions of DAG tasks. Users need to list tasks
for a given run, retry failed tasks, and access task logs for troubleshooting.

## Goal

Provide tools for task introspection, failure recovery, and debugging.

## Acceptance criteria

- [x] `airflow_task_list_instances` — list task instances for a DAG run
- [x] `airflow_task_retry` — retry a failed task
- [x] `airflow_task_logs` — fetch task logs with try number support
- [x] Unit tests covering all scenarios (missing params, not found, auth errors, etc.)

## Technical approach

### Handlers

- `handlers/tasks.py` — `list_task_instances`, `retry_task`
- `handlers/logs.py` — `fetch_task_logs`

### Schema

- `TaskRunParams(dag_id: str, run_id: str)` — for list_task_instances
- `RetryTaskParams(dag_id: str, run_id: str, task_id: str)`
- `FetchLogsParams(dag_id: str, task_id: str, run_id: str, try_number=1)`

### Tests

- `tests/unit/test_handlers_misc.py` — pause/unpause/retry tests
- Covers success, missing params, not found, auth errors, connection errors

## Integration tests

- `tests/integration/test_integration_more.py` already covers get_task_logs, retry

## MCP tools affected

- `airflow_task_list_instances` — paginated task instance listing
- `airflow_task_retry` — retry failed task execution
- `airflow_task_logs` — fetch task execution logs

## Related

- SPEC-002: DAG Management (prerequisite)
