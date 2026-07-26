import importlib
import sys

import pytest

from airflow_mcp_server.handlers import discovery

# Capture the real, unpatched import_module before any test monkeypatches
# `discovery.importlib.import_module` (it's the same module object as
# `importlib`, so patching one patches the other).
_real_import_module = importlib.import_module


@pytest.mark.asyncio
async def test_list_tools_skips_broken_module(monkeypatch):
    """A submodule that fails to import should be skipped, not crash discovery."""
    broken_name = "airflow_mcp_server.handlers.dags"

    def _flaky_import(name, *args, **kwargs):
        if name == broken_name:
            raise ImportError("simulated broken module")
        return _real_import_module(name, *args, **kwargs)

    monkeypatch.setattr(discovery.importlib, "import_module", _flaky_import)

    res = await discovery.list_tools({})

    assert res["success"] is True
    assert isinstance(res["data"], list)
    # Tools from the broken module must not be present.
    tool_names = {t["tool_name"] for t in res["data"]}
    assert "airflow_dag_list" not in tool_names
    # Tools from other, healthy modules should still be discovered.
    assert "airflow_health_check" in tool_names


@pytest.mark.asyncio
async def test_get_tool_skips_broken_module_and_finds_target(monkeypatch):
    """get_tool should keep scanning past a module that fails to import."""
    broken_name = "airflow_mcp_server.handlers.dags"

    def _flaky_import(name, *args, **kwargs):
        if name == broken_name:
            raise ImportError("simulated broken module")
        return _real_import_module(name, *args, **kwargs)

    monkeypatch.setattr(discovery.importlib, "import_module", _flaky_import)

    res = await discovery.get_tool({"tool_name": "airflow_health_check"})

    assert res["success"] is True
    assert res["data"]["tool_name"] == "airflow_health_check"


@pytest.mark.asyncio
async def test_get_tool_missing_from_broken_module_raises(monkeypatch):
    """If the requested tool only lives in the broken module, it must not be found."""
    broken_name = "airflow_mcp_server.handlers.dags"

    def _flaky_import(name, *args, **kwargs):
        if name == broken_name:
            raise ImportError("simulated broken module")
        return _real_import_module(name, *args, **kwargs)

    monkeypatch.setattr(discovery.importlib, "import_module", _flaky_import)

    with pytest.raises(ValueError):
        await discovery.get_tool({"tool_name": "airflow_dag_list"})


@pytest.mark.asyncio
async def test_get_tool_info_examples_default_when_missing(monkeypatch):
    """When a tool name has no canned example, examples must default to [{}]."""
    monkeypatch.setattr(discovery, "TOOL_EXAMPLES", {})

    res = await discovery.get_tool({"tool_name": "airflow_health_check"})

    assert res["success"] is True
    assert res["data"]["examples"] == [{}]


@pytest.mark.asyncio
async def test_list_tools_examples_default_when_missing(monkeypatch):
    """list_tools should also fall back to [{}] examples when TOOL_EXAMPLES is empty."""
    monkeypatch.setattr(discovery, "TOOL_EXAMPLES", {})

    res = await discovery.list_tools({})

    assert res["success"] is True
    assert len(res["data"]) > 0
    for tool_info in res["data"]:
        assert tool_info["examples"] == [{}]


@pytest.mark.asyncio
async def test_list_tools_handlers_package_import_failure(monkeypatch):
    """If the handlers package itself cannot be imported, list_tools degrades to an empty list."""
    monkeypatch.setitem(sys.modules, "airflow_mcp_server.handlers", None)

    res = await discovery.list_tools({})

    assert res["success"] is True
    assert res["data"] == []
    assert res["error"] is None


@pytest.mark.asyncio
async def test_get_tool_handlers_package_import_failure(monkeypatch):
    """If the handlers package itself cannot be imported, get_tool raises a not-found ValueError."""
    monkeypatch.setitem(sys.modules, "airflow_mcp_server.handlers", None)

    with pytest.raises(ValueError):
        await discovery.get_tool({"tool_name": "airflow_health_check"})


@pytest.mark.asyncio
async def test_list_tools_hides_admin_tool_when_disabled(monkeypatch):
    monkeypatch.setattr(discovery.cfg, "MCP_ENABLE_ADMIN_ENDPOINTS", False)

    res = await discovery.list_tools({})

    assert res["success"] is True
    tool_names = {t["tool_name"] for t in res["data"]}
    assert "airflow_config_get" not in tool_names


@pytest.mark.asyncio
async def test_list_tools_includes_admin_tool_when_enabled(monkeypatch):
    monkeypatch.setattr(discovery.cfg, "MCP_ENABLE_ADMIN_ENDPOINTS", True)

    res = await discovery.list_tools({})

    assert res["success"] is True
    tool_names = {t["tool_name"] for t in res["data"]}
    assert "airflow_config_get" in tool_names


@pytest.mark.asyncio
async def test_get_tool_admin_hidden_when_disabled(monkeypatch):
    monkeypatch.setattr(discovery.cfg, "MCP_ENABLE_ADMIN_ENDPOINTS", False)

    with pytest.raises(ValueError):
        await discovery.get_tool({"tool_name": "airflow_config_get"})
