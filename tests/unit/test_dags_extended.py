import pytest
import airflow_mcp_server.airflow_client as _client
from airflow_mcp_server.airflow_client import (
    AirflowNotFoundError,
    AirflowConnectionError,
    AirflowAuthError,
)
from airflow_mcp_server.handlers import dags


@pytest.mark.asyncio
async def test_get_dag_success(monkeypatch):
    async def _fake_get(dag_id):
        return {"dag_id": "my_dag", "is_paused": False, "owners": ["airflow"]}

    monkeypatch.setattr(_client.client, "get_dag", _fake_get)

    res = await dags.get_dag({"dag_id": "my_dag"})

    assert res["success"] is True
    assert res["data"]["dag_id"] == "my_dag"
    assert res["data"]["is_paused"] is False
    assert res["error"] is None


@pytest.mark.asyncio
async def test_get_dag_missing_id():
    with pytest.raises(Exception):
        await dags.get_dag({})


@pytest.mark.asyncio
async def test_get_dag_not_found(monkeypatch):
    async def _fake_get(dag_id):
        raise AirflowNotFoundError("dag not found")

    monkeypatch.setattr(_client.client, "get_dag", _fake_get)

    with pytest.raises(AirflowNotFoundError):
        await dags.get_dag({"dag_id": "nonexistent_dag"})


@pytest.mark.asyncio
async def test_get_dag_connection_error(monkeypatch):
    async def _fake_get(dag_id):
        raise AirflowConnectionError("unreachable")

    monkeypatch.setattr(_client.client, "get_dag", _fake_get)

    with pytest.raises(AirflowConnectionError):
        await dags.get_dag({"dag_id": "my_dag"})


@pytest.mark.asyncio
async def test_get_dag_auth_error(monkeypatch):
    async def _fake_get(dag_id):
        raise AirflowAuthError("unauthorized")

    monkeypatch.setattr(_client.client, "get_dag", _fake_get)

    with pytest.raises(AirflowAuthError):
        await dags.get_dag({"dag_id": "my_dag"})


@pytest.mark.asyncio
async def test_list_dag_runs_success(monkeypatch):
    async def _fake_list(dag_id, limit=100):
        return [
            {"dag_run_id": "run_1", "state": "success"},
            {"dag_run_id": "run_2", "state": "failed"},
        ]

    monkeypatch.setattr(_client.client, "list_dag_runs", _fake_list)

    res = await dags.list_dag_runs({"dag_id": "my_dag"})

    assert res["success"] is True
    assert isinstance(res["data"], list)
    assert len(res["data"]) == 2
    assert res["data"][0]["dag_run_id"] == "run_1"
    assert res["error"] is None


@pytest.mark.asyncio
async def test_list_dag_runs_empty(monkeypatch):
    async def _fake_list(dag_id, limit=100):
        return []

    monkeypatch.setattr(_client.client, "list_dag_runs", _fake_list)

    res = await dags.list_dag_runs({"dag_id": "my_dag"})

    assert res["success"] is True
    assert res["data"] == []


@pytest.mark.asyncio
async def test_list_dag_runs_missing_id():
    with pytest.raises(Exception):
        await dags.list_dag_runs({})


@pytest.mark.asyncio
async def test_list_dag_runs_connection_error(monkeypatch):
    async def _fake_list(dag_id, limit=100):
        raise AirflowConnectionError("unreachable")

    monkeypatch.setattr(_client.client, "list_dag_runs", _fake_list)

    with pytest.raises(AirflowConnectionError):
        await dags.list_dag_runs({"dag_id": "my_dag"})


@pytest.mark.asyncio
async def test_list_dag_runs_not_found(monkeypatch):
    async def _fake_list(dag_id, limit=100):
        raise AirflowNotFoundError("dag not found")

    monkeypatch.setattr(_client.client, "list_dag_runs", _fake_list)

    with pytest.raises(AirflowNotFoundError):
        await dags.list_dag_runs({"dag_id": "nonexistent_dag"})


@pytest.mark.asyncio
async def test_list_dag_runs_respects_limit(monkeypatch):
    received = {}

    async def _fake_list(dag_id, limit=100):
        received["dag_id"] = dag_id
        received["limit"] = limit
        return []

    monkeypatch.setattr(_client.client, "list_dag_runs", _fake_list)

    await dags.list_dag_runs({"dag_id": "my_dag", "limit": 5})

    assert received["dag_id"] == "my_dag"
    assert received["limit"] == 5
