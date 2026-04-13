from typing import Any
from airflow_mcp_server.airflow_client import client as airflow_client
from airflow_mcp_server.schemas import (
    ToolResponse,
    ListDagsParams,
    TriggerDagParams,
    DagIdParams,
    DagRunListParams,
)


async def list_dags(params: dict) -> ToolResponse:
    validated = ListDagsParams.model_validate(params or {})
    dags = await airflow_client.list_dags(limit=validated.limit, offset=validated.offset)
    return ToolResponse(success=True, data=dags, error=None).model_dump()


async def get_dag(params: dict) -> ToolResponse:
    validated = DagIdParams.model_validate(params or {})
    dag = await airflow_client.get_dag(validated.dag_id)
    return ToolResponse(success=True, data=dag, error=None).model_dump()


async def trigger_dag(params: dict) -> ToolResponse:
    validated = TriggerDagParams.model_validate(params or {})
    result = await airflow_client.trigger_dag(validated.dag_id, conf=validated.conf)
    return ToolResponse(success=True, data=result, error=None).model_dump()


async def list_dag_runs(params: dict) -> ToolResponse:
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
    validated = DagIdParams.model_validate(params or {})
    result = await airflow_client.pause_dag(validated.dag_id)
    return ToolResponse(success=True, data=result, error=None).model_dump()


async def unpause_dag(params: dict) -> ToolResponse:
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


# extend TOOLS
TOOLS.update({
    "airflow_dag_pause": pause_dag,
    "airflow_dag_unpause": unpause_dag,
    "airflow_dag_source": get_dag_source,
})
