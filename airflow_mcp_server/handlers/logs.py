from typing import Any
from airflow_mcp_server.airflow_client import client as airflow_client
from airflow_mcp_server.schemas import ToolResponse, FetchLogsParams


async def fetch_task_logs(params: dict) -> ToolResponse:
    """Fetch logs for a specific task in a DAG run.

    Args:
        params: Dictionary containing:
            - dag_id (str): The unique identifier of the DAG.
            - run_id (str): The run identifier.
            - task_id (str): The task identifier within the DAG.
            - try_number (int, optional): Attempt number (1 = first try, 2 = first retry, etc.). Default 1.

    Returns:
        {"success": True, "data": str, "error": None}

    Raises:
        ValueError: If any required parameter is empty.
        AirflowNotFoundError: If the DAG, run, or task does not exist.
        AirflowConnectionError: If Airflow is unreachable.
    """
    validated = FetchLogsParams.model_validate(params or {})
    logs = await airflow_client.get_task_logs(validated.dag_id, validated.run_id, validated.task_id, try_number=validated.try_number)
    return ToolResponse(success=True, data=logs, error=None).model_dump()


TOOLS = {
    "airflow_task_logs": fetch_task_logs,
}
