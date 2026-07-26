"""Unit tests for AirflowClient methods not covered by the existing suites.

Covers: variables, pools, xcom, import errors, dag source, datasets,
providers, plugins, dag-run lifecycle, task definitions/instances, event
logs, config, version, dag warnings, close(), the auth-switch retry logic
in `_request_with_fallback`, and the connection-retry/backoff path in
`_request`.
"""

import asyncio
import json as _json
import urllib.parse

import httpx
import pytest

from airflow_mcp_server.airflow_client import (
    AirflowClient,
    AirflowConnectionError,
    AirflowError,
    AirflowNotFoundError,
)
from airflow_mcp_server.config import cfg


def _body(request: httpx.Request) -> dict:
    """Best-effort parse of a request's JSON body."""
    if not request.content:
        return {}
    try:
        return _json.loads(request.content.decode())
    except Exception:
        return {}


# ---------------------------------------------------------------------------
# Variables
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_variables_success():
    def handler(request):
        assert request.url.path == "/api/v2/variables"
        return httpx.Response(200, json={"variables": [{"key": "k1", "value": "v1"}]})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        client = AirflowClient(http_client=ac)
        result = await client.list_variables()
        assert result == [{"key": "k1", "value": "v1"}]


@pytest.mark.asyncio
async def test_list_variables_non_dict_body_returns_empty_list():
    def handler(request):
        return httpx.Response(200, json=["unexpected", "list"])

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        client = AirflowClient(http_client=ac)
        result = await client.list_variables()
        assert result == []


@pytest.mark.asyncio
async def test_get_variable_success():
    def handler(request):
        assert request.url.path == "/api/v2/variables/my_key"
        return httpx.Response(200, json={"key": "my_key", "value": "my_value"})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        client = AirflowClient(http_client=ac)
        result = await client.get_variable("my_key")
        assert result["value"] == "my_value"


@pytest.mark.asyncio
async def test_set_variable_success():
    def handler(request):
        assert request.method == "POST"
        assert request.url.path == "/api/v2/variables"
        body = _body(request)
        assert body == {"key": "my_key", "value": "my_value"}
        return httpx.Response(200, json=body)

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        client = AirflowClient(http_client=ac)
        result = await client.set_variable("my_key", "my_value")
        assert result["key"] == "my_key"


@pytest.mark.asyncio
async def test_delete_variable_success():
    def handler(request):
        assert request.method == "DELETE"
        assert request.url.path == "/api/v2/variables/my_key"
        return httpx.Response(200, json={"deleted": True})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        client = AirflowClient(http_client=ac)
        result = await client.delete_variable("my_key")
        assert result == {"deleted": True}


# ---------------------------------------------------------------------------
# Pools
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_pools_success():
    def handler(request):
        assert request.url.path == "/api/v2/pools"
        return httpx.Response(200, json={"pools": [{"name": "default_pool"}]})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        client = AirflowClient(http_client=ac)
        result = await client.list_pools()
        assert result == [{"name": "default_pool"}]


@pytest.mark.asyncio
async def test_list_pools_non_dict_body_returns_empty_list():
    def handler(request):
        return httpx.Response(200, json="not-a-dict")

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        client = AirflowClient(http_client=ac)
        result = await client.list_pools()
        assert result == []


@pytest.mark.asyncio
async def test_get_pool_success():
    def handler(request):
        assert request.url.path == "/api/v2/pools/default_pool"
        return httpx.Response(200, json={"name": "default_pool", "slots": 128})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        client = AirflowClient(http_client=ac)
        result = await client.get_pool("default_pool")
        assert result["slots"] == 128


@pytest.mark.asyncio
async def test_set_pool_success_with_description():
    def handler(request):
        assert request.method == "POST"
        assert request.url.path == "/api/v2/pools"
        body = _body(request)
        assert body == {"name": "my_pool", "slots": 10, "description": "custom pool"}
        return httpx.Response(200, json=body)

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        client = AirflowClient(http_client=ac)
        result = await client.set_pool("my_pool", 10, description="custom pool")
        assert result["slots"] == 10


@pytest.mark.asyncio
async def test_set_pool_success_without_description():
    def handler(request):
        body = _body(request)
        assert "description" not in body
        return httpx.Response(200, json=body)

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        client = AirflowClient(http_client=ac)
        result = await client.set_pool("my_pool", 5)
        assert result == {"name": "my_pool", "slots": 5}


