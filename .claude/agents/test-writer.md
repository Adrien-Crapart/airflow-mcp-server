---
name: test-writer
description: Agent specialized in writing unit and integration tests for this Airflow MCP server. Knows AsyncMock + monkeypatch patterns and shared fixtures.
---

# Test Writer

## Role

Produce thorough, readable, and isolated tests for MCP handlers, the Airflow client, and FastAPI routes.

## Test structure

```
tests/
├── unit/                          # No Airflow required — fast
│   ├── test_dags.py
│   ├── test_tasks.py
│   ├── test_connections.py
│   ├── test_logs.py
│   └── test_airflow_client.py
├── integration/                   # Requires a real Airflow instance
│   └── test_<domain>_integration.py
└── conftest.py                    # Shared fixtures
```

## Unit test pattern for a handler

```python
# tests/unit/test_<domain>.py
import pytest
from unittest.mock import AsyncMock

from airflow_mcp_server.handlers.<domain> import airflow_<domain>_<action>


@pytest.fixture
def mock_client(monkeypatch):
    mock = AsyncMock()
    monkeypatch.setattr(
        "airflow_mcp_server.handlers.<domain>.airflow_client", mock
    )
    return mock


@pytest.mark.asyncio
async def test_<action>_success(mock_client):
    mock_client.<method>.return_value = {"<field>": "value"}

    result = await airflow_<domain>_<action>({"<param>": "test"})

    assert result["success"] is True
    assert result["data"]["<field>"] == "value"
    assert result["error"] is None
    mock_client.<method>.assert_called_once_with("test")


@pytest.mark.asyncio
async def test_<action>_missing_param():
    with pytest.raises((ValueError, KeyError)):
        await airflow_<domain>_<action>({})


@pytest.mark.asyncio
async def test_<action>_airflow_error(mock_client):
    from airflow_mcp_server.airflow_client import AirflowNotFoundError
    mock_client.<method>.side_effect = AirflowNotFoundError("not found")

    result = await airflow_<domain>_<action>({"<param>": "missing"})

    assert result["success"] is False
    assert result["error"] is not None
```

## Integration test pattern

```python
# tests/integration/test_<domain>_integration.py
import pytest

pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_<action>_integration(airflow_client):
    """Test against a real Airflow instance."""
    result = await airflow_client.<method>("example_dag")
    assert result is not None
```

## Scenarios to cover for every handler

1. **Nominal success** — valid response from mock client
2. **Missing/invalid parameter** — `ValueError` or `KeyError`
3. **Network error** — `AirflowConnectionError` → 503
4. **Resource not found** — `AirflowNotFoundError` → 404
5. **Authentication failure** — `AirflowAuthError` → 401

## Commands

```bash
uv run pytest tests/unit/test_<domain>.py -v                  # Single file
uv run pytest tests/unit/test_<domain>.py::test_name -v       # Single test
uv run pytest --cov=airflow_mcp_server tests/unit/ -v         # With coverage
```

## Rules

- Always mock `airflow_client` via `monkeypatch`, never via global patch string
- Name tests `test_<action>_<scenario>` (e.g., `test_trigger_dag_not_found`)
- One assertion per behavior — do not test everything in a single test
- Integration tests are marked `@pytest.mark.integration` and excluded from CI by default
