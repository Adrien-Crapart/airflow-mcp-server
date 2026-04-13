from typing import Any
from airflow_mcp_server.airflow_client import client as airflow_client
from airflow_mcp_server.schemas import ToolResponse, FetchLogsParams


async def fetch_task_logs(params: dict) -> ToolResponse:
    validated = FetchLogsParams.model_validate(params or {})
    logs = await airflow_client.get_task_logs(validated.dag_id, validated.run_id, validated.task_id, try_number=validated.try_number)
    return ToolResponse(success=True, data=logs, error=None).model_dump()


TOOLS = {
    "airflow_task_logs": fetch_task_logs,
}
