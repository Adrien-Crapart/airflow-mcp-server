from typing import Any
from airflow_mcp_server.airflow_client import client as airflow_client
from airflow_mcp_server.schemas import (
    ToolResponse,
    CreateConnectionParams,
    ConnectionIdParams,
    ListConnectionsParams,
)


async def list_connections(params: dict) -> ToolResponse:
    """List all Airflow connections.

    Args:
        params: Dictionary containing:
            - limit (int, optional): Maximum number of connections to return. Default 100.

    Returns:
        {"success": True, "data": [{"conn_id": str, "conn_type": str, ...}], "error": None}

    Raises:
        AirflowConnectionError: If Airflow is unreachable.
        AirflowAuthError: If credentials are invalid.
    """
    validated = ListConnectionsParams.model_validate(params or {})
    connections = await airflow_client.list_connections(limit=validated.limit)
    return ToolResponse(success=True, data=connections, error=None).model_dump()


async def get_connection(params: dict) -> ToolResponse:
    """Get details of a specific connection.

    Args:
        params: Dictionary containing:
            - conn_id (str): Unique connection identifier.

    Returns:
        {"success": True, "data": {"conn_id": str, "conn_type": str, ...}, "error": None}

    Raises:
        ValueError: If conn_id is empty.
        AirflowNotFoundError: If the connection does not exist.
        AirflowConnectionError: If Airflow is unreachable.
    """
    validated = ConnectionIdParams.model_validate(params or {})
    connection = await airflow_client.get_connection(validated.conn_id)
    return ToolResponse(success=True, data=connection, error=None).model_dump()


async def delete_connection(params: dict) -> ToolResponse:
    """Delete a connection.

    Args:
        params: Dictionary containing:
            - conn_id (str): Unique connection identifier.

    Returns:
        {"success": True, "data": dict, "error": None}

    Raises:
        ValueError: If conn_id is empty.
        AirflowNotFoundError: If the connection does not exist.
        AirflowConnectionError: If Airflow is unreachable.
    """
    validated = ConnectionIdParams.model_validate(params or {})
    result = await airflow_client.delete_connection(validated.conn_id)
    return ToolResponse(success=True, data=result, error=None).model_dump()


async def create_connection(params: dict) -> ToolResponse:
    """Create a new Airflow connection.

    Args:
        params: Dictionary containing:
            - conn_id (str): Unique connection identifier.
            - type (str): Connection type (e.g. 'http', 'postgres', 'aws').
            - host (str, optional): Connection host.
            - login (str, optional): Login/username.
            - password (str, optional): Password.
            - port (int, optional): Connection port.
            - extra (dict, optional): Extra configuration JSON.

    Returns:
        {"success": True, "data": dict, "error": None}

    Raises:
        ValueError: If conn_id is empty.
        AirflowConflictError: If connection already exists.
        AirflowConnectionError: If Airflow is unreachable.
    """
    validated = CreateConnectionParams.model_validate(params or {})
    result = await airflow_client.create_connection(
        conn_id=validated.conn_id,
        conn_type=validated.type,
        host=validated.host,
        login=validated.login,
        password=validated.password,
        port=validated.port,
        extra=validated.extra,
    )
    return ToolResponse(success=True, data=result, error=None).model_dump()


TOOLS = {
    "airflow_connection_list": list_connections,
    "airflow_connection_get": get_connection,
    "airflow_connection_delete": delete_connection,
    "airflow_connection_create": create_connection,
}
