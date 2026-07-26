import os
import json
import socket
from urllib.parse import urlparse

import pytest
import pytest_asyncio
import httpx

from airflow_mcp_server.airflow_client import (
    AirflowClient,
    AirflowAuthError,
    AirflowConnectionError,
)


DEFAULT_INTEGRATION_TIMEOUT_SECONDS = 10.0


def _is_airflow_tcp_reachable(base_url: str, timeout_seconds: float) -> bool:
    """Return True when the Airflow host:port accepts TCP connections."""
    parsed = urlparse(base_url)
    if not parsed.hostname:
        return False

    port = parsed.port
    if port is None:
        port = 443 if parsed.scheme == "https" else 80

    try:
        with socket.create_connection((parsed.hostname, port), timeout=timeout_seconds):
            return True
    except OSError:
        return False


@pytest_asyncio.fixture
async def airflow_client():
    """Provide an AirflowClient connected to a real Airflow or a mock.

    The fixture attempts a lightweight `list_dags()` call to detect whether
    the real Airflow instance is reachable and accepts configured credentials.
    Fallback to `httpx.MockTransport` is opt-in via
    `AIRFLOW_INTEGRATION_ALLOW_MOCK_FALLBACK=true`.
    """
    base = os.getenv("AIRFLOW_BASE_URL", "http://localhost:8080")
    TEST_DAG_ID = os.getenv("TEST_DAG_ID", "example_bash_operator")
    allow_mock_fallback = os.getenv("AIRFLOW_INTEGRATION_ALLOW_MOCK_FALLBACK", "false").lower() == "true"
    timeout_seconds = float(os.getenv("AIRFLOW_INTEGRATION_TIMEOUT_SECONDS", str(DEFAULT_INTEGRATION_TIMEOUT_SECONDS)))

    if not allow_mock_fallback and not _is_airflow_tcp_reachable(base, timeout_seconds=1.0):
        pytest.skip("Real Airflow unavailable for integration tests: TCP endpoint unreachable")

    ac = httpx.AsyncClient(base_url=base, timeout=timeout_seconds)
    client = AirflowClient(base_url=base, http_client=ac)
    mock_ac = None
    try:
        # Lightweight probe to detect connectivity/auth
        await client.list_dags()
        yield client
    except (AirflowAuthError, AirflowConnectionError) as exc:
        if not allow_mock_fallback:
            pytest.skip(f"Real Airflow unavailable for integration tests: {exc}")

        # Fallback mock transport to simulate common Airflow endpoints
        from httpx import MockTransport

        def handler(request):
            path = request.url.path
            method = request.method.upper()

            # list dags
            if method == "GET" and path.endswith("/api/v2/dags"):
                return httpx.Response(200, json={"dags": [{"dag_id": TEST_DAG_ID}]})

            # list dag runs
            if method == "GET" and f"/api/v2/dags/{TEST_DAG_ID}/dagRuns" in path:
                return httpx.Response(200, json={"dag_runs": [{"dag_run_id": "manual__1"}]})

            # get task instances
            if method == "GET" and ("/dagRuns/" in path and "/taskInstances" in path):
                return httpx.Response(200, json={"task_instances": [{"task_id": "task_1", "state": "success"}]})

            # get task logs
            if method == "GET" and path.endswith("/logs"):
                return httpx.Response(200, json={"content": "mock log content"})

            # trigger dag
            if method == "POST" and f"/api/v2/dags/{TEST_DAG_ID}/dagRuns" in path:
                return httpx.Response(200, json={"dag_run_id": "manual__1"})

            # create connection (echo payload)
            if method == "POST" and (path.endswith("/api/v2/connections") or "/connections" in path):
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
            if method == "PATCH" and "/api/v2/dags/" in path:
                try:
                    payload = json.loads(request.content.decode()) if request.content else {}
                except Exception:
                    payload = {}
                return httpx.Response(200, json=payload or {"result": "ok"})

            # Legacy setState / retry task
            if method == "POST" and "setState" in path:
                return httpx.Response(200, json={"status": "queued"})

            # Airflow 3 retry strategy (clear task instances)
            if method == "POST" and path.endswith("/clearTaskInstances"):
                return httpx.Response(200, json={"task_instances": [], "total_entries": 0})

            return httpx.Response(404, json={"detail": "Not found"})

        transport = MockTransport(handler)
        mock_ac = httpx.AsyncClient(transport=transport, base_url=base, timeout=timeout_seconds)
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
