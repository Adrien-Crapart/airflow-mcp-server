---
id: SPEC-007
title: "Agent Tools & Read-only Safety Mode"
status: done
domain: "handlers/agent_tools, server.py, config.py"
created: 2026-04-13
updated: 2026-04-13
branch: feature/SPEC-007-agent-tools
---

# SPEC-007: Agent Tools & Read-only Safety Mode

## Context

Agent-optimized tools aggregate multiple API calls into single operations, reducing LLM
round-trips and improving efficiency. Read-only mode restricts write operations for
production safety, allowing agents to inspect the system without risk of mutations.

## Goal

Provide efficiency tools for agents and implement safety guardrails for production deployments.

## Acceptance criteria

- [x] `airflow_dag_diagnose` — aggregate tool combining run status + failed tasks + logs
- [x] `airflow_system_health` — aggregate tool combining health + import errors + pool stats
- [x] Read-only mode: `MCP_READ_ONLY=true` filters write tools at server startup
- [x] Write-only tools marked in `WRITE_ONLY_TOOLS` set:
  - dag_trigger, dag_pause, dag_unpause, task_retry
  - connection_create, connection_delete
  - variable_set, variable_delete
  - pool_set
- [x] Unit tests for aggregate tools (14 tests covering success, partial failures, etc.)

## Technical approach

### Handler (`airflow_mcp_server/handlers/agent_tools.py`)

- `diagnose_dag_run(params)` — returns:
  - `dag_run` — full run metadata
  - `failed_tasks` — list of failed task instances
  - `recent_logs` — logs from first failed task (if any)
  - `error_summary` — human-readable error summary

- `system_health(params)` — returns:
  - `status` — health check result
  - `import_errors` — list of DAGs with parse errors
  - `pool_usage` — current pool usage stats

### Schema

- `DiagnoseDagRunParams(dag_id: str, run_id: str)`
- `SystemHealthParams()` — no parameters

### Server Changes

`airflow_mcp_server/server.py`:
- Define `WRITE_ONLY_TOOLS` set with 9 write operation tool names
- In `load_tools()`, filter tools if `cfg.MCP_READ_ONLY` is True

### Config Changes

`airflow_mcp_server/config.py`:
- Add `MCP_READ_ONLY: bool` from env var (default: False)

### Tests

- `tests/unit/test_agent_tools.py` — 14 test cases covering:
  - Success with full diagnosis output
  - Partial failures (one component fails, others succeed)
  - Missing parameters
  - DAG/run not found
  - Connection errors

## Integration tests

- Extend `conftest.py` mock with endpoints for diagnose/health tools
- Add `test_integration_more.py::test_system_health` and `test_diagnose_dag_run`

## MCP tools affected

### New tools (2)
- `airflow_dag_diagnose` — aggregate diagnostic tool for run troubleshooting
- `airflow_system_health` — aggregate system status tool

### Safety features
- Read-only mode filtering via `MCP_READ_ONLY` env var
- Write tools blocked when mode enabled: 9 tools restricted

## Related

- All prior specs — agent tools depend on working tools from SPEC-001 through SPEC-006
- Architecture: `specs/domain/architecture.md`
