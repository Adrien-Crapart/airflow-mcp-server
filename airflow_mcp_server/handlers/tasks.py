from typing import Any
from airflow_mcp_server.airflow_client import client as airflow_client
from airflow_mcp_server.schemas import ToolResponse, TaskRunParams, RetryTaskParams


async def list_task_instances(params: dict) -> ToolResponse:
    validated = TaskRunParams.model_validate(params or {})
    instances = await airflow_client.get_task_instances(validated.dag_id, validated.run_id)
    return ToolResponse(success=True, data=instances, error=None).model_dump()


TOOLS = {
    "airflow_task_list_instances": list_task_instances,
}


async def retry_task(params: dict) -> ToolResponse:
    validated = RetryTaskParams.model_validate(params or {})
    result = await airflow_client.retry_task(validated.dag_id, validated.run_id, validated.task_id)
    return ToolResponse(success=True, data=result, error=None).model_dump()


TOOLS.update({
    "airflow_task_retry": retry_task,
})
