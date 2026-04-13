import pytest
from airflow_mcp_server.handlers import dags


@pytest.mark.asyncio
async def test_list_dags(monkeypatch):
    async def _fake_list_dags(limit=100, offset=0):
        return []

    import airflow_mcp_server.airflow_client as _client
    monkeypatch.setattr(_client.client, "list_dags", _fake_list_dags)

    res = await dags.list_dags({})
    assert res["success"] is True
    assert isinstance(res["data"], list)


@pytest.mark.asyncio
async def test_trigger_dag_missing_id():
    with pytest.raises(ValueError):
        await dags.trigger_dag({})