# ---------------------------------------------------------------------------
# XCom
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_xcom_success():
    def handler(request):
        assert request.url.path == "/api/v2/dags/d1/dagRuns/r1/taskInstances/t1/xcomEntries/return_value"
        return httpx.Response(200, json={"key": "return_value", "value": "42"})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        client = AirflowClient(http_client=ac)
        result = await client.get_xcom("d1", "r1", "t1", "return_value")
        assert result["value"] == "42"


# ---------------------------------------------------------------------------
# Import errors
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_import_errors_success():
    def handler(request):
        assert request.url.path == "/api/v2/importErrors"
        return httpx.Response(200, json={"import_errors": [{"filename": "bad_dag.py"}]})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        client = AirflowClient(http_client=ac)
        result = await client.list_import_errors()
        assert result == [{"filename": "bad_dag.py"}]


@pytest.mark.asyncio
async def test_list_import_errors_non_dict_body_returns_empty_list():
    def handler(request):
        return httpx.Response(200, json=[1, 2, 3])

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        client = AirflowClient(http_client=ac)
        result = await client.list_import_errors()
        assert result == []


# ---------------------------------------------------------------------------
# DAG source
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_dag_source_success_plain_text():
    """Airflow returns DAG source as plain text; success path falls back to text
    when the body is not valid JSON (covers the `resp.json()` exception branch)."""

    def handler(request):
        assert request.url.path == "/api/v2/dagSources/abc123"
        return httpx.Response(200, content=b"print('hello world')")

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        client = AirflowClient(http_client=ac)
        result = await client.get_dag_source("abc123")
        assert result == "print('hello world')"


# ---------------------------------------------------------------------------
# Datasets
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_datasets_success():
    def handler(request):
        assert request.url.path == "/api/v2/datasets"
        return httpx.Response(200, json={"datasets": [{"uri": "s3://bucket/key"}]})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        client = AirflowClient(http_client=ac)
        result = await client.list_datasets()
        assert result == [{"uri": "s3://bucket/key"}]


@pytest.mark.asyncio
async def test_list_datasets_falls_back_to_assets_key():
    def handler(request):
        return httpx.Response(200, json={"assets": [{"uri": "s3://bucket/other"}]})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        client = AirflowClient(http_client=ac)
        result = await client.list_datasets()
        assert result == [{"uri": "s3://bucket/other"}]


@pytest.mark.asyncio
async def test_list_datasets_non_dict_body_returns_empty_list():
    def handler(request):
        return httpx.Response(200, json="oops")

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        client = AirflowClient(http_client=ac)
        result = await client.list_datasets()
        assert result == []


@pytest.mark.asyncio
async def test_get_dataset_url_encodes_uri():
    dataset_uri = "s3://bucket/key"
    expected_encoded = urllib.parse.quote(dataset_uri, safe="")

    def handler(request):
        # request.url.path percent-decodes; raw_path preserves the encoding
        # actually sent on the wire, which is what we need to verify here.
        assert request.url.raw_path == f"/api/v2/datasets/{expected_encoded}".encode()
        assert b"%3A%2F%2F" in request.url.raw_path
        return httpx.Response(200, json={"uri": dataset_uri})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        client = AirflowClient(http_client=ac)
        result = await client.get_dataset(dataset_uri)
        assert result["uri"] == dataset_uri


# ---------------------------------------------------------------------------
# Providers / plugins
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_providers_success():
    def handler(request):
        assert request.url.path == "/api/v2/providers"
        return httpx.Response(200, json={"providers": [{"package_name": "apache-airflow-providers-http"}]})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        client = AirflowClient(http_client=ac)
        result = await client.list_providers()
        assert result == [{"package_name": "apache-airflow-providers-http"}]


@pytest.mark.asyncio
async def test_list_providers_non_dict_body_returns_empty_list():
    def handler(request):
        return httpx.Response(200, json=[])

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        client = AirflowClient(http_client=ac)
        result = await client.list_providers()
        assert result == []


@pytest.mark.asyncio
async def test_list_plugins_success():
    def handler(request):
        assert request.url.path == "/api/v2/plugins"
        return httpx.Response(200, json={"plugins": [{"name": "my_plugin"}]})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        client = AirflowClient(http_client=ac)
        result = await client.list_plugins()
        assert result == [{"name": "my_plugin"}]


