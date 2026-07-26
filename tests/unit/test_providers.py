import pytest

import airflow_mcp_server.airflow_client as _client
from airflow_mcp_server.airflow_client import AirflowConnectionError
from airflow_mcp_server.handlers import providers


@pytest.mark.asyncio
async def test_list_providers_success(monkeypatch):
    async def _fake_list(limit=100):
        return [
            {"package_name": "apache-airflow-providers-google", "version": "10.0.0"},
            {"package_name": "apache-airflow-providers-http", "version": "4.0.0"},
        ]

    monkeypatch.setattr(_client.client, "list_providers", _fake_list)

    res = await providers.list_providers({})

    assert res["success"] is True
    assert isinstance(res["data"], list)
    assert len(res["data"]) == 2
    assert res["data"][0]["package_name"] == "apache-airflow-providers-google"
    assert res["error"] is None


@pytest.mark.asyncio
async def test_list_providers_connection_error(monkeypatch):
    async def _fake_list(limit=100):
        raise AirflowConnectionError("unreachable")

    monkeypatch.setattr(_client.client, "list_providers", _fake_list)

    with pytest.raises(AirflowConnectionError):
        await providers.list_providers({})


@pytest.mark.asyncio
async def test_list_plugins_success(monkeypatch):
    async def _fake_list(limit=100):
        return [
            {"name": "my_plugin", "source": "my_plugin.py"},
        ]

    monkeypatch.setattr(_client.client, "list_plugins", _fake_list)

    res = await providers.list_plugins({})

    assert res["success"] is True
    assert isinstance(res["data"], list)
    assert res["data"][0]["name"] == "my_plugin"
    assert res["error"] is None


@pytest.mark.asyncio
async def test_list_plugins_connection_error(monkeypatch):
    async def _fake_list(limit=100):
        raise AirflowConnectionError("unreachable")

    monkeypatch.setattr(_client.client, "list_plugins", _fake_list)

    with pytest.raises(AirflowConnectionError):
        await providers.list_plugins({})
