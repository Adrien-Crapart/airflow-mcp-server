import asyncio
import pytest
import httpx

from airflow_mcp_server.airflow_client import (
    AirflowClient,
    AirflowAuthError,
    AirflowPermissionError,
    AirflowNotFoundError,
    AirflowConflictError,
    AirflowServerError,
)


def _mk_transport(status: int, json_body=None, text_body=None):
    def handler(request):
        if json_body is not None:
            return httpx.Response(status, json=json_body)
        if text_body is not None:
            return httpx.Response(status, content=text_body)
        return httpx.Response(status)

    return httpx.MockTransport(handler)


@pytest.mark.asyncio
async def test_request_error_mappings():
    mapping = [
        (401, AirflowAuthError),
        (403, AirflowPermissionError),
        (404, AirflowNotFoundError),
        (409, AirflowConflictError),
    ]
    for status, exc in mapping:
        transport = _mk_transport(status, json_body={"detail": "x"})
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
            client = AirflowClient(http_client=ac)
            with pytest.raises(exc):
                await client._request("GET", "/api/v2/some")


@pytest.mark.asyncio
async def test_request_server_error_retries(monkeypatch):
    # always return 500
    def handler(request):
        return httpx.Response(500, text="boom")

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        client = AirflowClient(http_client=ac)

        async def _nosleep(_):
            return None

        monkeypatch.setattr(asyncio, "sleep", _nosleep)

        with pytest.raises(AirflowServerError):
            await client._request("GET", "/api/v2/some", retries=2)


@pytest.mark.asyncio
async def test_get_task_logs_parsing():
    transport = _mk_transport(200, json_body={"content": "my logs"})
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        client = AirflowClient(http_client=ac)
        logs = await client.get_task_logs("d", "r", "t")
        assert logs == "my logs"


@pytest.mark.asyncio
async def test_get_task_logs_airflow3_content_events_parsing():
    transport = _mk_transport(200, json_body={"content": [{"event": "line 1"}, {"event": "line 2"}]})
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        client = AirflowClient(http_client=ac)
        logs = await client.get_task_logs("d", "r", "t")
        assert logs == "line 1\nline 2"


@pytest.mark.asyncio
async def test_get_task_logs_falls_back_to_legacy_query_endpoint():
    calls = {"count": 0}

    def handler(request):
        calls["count"] += 1
        if request.url.path.endswith("/logs/1"):
            return httpx.Response(404, json={"detail": "not found"})
        if request.url.path.endswith("/logs"):
            assert request.url.params.get("try_number") == "1"
            return httpx.Response(200, json={"content": "legacy logs"})
        return httpx.Response(404, json={"detail": "not found"})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        client = AirflowClient(http_client=ac)
        logs = await client.get_task_logs("d", "r", "t")
        assert logs == "legacy logs"
        assert calls["count"] == 2


@pytest.mark.asyncio
async def test_create_connection_payload():
    def handler(request):
        # echo back the json payload
        import json as _json
        body = {}
        if request.content:
            try:
                body = _json.loads(request.content.decode())
            except Exception:
                body = {}
        assert body.get("connection_id") == "my_conn"
        assert body.get("conn_type") == "http"
        assert "type" not in body
        return httpx.Response(200, json=body)

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        client = AirflowClient(http_client=ac)
        res = await client.create_connection("my_conn", "http", "host", login="u", password="p", port=123)
        assert isinstance(res, dict)
        assert res.get("connection_id") == "my_conn"