@pytest.mark.asyncio
async def test_list_plugins_non_dict_body_returns_empty_list():
    def handler(request):
        return httpx.Response(200, json="nope")

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        client = AirflowClient(http_client=ac)
        result = await client.list_plugins()
        assert result == []


# ---------------------------------------------------------------------------
# DAG run lifecycle
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_dag_run_success():
    def handler(request):
        assert request.method == "GET"
        assert request.url.path == "/api/v2/dags/d1/dagRuns/r1"
        return httpx.Response(200, json={"dag_run_id": "r1", "state": "success"})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        client = AirflowClient(http_client=ac)
        result = await client.get_dag_run("d1", "r1")
        assert result["state"] == "success"


@pytest.mark.asyncio
async def test_clear_dag_run_success():
    def handler(request):
        assert request.method == "POST"
        assert request.url.path == "/api/v2/dags/d1/dagRuns/r1/clear"
        body = _body(request)
        assert body == {"dry_run": False, "only_failed": False, "reset_dag_runs": True}
        return httpx.Response(200, json={"cleared": True})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        client = AirflowClient(http_client=ac)
        result = await client.clear_dag_run("d1", "r1", only_failed=False)
        assert result == {"cleared": True}


@pytest.mark.asyncio
async def test_delete_dag_run_success():
    def handler(request):
        assert request.method == "DELETE"
        assert request.url.path == "/api/v2/dags/d1/dagRuns/r1"
        return httpx.Response(200, json={"deleted": True})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        client = AirflowClient(http_client=ac)
        result = await client.delete_dag_run("d1", "r1")
        assert result == {"deleted": True}


@pytest.mark.asyncio
async def test_update_dag_run_state_success():
    def handler(request):
        assert request.method == "PATCH"
        assert request.url.path == "/api/v2/dags/d1/dagRuns/r1"
        body = _body(request)
        assert body == {"state": "failed"}
        return httpx.Response(200, json=body)

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        client = AirflowClient(http_client=ac)
        result = await client.update_dag_run_state("d1", "r1", "failed")
        assert result["state"] == "failed"


# ---------------------------------------------------------------------------
# Task definitions / instances
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_tasks_success():
    def handler(request):
        assert request.url.path == "/api/v2/dags/d1/tasks"
        return httpx.Response(200, json={"tasks": [{"task_id": "t1"}]})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        client = AirflowClient(http_client=ac)
        result = await client.list_tasks("d1")
        assert result == [{"task_id": "t1"}]


@pytest.mark.asyncio
async def test_list_tasks_non_dict_body_returns_empty_list():
    def handler(request):
        return httpx.Response(200, json="oops")

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        client = AirflowClient(http_client=ac)
        result = await client.list_tasks("d1")
        assert result == []


@pytest.mark.asyncio
async def test_get_task_success():
    def handler(request):
        assert request.url.path == "/api/v2/dags/d1/tasks/t1"
        return httpx.Response(200, json={"task_id": "t1", "operator": "PythonOperator"})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        client = AirflowClient(http_client=ac)
        result = await client.get_task("d1", "t1")
        assert result["operator"] == "PythonOperator"


@pytest.mark.asyncio
async def test_set_task_instance_state_success():
    def handler(request):
        assert request.method == "PATCH"
        assert request.url.path == "/api/v2/dags/d1/dagRuns/r1/taskInstances/t1"
        body = _body(request)
        assert body == {"state": "success", "include_upstream": False, "include_downstream": False}
        return httpx.Response(200, json=body)

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        client = AirflowClient(http_client=ac)
        result = await client.set_task_instance_state("d1", "r1", "t1", "success")
        assert result["state"] == "success"


@pytest.mark.asyncio
async def test_clear_task_instance_success():
    def handler(request):
        assert request.method == "POST"
        assert request.url.path == "/api/v2/dags/d1/dagRuns/r1/taskInstances/t1/clear"
        return httpx.Response(200, json={"cleared": True})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        client = AirflowClient(http_client=ac)
        result = await client.clear_task_instance("d1", "r1", "t1")
        assert result == {"cleared": True}


