
from airflow_mcp_server.airflow_client import client as airflow_client
from airflow_mcp_server.schemas import (
    ToolResponse,
    ListEventLogsParams,
    EventLogIdParams,
)


async def list_event_logs(params: dict) -> dict:
    """List Airflow audit trail / event logs.

    Useful for tracking who triggered what and when, including DAG runs,
    state changes, and configuration modifications.

    Args:
        params: Dictionary containing:
            - limit (int, optional): Maximum number of events to return. Default 100.
            - dag_id (str, optional): Filter by DAG ID.
            - event (str, optional): Filter by event type (e.g., 'trigger', 'pause', 'success').

    Returns:
        {"success": True, "data": [{"event_id": int, "event": str, "dag_id": str, ...}], "error": None}

    Raises:
        AirflowConnectionError: If Airflow is unreachable.
        AirflowPermissionError: If user lacks audit log read permissions.
    """
    validated = ListEventLogsParams.model_validate(params or {})
    logs = await airflow_client.list_event_logs(limit=validated.limit, dag_id=validated.dag_id, event=validated.event)
    return ToolResponse(success=True, data=logs, error=None).model_dump()


async def get_event_log(params: dict) -> dict:
    """Fetch details of a specific audit event.

    Args:
        params: Dictionary containing:
            - event_log_id (int): Numeric ID of the audit event.

    Returns:
        {"success": True, "data": {"event_id": int, "event": str, "dag_id": str, ...}, "error": None}

    Raises:
        ValueError: If event_log_id is invalid.
        AirflowNotFoundError: If the event does not exist.
        AirflowConnectionError: If Airflow is unreachable.
    """
    validated = EventLogIdParams.model_validate(params or {})
    log = await airflow_client.get_event_log(validated.event_log_id)
    return ToolResponse(success=True, data=log, error=None).model_dump()


TOOLS = {
    "airflow_event_log_list": list_event_logs,
    "airflow_event_log_get": get_event_log,
}
