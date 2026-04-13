import pytest
import airflow_mcp_server.airflow_client as _client
from airflow_mcp_server.airflow_client import (
    AirflowNotFoundError,
    AirflowConnectionError,
    AirflowAuthError,
)
from airflow_mcp_server.handlers import pools


@pytest.mark.asyncio
async def test_list_pools(monkeypatch):
    async def _fake_list(limit=100):
        return [{"name": "default_pool", "slots": 128}]

    monkeypatch.setattr(_client.client, "list_pools", _fake_list)

    res = await pools.list_pools({})

    assert res["success"] is True
    assert isinstance(res["data"], list)
    assert res["error"] is None


@pytest.mark.asyncio
async def test_list_pools_empty(monkeypatch):
    async def _fake_list(limit=100):
        return []

    monkeypatch.setattr(_client.client, "list_pools", _fake_list)

    res = await pools.list_pools({})

    assert res["success"] is True
    assert res["data"] == []


@pytest.mark.asyncio
async def test_list_pools_connection_error(monkeypatch):
    async def _fake_list(limit=100):
        raise AirflowConnectionError("unreachable")

    monkeypatch.setattr(_client.client, "list_pools", _fake_list)

    with pytest.raises(AirflowConnectionError):
        await pools.list_pools({})


@pytest.mark.asyncio
async def test_get_pool_success(monkeypatch):
    async def _fake_get(pool_name):
        return {"name": "default_pool", "slots": 16}

    monkeypatch.setattr(_client.client, "get_pool", _fake_get)

    res = await pools.get_pool({"pool_name": "default_pool"})

    assert res["success"] is True
    assert res["data"]["name"] == "default_pool"
    assert res["data"]["slots"] == 16
    assert res["error"] is None


@pytest.mark.asyncio
async def test_get_pool_missing_name():
    with pytest.raises(Exception):
        await pools.get_pool({})


@pytest.mark.asyncio
async def test_get_pool_not_found(monkeypatch):
    async def _fake_get(pool_name):
        raise AirflowNotFoundError("pool not found")

    monkeypatch.setattr(_client.client, "get_pool", _fake_get)

    with pytest.raises(AirflowNotFoundError):
        await pools.get_pool({"pool_name": "nonexistent"})


@pytest.mark.asyncio
async def test_get_pool_connection_error(monkeypatch):
    async def _fake_get(pool_name):
        raise AirflowConnectionError("unreachable")

    monkeypatch.setattr(_client.client, "get_pool", _fake_get)

    with pytest.raises(AirflowConnectionError):
        await pools.get_pool({"pool_name": "default_pool"})


@pytest.mark.asyncio
async def test_get_pool_auth_error(monkeypatch):
    async def _fake_get(pool_name):
        raise AirflowAuthError("unauthorized")

    monkeypatch.setattr(_client.client, "get_pool", _fake_get)

    with pytest.raises(AirflowAuthError):
        await pools.get_pool({"pool_name": "default_pool"})


@pytest.mark.asyncio
async def test_set_pool_success(monkeypatch):
    async def _fake_set(pool_name, slots, description=None):
        return {"name": pool_name, "slots": slots, "description": description}

    monkeypatch.setattr(_client.client, "set_pool", _fake_set)

    res = await pools.set_pool({"pool_name": "my_pool", "slots": 4})

    assert res["success"] is True
    assert res["data"]["name"] == "my_pool"
    assert res["data"]["slots"] == 4
    assert res["error"] is None


@pytest.mark.asyncio
async def test_set_pool_with_description(monkeypatch):
    async def _fake_set(pool_name, slots, description=None):
        return {"name": pool_name, "slots": slots, "description": description}

    monkeypatch.setattr(_client.client, "set_pool", _fake_set)

    res = await pools.set_pool({"pool_name": "my_pool", "slots": 8, "description": "test pool"})

    assert res["success"] is True
    assert res["data"]["description"] == "test pool"


@pytest.mark.asyncio
async def test_set_pool_missing_params():
    with pytest.raises(Exception):
        await pools.set_pool({})


@pytest.mark.asyncio
async def test_set_pool_missing_slots():
    with pytest.raises(Exception):
        await pools.set_pool({"pool_name": "my_pool"})


@pytest.mark.asyncio
async def test_set_pool_missing_pool_name():
    with pytest.raises(Exception):
        await pools.set_pool({"slots": 4})


@pytest.mark.asyncio
async def test_set_pool_connection_error(monkeypatch):
    async def _fake_set(pool_name, slots, description=None):
        raise AirflowConnectionError("unreachable")

    monkeypatch.setattr(_client.client, "set_pool", _fake_set)

    with pytest.raises(AirflowConnectionError):
        await pools.set_pool({"pool_name": "my_pool", "slots": 4})
