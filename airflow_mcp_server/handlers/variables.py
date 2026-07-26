
import re
from typing import Any

from airflow_mcp_server.airflow_client import client as airflow_client
from airflow_mcp_server.schemas import (
    ToolResponse,
    ListVariablesParams,
    VariableKeyParams,
    SetVariableParams,
)


SENSITIVE_VARIABLE_KEY_RE = re.compile(
    r"(password|passwd|secret|token|api[_-]?key|access[_-]?key|private[_-]?key|credential|client[_-]?secret|fernet|jwt)",
    re.IGNORECASE,
)


def _is_sensitive_variable_key(variable_key: str) -> bool:
    """Return True when a variable key likely stores sensitive content."""
    return bool(SENSITIVE_VARIABLE_KEY_RE.search(variable_key))


def _mask_sensitive_payload(value: Any) -> Any:
    """Recursively mask sensitive dictionary keys in arbitrary payloads."""
    if isinstance(value, dict):
        masked: dict[Any, Any] = {}
        for key, nested in value.items():
            key_text = str(key)
            if _is_sensitive_variable_key(key_text):
                masked[key] = "***MASKED***"
            else:
                masked[key] = _mask_sensitive_payload(nested)
        return masked
    if isinstance(value, list):
        return [_mask_sensitive_payload(item) for item in value]
    return value


def _mask_variable_record(variable: Any, explicit_key: str | None = None) -> Any:
    """Mask variable value when key is sensitive and sanitize nested fields."""
    masked = _mask_sensitive_payload(variable)
    if not isinstance(masked, dict):
        return masked

    key_candidate = explicit_key
    if not key_candidate:
        raw_key = masked.get("key")
        key_candidate = str(raw_key) if raw_key is not None else ""

    if key_candidate and _is_sensitive_variable_key(key_candidate) and "value" in masked:
        masked["value"] = "***MASKED***"
    return masked


async def list_variables(params: dict) -> dict:
    """List all Airflow variables.

    Args:
        params: Dictionary containing:
            - limit (int, optional): Maximum number of variables to return (default: 100).

    Returns:
        {"success": bool, "data": list[dict], "error": str | None}
        Sensitive values are masked in the response.

    Raises:
        AirflowConnectionError: If Airflow is unreachable.
    """
    validated = ListVariablesParams.model_validate(params or {})
    variables = await airflow_client.list_variables(limit=validated.limit)
    if isinstance(variables, list):
        masked_variables = [_mask_variable_record(item) for item in variables]
    else:
        masked_variables = _mask_variable_record(variables)
    return ToolResponse(success=True, data=masked_variables, error=None).model_dump()


async def get_variable(params: dict) -> dict:
    """Retrieve an Airflow variable by key.

    Args:
        params: Dictionary containing:
            - key (str): The variable key.

    Returns:
        {"success": bool, "data": dict, "error": str | None}
        Sensitive values are masked in the response.

    Raises:
        ValueError: If key is empty.
        AirflowNotFoundError: If variable not found.
        AirflowConnectionError: If Airflow is unreachable.
    """
    validated = VariableKeyParams.model_validate(params or {})
    variable = await airflow_client.get_variable(validated.key)
    masked_variable = _mask_variable_record(variable, explicit_key=validated.key)
    return ToolResponse(success=True, data=masked_variable, error=None).model_dump()


async def set_variable(params: dict) -> dict:
    """Create or update an Airflow variable.

    Args:
        params: Dictionary containing:
            - key (str): The variable key.
            - value (str): The variable value.

    Returns:
        {"success": bool, "data": dict, "error": str | None}
        Sensitive values are masked in the response.

    Raises:
        ValueError: If key or value is empty.
        AirflowConnectionError: If Airflow is unreachable.
    """
    validated = SetVariableParams.model_validate(params or {})
    variable = await airflow_client.set_variable(validated.key, validated.value)
    masked_variable = _mask_variable_record(variable, explicit_key=validated.key)
    return ToolResponse(success=True, data=masked_variable, error=None).model_dump()


async def delete_variable(params: dict) -> dict:
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
