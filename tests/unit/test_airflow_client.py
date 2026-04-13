import pytest
import httpx

from airflow_mcp_server.airflow_client import AirflowClient


def _mock_transport(request):
    url = request.url.path
    import json as _json
    body = {}
    if request.content:
        try:
            body = _json.loads(request.content.decode())
        except Exception:
            body = {}

    if request.method == "GET" and url == "/api/v1/dags":
        return httpx.Response(200, json={"dags": []})
    if request.method == "POST" and url.startswith("/api/v1/dags/") and url.endswith("/dagRuns"):
        return httpx.Response(200, json={"dag_run_id": "r1", "state": "queued"})
    if request.method == "PATCH" and url.startswith("/api/v1/dags/"):
        return httpx.Response(200, json={"dag_id": url.split("/")[-1], "is_paused": body.get("is_paused")})
    if request.method == "POST" and url.endswith("/setState"):
        return httpx.Response(200, json={"state": body.get("state")})
    return httpx.Response(404, json={"detail": "not found"})


@pytest.mark.asyncio
async def test_list_and_trigger_and_pause_unpause_and_retry():
    transport = httpx.MockTransport(_mock_transport)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        client = AirflowClient(http_client=ac)

        dags = await client.list_dags()
        assert isinstance(dags, list)

        res = await client.trigger_dag("my_dag", conf={})
        assert res["dag_run_id"] == "r1"

        res = await client.pause_dag("my_dag")
        assert res.get("is_paused") is True

        res = await client.unpause_dag("my_dag")
        assert res.get("is_paused") is False

        res = await client.retry_task("my_dag", "run1", "task1")
        assert res.get("state") == "queued"
