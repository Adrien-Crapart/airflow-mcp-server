"""MCP Resources for read-only Airflow content via airflow:// URIs."""

import json
from typing import Any, Optional

from airflow_mcp_server.airflow_client import client as airflow_client


async def get_version_resource() -> str:
    """Get Airflow version and metadata as JSON.

    Resource: airflow://version
    MIME: application/json
    """
    version = await airflow_client.get_version()
    return json.dumps(version, indent=2)


async def get_config_resource() -> str:
    """Get Airflow configuration as JSON.

    Resource: airflow://config
    MIME: application/json
    Note: May require admin permissions
    """
    config = await airflow_client.get_config()
    return json.dumps(config, indent=2)


async def get_dag_resource(dag_id: str) -> str:
    """Get DAG metadata (schedule, owner, tags, is_paused, etc.) as JSON.

    Resource: airflow://dag/{dag_id}
    MIME: application/json
    """
    dag = await airflow_client.get_dag(dag_id)
    return json.dumps(dag, indent=2)


async def get_dag_source_resource(dag_id: str) -> str:
    """Get Python source code of the DAG file.

    Resource: airflow://dag/{dag_id}/source
    MIME: text/x-python
    """
    dag = await airflow_client.get_dag(dag_id)
    file_token = dag.get("file_token") if isinstance(dag, dict) else None
    if not file_token:
        return "# Source not available for this DAG"
    source = await airflow_client.get_dag_source(file_token)
    return source if isinstance(source, str) else json.dumps(source, indent=2)


async def get_task_log_resource(dag_id: str, run_id: str, task_id: str) -> str:
    """Get task execution log (most recent attempt) as text.

    Resource: airflow://dag/{dag_id}/run/{run_id}/log/{task_id}
    MIME: text/plain
    """
    logs = await airflow_client.get_task_logs(dag_id, run_id, task_id, try_number=1)
    return logs if isinstance(logs, str) else json.dumps(logs, indent=2)


async def get_variable_resource(key: str) -> str:
    """Get variable value as JSON. Sensitive values are masked.

    Resource: airflow://variable/{key}
    MIME: application/json
    Note: Variables with 'password', 'secret', 'token', 'api_key' in name are masked
    """
    var = await airflow_client.get_variable(key)
    # Mask values with 'password', 'secret', 'token', 'key' in name
    if any(s in key.lower() for s in ["password", "secret", "token", "api_key"]):
        if isinstance(var, dict) and "value" in var:
            var = {**var, "value": "***MASKED***"}
    return json.dumps(var, indent=2)


async def get_providers_resource() -> str:
    """Get list of installed Airflow providers as JSON.

    Resource: airflow://providers
    MIME: application/json
    """
    providers = await airflow_client.list_providers()
    return json.dumps(providers, indent=2)


def register_all(mcp: Any) -> None:
    """Register all MCP resources with the MCP server.

    Args:
        mcp: FastMCP server instance
    """
    try:
        # Static resources (no parameters)
        mcp.resource("airflow://version", description="Airflow version and metadata")(get_version_resource)
        mcp.resource("airflow://config", description="Airflow configuration (may require admin)")(get_config_resource)
        mcp.resource("airflow://providers", description="Installed Airflow providers")(get_providers_resource)

        # Parameterized resources
        mcp.resource("airflow://dag/{dag_id}", description="DAG metadata")(get_dag_resource)
        mcp.resource("airflow://dag/{dag_id}/source", description="DAG source code")(get_dag_source_resource)
        mcp.resource("airflow://dag/{dag_id}/run/{run_id}/log/{task_id}", description="Task execution log")(
            get_task_log_resource
        )
        mcp.resource("airflow://variable/{key}", description="Variable value (sensitive values masked)")(
            get_variable_resource
        )
    except Exception as e:
        import logging

        logger = logging.getLogger(__name__)
        logger.warning("Failed to register MCP resources: %s", e)
