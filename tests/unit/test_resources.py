import json
import pytest

import airflow_mcp_server.airflow_client as _client
from airflow_mcp_server.airflow_client import AirflowPermissionError
from airflow_mcp_server.config import cfg
from airflow_mcp_server.handlers import resources


@pytest.mark.asyncio
async def test_version_resource_returns_json(monkeypatch):
    async def _fake_get_version():
        return {"version": "2.5.1", "git_version": "abc123"}

    monkeypatch.setattr(_client.client, "get_version", _fake_get_version)
    result = await resources.get_version_resource()
    assert isinstance(result, str)
    data = json.loads(result)
    assert data["version"] == "2.5.1"


@pytest.mark.asyncio
async def test_config_resource_returns_json(monkeypatch):
    monkeypatch.setattr(cfg, "MCP_ENABLE_ADMIN_ENDPOINTS", True)

    async def _fake_get_config(section=None):
        return {"core": {"dags_folder": "/opt/airflow/dags"}, "scheduler": {}}

    monkeypatch.setattr(_client.client, "get_config", _fake_get_config)
    result = await resources.get_config_resource()
    assert isinstance(result, str)
    data = json.loads(result)
    assert "core" in data


@pytest.mark.asyncio
async def test_config_resource_disabled_by_policy(monkeypatch):
    monkeypatch.setattr(cfg, "MCP_ENABLE_ADMIN_ENDPOINTS", False)

    with pytest.raises(AirflowPermissionError, match="disabled"):
        await resources.get_config_resource()


@pytest.mark.asyncio
async def test_config_resource_masks_sensitive_keys(monkeypatch):
    monkeypatch.setattr(cfg, "MCP_ENABLE_ADMIN_ENDPOINTS", True)

    async def _fake_get_config(section=None):
        return {
            "core": {"dags_folder": "/opt/airflow/dags", "fernet_key": "abc"},
            "smtp": {"smtp_password": "secret"},
            "api": {"api_key": "k"},
        }

    monkeypatch.setattr(_client.client, "get_config", _fake_get_config)
    result = await resources.get_config_resource()
    data = json.loads(result)

    assert data["core"]["fernet_key"] == "***MASKED***"
    assert data["smtp"]["smtp_password"] == "***MASKED***"
    assert data["api"]["api_key"] == "***MASKED***"


@pytest.mark.asyncio
async def test_dag_resource_returns_metadata(monkeypatch):
    async def _fake_get_dag(dag_id):
        return {"dag_id": dag_id, "is_paused": False, "owner": "airflow"}

    monkeypatch.setattr(_client.client, "get_dag", _fake_get_dag)
    result = await resources.get_dag_resource("my_etl_dag")
    assert isinstance(result, str)
    data = json.loads(result)
    assert data["dag_id"] == "my_etl_dag"


@pytest.mark.asyncio
async def test_dag_source_resource_returns_source(monkeypatch):
    async def _fake_get_dag(dag_id):
        return {"dag_id": dag_id, "file_token": "token123"}

    async def _fake_get_dag_source(file_token):
        return "from airflow import DAG\n# Source code"

    monkeypatch.setattr(_client.client, "get_dag", _fake_get_dag)
    monkeypatch.setattr(_client.client, "get_dag_source", _fake_get_dag_source)
    result = await resources.get_dag_source_resource("my_etl_dag")
    assert "from airflow import DAG" in result


@pytest.mark.asyncio
async def test_dag_source_resource_no_file_token(monkeypatch):
    async def _fake_get_dag(dag_id):
        return {"dag_id": dag_id}

    monkeypatch.setattr(_client.client, "get_dag", _fake_get_dag)
    result = await resources.get_dag_source_resource("my_etl_dag")
    assert "Source not available" in result


@pytest.mark.asyncio
async def test_task_log_resource_returns_text(monkeypatch):
    async def _fake_get_task_logs(dag_id, run_id, task_id, try_number=1):
        return "Log line 1\nLog line 2\n"

    monkeypatch.setattr(_client.client, "get_task_logs", _fake_get_task_logs)
    result = await resources.get_task_log_resource("my_dag", "run1", "task1")
    assert "Log line 1" in result


@pytest.mark.asyncio
async def test_variable_resource_returns_value(monkeypatch):
    async def _fake_get_variable(key):
        return {"key": key, "value": "my_value"}

    monkeypatch.setattr(_client.client, "get_variable", _fake_get_variable)
    result = await resources.get_variable_resource("my_var")
    assert isinstance(result, str)
    data = json.loads(result)
    assert data["value"] == "my_value"


@pytest.mark.asyncio
async def test_variable_resource_masks_sensitive_keys(monkeypatch):
    async def _fake_get_variable(key):
        return {"key": key, "value": "super_secret"}

    monkeypatch.setattr(_client.client, "get_variable", _fake_get_variable)
    result = await resources.get_variable_resource("db_password")
    data = json.loads(result)
    assert data["value"] == "***MASKED***"


@pytest.mark.asyncio
async def test_variable_resource_masks_secret_token(monkeypatch):
    async def _fake_get_variable(key):
        return {"key": key, "value": "secret_value"}

    monkeypatch.setattr(_client.client, "get_variable", _fake_get_variable)
    result = await resources.get_variable_resource("api_token")
    data = json.loads(result)
    assert data["value"] == "***MASKED***"


@pytest.mark.asyncio
async def test_variable_resource_masks_access_key(monkeypatch):
    async def _fake_get_variable(key):
        return {"key": key, "value": "access_secret"}

    monkeypatch.setattr(_client.client, "get_variable", _fake_get_variable)
    result = await resources.get_variable_resource("aws_access_key")
    data = json.loads(result)
    assert data["value"] == "***MASKED***"


@pytest.mark.asyncio
async def test_variable_resource_masks_private_key(monkeypatch):
    async def _fake_get_variable(key):
        return {"key": key, "value": "private_value"}

    monkeypatch.setattr(_client.client, "get_variable", _fake_get_variable)
    result = await resources.get_variable_resource("private_key")
    data = json.loads(result)
    assert data["value"] == "***MASKED***"


@pytest.mark.asyncio
async def test_providers_resource_returns_json(monkeypatch):
    async def _fake_list_providers(limit=100):
        return [{"package_name": "apache-airflow-providers-google", "version": "10.0.0"}]

    monkeypatch.setattr(_client.client, "list_providers", _fake_list_providers)
    result = await resources.get_providers_resource()
    assert isinstance(result, str)
    data = json.loads(result)
    assert isinstance(data, list)
    assert len(data) > 0


def test_register_all_swallows_registration_errors():
    """If mcp.resource(...) raises, register_all must catch it and not propagate."""

    class FakeMcp:
        def resource(self, *args, **kwargs):
            raise RuntimeError("registration failed")

    # Should not raise despite every mcp.resource(...) call failing.
    resources.register_all(FakeMcp())
