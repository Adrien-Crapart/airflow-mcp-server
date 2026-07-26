"""Coverage-focused unit tests for airflow_mcp_server/server.py.

These tests exercise load_tools(), create_app() (both HTTP endpoints and the
/health endpoint), _get_mcp_server(), _register_tools_with_mcp(),
_register_resources_with_mcp(), _register_prompts_with_mcp(), and
create_stdio_server() without requiring a live Airflow instance.
"""

import sys

import pytest
from fastapi.testclient import TestClient

import airflow_mcp_server.airflow_client as airflow_client_module
import airflow_mcp_server.server as server_module
from airflow_mcp_server.airflow_client import (
    AirflowAuthError,
    AirflowConflictError,
    AirflowConnectionError,
    AirflowNotFoundError,
    AirflowPermissionError,
    AirflowServerError,
)
from airflow_mcp_server.server import (
    _register_prompts_with_mcp,
    _register_resources_with_mcp,
    _register_tools_with_mcp,
    create_app,
    create_stdio_server,
    load_tools,
)


# ---------------------------------------------------------------------------
# load_tools()
# ---------------------------------------------------------------------------


def test_load_tools_default_includes_write_tools():
    """By default (MCP_READ_ONLY=False), write-only tools are present."""
    tools = load_tools()

    assert "airflow_dag_trigger" in tools
    assert "airflow_dag_list" in tools


def test_load_tools_read_only_excludes_write_tools(monkeypatch):
    """When MCP_READ_ONLY=True, write-only tools are filtered out."""
    from airflow_mcp_server.config import cfg

    monkeypatch.setattr(cfg, "MCP_READ_ONLY", True)

    tools = load_tools()

    assert "airflow_dag_trigger" not in tools
    assert "airflow_variable_set" not in tools
    assert "airflow_dag_list" in tools


def test_load_tools_admin_disabled_hides_admin_tools(monkeypatch):
    """When MCP_ENABLE_ADMIN_ENDPOINTS=False, admin tools are not exposed."""
    from airflow_mcp_server.config import cfg

    monkeypatch.setattr(cfg, "MCP_ENABLE_ADMIN_ENDPOINTS", False)

    tools = load_tools()

    assert "airflow_config_get" not in tools


def test_load_tools_admin_enabled_exposes_admin_tools(monkeypatch):
    """When MCP_ENABLE_ADMIN_ENDPOINTS=True, admin tools are exposed."""
    from airflow_mcp_server.config import cfg

    monkeypatch.setattr(cfg, "MCP_ENABLE_ADMIN_ENDPOINTS", True)

    tools = load_tools()

    assert "airflow_config_get" in tools


def test_load_tools_skips_handler_module_that_fails_to_import(monkeypatch):
    """A handler module that fails to import is skipped, not fatal."""
    import importlib as _importlib

    real_import_module = _importlib.import_module

    def _fake_import_module(name, *args, **kwargs):
        if name.endswith(".dags"):
            raise RuntimeError("boom")
        return real_import_module(name, *args, **kwargs)

    monkeypatch.setattr(server_module.importlib, "import_module", _fake_import_module)

    tools = load_tools()

    # dags module tools should be absent, but other modules still loaded fine.
    assert "airflow_dag_list" not in tools
    assert "airflow_health_check" in tools


def test_load_tools_handlers_package_import_failure(monkeypatch):
    """If the handlers package itself cannot be imported, return empty dict."""

    # load_tools() does `import airflow_mcp_server.handlers as handlers_pkg`,
    # which goes through builtins.__import__ with fromlist=None (not
    # importlib.import_module), so we intercept it there.
    import builtins

    real_import = builtins.__import__

    def _fake_builtins_import(name, globals=None, locals=None, fromlist=None, level=0):
        if name == "airflow_mcp_server.handlers" and not fromlist:
            raise ImportError("simulated failure")
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", _fake_builtins_import)

    tools = load_tools()

    assert tools == {}


# ---------------------------------------------------------------------------
# _get_mcp_server() / create_stdio_server()
# ---------------------------------------------------------------------------


