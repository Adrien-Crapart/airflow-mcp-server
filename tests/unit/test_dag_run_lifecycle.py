import pytest

import airflow_mcp_server.airflow_client as _client
from airflow_mcp_server.handlers import dags, tasks
from airflow_mcp_server.airflow_client import AirflowNotFoundError, AirflowConnectionError


# DAG Run Tests
@pytest.mark.asyncio
async def test_get_dag_run_success(monkeypatch):
    async def _fake_get(dag_id, run_id):
        return {"dag_run_id": run_id, "state": "success"}

    monkeypatch.setattr(_client.client, "get_dag_run", _fake_get)
    res = await dags.get_dag_run({"dag_id": "d1", "run_id": "r1"})
    assert res["success"] is True
    assert res["data"]["state"] == "success"


@pytest.mark.asyncio
async def test_get_dag_run_missing_params(monkeypatch):
    async def _fake_get(dag_id, run_id):
        return {"dag_run_id": run_id}

    monkeypatch.setattr(_client.client, "get_dag_run", _fake_get)
    with pytest.raises(ValueError):
        await dags.get_dag_run({"dag_id": "d1"})  # missing run_id


@pytest.mark.asyncio
async def test_get_dag_run_not_found(monkeypatch):
    async def _fake_get(dag_id, run_id):
        raise AirflowNotFoundError("not found")

    monkeypatch.setattr(_client.client, "get_dag_run", _fake_get)
    with pytest.raises(AirflowNotFoundError):
        await dags.get_dag_run({"dag_id": "d1", "run_id": "r1"})


@pytest.mark.asyncio
async def test_get_dag_run_connection_error(monkeypatch):
    async def _fake_get(dag_id, run_id):
        raise AirflowConnectionError("connection failed")

    monkeypatch.setattr(_client.client, "get_dag_run", _fake_get)
    with pytest.raises(AirflowConnectionError):
        await dags.get_dag_run({"dag_id": "d1", "run_id": "r1"})


@pytest.mark.asyncio
async def test_clear_dag_run_success(monkeypatch):
    async def _fake_clear(dag_id, run_id, only_failed=True):
        return {"result": "cleared"}

    monkeypatch.setattr(_client.client, "clear_dag_run", _fake_clear)
    res = await dags.clear_dag_run({"dag_id": "d1", "run_id": "r1", "only_failed": True})
    assert res["success"] is True
    assert res["data"]["result"] == "cleared"


@pytest.mark.asyncio
async def test_clear_dag_run_missing_params(monkeypatch):
    async def _fake_clear(dag_id, run_id, only_failed=True):
        return {"result": "cleared"}

    monkeypatch.setattr(_client.client, "clear_dag_run", _fake_clear)
    with pytest.raises(ValueError):
        await dags.clear_dag_run({"dag_id": "d1"})  # missing run_id


@pytest.mark.asyncio
async def test_clear_dag_run_connection_error(monkeypatch):
    async def _fake_clear(dag_id, run_id, only_failed=True):
        raise AirflowConnectionError("connection failed")

    monkeypatch.setattr(_client.client, "clear_dag_run", _fake_clear)
    with pytest.raises(AirflowConnectionError):
        await dags.clear_dag_run({"dag_id": "d1", "run_id": "r1"})


@pytest.mark.asyncio
async def test_cancel_dag_run_success(monkeypatch):
    async def _fake_delete(dag_id, run_id):
        return {"result": "deleted"}

    monkeypatch.setattr(_client.client, "delete_dag_run", _fake_delete)
    res = await dags.cancel_dag_run({"dag_id": "d1", "run_id": "r1"})
    assert res["success"] is True
    assert res["data"]["result"] == "deleted"


@pytest.mark.asyncio
async def test_cancel_dag_run_not_found(monkeypatch):
    async def _fake_delete(dag_id, run_id):
        raise AirflowNotFoundError("not found")

    monkeypatch.setattr(_client.client, "delete_dag_run", _fake_delete)
    with pytest.raises(AirflowNotFoundError):
        await dags.cancel_dag_run({"dag_id": "d1", "run_id": "r1"})


@pytest.mark.asyncio
async def test_set_dag_run_state_success(monkeypatch):
    async def _fake_update(dag_id, run_id, state):
        return {"state": state}

    monkeypatch.setattr(_client.client, "update_dag_run_state", _fake_update)
    res = await dags.set_dag_run_state({"dag_id": "d1", "run_id": "r1", "state": "success"})
    assert res["success"] is True
    assert res["data"]["state"] == "success"


@pytest.mark.asyncio
async def test_set_dag_run_state_missing_state(monkeypatch):
    async def _fake_update(dag_id, run_id, state):
        return {"state": state}

    monkeypatch.setattr(_client.client, "update_dag_run_state", _fake_update)
    with pytest.raises(ValueError):
        await dags.set_dag_run_state({"dag_id": "d1", "run_id": "r1"})  # missing state


