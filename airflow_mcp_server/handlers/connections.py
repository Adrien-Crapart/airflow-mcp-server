import re
from typing import Any

from airflow_mcp_server.airflow_client import client as airflow_client
from airflow_mcp_server.schemas import (
    ToolResponse,
    CreateConnectionParams,
    ConnectionIdParams,
    ListConnectionsParams,
)


SENSITIVE_CONNECTION_KEY_RE = re.compile(
    r"(password|passwd|secret|token|api[_-]?key|access[_-]?key|private[_-]?key|credential|client[_-]?secret|fernet|jwt|extra|uri)",
    re.IGNORECASE,
)


def _is_sensitive_connection_key(key: str) -> bool:
    """Return True if a key likely carries connection secrets."""
    return bool(SENSITIVE_CONNECTION_KEY_RE.search(key))


def _mask_connection_payload(value: Any) -> Any:
    """Recursively mask sensitive keys in connection payloads."""
    if isinstance(value, dict):
        masked: dict[Any, Any] = {}
        for key, nested in value.items():
            key_text = str(key)
            if _is_sensitive_connection_key(key_text):
                masked[key] = "***MASKED***"
            else:
                masked[key] = _mask_connection_payload(nested)
        return masked
    if isinstance(value, list):
        return [_mask_connection_payload(item) for item in value]
    return value


async def list_connections(params: dict) -> dict:
    """List all Airflow connections.

    Args:
        params: Dictionary containing:
            - limit (int, optional): Maximum number of connections to return. Default 100.

    Returns:
        {"success": True, "data": [{"conn_id": str, "conn_type": str, ...}], "error": None}
        Sensitive fields are masked in the response.

    Raises:
        AirflowConnectionError: If Airflow is unreachable.
        AirflowAuthError: If credentials are invalid.
    """
    validated = ListConnectionsParams.model_validate(params or {})
    connections = await airflow_client.list_connections(limit=validated.limit)
    return ToolResponse(success=True, data=_mask_connection_payload(connections), error=None).model_dump()


async def get_connection(params: dict) -> dict:
    """Get details of a specific connection.

    Args:
        params: Dictionary containing:
            - conn_id (str): Unique connection identifier.

    Returns:
        {"success": True, "data": {"conn_id": str, "conn_type": str, ...}, "error": None}
        Sensitive fields are masked in the response.

    Raises:
        ValueError: If conn_id is empty.
        AirflowNotFoundError: If the connection does not exist.
        AirflowConnectionError: If Airflow is unreachable.
    """
    validated = ConnectionIdParams.model_validate(params or {})
    connection = await airflow_client.get_connection(validated.conn_id)
    return ToolResponse(success=True, data=_mask_connection_payload(connection), error=None).model_dump()


async def delete_connection(params: dict) -> dict:
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


async def create_connection(params: dict) -> dict:
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
        Sensitive fields are masked in the response.

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
    return ToolResponse(success=True, data=_mask_connection_payload(result), error=None).model_dump()


TOOLS = {
    "airflow_connection_list": list_connections,
    "airflow_connection_get": get_connection,
    "airflow_connection_delete": delete_connection,
    "airflow_connection_create": create_connection,
}
