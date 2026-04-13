import pytest
import airflow_mcp_server.airflow_client as _client
from airflow_mcp_server.airflow_client import (
    AirflowConnectionError,
    AirflowAuthError,
)
from airflow_mcp_server.handlers import import_errors


@pytest.mark.asyncio
async def test_list_import_errors_success(monkeypatch):
    async def _fake_list(limit=100):
        return [
            {"import_error_id": 1, "filename": "broken_dag.py", "stack_trace": "SyntaxError"},
            {"import_error_id": 2, "filename": "another.py", "stack_trace": "ImportError"},
        ]

    monkeypatch.setattr(_client.client, "list_import_errors", _fake_list)

    res = await import_errors.list_import_errors({})

    assert res["success"] is True
    assert isinstance(res["data"], list)
    assert len(res["data"]) == 2
    assert res["data"][0]["filename"] == "broken_dag.py"
    assert res["error"] is None


@pytest.mark.asyncio
async def test_list_import_errors_empty(monkeypatch):
    async def _fake_list(limit=100):
        return []

    monkeypatch.setattr(_client.client, "list_import_errors", _fake_list)

    res = await import_errors.list_import_errors({})

    assert res["success"] is True
    assert res["data"] == []
    assert res["error"] is None


@pytest.mark.asyncio
async def test_list_import_errors_connection_error(monkeypatch):
    async def _fake_list(limit=100):
        raise AirflowConnectionError("unreachable")

    monkeypatch.setattr(_client.client, "list_import_errors", _fake_list)

    with pytest.raises(AirflowConnectionError):
        await import_errors.list_import_errors({})


@pytest.mark.asyncio
async def test_list_import_errors_auth_error(monkeypatch):
    async def _fake_list(limit=100):
        raise AirflowAuthError("unauthorized")

    monkeypatch.setattr(_client.client, "list_import_errors", _fake_list)

    with pytest.raises(AirflowAuthError):
        await import_errors.list_import_errors({})


@pytest.mark.asyncio
async def test_list_import_errors_respects_limit(monkeypatch):
    received_limit = None

    async def _fake_list(limit=100):
        nonlocal received_limit
        received_limit = limit
        return []

    monkeypatch.setattr(_client.client, "list_import_errors", _fake_list)

    await import_errors.list_import_errors({"limit": 10})

    assert received_limit == 10
