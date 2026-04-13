from typing import Any

from airflow_mcp_server.airflow_client import client as airflow_client
from airflow_mcp_server.schemas import (
    ToolResponse,
    XcomGetParams,
)


async def get_xcom(params: dict) -> ToolResponse:
    """Retrieve an XCom value from a task instance.

    Args:
        params: Dictionary containing:
            - dag_id (str): The DAG ID.
            - run_id (str): The DAG run ID.
            - task_id (str): The task ID.
            - key (str): The XCom key.

    Returns:
        {"success": bool, "data": dict, "error": str | None}

    Raises:
        ValueError: If any required parameter is empty.
        AirflowNotFoundError: If XCom not found.
        AirflowConnectionError: If Airflow is unreachable.
    """
    validated = XcomGetParams.model_validate(params or {})
    xcom = await airflow_client.get_xcom(
        validated.dag_id,
        validated.run_id,
        validated.task_id,
        validated.key,
    )
    return ToolResponse(success=True, data=xcom, error=None).model_dump()


TOOLS = {
    "airflow_xcom_get": get_xcom,
}
