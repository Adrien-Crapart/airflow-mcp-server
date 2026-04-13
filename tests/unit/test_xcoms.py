import pytest
import airflow_mcp_server.airflow_client as _client
from airflow_mcp_server.airflow_client import (
    AirflowNotFoundError,
    AirflowConnectionError,
    AirflowAuthError,
)
from airflow_mcp_server.handlers import xcoms


@pytest.mark.asyncio
async def test_get_xcom_success(monkeypatch):
    async def _fake_get(dag_id, run_id, task_id, key):
        return {"key": "return_value", "value": 42}

    monkeypatch.setattr(_client.client, "get_xcom", _fake_get)

    res = await xcoms.get_xcom({
        "dag_id": "my_dag",
        "run_id": "run_2024",
        "task_id": "my_task",
        "key": "return_value",
    })

    assert res["success"] is True
    assert res["data"]["key"] == "return_value"
    assert res["data"]["value"] == 42
    assert res["error"] is None


@pytest.mark.asyncio
async def test_get_xcom_missing_params():
    with pytest.raises(Exception):
        await xcoms.get_xcom({})


@pytest.mark.asyncio
async def test_get_xcom_missing_dag_id():
    with pytest.raises(Exception):
        await xcoms.get_xcom({"run_id": "run_1", "task_id": "task_1", "key": "k"})


@pytest.mark.asyncio
async def test_get_xcom_missing_run_id():
    with pytest.raises(Exception):
        await xcoms.get_xcom({"dag_id": "dag_1", "task_id": "task_1", "key": "k"})


@pytest.mark.asyncio
async def test_get_xcom_not_found(monkeypatch):
    async def _fake_get(dag_id, run_id, task_id, key):
        raise AirflowNotFoundError("xcom not found")

    monkeypatch.setattr(_client.client, "get_xcom", _fake_get)

    with pytest.raises(AirflowNotFoundError):
        await xcoms.get_xcom({
            "dag_id": "my_dag",
            "run_id": "run_2024",
            "task_id": "my_task",
            "key": "missing_key",
        })


@pytest.mark.asyncio
async def test_get_xcom_connection_error(monkeypatch):
    async def _fake_get(dag_id, run_id, task_id, key):
        raise AirflowConnectionError("unreachable")

    monkeypatch.setattr(_client.client, "get_xcom", _fake_get)

    with pytest.raises(AirflowConnectionError):
        await xcoms.get_xcom({
            "dag_id": "my_dag",
            "run_id": "run_2024",
            "task_id": "my_task",
            "key": "return_value",
        })


@pytest.mark.asyncio
async def test_get_xcom_auth_error(monkeypatch):
    async def _fake_get(dag_id, run_id, task_id, key):
        raise AirflowAuthError("unauthorized")

    monkeypatch.setattr(_client.client, "get_xcom", _fake_get)

    with pytest.raises(AirflowAuthError):
        await xcoms.get_xcom({
            "dag_id": "my_dag",
            "run_id": "run_2024",
            "task_id": "my_task",
            "key": "return_value",
        })
