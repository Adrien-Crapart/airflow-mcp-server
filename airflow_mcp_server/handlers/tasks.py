from airflow_mcp_server.airflow_client import client as airflow_client
from airflow_mcp_server.schemas import (
    ToolResponse,
    TaskRunParams,
    RetryTaskParams,
    TaskListParams,
    TaskGetParams,
    SetTaskStateParams,
    ClearTaskParams,
)


async def list_task_instances(params: dict) -> dict:
    """List all task instances in a DAG run.

    Args:
        params: Dictionary containing:
            - dag_id (str): The unique identifier of the DAG.
            - run_id (str): The run identifier.

    Returns:
        {"success": True, "data": [{"task_id": str, "state": str, ...}], "error": None}

    Raises:
        ValueError: If dag_id or run_id is empty.
        AirflowNotFoundError: If the DAG or run does not exist.
        AirflowConnectionError: If Airflow is unreachable.
    """
    validated = TaskRunParams.model_validate(params or {})
    instances = await airflow_client.get_task_instances(validated.dag_id, validated.run_id)
    return ToolResponse(success=True, data=instances, error=None).model_dump()


TOOLS = {
    "airflow_task_list_instances": list_task_instances,
}


async def retry_task(params: dict) -> dict:
    """Retry a failed task in a DAG run.

    Args:
        params: Dictionary containing:
            - dag_id (str): The unique identifier of the DAG.
            - run_id (str): The run identifier.
            - task_id (str): The task identifier within the DAG.

    Returns:
        {"success": True, "data": dict, "error": None}

    Raises:
        ValueError: If any required parameter is empty.
        AirflowNotFoundError: If the DAG, run, or task does not exist.
        AirflowConnectionError: If Airflow is unreachable.
    """
    validated = RetryTaskParams.model_validate(params or {})
    result = await airflow_client.retry_task(validated.dag_id, validated.run_id, validated.task_id)
    return ToolResponse(success=True, data=result, error=None).model_dump()


async def list_tasks(params: dict) -> dict:
    """List all task definitions in a DAG.

    Returns the task structure/definitions, not task instances.

    Args:
        params: Dictionary containing:
            - dag_id (str): The unique identifier of the DAG.

    Returns:
        {"success": True, "data": [{"task_id": str, "task_type": str, ...}], "error": None}

    Raises:
        ValueError: If dag_id is empty.
        AirflowNotFoundError: If the DAG does not exist.
        AirflowConnectionError: If Airflow is unreachable.
    """
    validated = TaskListParams.model_validate(params or {})
    tasks = await airflow_client.list_tasks(validated.dag_id)
    return ToolResponse(success=True, data=tasks, error=None).model_dump()


async def get_task(params: dict) -> dict:
    """Get a specific task definition from a DAG.

    Args:
        params: Dictionary containing:
            - dag_id (str): The unique identifier of the DAG.
            - task_id (str): The task identifier within the DAG.

    Returns:
        {"success": True, "data": {"task_id": str, "task_type": str, ...}, "error": None}

    Raises:
        ValueError: If dag_id or task_id is empty.
        AirflowNotFoundError: If the DAG or task does not exist.
        AirflowConnectionError: If Airflow is unreachable.
    """
    validated = TaskGetParams.model_validate(params or {})
    task = await airflow_client.get_task(validated.dag_id, validated.task_id)
    return ToolResponse(success=True, data=task, error=None).model_dump()


async def set_task_state(params: dict) -> dict:
    """Update the state of a task instance.

    Args:
        params: Dictionary containing:
            - dag_id (str): The unique identifier of the DAG.
            - run_id (str): The run identifier.
            - task_id (str): The task identifier within the DAG.
            - state (str): Target state (e.g., 'success', 'failed', 'skipped', 'up_for_retry').

    Returns:
        {"success": True, "data": dict, "error": None}

    Raises:
        ValueError: If required parameters are empty or state is invalid.
        AirflowNotFoundError: If the DAG, run, or task does not exist.
        AirflowConnectionError: If Airflow is unreachable.
    """
    validated = SetTaskStateParams.model_validate(params or {})
    result = await airflow_client.set_task_instance_state(validated.dag_id, validated.run_id, validated.task_id, validated.state)
    return ToolResponse(success=True, data=result, error=None).model_dump()


async def clear_task(params: dict) -> dict:
    """Clear a task instance to force re-run.

    Args:
        params: Dictionary containing:
            - dag_id (str): The unique identifier of the DAG.
            - run_id (str): The run identifier.
            - task_id (str): The task identifier within the DAG.

    Returns:
        {"success": True, "data": dict, "error": None}

    Raises:
        ValueError: If required parameters are empty.
        AirflowNotFoundError: If the DAG, run, or task does not exist.
        AirflowConnectionError: If Airflow is unreachable.
    """
    validated = ClearTaskParams.model_validate(params or {})
    result = await airflow_client.clear_task_instance(validated.dag_id, validated.run_id, validated.task_id)
    return ToolResponse(success=True, data=result, error=None).model_dump()


TOOLS.update({
    "airflow_task_retry": retry_task,
    "airflow_task_list": list_tasks,
    "airflow_task_get": get_task,
    "airflow_task_set_state": set_task_state,
    "airflow_task_clear": clear_task,
})
