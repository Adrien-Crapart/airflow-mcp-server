from typing import Any

from airflow_mcp_server.airflow_client import client as airflow_client
from airflow_mcp_server.schemas import (
    ToolResponse,
    DiagnoseDagRunParams,
    SystemHealthParams,
)


async def diagnose_dag_run(params: dict) -> ToolResponse:
    """Diagnose a DAG run by aggregating status, failed tasks, and logs.

    This tool combines multiple API calls into one, reducing LLM iterations.
    Useful for quickly understanding what went wrong with a DAG run.

    Args:
        params: Dictionary containing:
            - dag_id (str): The DAG ID.
            - run_id (str): The DAG run ID.

    Returns:
        {"success": bool, "data": {
            "dag_run": dict,
            "failed_tasks": list[dict],
            "task_logs": dict[str, str]  # task_id -> log content
        }, "error": str | None}

    Raises:
        ValueError: If dag_id or run_id is empty.
        AirflowNotFoundError: If DAG run not found.
        AirflowConnectionError: If Airflow is unreachable.
    """
    validated = DiagnoseDagRunParams.model_validate(params or {})

    # Fetch the DAG run and all task instances
    dag_run = None
    task_instances = []

    try:
        # Get the DAG run details
        dag_runs = await airflow_client.list_dag_runs(validated.dag_id, limit=100)
        dag_run = next((r for r in dag_runs if r.get("dag_run_id") == validated.run_id or r.get("run_id") == validated.run_id), None)

        # Get all task instances for this run
        task_instances = await airflow_client.get_task_instances(validated.dag_id, validated.run_id)
    except Exception as e:
        return ToolResponse(success=False, data=None, error=f"Failed to fetch DAG run details: {str(e)}").model_dump()

    # Filter failed tasks
    failed_tasks = [t for t in task_instances if t.get("state") in ("failed", "upstream_failed")]

    # Fetch logs for failed tasks (up to 5 to avoid overload)
    task_logs: dict[str, str] = {}
    for task in failed_tasks[:5]:
        try:
            task_id = task.get("task_id")
            logs = await airflow_client.get_task_logs(
                validated.dag_id,
                validated.run_id,
                task_id,
                try_number=task.get("try_number", 1),
            )
            task_logs[task_id] = logs
        except Exception:
            task_logs[task_id] = "[Unable to fetch logs]"

    result = {
        "dag_run": dag_run,
        "failed_tasks": failed_tasks,
        "task_logs": task_logs,
    }
    return ToolResponse(success=True, data=result, error=None).model_dump()


async def system_health(params: dict) -> ToolResponse:
    """Get a health overview of the Airflow system.

    Aggregates health status, import errors, and pool usage in one call.
    Useful for quick system diagnostics.

    Args:
        params: Empty dictionary (no parameters).

    Returns:
        {"success": bool, "data": {
            "health": dict,
            "import_errors": list[dict],
            "pools": list[dict]
        }, "error": str | None}

    Raises:
        AirflowConnectionError: If Airflow is unreachable.
    """
    result = {}

    try:
        # Attempt to get health status (generic endpoint)
        health = await airflow_client._request_with_fallback("GET", f"{airflow_client.api_prefix}/health")
        result["health"] = health if isinstance(health, dict) else {"status": str(health)}
    except Exception as e:
        result["health"] = {"error": str(e)}

    try:
        # Get import errors
        errors = await airflow_client.list_import_errors(limit=50)
        result["import_errors"] = errors
    except Exception as e:
        result["import_errors"] = []

    try:
        # Get pool stats
        pools = await airflow_client.list_pools(limit=100)
        result["pools"] = pools
    except Exception as e:
        result["pools"] = []

    return ToolResponse(success=True, data=result, error=None).model_dump()


TOOLS = {
    "airflow_dag_diagnose": diagnose_dag_run,
    "airflow_system_health": system_health,
}
