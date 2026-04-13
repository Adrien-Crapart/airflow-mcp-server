import pytest

from airflow_mcp_server.airflow_client import AirflowClient, AirflowNotFoundError


@pytest.mark.asyncio
async def test_get_dag_not_found(monkeypatch):
    client = AirflowClient(base_url="http://fake")

    async def _raise(*args, **kwargs):
        raise AirflowNotFoundError("not found")

    monkeypatch.setattr(client, "_request", _raise)

    with pytest.raises(AirflowNotFoundError):
        await client.get_dag("missing")
