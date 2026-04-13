from typing import Any

from airflow_mcp_server.airflow_client import client as airflow_client
from airflow_mcp_server.schemas import (
    ToolResponse,
    ListVariablesParams,
    VariableKeyParams,
    SetVariableParams,
)


async def list_variables(params: dict) -> ToolResponse:
    """List all Airflow variables.

    Args:
        params: Dictionary containing:
            - limit (int, optional): Maximum number of variables to return (default: 100).

    Returns:
        {"success": bool, "data": list[dict], "error": str | None}

    Raises:
        AirflowConnectionError: If Airflow is unreachable.
    """
    validated = ListVariablesParams.model_validate(params or {})
    variables = await airflow_client.list_variables(limit=validated.limit)
    return ToolResponse(success=True, data=variables, error=None).model_dump()


async def get_variable(params: dict) -> ToolResponse:
    """Retrieve an Airflow variable by key.

    Args:
        params: Dictionary containing:
            - key (str): The variable key.

    Returns:
        {"success": bool, "data": dict, "error": str | None}

    Raises:
        ValueError: If key is empty.
        AirflowNotFoundError: If variable not found.
        AirflowConnectionError: If Airflow is unreachable.
    """
    validated = VariableKeyParams.model_validate(params or {})
    variable = await airflow_client.get_variable(validated.key)
    return ToolResponse(success=True, data=variable, error=None).model_dump()


async def set_variable(params: dict) -> ToolResponse:
    """Create or update an Airflow variable.

    Args:
        params: Dictionary containing:
            - key (str): The variable key.
            - value (str): The variable value.

    Returns:
        {"success": bool, "data": dict, "error": str | None}

    Raises:
        ValueError: If key or value is empty.
        AirflowConnectionError: If Airflow is unreachable.
    """
    validated = SetVariableParams.model_validate(params or {})
    variable = await airflow_client.set_variable(validated.key, validated.value)
    return ToolResponse(success=True, data=variable, error=None).model_dump()


async def delete_variable(params: dict) -> ToolResponse:
    """Delete an Airflow variable.

    Args:
        params: Dictionary containing:
            - key (str): The variable key.

    Returns:
        {"success": bool, "data": dict, "error": str | None}

    Raises:
        ValueError: If key is empty.
        AirflowNotFoundError: If variable not found.
        AirflowConnectionError: If Airflow is unreachable.
    """
    validated = VariableKeyParams.model_validate(params or {})
    result = await airflow_client.delete_variable(validated.key)
    return ToolResponse(success=True, data=result, error=None).model_dump()


TOOLS = {
    "airflow_variable_list": list_variables,
    "airflow_variable_get": get_variable,
    "airflow_variable_set": set_variable,
    "airflow_variable_delete": delete_variable,
}
