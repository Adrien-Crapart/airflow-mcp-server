
from airflow_mcp_server.airflow_client import client as airflow_client
from airflow_mcp_server.schemas import (
    ToolResponse,
    ListProvidersParams,
    ListPluginsParams,
)


async def list_providers(params: dict) -> dict:
    """List all installed Airflow providers.

    Providers extend Airflow with operators, hooks, and connections for
    external systems (e.g., apache-airflow-providers-google).

    Args:
        params: Dictionary containing:
            - limit (int, optional): Maximum number of providers to return (default: 100).

    Returns:
        {"success": bool, "data": list[dict], "error": str | None}

    Raises:
        AirflowConnectionError: If Airflow is unreachable.
    """
    validated = ListProvidersParams.model_validate(params or {})
    providers = await airflow_client.list_providers(limit=validated.limit)
    return ToolResponse(success=True, data=providers, error=None).model_dump()


async def list_plugins(params: dict) -> dict:
    """List all active Airflow plugins.

    Plugins extend Airflow with custom views, operators, hooks, etc.

    Args:
        params: Dictionary containing:
            - limit (int, optional): Maximum number of plugins to return (default: 100).

    Returns:
        {"success": bool, "data": list[dict], "error": str | None}

    Raises:
        AirflowConnectionError: If Airflow is unreachable.
    """
    validated = ListPluginsParams.model_validate(params or {})
    plugins = await airflow_client.list_plugins(limit=validated.limit)
    return ToolResponse(success=True, data=plugins, error=None).model_dump()


TOOLS = {
    "airflow_provider_list": list_providers,
    "airflow_plugin_list": list_plugins,
}
