import pytest
import airflow_mcp_server.airflow_client as _client
from airflow_mcp_server.airflow_client import (
    AirflowNotFoundError,
    AirflowConnectionError,
    AirflowAuthError,
)
from airflow_mcp_server.handlers import agent_tools


# ---------------------------------------------------------------------------
# diagnose_dag_run
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_diagnose_dag_run_success(monkeypatch):
    """All tasks passed — no failed tasks, no logs fetched."""

    async def _fake_list_dag_runs(dag_id, limit=100):
        return [{"dag_run_id": "run_1", "state": "success"}]

    async def _fake_get_task_instances(dag_id, run_id):
        return [
            {"task_id": "task_a", "state": "success"},
            {"task_id": "task_b", "state": "success"},
        ]

    monkeypatch.setattr(_client.client, "list_dag_runs", _fake_list_dag_runs)
    monkeypatch.setattr(_client.client, "get_task_instances", _fake_get_task_instances)

    res = await agent_tools.diagnose_dag_run({"dag_id": "my_dag", "run_id": "run_1"})

    assert res["success"] is True
    assert res["data"]["dag_run"]["dag_run_id"] == "run_1"
    assert res["data"]["failed_tasks"] == []
    assert res["data"]["task_logs"] == {}
    assert res["error"] is None


@pytest.mark.asyncio
async def test_diagnose_dag_run_with_failures(monkeypatch):
    """One failed task — logs should be fetched for it."""

    async def _fake_list_dag_runs(dag_id, limit=100):
        return [{"dag_run_id": "run_2", "state": "failed"}]

    async def _fake_get_task_instances(dag_id, run_id):
        return [
            {"task_id": "task_ok", "state": "success"},
            {"task_id": "task_fail", "state": "failed", "try_number": 1},
        ]

    async def _fake_get_task_logs(dag_id, run_id, task_id, try_number=1):
        return "Traceback (most recent call last): ..."

    monkeypatch.setattr(_client.client, "list_dag_runs", _fake_list_dag_runs)
    monkeypatch.setattr(_client.client, "get_task_instances", _fake_get_task_instances)
    monkeypatch.setattr(_client.client, "get_task_logs", _fake_get_task_logs)

    res = await agent_tools.diagnose_dag_run({"dag_id": "my_dag", "run_id": "run_2"})

    assert res["success"] is True
    assert len(res["data"]["failed_tasks"]) == 1
    assert res["data"]["failed_tasks"][0]["task_id"] == "task_fail"
    assert "task_fail" in res["data"]["task_logs"]
    assert "Traceback" in res["data"]["task_logs"]["task_fail"]


@pytest.mark.asyncio
async def test_diagnose_dag_run_upstream_failed(monkeypatch):
    """upstream_failed tasks are also counted as failed."""

    async def _fake_list_dag_runs(dag_id, limit=100):
        return [{"dag_run_id": "run_3", "state": "failed"}]

    async def _fake_get_task_instances(dag_id, run_id):
        return [
            {"task_id": "task_upstream", "state": "upstream_failed", "try_number": 1},
        ]

    async def _fake_get_task_logs(dag_id, run_id, task_id, try_number=1):
        return "[upstream failed log]"

    monkeypatch.setattr(_client.client, "list_dag_runs", _fake_list_dag_runs)
    monkeypatch.setattr(_client.client, "get_task_instances", _fake_get_task_instances)
    monkeypatch.setattr(_client.client, "get_task_logs", _fake_get_task_logs)

    res = await agent_tools.diagnose_dag_run({"dag_id": "my_dag", "run_id": "run_3"})

    assert res["success"] is True
    assert len(res["data"]["failed_tasks"]) == 1
    assert res["data"]["failed_tasks"][0]["state"] == "upstream_failed"


@pytest.mark.asyncio
async def test_diagnose_dag_run_missing_params():
    with pytest.raises(Exception):
        await agent_tools.diagnose_dag_run({})


@pytest.mark.asyncio
async def test_diagnose_dag_run_missing_run_id():
    with pytest.raises(Exception):
        await agent_tools.diagnose_dag_run({"dag_id": "my_dag"})


@pytest.mark.asyncio
async def test_diagnose_dag_run_connection_error(monkeypatch):
    """AirflowConnectionError from list_dag_runs is caught internally and returns success=False."""

    async def _fake_list_dag_runs(dag_id, limit=100):
        raise AirflowConnectionError("unreachable")

    monkeypatch.setattr(_client.client, "list_dag_runs", _fake_list_dag_runs)

    res = await agent_tools.diagnose_dag_run({"dag_id": "my_dag", "run_id": "run_1"})

    assert res["success"] is False
    assert res["error"] is not None
    assert "unreachable" in res["error"]


@pytest.mark.asyncio
async def test_diagnose_dag_run_not_found_returns_none_dag_run(monkeypatch):
    """When run_id does not match any run, dag_run is None but success is still True."""

    async def _fake_list_dag_runs(dag_id, limit=100):
        return [{"dag_run_id": "different_run", "state": "success"}]

    async def _fake_get_task_instances(dag_id, run_id):
        return []

    monkeypatch.setattr(_client.client, "list_dag_runs", _fake_list_dag_runs)
    monkeypatch.setattr(_client.client, "get_task_instances", _fake_get_task_instances)

    res = await agent_tools.diagnose_dag_run({"dag_id": "my_dag", "run_id": "nonexistent"})

    assert res["success"] is True
    assert res["data"]["dag_run"] is None


