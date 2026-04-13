---
id: SPEC-005
title: "Variable & Pool Management — CRUD Variables + Pool Control"
status: done
domain: "handlers/variables, handlers/pools"
created: 2026-04-13
updated: 2026-04-13
branch: feature/SPEC-005-variables-pools
---

# SPEC-005: Variable & Pool Management

## Context

Variables store key-value data shared across DAGs. Pools control concurrency by limiting
parallel task execution per resource. Both are critical for DAG configuration and execution control.

## Goal

Provide full variable management and pool control for Airflow operations.

## Acceptance criteria

- [x] `airflow_variable_list` — list all variables
- [x] `airflow_variable_get` — fetch a variable by key
- [x] `airflow_variable_set` — create/update a variable
- [x] `airflow_variable_delete` — delete a variable
- [x] `airflow_pool_list` — list all pools
- [x] `airflow_pool_get` — fetch pool by name
- [x] `airflow_pool_set` — create/update pool
- [x] Unit tests covering all 7 tools with full error scenarios

## Technical approach

### Handlers

- `handlers/variables.py` — variable CRUD operations
- `handlers/pools.py` — pool management

### Schema

- `ListVariablesParams(limit=100)`, `VariableKeyParams(key: str)`, `SetVariableParams(key, value)`
- `ListPoolsParams(limit=100)`, `PoolNameParams(pool_name: str)`, `SetPoolParams(pool_name, slots, description?)`

### Tests

- `tests/unit/test_variables.py` — 16 test cases
- `tests/unit/test_pools.py` — 14 test cases

## MCP tools affected

- `airflow_variable_list`, `airflow_variable_get`, `airflow_variable_set`, `airflow_variable_delete`
- `airflow_pool_list`, `airflow_pool_get`, `airflow_pool_set`

## Related

- SPEC-001: Core Infrastructure