# ---------------------------------------------------------------------------
# Event logs
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_event_logs_success_no_filters():
    def handler(request):
        assert request.url.path == "/api/v2/eventLogs"
        assert "dag_id" not in request.url.params
        assert "event" not in request.url.params
        return httpx.Response(200, json={"entries": [{"id": 1, "event": "trigger"}]})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        client = AirflowClient(http_client=ac)
        result = await client.list_event_logs()
        assert result == [{"id": 1, "event": "trigger"}]


@pytest.mark.asyncio
async def test_list_event_logs_success_with_filters():
    def handler(request):
        assert request.url.params.get("dag_id") == "d1"
        assert request.url.params.get("event") == "trigger"
        return httpx.Response(200, json={"events": [{"id": 2, "event": "trigger", "dag_id": "d1"}]})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        client = AirflowClient(http_client=ac)
        result = await client.list_event_logs(dag_id="d1", event="trigger")
        assert result == [{"id": 2, "event": "trigger", "dag_id": "d1"}]


@pytest.mark.asyncio
async def test_list_event_logs_non_dict_body_returns_empty_list():
    def handler(request):
        return httpx.Response(200, json="nope")

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        client = AirflowClient(http_client=ac)
        result = await client.list_event_logs()
        assert result == []


@pytest.mark.asyncio
async def test_get_event_log_success():
    def handler(request):
        assert request.url.path == "/api/v2/eventLogs/42"
        return httpx.Response(200, json={"id": 42, "event": "pause"})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        client = AirflowClient(http_client=ac)
        result = await client.get_event_log(42)
        assert result["id"] == 42


# ---------------------------------------------------------------------------
# Config / version / dag warnings
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_config_without_section_returns_full_dict():
    def handler(request):
        assert request.url.path == "/api/v2/config"
        return httpx.Response(200, json={"core": {"dags_folder": "/dags"}, "webserver": {"base_url": "http://x"}})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        client = AirflowClient(http_client=ac)
        result = await client.get_config()
        assert set(result.keys()) == {"core", "webserver"}


@pytest.mark.asyncio
async def test_get_config_with_section_returns_only_that_section():
    def handler(request):
        return httpx.Response(200, json={"core": {"dags_folder": "/dags"}, "webserver": {"base_url": "http://x"}})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        client = AirflowClient(http_client=ac)
        result = await client.get_config(section="core")
        assert result == {"dags_folder": "/dags"}


@pytest.mark.asyncio
async def test_get_version_success():
    def handler(request):
        assert request.url.path == "/api/v2/version"
        return httpx.Response(200, json={"version": "3.0.0"})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        client = AirflowClient(http_client=ac)
        result = await client.get_version()
        assert result["version"] == "3.0.0"


@pytest.mark.asyncio
async def test_get_health_uses_monitor_endpoint_when_available():
    def handler(request):
        assert request.url.path == "/api/v2/monitor/health"
        return httpx.Response(200, json={"metadatabase": {"status": "healthy"}})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        client = AirflowClient(http_client=ac)
        result = await client.get_health()
        assert result["metadatabase"]["status"] == "healthy"


@pytest.mark.asyncio
async def test_get_health_falls_back_to_legacy_health_endpoint():
    calls = {"count": 0}

    def handler(request):
        calls["count"] += 1
        if request.url.path == "/api/v2/monitor/health":
            return httpx.Response(404, json={"detail": "not found"})
        assert request.url.path == "/api/v2/health"
        return httpx.Response(200, json={"status": "healthy"})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        client = AirflowClient(http_client=ac)
        result = await client.get_health()
        assert result["status"] == "healthy"
        assert calls["count"] == 2


@pytest.mark.asyncio
async def test_get_health_raises_not_found_when_both_endpoints_absent(monkeypatch):
    client = AirflowClient(base_url="http://test")

    async def _fake_request_with_fallback(method, path, params=None, json=None, retries=3, allow_auth_switch=True):
        raise AirflowNotFoundError(f"not found on {path}")

    monkeypatch.setattr(client, "_request_with_fallback", _fake_request_with_fallback)

    try:
        with pytest.raises(AirflowNotFoundError):
            await client.get_health()
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_list_dag_warnings_success_no_dag_id():
    def handler(request):
        assert request.url.path == "/api/v2/dagWarnings"
        assert "dag_id" not in request.url.params
        return httpx.Response(200, json={"dag_warnings": [{"message": "warn"}]})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        client = AirflowClient(http_client=ac)
        result = await client.list_dag_warnings()
        assert result == [{"message": "warn"}]


