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


@pytest.mark.asyncio
async def test_trigger_dag_success(monkeypatch):
    async def _fake_trigger(dag_id, conf=None):
        return {"dag_run_id": "manual__2026-01-01T00:00:00+00:00", "state": "queued"}

    monkeypatch.setattr(_client.client, "trigger_dag", _fake_trigger)

    res = await dags.trigger_dag({"dag_id": "my_dag"})

    assert res["success"] is True
    assert res["data"]["dag_run_id"] == "manual__2026-01-01T00:00:00+00:00"
    assert res["error"] is None


@pytest.mark.asyncio
async def test_trigger_dag_passes_conf(monkeypatch):
    received = {}

    async def _fake_trigger(dag_id, conf=None):
        received["dag_id"] = dag_id
        received["conf"] = conf
        return {"dag_run_id": "run_1", "state": "queued"}

    monkeypatch.setattr(_client.client, "trigger_dag", _fake_trigger)

    await dags.trigger_dag({"dag_id": "my_dag", "conf": {"key": "value"}})

    assert received["dag_id"] == "my_dag"
    assert received["conf"] == {"key": "value"}


@pytest.mark.asyncio
async def test_trigger_dag_missing_id():
    with pytest.raises(Exception):
        await dags.trigger_dag({})


@pytest.mark.asyncio
async def test_trigger_dag_not_found(monkeypatch):
    async def _fake_trigger(dag_id, conf=None):
        raise AirflowNotFoundError("dag not found")

    monkeypatch.setattr(_client.client, "trigger_dag", _fake_trigger)

    with pytest.raises(AirflowNotFoundError):
        await dags.trigger_dag({"dag_id": "nonexistent_dag"})


@pytest.mark.asyncio
async def test_trigger_dag_connection_error(monkeypatch):
    async def _fake_trigger(dag_id, conf=None):
        raise AirflowConnectionError("unreachable")

    monkeypatch.setattr(_client.client, "trigger_dag", _fake_trigger)

    with pytest.raises(AirflowConnectionError):
        await dags.trigger_dag({"dag_id": "my_dag"})


@pytest.mark.asyncio
async def test_get_dag_source_no_file_token_skips_source_call(monkeypatch):
    async def _fake_get(dag_id):
        return {"dag_id": dag_id, "is_paused": False}

    async def _fake_get_source(file_token):
        raise AssertionError("get_dag_source must not be called without a file_token")

    monkeypatch.setattr(_client.client, "get_dag", _fake_get)
    monkeypatch.setattr(_client.client, "get_dag_source", _fake_get_source)

    res = await dags.get_dag_source({"dag_id": "my_dag"})

    assert res["success"] is False
    assert res["data"] is None
    assert res["error"] == "file_token not available for this DAG"


@pytest.mark.asyncio
async def test_get_dag_source_with_file_token_calls_source(monkeypatch):
    async def _fake_get(dag_id):
        return {"dag_id": dag_id, "file_token": "token123"}

    async def _fake_get_source(file_token):
        assert file_token == "token123"
        return "from airflow import DAG\n# source"

    monkeypatch.setattr(_client.client, "get_dag", _fake_get)
    monkeypatch.setattr(_client.client, "get_dag_source", _fake_get_source)

    res = await dags.get_dag_source({"dag_id": "my_dag"})

    assert res["success"] is True
    assert res["data"] == "from airflow import DAG\n# source"
    assert res["error"] is None


@pytest.mark.asyncio
async def test_get_dag_source_missing_id():
    with pytest.raises(Exception):
        await dags.get_dag_source({})
