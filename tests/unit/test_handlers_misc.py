import pytest
from airflow_mcp_server.handlers import dags, tasks


@pytest.mark.asyncio
async def test_pause_unpause_dag(monkeypatch):
    async def _fake_pause(dag_id):
        return {"dag_id": dag_id, "is_paused": True}

    async def _fake_unpause(dag_id):
        return {"dag_id": dag_id, "is_paused": False}

    import airflow_mcp_server.airflow_client as _client

    monkeypatch.setattr(_client.client, "pause_dag", _fake_pause)
    monkeypatch.setattr(_client.client, "unpause_dag", _fake_unpause)

    res = await dags.pause_dag({"dag_id": "my_dag"})
    assert res["success"] is True
    assert res["data"]["is_paused"] is True

    res = await dags.unpause_dag({"dag_id": "my_dag"})
    assert res["success"] is True
    assert res["data"]["is_paused"] is False


@pytest.mark.asyncio
async def test_retry_task(monkeypatch):
    async def _fake_retry(dag_id, run_id, task_id):
        return {"dag_id": dag_id, "run_id": run_id, "task_id": task_id, "state": "queued"}

    import airflow_mcp_server.airflow_client as _client
    monkeypatch.setattr(_client.client, "retry_task", _fake_retry)

    res = await tasks.retry_task({"dag_id": "d", "run_id": "r", "task_id": "t"})
    assert res["success"] is True
    assert res["data"]["state"] == "queued"