@pytest.mark.asyncio
async def test_list_dag_warnings_success_with_dag_id():
    def handler(request):
        assert request.url.params.get("dag_id") == "d1"
        return httpx.Response(200, json={"warnings": [{"message": "warn", "dag_id": "d1"}]})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        client = AirflowClient(http_client=ac)
        result = await client.list_dag_warnings(dag_id="d1")
        assert result == [{"message": "warn", "dag_id": "d1"}]


@pytest.mark.asyncio
async def test_list_dag_warnings_non_dict_body_returns_empty_list():
    def handler(request):
        return httpx.Response(200, json="nope")

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        client = AirflowClient(http_client=ac)
        result = await client.list_dag_warnings()
        assert result == []


# ---------------------------------------------------------------------------
# close()
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_close_closes_underlying_client():
    def handler(request):
        return httpx.Response(200, json={})

    transport = httpx.MockTransport(handler)
    ac = httpx.AsyncClient(transport=transport, base_url="http://test")
    client = AirflowClient(http_client=ac)
    assert ac.is_closed is False
    await client.close()
    assert ac.is_closed is True


# ---------------------------------------------------------------------------
# Auth-switch retry logic in `_request_with_fallback`
# ---------------------------------------------------------------------------


# NOTE: `_request` builds a brand-new `httpx.AsyncClient` (without any
# `transport=` override) whenever an auth override is in play, so a
# MockTransport attached only to the *primary* client cannot observe that
# retry — it would otherwise try to hit the real network. Per the task
# guidance we instead monkeypatch `httpx.AsyncClient.request` so both the
# primary client and any short-lived override-auth client are intercepted.


@pytest.mark.asyncio
async def test_auth_switch_retries_without_auth_when_basic_auth_gets_401(monkeypatch):
    """Client sends BasicAuth, server 401s, fallback retries with no auth
    and succeeds."""

    async def fake_request(self, method, url, params=None, json=None):
        if getattr(self, "auth", None):
            return httpx.Response(401, json={"detail": "unauthorized"})
        return httpx.Response(200, json={"ok": True})

    monkeypatch.setattr(httpx.AsyncClient, "request", fake_request)

    ac = httpx.AsyncClient(base_url="http://test", auth=httpx.BasicAuth("user", "pass"))
    client = AirflowClient(http_client=ac, username="user", password="pass")
    try:
        result = await client._request_with_fallback("GET", "/api/v2/version")
        assert result == {"ok": True}
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_auth_switch_retries_with_basic_auth_when_no_auth_gets_401(monkeypatch):
    """Client sends no auth, server 401s, fallback retries with BasicAuth
    built from configured username/password and succeeds."""

    async def fake_request(self, method, url, params=None, json=None):
        if not getattr(self, "auth", None):
            return httpx.Response(401, json={"detail": "unauthorized"})
        return httpx.Response(200, json={"ok": True})

    monkeypatch.setattr(httpx.AsyncClient, "request", fake_request)

    ac = httpx.AsyncClient(base_url="http://test")  # no auth configured
    client = AirflowClient(http_client=ac, username="user", password="pass")
    try:
        result = await client._request_with_fallback("GET", "/api/v2/version")
        assert result == {"ok": True}
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_auth_switch_reraises_when_fallback_also_fails(monkeypatch):
    """Both the original attempt and the auth-switch retry return 401; the
    original AirflowAuthError propagates."""

    async def fake_request(self, method, url, params=None, json=None):
        return httpx.Response(401, json={"detail": "unauthorized"})

    monkeypatch.setattr(httpx.AsyncClient, "request", fake_request)

    ac = httpx.AsyncClient(base_url="http://test", auth=httpx.BasicAuth("user", "pass"))
    client = AirflowClient(http_client=ac, username="user", password="pass")
    from airflow_mcp_server.airflow_client import AirflowAuthError

    try:
        with pytest.raises(AirflowAuthError):
            await client._request_with_fallback("GET", "/api/v2/version")
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_auth_switch_disabled_reraises_immediately():
    """When `allow_auth_switch=False`, a 401 is not retried at all."""

    calls = {"count": 0}

    def handler(request):
        calls["count"] += 1
        return httpx.Response(401, json={"detail": "unauthorized"})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        client = AirflowClient(http_client=ac, username="user", password="pass")
        from airflow_mcp_server.airflow_client import AirflowAuthError

        with pytest.raises(AirflowAuthError):
            await client._request_with_fallback("GET", "/api/v2/version", allow_auth_switch=False)
        assert calls["count"] == 1