def test_get_mcp_server_import_error_returns_none(monkeypatch):
    """If the mcp SDK is unavailable, _get_mcp_server() returns None."""
    monkeypatch.setattr(server_module, "_mcp_server", None)
    monkeypatch.setitem(sys.modules, "mcp.server.fastmcp", None)

    result = server_module._get_mcp_server()

    assert result is None


def test_get_mcp_server_success_returns_instance(monkeypatch):
    """When the mcp SDK is available, _get_mcp_server() builds and caches it."""
    monkeypatch.setattr(server_module, "_mcp_server", None)

    result = server_module._get_mcp_server()

    assert result is not None
    # Calling again returns the same cached instance.
    assert server_module._get_mcp_server() is result


def test_create_stdio_server_success():
    server = create_stdio_server()
    assert server is not None


def test_create_stdio_server_raises_when_mcp_unavailable(monkeypatch):
    monkeypatch.setattr(server_module, "_get_mcp_server", lambda: None)

    with pytest.raises(RuntimeError):
        create_stdio_server()


# ---------------------------------------------------------------------------
# _register_tools_with_mcp() — direct, isolated tests using a fake MCP object
# ---------------------------------------------------------------------------


class _FakeMCP:
    """Minimal stand-in for FastMCP capturing registered tool callables."""

    def __init__(self):
        self.registered = {}

    def tool(self, name=None, description=None):
        def decorator(fn):
            self.registered[name] = fn
            return fn

        return decorator


@pytest.mark.asyncio
async def test_register_tools_with_model_success():
    """A tool whose name has a schema model gets validated params and its dict passed through."""

    def handler(params):
        return {"success": True, "data": params, "error": None}

    fake_mcp = _FakeMCP()
    _register_tools_with_mcp(fake_mcp, {"airflow_dag_get": handler})

    result = await fake_mcp.registered["airflow_dag_get"](dag_id="my_dag")

    assert result == {"success": True, "data": {"dag_id": "my_dag"}, "error": None}


@pytest.mark.asyncio
async def test_register_tools_with_model_invalid_params():
    """Invalid/missing params for a modeled tool produce an error dict, not an exception."""

    def handler(params):
        return {"success": True, "data": params, "error": None}

    fake_mcp = _FakeMCP()
    _register_tools_with_mcp(fake_mcp, {"airflow_dag_get": handler})

    # DagIdParams requires dag_id -> validation fails
    result = await fake_mcp.registered["airflow_dag_get"]()

    assert result["success"] is False
    assert "Invalid params" in result["error"]


@pytest.mark.asyncio
async def test_register_tools_with_model_handler_raises():
    """An exception raised by the handler is caught and turned into an error dict."""

    def handler(params):
        raise RuntimeError("boom")

    fake_mcp = _FakeMCP()
    _register_tools_with_mcp(fake_mcp, {"airflow_dag_get": handler})

    result = await fake_mcp.registered["airflow_dag_get"](dag_id="my_dag")

    assert result == {"success": False, "data": None, "error": "boom"}


@pytest.mark.asyncio
async def test_register_tools_with_model_handler_returns_non_dict():
    """A modeled tool whose handler returns a non-dict value gets wrapped."""

    async def handler(params):
        return 42

    fake_mcp = _FakeMCP()
    _register_tools_with_mcp(fake_mcp, {"airflow_dag_get": handler})

    result = await fake_mcp.registered["airflow_dag_get"](dag_id="my_dag")

    assert result == {"success": True, "data": 42, "error": None}


@pytest.mark.asyncio
async def test_register_tools_without_model_success():
    """A tool with no schema model calls handler({}) directly."""

    def handler(params):
        assert params == {}
        return {"success": True, "data": "ok", "error": None}

    fake_mcp = _FakeMCP()
    _register_tools_with_mcp(fake_mcp, {"airflow_health_check": handler})

    result = await fake_mcp.registered["airflow_health_check"]()

    assert result == {"success": True, "data": "ok", "error": None}


@pytest.mark.asyncio
async def test_register_tools_without_model_handler_raises():
    def handler(params):
        raise RuntimeError("no-model-boom")

    fake_mcp = _FakeMCP()
    _register_tools_with_mcp(fake_mcp, {"airflow_health_check": handler})

    result = await fake_mcp.registered["airflow_health_check"]()

    assert result == {"success": False, "data": None, "error": "no-model-boom"}


