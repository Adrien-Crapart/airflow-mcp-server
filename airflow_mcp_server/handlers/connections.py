from typing import Any
from airflow_mcp_server.airflow_client import client as airflow_client
from airflow_mcp_server.schemas import (
    ToolResponse,
    CreateConnectionParams,
    ConnectionIdParams,
    ListConnectionsParams,
)


async def list_connections(params: dict) -> ToolResponse:
    validated = ListConnectionsParams.model_validate(params or {})
    connections = await airflow_client.list_connections(limit=validated.limit)
    return ToolResponse(success=True, data=connections, error=None).model_dump()


async def get_connection(params: dict) -> ToolResponse:
    validated = ConnectionIdParams.model_validate(params or {})
    connection = await airflow_client.get_connection(validated.conn_id)
    return ToolResponse(success=True, data=connection, error=None).model_dump()


async def delete_connection(params: dict) -> ToolResponse:
    validated = ConnectionIdParams.model_validate(params or {})
    result = await airflow_client.delete_connection(validated.conn_id)
    return ToolResponse(success=True, data=result, error=None).model_dump()


async def create_connection(params: dict) -> ToolResponse:
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