@pytest.mark.asyncio
async def test_auth_switch_reraises_when_basic_auth_retry_also_fails(monkeypatch):
    """Client has no auth configured; the fallback retry with BasicAuth
    (built from configured credentials) also gets a 401, so the original
    error is re-raised."""

    async def fake_request(self, method, url, params=None, json=None):
        return httpx.Response(401, json={"detail": "unauthorized"})

    monkeypatch.setattr(httpx.AsyncClient, "request", fake_request)

    ac = httpx.AsyncClient(base_url="http://test")  # no auth configured
    client = AirflowClient(http_client=ac, username="user", password="pass")
    from airflow_mcp_server.airflow_client import AirflowAuthError

    try:
        with pytest.raises(AirflowAuthError):
            await client._request_with_fallback("GET", "/api/v2/version")
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_request_with_fallback_swallows_exception_reading_auth_attribute():
    """If reading `self._client.auth` itself raises, the auth-switch logic
    treats it as "no auth present" and, with no credentials configured
    either, simply re-raises the original AirflowAuthError."""

    class _RaisingAuthClient:
        def __init__(self, response):
            self._response = response
            self.base_url = "http://test"
            self.timeout = 30.0

        @property
        def auth(self):
            raise RuntimeError("boom")

        async def request(self, method, url, params=None, json=None):
            return self._response

        async def aclose(self):
            pass

    client = AirflowClient(base_url="http://test", username="", password="")
    client._client = _RaisingAuthClient(httpx.Response(401, json={"detail": "no"}))

    from airflow_mcp_server.airflow_client import AirflowAuthError

    with pytest.raises(AirflowAuthError):
        await client._request_with_fallback("GET", "/api/v2/version")


@pytest.mark.asyncio
async def test_override_auth_falls_back_to_base_url_and_preserves_bearer_token(monkeypatch):
    """Covers the override-auth branch's own base_url exception/fallback
    handling, and confirms the short-lived override client preserves the
    Bearer-token header when `self.token` is set."""

    class _RaisingBaseUrlClient:
        def __init__(self, response):
            self._response = response
            self.timeout = 30.0

        @property
        def base_url(self):
            raise RuntimeError("no base url")

        @property
        def auth(self):
            return None

        async def request(self, method, url, params=None, json=None):
            return self._response

        async def aclose(self):
            pass

    async def fake_asyncclient_request(self, method, url, params=None, json=None):
        # Only the short-lived override-auth client reaches here (the
        # primary `_client` is the custom stub above).
        assert self.headers.get("authorization") == "Bearer sometoken"
        return httpx.Response(200, json={"ok": True})

    monkeypatch.setattr(httpx.AsyncClient, "request", fake_asyncclient_request)

    client = AirflowClient(base_url="http://test", username="user", password="pass")
    client.token = "sometoken"
    client._client = _RaisingBaseUrlClient(httpx.Response(401, json={"detail": "no"}))

    result = await client._request_with_fallback("GET", "/api/v2/version")
    assert result == {"ok": True}


# ---------------------------------------------------------------------------
# Connection-retry/backoff path in `_request`
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_request_connect_error_retries_then_raises_connection_error(monkeypatch):
    def handler(request):
        raise httpx.ConnectError("connection refused")

    sleeps = []

    async def _nosleep(seconds):
        sleeps.append(seconds)

    monkeypatch.setattr(asyncio, "sleep", _nosleep)

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        client = AirflowClient(http_client=ac)
        with pytest.raises(AirflowConnectionError):
            await client._request("GET", "/api/v2/version", retries=2)
        # Retried twice (attempt 0 -> sleep, attempt 1 -> sleep) before
        # exhausting retries on the 3rd failure.
        assert sleeps == [1, 2]


@pytest.mark.asyncio
async def test_request_connect_error_succeeds_after_retry(monkeypatch):
    calls = {"count": 0}

    def handler(request):
        calls["count"] += 1
        if calls["count"] < 2:
            raise httpx.ConnectError("connection refused")
        return httpx.Response(200, json={"ok": True})

    async def _nosleep(seconds):
        return None

    monkeypatch.setattr(asyncio, "sleep", _nosleep)

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        client = AirflowClient(http_client=ac)
        result = await client._request("GET", "/api/v2/version", retries=2)
        assert result == {"ok": True}
        assert calls["count"] == 2


