from typing import Any
from airflow_mcp_server.airflow_client import client as airflow_client
from airflow_mcp_server.schemas import ToolResponse, TaskRunParams, RetryTaskParams


async def list_task_instances(params: dict) -> ToolResponse:
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


async def retry_task(params: dict) -> ToolResponse:
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


TOOLS.update({
    "airflow_task_retry": retry_task,
})
