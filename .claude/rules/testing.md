---
name: testing
description: Rules for writing and organizing tests — unit vs integration, coverage, fixtures.
---

# Testing Rules

## Organization

- `tests/unit/` — fast tests, mocked Airflow client, no Airflow instance required
- `tests/integration/` — tests against a real Airflow instance, marked `@pytest.mark.integration`
- `tests/conftest.py` — shared fixtures between both types

## Mandatory rules

- Always mock `airflow_client` via `monkeypatch.setattr()`, never via global `patch()` string
- Decorate coroutines with `@pytest.mark.asyncio`
- Integration tests must be marked `pytestmark = pytest.mark.integration`
- Naming: `test_<action>_<scenario>` — e.g., `test_trigger_dag_not_found`

## Scenarios to cover for every handler

1. Nominal success
2. Missing required parameter
3. `AirflowNotFoundError` (resource absent)
4. `AirflowConnectionError` (Airflow unreachable)
5. `AirflowAuthError` (401)

## Commands

```bash
just test                                                      # CI — excludes integration
uv run pytest tests/unit/test_<domain>.py -v                   # Single file
uv run pytest tests/unit/test_<domain>.py::test_name -v        # Single test
uv run pytest --cov=airflow_mcp_server tests/unit/ -v          # With coverage
uv run pytest -v                                               # All (requires Airflow)
```

## Coverage target

80%+ on `airflow_mcp_server/`, excluding `main.py`.
