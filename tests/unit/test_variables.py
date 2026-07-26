import pytest
import airflow_mcp_server.airflow_client as _client
from airflow_mcp_server.airflow_client import (
    AirflowNotFoundError,
    AirflowConnectionError,
    AirflowAuthError,
)
from airflow_mcp_server.handlers import variables


@pytest.mark.asyncio
async def test_list_variables(monkeypatch):
    async def _fake_list(limit=100):
        return [{"key": "k", "value": "v"}]

    monkeypatch.setattr(_client.client, "list_variables", _fake_list)

    res = await variables.list_variables({})

    assert res["success"] is True
    assert isinstance(res["data"], list)
    assert res["error"] is None


@pytest.mark.asyncio
async def test_list_variables_masks_sensitive_variable_values(monkeypatch):
    async def _fake_list(limit=100):
        return [
            {"key": "plain_var", "value": "visible"},
            {"key": "secret_token", "value": "very-secret"},
        ]

    monkeypatch.setattr(_client.client, "list_variables", _fake_list)

    res = await variables.list_variables({})

    assert res["success"] is True
    assert res["data"][0]["value"] == "visible"
    assert res["data"][1]["value"] == "***MASKED***"


@pytest.mark.asyncio
async def test_list_variables_empty(monkeypatch):
    async def _fake_list(limit=100):
        return []

    monkeypatch.setattr(_client.client, "list_variables", _fake_list)

    res = await variables.list_variables({})

    assert res["success"] is True
    assert res["data"] == []


@pytest.mark.asyncio
async def test_list_variables_connection_error(monkeypatch):
    async def _fake_list(limit=100):
        raise AirflowConnectionError("unreachable")

    monkeypatch.setattr(_client.client, "list_variables", _fake_list)

    with pytest.raises(AirflowConnectionError):
        await variables.list_variables({})


@pytest.mark.asyncio
async def test_get_variable_success(monkeypatch):
    async def _fake_get(key):
        return {"key": "my_key", "value": "hello"}

    monkeypatch.setattr(_client.client, "get_variable", _fake_get)

    res = await variables.get_variable({"key": "my_key"})

    assert res["success"] is True
    assert res["data"]["key"] == "my_key"
    assert res["data"]["value"] == "hello"
    assert res["error"] is None


@pytest.mark.asyncio
async def test_get_variable_masks_sensitive_variable_value(monkeypatch):
    async def _fake_get(key):
        return {"key": key, "value": "super-secret"}

    monkeypatch.setattr(_client.client, "get_variable", _fake_get)

    res = await variables.get_variable({"key": "api_token"})

    assert res["success"] is True
    assert res["data"]["key"] == "api_token"
    assert res["data"]["value"] == "***MASKED***"


@pytest.mark.asyncio
async def test_get_variable_missing_key():
    with pytest.raises(Exception):
        await variables.get_variable({})


@pytest.mark.asyncio
async def test_get_variable_not_found(monkeypatch):
    async def _fake_get(key):
        raise AirflowNotFoundError("variable not found")

    monkeypatch.setattr(_client.client, "get_variable", _fake_get)

    with pytest.raises(AirflowNotFoundError):
        await variables.get_variable({"key": "missing"})


@pytest.mark.asyncio
async def test_get_variable_connection_error(monkeypatch):
    async def _fake_get(key):
        raise AirflowConnectionError("unreachable")

    monkeypatch.setattr(_client.client, "get_variable", _fake_get)

    with pytest.raises(AirflowConnectionError):
        await variables.get_variable({"key": "some_key"})


@pytest.mark.asyncio
async def test_get_variable_auth_error(monkeypatch):
    async def _fake_get(key):
        raise AirflowAuthError("unauthorized")

    monkeypatch.setattr(_client.client, "get_variable", _fake_get)

    with pytest.raises(AirflowAuthError):
        await variables.get_variable({"key": "some_key"})


@pytest.mark.asyncio
async def test_set_variable_success(monkeypatch):
    async def _fake_set(key, value):
        return {"key": key, "value": value}

    monkeypatch.setattr(_client.client, "set_variable", _fake_set)

    res = await variables.set_variable({"key": "new_key", "value": "new_value"})

    assert res["success"] is True
    assert res["data"]["key"] == "new_key"
    assert res["data"]["value"] == "new_value"
    assert res["error"] is None


@pytest.mark.asyncio
async def test_set_variable_masks_sensitive_variable_value(monkeypatch):
    async def _fake_set(key, value):
        return {"key": key, "value": value}

    monkeypatch.setattr(_client.client, "set_variable", _fake_set)

    res = await variables.set_variable({"key": "db_password", "value": "p@ss"})

    assert res["success"] is True
    assert res["data"]["key"] == "db_password"
    assert res["data"]["value"] == "***MASKED***"


@pytest.mark.asyncio
async def test_set_variable_missing_params():
    with pytest.raises(Exception):
        await variables.set_variable({})


@pytest.mark.asyncio
async def test_set_variable_missing_value():
    with pytest.raises(Exception):
        await variables.set_variable({"key": "only_key"})


@pytest.mark.asyncio
async def test_set_variable_connection_error(monkeypatch):
    async def _fake_set(key, value):
        raise AirflowConnectionError("unreachable")

    monkeypatch.setattr(_client.client, "set_variable", _fake_set)

    with pytest.raises(AirflowConnectionError):
        await variables.set_variable({"key": "k", "value": "v"})


@pytest.mark.asyncio
async def test_delete_variable_success(monkeypatch):
    async def _fake_delete(key):
        return None

    monkeypatch.setattr(_client.client, "delete_variable", _fake_delete)

    res = await variables.delete_variable({"key": "old_key"})

    assert res["success"] is True
    assert res["error"] is None


@pytest.mark.asyncio
async def test_delete_variable_not_found(monkeypatch):
    async def _fake_delete(key):
        raise AirflowNotFoundError("variable not found")

    monkeypatch.setattr(_client.client, "delete_variable", _fake_delete)

    with pytest.raises(AirflowNotFoundError):
        await variables.delete_variable({"key": "missing"})


@pytest.mark.asyncio
async def test_delete_variable_missing_key():
    with pytest.raises(Exception):
        await variables.delete_variable({})


@pytest.mark.asyncio
async def test_delete_variable_connection_error(monkeypatch):
    async def _fake_delete(key):
        raise AirflowConnectionError("unreachable")

    monkeypatch.setattr(_client.client, "delete_variable", _fake_delete)

    with pytest.raises(AirflowConnectionError):
        await variables.delete_variable({"key": "k"})