@pytest.mark.asyncio
async def test_set_dag_run_state_connection_error(monkeypatch):
    async def _fake_update(dag_id, run_id, state):
        raise AirflowConnectionError("connection failed")

    monkeypatch.setattr(_client.client, "update_dag_run_state", _fake_update)
    with pytest.raises(AirflowConnectionError):
        await dags.set_dag_run_state({"dag_id": "d1", "run_id": "r1", "state": "success"})


# Task Definition Tests
@pytest.mark.asyncio
async def test_list_tasks_success(monkeypatch):
    async def _fake_list(dag_id):
        return [{"task_id": "t1", "task_type": "PythonOperator"}]

    monkeypatch.setattr(_client.client, "list_tasks", _fake_list)
    res = await tasks.list_tasks({"dag_id": "d1"})
    assert res["success"] is True
    assert isinstance(res["data"], list)
    assert len(res["data"]) == 1


@pytest.mark.asyncio
async def test_list_tasks_missing_dag_id(monkeypatch):
    async def _fake_list(dag_id):
        return []

    monkeypatch.setattr(_client.client, "list_tasks", _fake_list)
    with pytest.raises(ValueError):
        await tasks.list_tasks({})  # missing dag_id


@pytest.mark.asyncio
async def test_list_tasks_not_found(monkeypatch):
    async def _fake_list(dag_id):
        raise AirflowNotFoundError("not found")

    monkeypatch.setattr(_client.client, "list_tasks", _fake_list)
    with pytest.raises(AirflowNotFoundError):
        await tasks.list_tasks({"dag_id": "d1"})


@pytest.mark.asyncio
async def test_get_task_success(monkeypatch):
    async def _fake_get(dag_id, task_id):
        return {"task_id": task_id, "task_type": "PythonOperator"}

    monkeypatch.setattr(_client.client, "get_task", _fake_get)
    res = await tasks.get_task({"dag_id": "d1", "task_id": "t1"})
    assert res["success"] is True
    assert res["data"]["task_id"] == "t1"


@pytest.mark.asyncio
async def test_get_task_missing_params(monkeypatch):
    async def _fake_get(dag_id, task_id):
        return {}

    monkeypatch.setattr(_client.client, "get_task", _fake_get)
    with pytest.raises(ValueError):
        await tasks.get_task({"dag_id": "d1"})  # missing task_id


@pytest.mark.asyncio
async def test_get_task_connection_error(monkeypatch):
    async def _fake_get(dag_id, task_id):
        raise AirflowConnectionError("connection failed")

    monkeypatch.setattr(_client.client, "get_task", _fake_get)
    with pytest.raises(AirflowConnectionError):
        await tasks.get_task({"dag_id": "d1", "task_id": "t1"})


@pytest.mark.asyncio
async def test_set_task_state_success(monkeypatch):
    async def _fake_set(dag_id, run_id, task_id, state):
        return {"state": state}

    monkeypatch.setattr(_client.client, "set_task_instance_state", _fake_set)
    res = await tasks.set_task_state({"dag_id": "d1", "run_id": "r1", "task_id": "t1", "state": "success"})
    assert res["success"] is True
    assert res["data"]["state"] == "success"


@pytest.mark.asyncio
async def test_set_task_state_missing_params(monkeypatch):
    async def _fake_set(dag_id, run_id, task_id, state):
        return {"state": state}

    monkeypatch.setattr(_client.client, "set_task_instance_state", _fake_set)
    with pytest.raises(ValueError):
        await tasks.set_task_state({"dag_id": "d1", "run_id": "r1", "task_id": "t1"})  # missing state


@pytest.mark.asyncio
async def test_set_task_state_connection_error(monkeypatch):
    async def _fake_set(dag_id, run_id, task_id, state):
        raise AirflowConnectionError("connection failed")

    monkeypatch.setattr(_client.client, "set_task_instance_state", _fake_set)
    with pytest.raises(AirflowConnectionError):
        await tasks.set_task_state({"dag_id": "d1", "run_id": "r1", "task_id": "t1", "state": "success"})


@pytest.mark.asyncio
async def test_clear_task_success(monkeypatch):
    async def _fake_clear(dag_id, run_id, task_id):
        return {"result": "cleared"}

    monkeypatch.setattr(_client.client, "clear_task_instance", _fake_clear)
    res = await tasks.clear_task({"dag_id": "d1", "run_id": "r1", "task_id": "t1"})
    assert res["success"] is True
    assert res["data"]["result"] == "cleared"


@pytest.mark.asyncio
async def test_clear_task_missing_params(monkeypatch):
    async def _fake_clear(dag_id, run_id, task_id):
        return {"result": "cleared"}

    monkeypatch.setattr(_client.client, "clear_task_instance", _fake_clear)
    with pytest.raises(ValueError):
        await tasks.clear_task({"dag_id": "d1", "run_id": "r1"})  # missing task_id


@pytest.mark.asyncio
async def test_clear_task_not_found(monkeypatch):
    async def _fake_clear(dag_id, run_id, task_id):
        raise AirflowNotFoundError("not found")

    monkeypatch.setattr(_client.client, "clear_task_instance", _fake_clear)
    with pytest.raises(AirflowNotFoundError):
        await tasks.clear_task({"dag_id": "d1", "run_id": "r1", "task_id": "t1"})
