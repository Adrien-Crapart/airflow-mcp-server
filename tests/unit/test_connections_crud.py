import pytest
import airflow_mcp_server.airflow_client as _client
from airflow_mcp_server.airflow_client import (
    AirflowNotFoundError,
    AirflowConnectionError,
    AirflowAuthError,
)
from airflow_mcp_server.handlers import connections


@pytest.mark.asyncio
async def test_list_connections_success(monkeypatch):
    async def _fake_list(limit=100):
        return [
            {"conn_id": "postgres_default", "conn_type": "postgres"},
            {"conn_id": "http_default", "conn_type": "http"},
        ]

    monkeypatch.setattr(_client.client, "list_connections", _fake_list)

    res = await connections.list_connections({})

    assert res["success"] is True
    assert isinstance(res["data"], list)
    assert len(res["data"]) == 2
    assert res["error"] is None


@pytest.mark.asyncio
async def test_list_connections_empty(monkeypatch):
    async def _fake_list(limit=100):
        return []

    monkeypatch.setattr(_client.client, "list_connections", _fake_list)

    res = await connections.list_connections({})

    assert res["success"] is True
    assert res["data"] == []


@pytest.mark.asyncio
async def test_list_connections_connection_error(monkeypatch):
    async def _fake_list(limit=100):
        raise AirflowConnectionError("unreachable")

    monkeypatch.setattr(_client.client, "list_connections", _fake_list)

    with pytest.raises(AirflowConnectionError):
        await connections.list_connections({})


@pytest.mark.asyncio
async def test_get_connection_success(monkeypatch):
    async def _fake_get(conn_id):
        return {"conn_id": "postgres_default", "conn_type": "postgres", "host": "localhost"}

    monkeypatch.setattr(_client.client, "get_connection", _fake_get)

    res = await connections.get_connection({"conn_id": "postgres_default"})

    assert res["success"] is True
    assert res["data"]["conn_id"] == "postgres_default"
    assert res["data"]["conn_type"] == "postgres"
    assert res["error"] is None


@pytest.mark.asyncio
async def test_get_connection_missing_conn_id():
    with pytest.raises(Exception):
        await connections.get_connection({})


@pytest.mark.asyncio
async def test_get_connection_not_found(monkeypatch):
    async def _fake_get(conn_id):
        raise AirflowNotFoundError("connection not found")

    monkeypatch.setattr(_client.client, "get_connection", _fake_get)

    with pytest.raises(AirflowNotFoundError):
        await connections.get_connection({"conn_id": "nonexistent"})


@pytest.mark.asyncio
async def test_get_connection_connection_error(monkeypatch):
    async def _fake_get(conn_id):
        raise AirflowConnectionError("unreachable")

    monkeypatch.setattr(_client.client, "get_connection", _fake_get)

    with pytest.raises(AirflowConnectionError):
        await connections.get_connection({"conn_id": "postgres_default"})


@pytest.mark.asyncio
async def test_get_connection_auth_error(monkeypatch):
    async def _fake_get(conn_id):
        raise AirflowAuthError("unauthorized")

    monkeypatch.setattr(_client.client, "get_connection", _fake_get)

    with pytest.raises(AirflowAuthError):
        await connections.get_connection({"conn_id": "postgres_default"})


@pytest.mark.asyncio
async def test_delete_connection_success(monkeypatch):
    async def _fake_delete(conn_id):
        return None

    monkeypatch.setattr(_client.client, "delete_connection", _fake_delete)

    res = await connections.delete_connection({"conn_id": "old_conn"})

    assert res["success"] is True
    assert res["error"] is None


@pytest.mark.asyncio
async def test_delete_connection_not_found(monkeypatch):
    async def _fake_delete(conn_id):
        raise AirflowNotFoundError("connection not found")

    monkeypatch.setattr(_client.client, "delete_connection", _fake_delete)

    with pytest.raises(AirflowNotFoundError):
        await connections.delete_connection({"conn_id": "nonexistent"})


@pytest.mark.asyncio
async def test_delete_connection_missing_conn_id():
    with pytest.raises(Exception):
        await connections.delete_connection({})


@pytest.mark.asyncio
async def test_delete_connection_connection_error(monkeypatch):
    async def _fake_delete(conn_id):
        raise AirflowConnectionError("unreachable")

    monkeypatch.setattr(_client.client, "delete_connection", _fake_delete)

    with pytest.raises(AirflowConnectionError):
        await connections.delete_connection({"conn_id": "some_conn"})
