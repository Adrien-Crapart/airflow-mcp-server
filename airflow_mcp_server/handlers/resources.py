"""MCP Resources for read-only Airflow content via airflow:// URIs."""

import json
import re
from typing import Any

from airflow_mcp_server.airflow_client import AirflowPermissionError, client as airflow_client
from airflow_mcp_server.config import cfg


SENSITIVE_RESOURCE_KEY_RE = re.compile(
    r"(password|passwd|secret|token|api[_-]?key|access[_-]?key|private[_-]?key|credential|client[_-]?secret|fernet|jwt|(?:^|[_-])key(?:$|[_-]))",
    re.IGNORECASE,
)


def _is_sensitive_key(key: str) -> bool:
    """Return True if a key name is likely to carry sensitive data."""
    return bool(SENSITIVE_RESOURCE_KEY_RE.search(key))


def _mask_sensitive(value: Any) -> Any:
    """Recursively mask sensitive keys in dictionaries and lists."""
    if isinstance(value, dict):
        masked: dict[Any, Any] = {}
        for key, nested in value.items():
            key_text = str(key)
            if _is_sensitive_key(key_text):
                masked[key] = "***MASKED***"
            else:
                masked[key] = _mask_sensitive(nested)
        return masked
    if isinstance(value, list):
        return [_mask_sensitive(item) for item in value]
    return value


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
    if not cfg.MCP_ENABLE_ADMIN_ENDPOINTS:
        raise AirflowPermissionError("Config resource is disabled by server policy")

    config = await airflow_client.get_config()
    return json.dumps(_mask_sensitive(config), indent=2)


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
    Note: Variables with sensitive key names are masked
    """
    var = await airflow_client.get_variable(key)
    # Mask value if the variable name itself indicates a secret.
    if _is_sensitive_key(key.lower()):
        if isinstance(var, dict) and "value" in var:
            var = {**var, "value": "***MASKED***"}
    return json.dumps(_mask_sensitive(var), indent=2)


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
        if cfg.MCP_ENABLE_ADMIN_ENDPOINTS:
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
