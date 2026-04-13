from typing import Any

from airflow_mcp_server.airflow_client import client as airflow_client
from airflow_mcp_server.schemas import (
    ToolResponse,
    GetConfigParams,
    ListDagWarningsParams,
)


async def get_config(params: dict) -> ToolResponse:
    """Retrieve Airflow configuration.

    Returns the complete Airflow configuration dictionary. May require admin permissions.

    Args:
        params: Dictionary containing:
            - section (str, optional): Config section to filter (e.g., 'core', 'scheduler').

    Returns:
        {"success": True, "data": {config dict or filtered section}, "error": None}

    Raises:
        AirflowPermissionError: If user lacks admin permissions (HTTP 403).
        AirflowConnectionError: If Airflow is unreachable.
    """
    validated = GetConfigParams.model_validate(params or {})
    config = await airflow_client.get_config(section=validated.section)
    return ToolResponse(success=True, data=config, error=None).model_dump()


async def get_version(params: dict) -> ToolResponse:
    """Get Airflow version and metadata.

    Returns version string, git commit hash, and other build information.

    Args:
        params: Empty dictionary (no parameters).

    Returns:
        {"success": True, "data": {"version": str, "git_version": str, ...}, "error": None}

    Raises:
        AirflowConnectionError: If Airflow is unreachable.
    """
    version = await airflow_client.get_version()
    return ToolResponse(success=True, data=version, error=None).model_dump()


async def list_dag_warnings(params: dict) -> ToolResponse:
    """List DAG warnings (SLA misses, import warnings, etc.).

    Useful for monitoring DAG health and configuration issues.

    Args:
        params: Dictionary containing:
            - dag_id (str, optional): Filter by DAG ID (None = all DAGs).
            - limit (int, optional): Maximum number of warnings to return. Default 100.

    Returns:
        {"success": True, "data": [{"dag_id": str, "warning_type": str, ...}], "error": None}

    Raises:
        AirflowConnectionError: If Airflow is unreachable.
    """
    validated = ListDagWarningsParams.model_validate(params or {})
    warnings = await airflow_client.list_dag_warnings(dag_id=validated.dag_id, limit=validated.limit)
    return ToolResponse(success=True, data=warnings, error=None).model_dump()


TOOLS = {
    "airflow_config_get": get_config,
    "airflow_version_get": get_version,
    "airflow_dag_warning_list": list_dag_warnings,
}