@pytest.mark.asyncio
async def test_register_tools_without_model_handler_returns_non_dict():
    def handler(params):
        return "plain-string"

    fake_mcp = _FakeMCP()
    _register_tools_with_mcp(fake_mcp, {"airflow_health_check": handler})

    result = await fake_mcp.registered["airflow_health_check"]()

    assert result == {"success": True, "data": "plain-string", "error": None}


@pytest.mark.asyncio
async def test_register_tools_without_model_handler_is_coroutine():
    async def handler(params):
        return {"success": True, "data": "async-ok", "error": None}

    fake_mcp = _FakeMCP()
    _register_tools_with_mcp(fake_mcp, {"airflow_health_check": handler})

    result = await fake_mcp.registered["airflow_health_check"]()

    assert result == {"success": True, "data": "async-ok", "error": None}


@pytest.mark.asyncio
async def test_register_tools_without_model_no_late_binding_bug():
    """Regression test: each no-model closure must call its own handler, not the last one
    registered in the loop (previously a closure late-binding bug caused every no-model
    tool to invoke whichever handler was processed last)."""

    def handler_a(params):
        return {"success": True, "data": "from_a", "error": None}

    def handler_b(params):
        return {"success": True, "data": "from_b", "error": None}

    fake_mcp = _FakeMCP()
    _register_tools_with_mcp(
        fake_mcp,
        {
            "airflow_health_check": handler_a,
            "airflow_version_get": handler_b,
        },
    )

    result_a = await fake_mcp.registered["airflow_health_check"]()
    result_b = await fake_mcp.registered["airflow_version_get"]()

    assert result_a["data"] == "from_a"
    assert result_b["data"] == "from_b"


def test_register_tools_with_mcp_empty_tools_dict():
    fake_mcp = _FakeMCP()
    _register_tools_with_mcp(fake_mcp, {})
    assert fake_mcp.registered == {}


# ---------------------------------------------------------------------------
# _register_resources_with_mcp() / _register_prompts_with_mcp() failure paths
# ---------------------------------------------------------------------------


def test_register_resources_with_mcp_failure_is_swallowed(monkeypatch):
    from airflow_mcp_server.handlers import resources as resources_module

    def _boom(mcp):
        raise RuntimeError("resources boom")

    monkeypatch.setattr(resources_module, "register_all", _boom)

    # Must not raise.
    _register_resources_with_mcp(object())


def test_register_resources_with_mcp_success():
    fake_mcp = _FakeMCP()
    # Must not raise, and should actually register resources on success path.
    _register_resources_with_mcp(fake_mcp)


def test_register_prompts_with_mcp_failure_is_swallowed(monkeypatch):
    from airflow_mcp_server.handlers import prompts as prompts_module

    def _boom(mcp):
        raise RuntimeError("prompts boom")

    monkeypatch.setattr(prompts_module, "register_all", _boom)

    # Must not raise.
    _register_prompts_with_mcp(object())


def test_register_prompts_with_mcp_success():
    fake_mcp = _FakeMCP()
    _register_prompts_with_mcp(fake_mcp)


# ---------------------------------------------------------------------------
# create_app() — HTTP endpoints
# ---------------------------------------------------------------------------


@pytest.fixture
def client():
    app = create_app()
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def read_only_client(monkeypatch):
    """A TestClient built with MCP_READ_ONLY enabled, so write tools are absent."""
    from airflow_mcp_server.config import cfg

    monkeypatch.setattr(cfg, "MCP_READ_ONLY", True)
    app = create_app()
    with TestClient(app) as test_client:
        yield test_client


def test_create_app_mount_mcp_failure_is_swallowed(monkeypatch):
    """If mounting the MCP HTTP transport fails, create_app() logs a warning and continues."""

    class _BrokenMCP:
        def streamable_http_app(self):
            raise RuntimeError("mount boom")

    monkeypatch.setattr(server_module, "_get_mcp_server", lambda: _BrokenMCP())

    app = create_app()

    with TestClient(app) as test_client:
        response = test_client.get("/health")
        assert response.status_code == 200


