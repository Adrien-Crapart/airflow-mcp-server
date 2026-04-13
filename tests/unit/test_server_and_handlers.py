import pytest

from airflow_mcp_server.server import create_app, load_tools
import airflow_mcp_server.airflow_client as _client
from airflow_mcp_server.handlers import connections, logs, tasks


def test_load_tools_keys():
    tools = load_tools()
    # basic expectation: common tools are present
    assert "airflow_health_check" in tools
    assert "airflow_dag_list" in tools


def test_models_toolresponse_import():
    # ensure models module and ToolResponse type are importable
    from airflow_mcp_server.models import ToolResponse

    tr: ToolResponse = {"success": True, "data": None, "error": None}
    assert tr["success"] is True


@pytest.mark.asyncio
async def test_create_connection_handler(monkeypatch):
    async def _fake_create(conn_id, conn_type, host, login=None, password=None, port=None, extra=None):
        return {"connection_id": conn_id}

    monkeypatch.setattr(_client.client, "create_connection", _fake_create)

    res = await connections.create_connection({"conn_id": "c1", "type": "http", "host": "h"})
    assert res["success"] is True
    assert res["data"]["connection_id"] == "c1"


@pytest.mark.asyncio
async def test_fetch_task_logs_and_list_instances(monkeypatch):
    async def _fake_logs(dag_id, run_id, task_id, try_number=1):
        return "logs content"

    async def _fake_instances(dag_id, run_id):
        return [{"task_id": "t1"}]

    monkeypatch.setattr(_client.client, "get_task_logs", _fake_logs)
    monkeypatch.setattr(_client.client, "get_task_instances", _fake_instances)

    res = await logs.fetch_task_logs({"dag_id": "d", "task_id": "t", "run_id": "r"})
    assert res["success"] is True
    assert res["data"] == "logs content"

    res2 = await tasks.list_task_instances({"dag_id": "d", "run_id": "r"})
    assert res2["success"] is True
    assert isinstance(res2["data"], list)
