---
id: SPEC-006
title: "Observability Tools — XComs, Import Errors, Datasets, Providers/Plugins"
status: active
domain: "handlers/xcoms, handlers/import_errors, handlers/datasets, handlers/providers"
created: 2026-04-13
updated: 2026-04-13
branch: feature/SPEC-006-observability
---

# SPEC-006: Observability Tools

## Context

XCom values are outputs from tasks used by downstream tasks. Import errors track DAGs that
failed to parse. Datasets represent data lineage. Providers and plugins extend Airflow capabilities.
These tools provide visibility into system health and DAG dependencies.

## Goal

Expose XCom access, error visibility, and data lineage/provider information for observability.

## Acceptance criteria

- [x] `airflow_xcom_get` — retrieve XCom value from task instance
- [x] `airflow_import_error_list` — list DAG import errors
- [x] `airflow_dataset_list` — list datasets (data lineage)
- [x] `airflow_dataset_get` — fetch dataset by URI
- [x] `airflow_provider_list` — list installed providers
- [x] `airflow_plugin_list` — list active plugins
- [x] Unit tests for XCom and import errors (14 tests total)

## Technical approach

### Handlers

- `handlers/xcoms.py` — `get_xcom(dag_id, run_id, task_id, key)`
- `handlers/import_errors.py` — `list_import_errors(limit)`
- `handlers/datasets.py` — `list_datasets(limit)`, `get_dataset(dataset_uri)`
- `handlers/providers.py` — `list_providers(limit)`, `list_plugins(limit)`

### Schema

- `XcomGetParams(dag_id, run_id, task_id, key)`
- `ListImportErrorsParams(limit=100)`
- `ListDatasetsParams(limit=100)`, `DatasetUriParams(dataset_uri: str)`
- `ListProvidersParams(limit=100)`, `ListPluginsParams(limit=100)`

### Tests

- `tests/unit/test_xcoms.py` — 7 test cases
- `tests/unit/test_import_errors.py` — 5 test cases
- No specific tests for datasets/providers (they follow standard patterns)

### Notes

- Datasets endpoint in Airflow 3.x called "assets" — fallback handled by `_to_snake_path`
- URI parameters are URL-encoded by httpx

## MCP tools affected

- `airflow_xcom_get` — retrieve task output values
- `airflow_import_error_list` — identify parsing failures
- `airflow_dataset_list`, `airflow_dataset_get` — data lineage visibility
- `airflow_provider_list`, `airflow_plugin_list` — extension inventory

## Related

- SPEC-001: Core Infrastructure
