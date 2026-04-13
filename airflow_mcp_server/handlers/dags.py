from typing import Any
from airflow_mcp_server.airflow_client import client as airflow_client
from airflow_mcp_server.schemas import (
    ToolResponse,
    ListDagsParams,
    TriggerDagParams,
    DagIdParams,
    DagRunListParams,
    DagRunIdParams,
    ClearDagRunParams,
    SetDagRunStateParams,
)


async def list_dags(params: dict) -> ToolResponse:
    """List all available DAGs.

    Args:
        params: Dictionary containing:
            - limit (int, optional): Maximum number of DAGs to return. Default 100.
            - offset (int, optional): Pagination offset. Default 0.

    Returns:
        {"success": True, "data": [{"dag_id": str, "is_paused": bool, ...}], "error": None}

    Raises:
        AirflowConnectionError: If Airflow is unreachable.
        AirflowAuthError: If credentials are invalid.
    """
    validated = ListDagsParams.model_validate(params or {})
    dags = await airflow_client.list_dags(limit=validated.limit, offset=validated.offset)
    return ToolResponse(success=True, data=dags, error=None).model_dump()


async def get_dag(params: dict) -> ToolResponse:
    """Get details of a specific DAG.

    Args:
        params: Dictionary containing:
            - dag_id (str): The unique identifier of the DAG.

    Returns:
        {"success": True, "data": {"dag_id": str, "is_paused": bool, ...}, "error": None}

    Raises:
        ValueError: If dag_id is empty.
        AirflowNotFoundError: If the DAG does not exist.
        AirflowConnectionError: If Airflow is unreachable.
    """
    validated = DagIdParams.model_validate(params or {})
    dag = await airflow_client.get_dag(validated.dag_id)
    return ToolResponse(success=True, data=dag, error=None).model_dump()


async def trigger_dag(params: dict) -> ToolResponse:
    """Trigger a DAG run.

    Args:
        params: Dictionary containing:
            - dag_id (str): The unique identifier of the DAG to trigger.
            - conf (dict, optional): Optional run configuration.

    Returns:
        {"success": True, "data": {"dag_run_id": str, ...}, "error": None}

    Raises:
        ValueError: If dag_id is empty.
        AirflowNotFoundError: If the DAG does not exist.
        AirflowConnectionError: If Airflow is unreachable.
    """
    validated = TriggerDagParams.model_validate(params or {})
    result = await airflow_client.trigger_dag(validated.dag_id, conf=validated.conf)
    return ToolResponse(success=True, data=result, error=None).model_dump()


async def list_dag_runs(params: dict) -> ToolResponse:
    """List all runs of a specific DAG.

    Args:
        params: Dictionary containing:
            - dag_id (str): The unique identifier of the DAG.
            - limit (int, optional): Maximum number of runs to return. Default 100.

    Returns:
        {"success": True, "data": [{"dag_run_id": str, "state": str, ...}], "error": None}

    Raises:
        ValueError: If dag_id is empty.
        AirflowNotFoundError: If the DAG does not exist.
        AirflowConnectionError: If Airflow is unreachable.
    """
    validated = DagRunListParams.model_validate(params or {})
    runs = await airflow_client.list_dag_runs(validated.dag_id, limit=validated.limit)
    return ToolResponse(success=True, data=runs, error=None).model_dump()


TOOLS = {
    "airflow_dag_list": list_dags,
    "airflow_dag_get": get_dag,
    "airflow_dag_trigger": trigger_dag,
    "airflow_dag_run_list": list_dag_runs,
}


async def pause_dag(params: dict) -> ToolResponse:
    """Pause a DAG to prevent automatic scheduling.

    Args:
        params: Dictionary containing:
            - dag_id (str): The unique identifier of the DAG.

    Returns:
        {"success": True, "data": dict, "error": None}

    Raises:
        ValueError: If dag_id is empty.
        AirflowNotFoundError: If the DAG does not exist.
        AirflowConnectionError: If Airflow is unreachable.
    """
    validated = DagIdParams.model_validate(params or {})
    result = await airflow_client.pause_dag(validated.dag_id)
    return ToolResponse(success=True, data=result, error=None).model_dump()


async def unpause_dag(params: dict) -> ToolResponse:
    """Resume a paused DAG to enable automatic scheduling.

    Args:
        params: Dictionary containing:
            - dag_id (str): The unique identifier of the DAG.

    Returns:
        {"success": True, "data": dict, "error": None}

    Raises:
        ValueError: If dag_id is empty.
        AirflowNotFoundError: If the DAG does not exist.
        AirflowConnectionError: If Airflow is unreachable.
    """
    validated = DagIdParams.model_validate(params or {})
    result = await airflow_client.unpause_dag(validated.dag_id)
    return ToolResponse(success=True, data=result, error=None).model_dump()


