import pytest

import airflow_mcp_server.airflow_client as _client
from airflow_mcp_server.handlers import event_logs
from airflow_mcp_server.airflow_client import AirflowNotFoundError, AirflowConnectionError


@pytest.mark.asyncio
async def test_list_event_logs_success(monkeypatch):
    async def _fake_list(limit=100, dag_id=None, event=None):
        return [{"event_id": 1, "event": "trigger", "dag_id": "d1"}]

    monkeypatch.setattr(_client.client, "list_event_logs", _fake_list)
    res = await event_logs.list_event_logs({"limit": 10})
    assert res["success"] is True
    assert isinstance(res["data"], list)
    assert len(res["data"]) == 1


@pytest.mark.asyncio
async def test_list_event_logs_filtered_by_dag(monkeypatch):
    async def _fake_list(limit=100, dag_id=None, event=None):
        if dag_id == "d1":
            return [{"event_id": 1, "event": "trigger", "dag_id": "d1"}]
        return []

    monkeypatch.setattr(_client.client, "list_event_logs", _fake_list)
    res = await event_logs.list_event_logs({"dag_id": "d1"})
    assert res["success"] is True
    assert len(res["data"]) == 1


@pytest.mark.asyncio
async def test_list_event_logs_filtered_by_event(monkeypatch):
    async def _fake_list(limit=100, dag_id=None, event=None):
        if event == "trigger":
            return [{"event_id": 1, "event": "trigger"}]
        return []

    monkeypatch.setattr(_client.client, "list_event_logs", _fake_list)
    res = await event_logs.list_event_logs({"event": "trigger"})
    assert res["success"] is True


@pytest.mark.asyncio
async def test_list_event_logs_empty(monkeypatch):
    async def _fake_list(limit=100, dag_id=None, event=None):
        return []

    monkeypatch.setattr(_client.client, "list_event_logs", _fake_list)
    res = await event_logs.list_event_logs({})
    assert res["success"] is True
    assert res["data"] == []


@pytest.mark.asyncio
async def test_list_event_logs_connection_error(monkeypatch):
    async def _fake_list(limit=100, dag_id=None, event=None):
        raise AirflowConnectionError("connection failed")

    monkeypatch.setattr(_client.client, "list_event_logs", _fake_list)
    with pytest.raises(AirflowConnectionError):
        await event_logs.list_event_logs({})


@pytest.mark.asyncio
async def test_get_event_log_success(monkeypatch):
    async def _fake_get(event_log_id):
        return {"event_id": event_log_id, "event": "trigger", "dag_id": "d1"}

    monkeypatch.setattr(_client.client, "get_event_log", _fake_get)
    res = await event_logs.get_event_log({"event_log_id": 123})
    assert res["success"] is True
    assert res["data"]["event_id"] == 123


@pytest.mark.asyncio
async def test_get_event_log_missing_id(monkeypatch):
    async def _fake_get(event_log_id):
        return {}

    monkeypatch.setattr(_client.client, "get_event_log", _fake_get)
    with pytest.raises(ValueError):
        await event_logs.get_event_log({})  # missing event_log_id


@pytest.mark.asyncio
async def test_get_event_log_not_found(monkeypatch):
    async def _fake_get(event_log_id):
        raise AirflowNotFoundError("not found")

    monkeypatch.setattr(_client.client, "get_event_log", _fake_get)
    with pytest.raises(AirflowNotFoundError):
        await event_logs.get_event_log({"event_log_id": 999})


@pytest.mark.asyncio
async def test_get_event_log_connection_error(monkeypatch):
    async def _fake_get(event_log_id):
        raise AirflowConnectionError("connection failed")

    monkeypatch.setattr(_client.client, "get_event_log", _fake_get)
    with pytest.raises(AirflowConnectionError):
        await event_logs.get_event_log({"event_log_id": 123})
