import pytest

from airflow_mcp_server.server import create_app, load_tools
import airflow_mcp_server.airflow_client as _client
from airflow_mcp_server.handlers import connections, logs, tasks, discovery


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


@pytest.mark.asyncio
async def test_list_tools_has_input_schema():
    """Ensure every tool in list_tools response has input_schema."""
    res = await discovery.list_tools({})
    assert res["success"] is True
    tools = res["data"]
    assert len(tools) > 0

    for tool in tools:
        assert "input_schema" in tool, f"Tool {tool.get('tool_name')} missing input_schema"
        assert isinstance(tool["input_schema"], dict), f"Tool {tool.get('tool_name')} input_schema not a dict"
        assert "type" in tool["input_schema"], f"Tool {tool.get('tool_name')} input_schema missing 'type'"


@pytest.mark.asyncio
async def test_list_tools_has_category():
    """Ensure every tool has a category."""
    res = await discovery.list_tools({})
    assert res["success"] is True
    tools = res["data"]

    for tool in tools:
        assert "category" in tool, f"Tool {tool.get('tool_name')} missing category"
        assert isinstance(tool["category"], str), f"Tool {tool.get('tool_name')} category not a string"
        assert len(tool["category"]) > 0, f"Tool {tool.get('tool_name')} has empty category"


@pytest.mark.asyncio
async def test_list_tools_read_only_flag():
    """Ensure read_only flag is set correctly."""
    res = await discovery.list_tools({})
    assert res["success"] is True
    tools = res["data"]

    # Check a few known read-only tools
    read_only_tools = [t for t in tools if t["tool_name"] in ["airflow_dag_list", "airflow_dag_get", "airflow_task_logs"]]
    for tool in read_only_tools:
        assert tool["read_only"] is True, f"Tool {tool['tool_name']} should be read-only"

    # Check a few known write tools
    write_tools = [t for t in tools if t["tool_name"] in ["airflow_dag_trigger", "airflow_variable_set"]]
    for tool in write_tools:
        assert tool["read_only"] is False, f"Tool {tool['tool_name']} should not be read-only"


@pytest.mark.asyncio
async def test_list_tools_has_examples():
    """Ensure every tool has at least one example."""
    res = await discovery.list_tools({})
    assert res["success"] is True
    tools = res["data"]

    for tool in tools:
        assert "examples" in tool, f"Tool {tool.get('tool_name')} missing examples"
        assert isinstance(tool["examples"], list), f"Tool {tool.get('tool_name')} examples not a list"
        assert len(tool["examples"]) > 0, f"Tool {tool.get('tool_name')} has no examples"


@pytest.mark.asyncio
async def test_list_tools_has_description():
    """Ensure every tool has a description."""
    res = await discovery.list_tools({})
    assert res["success"] is True
    tools = res["data"]

    for tool in tools:
        assert "description" in tool, f"Tool {tool.get('tool_name')} missing description"
        assert isinstance(tool["description"], str), f"Tool {tool.get('tool_name')} description not a string"


@pytest.mark.asyncio
async def test_get_tool_returns_full_schema():
    """Test that get_tool returns full schema for a single tool."""
    res = await discovery.get_tool({"tool_name": "airflow_dag_list"})
    assert res["success"] is True

    tool = res["data"]
    assert tool["tool_name"] == "airflow_dag_list"
    assert "input_schema" in tool
    assert "category" in tool
    assert tool["category"] == "dag"
    assert "read_only" in tool
    assert tool["read_only"] is True
    assert "examples" in tool
    assert "description" in tool


@pytest.mark.asyncio
async def test_get_tool_nonexistent():
    """Test that get_tool raises error for nonexistent tool."""
    with pytest.raises(ValueError, match="Tool .* not found"):
        await discovery.get_tool({"tool_name": "nonexistent_tool"})
