import os
import json

import pytest
import pytest_asyncio
import httpx

from airflow_mcp_server.airflow_client import (
    AirflowClient,
    AirflowAuthError,
    AirflowConnectionError,
)


@pytest_asyncio.fixture
async def airflow_client():
    """Provide an AirflowClient connected to a real Airflow or a mock.

    The fixture attempts a lightweight `list_dags()` call to detect whether
    the real Airflow instance is reachable and accepts the configured
    credentials. If the request fails with authentication or connection
    errors, the fixture falls back to an `httpx.MockTransport` that simulates
    a richer set of endpoints used by integration tests.
    """
    base = os.getenv("AIRFLOW_BASE_URL", "http://localhost:8080")
    TEST_DAG_ID = os.getenv("TEST_DAG_ID", "example_bash_operator")

    ac = httpx.AsyncClient()
    client = AirflowClient(base_url=base, http_client=ac)
    mock_ac = None
    try:
        # Lightweight probe to detect connectivity/auth
        await client.list_dags()
        yield client
    except (AirflowAuthError, AirflowConnectionError):
        # Fallback mock transport to simulate common Airflow endpoints
        from httpx import MockTransport

        def handler(request):
            path = request.url.path
            method = request.method.upper()

            # list dags
            if method == "GET" and (path.endswith("/api/v1/dags") or path.endswith("/api/v2/dags")):
                return httpx.Response(200, json={"dags": [{"dag_id": TEST_DAG_ID}]})

            # list dag runs
            if (
                method == "GET"
                and (f"/api/v1/dags/{TEST_DAG_ID}/dagRuns" in path or f"/api/v2/dags/{TEST_DAG_ID}/dagRuns" in path)
            ):
                return httpx.Response(200, json={"dag_runs": [{"dag_run_id": "manual__1"}]})

            # get task instances
            if method == "GET" and ("/dagRuns/" in path and "/taskInstances" in path):
                return httpx.Response(200, json={"task_instances": [{"task_id": "task_1", "state": "success"}]})

            # get task logs
            if method == "GET" and path.endswith("/logs"):
                return httpx.Response(200, json={"content": "mock log content"})

            # trigger dag
            if (
                method == "POST"
                and (f"/api/v1/dags/{TEST_DAG_ID}/dagRuns" in path or f"/api/v2/dags/{TEST_DAG_ID}/dagRuns" in path)
            ):
                return httpx.Response(200, json={"dag_run_id": "manual__1"})

            # create connection (echo payload)
            if method == "POST" and (path.endswith("/api/v1/connections") or path.endswith("/api/v2/connections") or "/connections" in path):
                try:
                    body = json.loads(request.content.decode()) if request.content else {}
                except Exception:
                    body = {}
                if "connection_id" not in body and "conn_id" in body:
                    body["connection_id"] = body.get("conn_id")
                if "connection_id" not in body:
                    body["connection_id"] = "mock_conn"
                return httpx.Response(200, json=body)

            # pause/unpause dag (PATCH)
            if method == "PATCH" and ("/api/v1/dags/" in path or "/api/v2/dags/" in path):
                try:
                    payload = json.loads(request.content.decode()) if request.content else {}
                except Exception:
                    payload = {}
                return httpx.Response(200, json=payload or {"result": "ok"})

            # setState / retry task
            if method == "POST" and "setState" in path:
                return httpx.Response(200, json={"status": "queued"})

            return httpx.Response(404, json={"detail": "Not found"})

        transport = MockTransport(handler)
        mock_ac = httpx.AsyncClient(transport=transport, base_url=base)
        client = AirflowClient(base_url=base, http_client=mock_ac)
        yield client
    finally:
        try:
            await ac.aclose()
        except Exception:
            pass
        if mock_ac is not None:
            try:
                await mock_ac.aclose()
            except Exception:
                pass