def test_invoke_tool_requires_token_when_configured(monkeypatch):
    """When MCP_AUTH_TOKEN is set, protected routes require valid credentials."""
    from airflow_mcp_server.config import cfg

    monkeypatch.setattr(cfg, "MCP_REQUIRE_AUTH", True)
    monkeypatch.setattr(cfg, "MCP_AUTH_TOKEN", "top-secret")

    app = create_app()
    with TestClient(app) as test_client:
        unauthorized = test_client.post("/tool/airflow_health_check", json={})
        assert unauthorized.status_code == 401

        wrong_token = test_client.post(
            "/tool/airflow_health_check",
            json={},
            headers={"Authorization": "Bearer wrong"},
        )
        assert wrong_token.status_code == 401

        authorized = test_client.post(
            "/tool/airflow_health_check",
            json={},
            headers={"Authorization": "Bearer top-secret"},
        )
        assert authorized.status_code == 200


def test_health_endpoint(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ready_endpoint_success(monkeypatch, client):
    async def _fake_health():
        return {"metadatabase": {"status": "healthy"}}

    monkeypatch.setattr(airflow_client_module.client, "get_health", _fake_health)

    response = client.get("/ready")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ready"
    assert body["airflow"]["metadatabase"]["status"] == "healthy"


def test_ready_endpoint_failure_returns_503(monkeypatch, client):
    async def _raise():
        raise AirflowConnectionError("airflow unreachable")

    monkeypatch.setattr(airflow_client_module.client, "get_health", _raise)

    response = client.get("/ready")

    assert response.status_code == 503
    assert response.json() == {"status": "not_ready", "error": "airflow unreachable"}


def test_invoke_tool_success_no_schema(client):
    response = client.post("/tool/airflow_health_check", json={})

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"] == {"status": "ok"}
    assert body["error"] is None


def test_invoke_tool_success_wraps_non_dict_result(monkeypatch, client):
    """When a handler returns a non-dict value, the endpoint wraps it in a ToolResponse."""
    from airflow_mcp_server.handlers import health as health_module

    def fake_handler(params):
        return 42

    monkeypatch.setitem(health_module.TOOLS, "airflow_health_check", fake_handler)

    # Rebuild the app so create_app() re-captures the (now patched) tools dict.
    app = create_app()
    with TestClient(app) as patched_client:
        response = patched_client.post("/tool/airflow_health_check", json={})

    assert response.status_code == 200
    assert response.json() == {"success": True, "data": 42, "error": None}


def test_invoke_tool_unknown_tool_returns_404(client):
    response = client.post("/tool/airflow_does_not_exist", json={})

    assert response.status_code == 404
    body = response.json()
    assert body["success"] is False
    assert body["error"] == "Tool not found"


def test_invoke_tool_malformed_json_body_defaults_to_empty_params(client):
    """Malformed JSON in the request body must not crash; params default to {}."""
    response = client.post(
        "/tool/airflow_health_check",
        content="not valid json {{{",
        headers={"Content-Type": "application/json"},
    )

    assert response.status_code == 200
    assert response.json()["success"] is True


def test_invoke_tool_invalid_schema_params_returns_400(client):
    """A modeled tool with missing required params is rejected before the handler runs."""
    response = client.post("/tool/airflow_dag_get", json={"params": {}})

    assert response.status_code == 400
    body = response.json()
    assert body["success"] is False
    assert "Invalid params" in body["error"]


def test_invoke_tool_handler_value_error_returns_400(client):
    """airflow_tool_get raises a bare ValueError for an unknown tool name."""
    response = client.post("/tool/airflow_tool_get", json={"params": {"tool_name": "not_a_real_tool"}})

    assert response.status_code == 400
    assert response.json()["success"] is False


def test_invoke_tool_read_only_mode_hides_write_tool(read_only_client):
    response = read_only_client.post("/tool/airflow_dag_trigger", json={"params": {"dag_id": "d1"}})

    assert response.status_code == 404


@pytest.mark.parametrize(
    "exc,status",
    [
        (AirflowAuthError("auth failed"), 401),
        (AirflowPermissionError("forbidden"), 403),
        (AirflowNotFoundError("missing"), 404),
        (AirflowConflictError("conflict"), 409),
        (AirflowConnectionError("unreachable"), 503),
        (AirflowServerError("server broke"), 502),
        (RuntimeError("unexpected"), 500),
    ],
)
def test_invoke_tool_exception_mapping(monkeypatch, client, exc, status):
    async def _raise(*args, **kwargs):
        raise exc

    monkeypatch.setattr(airflow_client_module.client, "get_dag", _raise)

    response = client.post("/tool/airflow_dag_get", json={"params": {"dag_id": "d1"}})

    assert response.status_code == status
    body = response.json()
    assert body["success"] is False
    assert body["error"] is not None


# ---------------------------------------------------------------------------
# create_app() — POST /tool fallback endpoint
# ---------------------------------------------------------------------------


def test_invoke_tool_body_success_with_tool_name_key(client):
    response = client.post("/tool", json={"tool_name": "airflow_health_check", "params": {}})

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"] == {"status": "ok"}


def test_invoke_tool_body_success_with_tool_key(client):
    response = client.post("/tool", json={"tool": "airflow_health_check", "params": {}})

    assert response.status_code == 200
    assert response.json()["success"] is True


def test_invoke_tool_body_missing_tool_name_returns_400(client):
    response = client.post("/tool", json={"params": {}})

    assert response.status_code == 400
    body = response.json()
    assert body["success"] is False
    assert body["error"] == "Missing 'tool_name' in body"


def test_invoke_tool_body_unknown_tool_returns_404(client):
    response = client.post("/tool", json={"tool_name": "airflow_does_not_exist"})

    assert response.status_code == 404
    assert response.json()["error"] == "Tool not found"


def test_invoke_tool_body_malformed_json_defaults_to_empty_payload(client):
    response = client.post(
        "/tool",
        content="not valid json {{{",
        headers={"Content-Type": "application/json"},
    )

    assert response.status_code == 400
    assert response.json()["error"] == "Missing 'tool_name' in body"


def test_invoke_tool_body_handler_value_error_returns_400(client):
    """airflow_tool_get raises a bare ValueError for an unknown tool name (fallback endpoint)."""
    response = client.post(
        "/tool",
        json={"tool_name": "airflow_tool_get", "params": {"tool_name": "not_a_real_tool"}},
    )

    assert response.status_code == 400
    assert response.json()["success"] is False


def test_invoke_tool_body_invalid_schema_params_returns_400(client):
    response = client.post("/tool", json={"tool_name": "airflow_dag_get", "params": {}})

    assert response.status_code == 400
    body = response.json()
    assert body["success"] is False
    assert "Invalid params" in body["error"]


@pytest.mark.parametrize(
    "exc,status",
    [
        (AirflowAuthError("auth failed"), 401),
        (AirflowPermissionError("forbidden"), 403),
        (AirflowNotFoundError("missing"), 404),
        (AirflowConflictError("conflict"), 409),
        (AirflowConnectionError("unreachable"), 503),
        (AirflowServerError("server broke"), 502),
        (RuntimeError("unexpected"), 500),
    ],
)
def test_invoke_tool_body_exception_mapping(monkeypatch, client, exc, status):
    async def _raise(*args, **kwargs):
        raise exc

    monkeypatch.setattr(airflow_client_module.client, "get_dag", _raise)

    response = client.post("/tool", json={"tool_name": "airflow_dag_get", "params": {"dag_id": "d1"}})

    assert response.status_code == status
    assert response.json()["success"] is False


def test_invoke_tool_body_success_wraps_non_dict_result(monkeypatch):
    from airflow_mcp_server.handlers import health as health_module

    def fake_handler(params):
        return ["a", "b"]

    monkeypatch.setitem(health_module.TOOLS, "airflow_health_check", fake_handler)

    app = create_app()
    with TestClient(app) as patched_client:
        response = patched_client.post("/tool", json={"tool_name": "airflow_health_check"})

    assert response.status_code == 200
    assert response.json() == {"success": True, "data": ["a", "b"], "error": None}