@pytest.mark.asyncio
async def test_diagnose_dag_run_log_fetch_failure(monkeypatch):
    """If log fetching fails, task_logs contains the fallback sentinel."""

    async def _fake_list_dag_runs(dag_id, limit=100):
        return [{"dag_run_id": "run_1", "state": "failed"}]

    async def _fake_get_task_instances(dag_id, run_id):
        return [{"task_id": "bad_task", "state": "failed", "try_number": 1}]

    async def _fake_get_task_logs(dag_id, run_id, task_id, try_number=1):
        raise Exception("log service down")

    monkeypatch.setattr(_client.client, "list_dag_runs", _fake_list_dag_runs)
    monkeypatch.setattr(_client.client, "get_task_instances", _fake_get_task_instances)
    monkeypatch.setattr(_client.client, "get_task_logs", _fake_get_task_logs)

    res = await agent_tools.diagnose_dag_run({"dag_id": "my_dag", "run_id": "run_1"})

    assert res["success"] is True
    assert res["data"]["task_logs"]["bad_task"] == "[Unable to fetch logs]"


# ---------------------------------------------------------------------------
# system_health
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_system_health_success(monkeypatch):
    """All sub-calls succeed — result has health, import_errors, and pools keys."""

    async def _fake_health(*args, **kwargs):
        return {"metadatabase": {"status": "healthy"}, "scheduler": {"status": "healthy"}}

    async def _fake_import_errors(limit=50):
        return []

    async def _fake_pools(limit=100):
        return [{"name": "default_pool", "slots": 128}]

    monkeypatch.setattr(_client.client, "_request_with_fallback", _fake_health)
    monkeypatch.setattr(_client.client, "list_import_errors", _fake_import_errors)
    monkeypatch.setattr(_client.client, "list_pools", _fake_pools)

    res = await agent_tools.system_health({})

    assert res["success"] is True
    assert res["data"]["health"]["metadatabase"]["status"] == "healthy"
    assert res["data"]["import_errors"] == []
    assert isinstance(res["data"]["pools"], list)
    assert res["error"] is None


@pytest.mark.asyncio
async def test_system_health_partial_failure_health(monkeypatch):
    """Health check fails — result still has success=True with error recorded in health key."""

    async def _fake_health(*args, **kwargs):
        raise AirflowConnectionError("health endpoint unreachable")

    async def _fake_import_errors(limit=50):
        return []

    async def _fake_pools(limit=100):
        return []

    monkeypatch.setattr(_client.client, "_request_with_fallback", _fake_health)
    monkeypatch.setattr(_client.client, "list_import_errors", _fake_import_errors)
    monkeypatch.setattr(_client.client, "list_pools", _fake_pools)

    res = await agent_tools.system_health({})

    assert res["success"] is True
    assert "error" in res["data"]["health"]
    assert "unreachable" in res["data"]["health"]["error"]


@pytest.mark.asyncio
async def test_system_health_partial_failure_import_errors(monkeypatch):
    """import_errors call fails — result still has success=True with empty list."""

    async def _fake_health(*args, **kwargs):
        return {"status": "healthy"}

    async def _fake_import_errors(limit=50):
        raise AirflowConnectionError("unreachable")

    async def _fake_pools(limit=100):
        return []

    monkeypatch.setattr(_client.client, "_request_with_fallback", _fake_health)
    monkeypatch.setattr(_client.client, "list_import_errors", _fake_import_errors)
    monkeypatch.setattr(_client.client, "list_pools", _fake_pools)

    res = await agent_tools.system_health({})

    assert res["success"] is True
    assert res["data"]["import_errors"] == []


@pytest.mark.asyncio
async def test_system_health_partial_failure_pools(monkeypatch):
    """pools call fails — result still has success=True with empty list."""

    async def _fake_health(*args, **kwargs):
        return {"status": "healthy"}

    async def _fake_import_errors(limit=50):
        return []

    async def _fake_pools(limit=100):
        raise AirflowConnectionError("unreachable")

    monkeypatch.setattr(_client.client, "_request_with_fallback", _fake_health)
    monkeypatch.setattr(_client.client, "list_import_errors", _fake_import_errors)
    monkeypatch.setattr(_client.client, "list_pools", _fake_pools)

    res = await agent_tools.system_health({})

    assert res["success"] is True
    assert res["data"]["pools"] == []


@pytest.mark.asyncio
async def test_system_health_all_fail(monkeypatch):
    """All sub-calls fail — result still has success=True with degraded data."""

    async def _fake_health(*args, **kwargs):
        raise AirflowConnectionError("down")

    async def _fake_import_errors(limit=50):
        raise AirflowConnectionError("down")

    async def _fake_pools(limit=100):
        raise AirflowConnectionError("down")

    monkeypatch.setattr(_client.client, "_request_with_fallback", _fake_health)
    monkeypatch.setattr(_client.client, "list_import_errors", _fake_import_errors)
    monkeypatch.setattr(_client.client, "list_pools", _fake_pools)

    res = await agent_tools.system_health({})

    assert res["success"] is True
    assert "error" in res["data"]["health"]
    assert res["data"]["import_errors"] == []
    assert res["data"]["pools"] == []
