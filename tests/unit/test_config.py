import pytest

import airflow_mcp_server.airflow_client as _client
from airflow_mcp_server.handlers import config
from airflow_mcp_server.airflow_client import AirflowPermissionError, AirflowConnectionError
from airflow_mcp_server.config import cfg


@pytest.mark.asyncio
async def test_get_config_disabled_by_policy(monkeypatch):
    monkeypatch.setattr(cfg, "MCP_ENABLE_ADMIN_ENDPOINTS", False)

    with pytest.raises(AirflowPermissionError, match="disabled"):
        await config.get_config({})


@pytest.mark.asyncio
async def test_get_config_success(monkeypatch):
    monkeypatch.setattr(cfg, "MCP_ENABLE_ADMIN_ENDPOINTS", True)

    async def _fake_get_config(section=None):
        if section == "core":
            return {"dags_folder": "/opt/airflow/dags", "parallelism": 32}
        return {"core": {"dags_folder": "/opt/airflow/dags"}, "scheduler": {}}

    monkeypatch.setattr(_client.client, "get_config", _fake_get_config)
    res = await config.get_config({})
    assert res["success"] is True
    assert isinstance(res["data"], dict)


@pytest.mark.asyncio
async def test_get_config_filtered_section(monkeypatch):
    monkeypatch.setattr(cfg, "MCP_ENABLE_ADMIN_ENDPOINTS", True)

    async def _fake_get_config(section=None):
        if section == "core":
            return {"dags_folder": "/opt/airflow/dags", "parallelism": 32}
        return {}

    monkeypatch.setattr(_client.client, "get_config", _fake_get_config)
    res = await config.get_config({"section": "core"})
    assert res["success"] is True


@pytest.mark.asyncio
async def test_get_config_masks_sensitive_values(monkeypatch):
    monkeypatch.setattr(cfg, "MCP_ENABLE_ADMIN_ENDPOINTS", True)

    async def _fake_get_config(section=None):
        return {"core": {"fernet_key": "abc", "parallelism": 32}}

    monkeypatch.setattr(_client.client, "get_config", _fake_get_config)
    res = await config.get_config({})

    assert res["success"] is True
    assert res["data"]["core"]["fernet_key"] == "***MASKED***"


@pytest.mark.asyncio
async def test_get_config_permission_error(monkeypatch):
    monkeypatch.setattr(cfg, "MCP_ENABLE_ADMIN_ENDPOINTS", True)

    async def _fake_get_config(section=None):
        raise AirflowPermissionError("forbidden")

    monkeypatch.setattr(_client.client, "get_config", _fake_get_config)
    with pytest.raises(AirflowPermissionError):
        await config.get_config({})


@pytest.mark.asyncio
async def test_get_config_connection_error(monkeypatch):
    monkeypatch.setattr(cfg, "MCP_ENABLE_ADMIN_ENDPOINTS", True)

    async def _fake_get_config(section=None):
        raise AirflowConnectionError("connection failed")

    monkeypatch.setattr(_client.client, "get_config", _fake_get_config)
    with pytest.raises(AirflowConnectionError):
        await config.get_config({})


@pytest.mark.asyncio
async def test_get_version_success(monkeypatch):
    async def _fake_get_version():
        return {"version": "2.5.1", "git_version": "abc123"}

    monkeypatch.setattr(_client.client, "get_version", _fake_get_version)
    res = await config.get_version({})
    assert res["success"] is True
    assert res["data"]["version"] == "2.5.1"


@pytest.mark.asyncio
async def test_get_version_connection_error(monkeypatch):
    async def _fake_get_version():
        raise AirflowConnectionError("connection failed")

    monkeypatch.setattr(_client.client, "get_version", _fake_get_version)
    with pytest.raises(AirflowConnectionError):
        await config.get_version({})


@pytest.mark.asyncio
async def test_list_dag_warnings_success(monkeypatch):
    async def _fake_list(dag_id=None, limit=100):
        return [{"dag_id": "d1", "warning_type": "sla_miss"}]

    monkeypatch.setattr(_client.client, "list_dag_warnings", _fake_list)
    res = await config.list_dag_warnings({})
    assert res["success"] is True
    assert isinstance(res["data"], list)


@pytest.mark.asyncio
async def test_list_dag_warnings_filtered_by_dag(monkeypatch):
    async def _fake_list(dag_id=None, limit=100):
        if dag_id == "d1":
            return [{"dag_id": "d1", "warning_type": "sla_miss"}]
        return []

    monkeypatch.setattr(_client.client, "list_dag_warnings", _fake_list)
    res = await config.list_dag_warnings({"dag_id": "d1"})
    assert res["success"] is True
    assert len(res["data"]) == 1


@pytest.mark.asyncio
async def test_list_dag_warnings_empty(monkeypatch):
    async def _fake_list(dag_id=None, limit=100):
        return []

    monkeypatch.setattr(_client.client, "list_dag_warnings", _fake_list)
    res = await config.list_dag_warnings({})
    assert res["success"] is True
    assert res["data"] == []


@pytest.mark.asyncio
async def test_list_dag_warnings_connection_error(monkeypatch):
    async def _fake_list(dag_id=None, limit=100):
        raise AirflowConnectionError("connection failed")

    monkeypatch.setattr(_client.client, "list_dag_warnings", _fake_list)
    with pytest.raises(AirflowConnectionError):
        await config.list_dag_warnings({})