async def get_dag_source(params: dict) -> ToolResponse:
    """Retrieve the source code of a DAG.

    Fetches the DAG metadata first to obtain the file_token, then retrieves
    the source code via the dagSources endpoint.

    Args:
        params: Dictionary containing:
            - dag_id (str): The DAG ID.

    Returns:
        {"success": bool, "data": dict | str, "error": str | None}

    Raises:
        ValueError: If dag_id is empty.
        AirflowNotFoundError: If the DAG does not exist.
        AirflowConnectionError: If Airflow is unreachable.
    """
    validated = DagIdParams.model_validate(params or {})
    dag = await airflow_client.get_dag(validated.dag_id)
    file_token = dag.get("file_token") if isinstance(dag, dict) else None
    if not file_token:
        return ToolResponse(success=False, data=None, error="file_token not available for this DAG").model_dump()
    source = await airflow_client.get_dag_source(file_token)
    return ToolResponse(success=True, data=source, error=None).model_dump()


async def get_dag_run(params: dict) -> ToolResponse:
    """Fetch details of a specific DAG run.

    Args:
        params: Dictionary containing:
            - dag_id (str): The unique identifier of the DAG.
            - run_id (str): The run identifier.

    Returns:
        {"success": True, "data": {"dag_run_id": str, "state": str, ...}, "error": None}

    Raises:
        ValueError: If dag_id or run_id is empty.
        AirflowNotFoundError: If the DAG or run does not exist.
        AirflowConnectionError: If Airflow is unreachable.
    """
    validated = DagRunIdParams.model_validate(params or {})
    run = await airflow_client.get_dag_run(validated.dag_id, validated.run_id)
    return ToolResponse(success=True, data=run, error=None).model_dump()


async def clear_dag_run(params: dict) -> ToolResponse:
    """Clear/re-run a DAG run from scratch or from failed tasks.

    Args:
        params: Dictionary containing:
            - dag_id (str): The unique identifier of the DAG.
            - run_id (str): The DAG run to clear.
            - only_failed (bool, optional): Only clear failed tasks. Default True.

    Returns:
        {"success": True, "data": dict, "error": None}

    Raises:
        ValueError: If dag_id or run_id is empty.
        AirflowNotFoundError: If the DAG or run does not exist.
        AirflowConnectionError: If Airflow is unreachable.
    """
    validated = ClearDagRunParams.model_validate(params or {})
    result = await airflow_client.clear_dag_run(validated.dag_id, validated.run_id, only_failed=validated.only_failed)
    return ToolResponse(success=True, data=result, error=None).model_dump()


async def cancel_dag_run(params: dict) -> ToolResponse:
    """Cancel/delete a running DAG run.

    Args:
        params: Dictionary containing:
            - dag_id (str): The unique identifier of the DAG.
            - run_id (str): The run identifier.

    Returns:
        {"success": True, "data": dict, "error": None}

    Raises:
        ValueError: If dag_id or run_id is empty.
        AirflowNotFoundError: If the DAG or run does not exist.
        AirflowConnectionError: If Airflow is unreachable.
    """
    validated = DagRunIdParams.model_validate(params or {})
    result = await airflow_client.delete_dag_run(validated.dag_id, validated.run_id)
    return ToolResponse(success=True, data=result, error=None).model_dump()


async def set_dag_run_state(params: dict) -> ToolResponse:
    """Update the state of a DAG run (mark as success, failed, queued, etc.).

    Args:
        params: Dictionary containing:
            - dag_id (str): The unique identifier of the DAG.
            - run_id (str): The run identifier.
            - state (str): Target state (e.g., 'success', 'failed', 'queued', 'running').

    Returns:
        {"success": True, "data": dict, "error": None}

    Raises:
        ValueError: If required parameters are empty or state is invalid.
        AirflowNotFoundError: If the DAG or run does not exist.
        AirflowConnectionError: If Airflow is unreachable.
    """
    validated = SetDagRunStateParams.model_validate(params or {})
    result = await airflow_client.update_dag_run_state(validated.dag_id, validated.run_id, validated.state)
    return ToolResponse(success=True, data=result, error=None).model_dump()


# extend TOOLS
TOOLS.update({
    "airflow_dag_pause": pause_dag,
    "airflow_dag_unpause": unpause_dag,
    "airflow_dag_source": get_dag_source,
    "airflow_dag_run_get": get_dag_run,
    "airflow_dag_run_clear": clear_dag_run,
    "airflow_dag_run_cancel": cancel_dag_run,
    "airflow_dag_run_set_state": set_dag_run_state,
})