# ---------------------------------------------------------------------------
# Generic 4xx mapping (other than 401/403/404/409)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_request_other_4xx_raises_generic_airflow_error():
    def handler(request):
        return httpx.Response(418, json={"detail": "I'm a teapot"})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        client = AirflowClient(http_client=ac)
        with pytest.raises(AirflowError):
            await client._request("GET", "/api/v2/version")


# ---------------------------------------------------------------------------
# Constructor branches: http_client without a configured base_url, and
# no http_client at all, must build their own internal client honoring
# Bearer-token vs BasicAuth precedence.
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_init_http_client_without_base_url_uses_bearer_token(monkeypatch):
    # An AsyncClient created without base_url has an empty base_url, which
    # is falsy for our purposes and triggers the "rebuild" branch.
    monkeypatch.setattr(cfg, "AIRFLOW_API_TOKEN", "secret-token")
    bare_client = httpx.AsyncClient()
    try:
        client = AirflowClient(base_url="http://rebuilt", http_client=bare_client)
        assert client._client is not bare_client
        assert client._client.headers.get("authorization") == "Bearer secret-token"
        assert client._client.auth is None
    finally:
        await bare_client.aclose()
        await client.close()


@pytest.mark.asyncio
async def test_init_http_client_without_base_url_uses_basic_auth(monkeypatch):
    monkeypatch.setattr(cfg, "AIRFLOW_API_TOKEN", "")
    bare_client = httpx.AsyncClient()
    try:
        client = AirflowClient(base_url="http://rebuilt", http_client=bare_client, username="user", password="pass")
        assert client._client is not bare_client
        assert bool(client._client.auth) is True
    finally:
        await bare_client.aclose()
        await client.close()


@pytest.mark.asyncio
async def test_init_http_client_without_base_url_no_auth_when_credentials_missing(monkeypatch):
    monkeypatch.setattr(cfg, "AIRFLOW_API_TOKEN", "")
    bare_client = httpx.AsyncClient()
    try:
        client = AirflowClient(base_url="http://rebuilt", http_client=bare_client, username="", password="")
        assert client._client is not bare_client
        assert client._client.auth is None
    finally:
        await bare_client.aclose()
        await client.close()


@pytest.mark.asyncio
async def test_init_no_http_client_uses_bearer_token(monkeypatch):
    monkeypatch.setattr(cfg, "AIRFLOW_API_TOKEN", "secret-token")
    client = AirflowClient(base_url="http://rebuilt")
    try:
        assert client._client.headers.get("authorization") == "Bearer secret-token"
        assert client._client.auth is None
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_init_no_http_client_uses_basic_auth(monkeypatch):
    monkeypatch.setattr(cfg, "AIRFLOW_API_TOKEN", "")
    client = AirflowClient(base_url="http://rebuilt", username="user", password="pass")
    try:
        assert bool(client._client.auth) is True
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_init_no_http_client_no_auth_when_credentials_missing(monkeypatch):
    monkeypatch.setattr(cfg, "AIRFLOW_API_TOKEN", "")
    client = AirflowClient(base_url="http://rebuilt", username="", password="")
    try:
        assert client._client.auth is None
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_request_target_built_from_base_url_when_client_has_no_base_url():
    """When `self._client` lacks a `base_url` attribute entirely, `_request`
    falls back to prefixing `self.base_url` onto the relative path."""

    class _FakeNoBaseClient:
        def __init__(self, response):
            self._response = response
            self.captured_url = None
            self.auth = None
            self.timeout = 30.0

        async def request(self, method, url, params=None, json=None):
            self.captured_url = url
            return self._response

        async def aclose(self):
            pass

    transport = httpx.MockTransport(lambda request: httpx.Response(200, json={"ok": True}))
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        client = AirflowClient(base_url="http://test", http_client=ac)
        fake = _FakeNoBaseClient(httpx.Response(200, json={"ok": True}))
        client._client = fake

        result = await client._request("GET", "/api/v2/version")

        assert result == {"ok": True}
        assert fake.captured_url == "http://test/api/v2/version"
