import pkgutil
import importlib
import inspect
from typing import Any, Dict, List

from airflow_mcp_server.schemas import ToolResponse, TOOL_INPUT_MODELS


# Category mapping: handler module -> category
TOOL_CATEGORIES = {
    "dags": "dag",
    "tasks": "task",
    "logs": "log",
    "connections": "connection",
    "variables": "variable",
    "pools": "pool",
    "xcoms": "xcom",
    "datasets": "dataset",
    "providers": "system",
    "import_errors": "monitoring",
    "agent_tools": "agent",
    "health": "monitoring",
    "discovery": "meta",
    "event_logs": "audit",
    "config": "admin",
}

# Tools that are read-only (don't modify state)
READ_ONLY_TOOLS = {
    "airflow_dag_list",
    "airflow_dag_get",
    "airflow_dag_run_list",
    "airflow_dag_run_get",
    "airflow_dag_source",
    "airflow_task_list_instances",
    "airflow_task_logs",
    "airflow_task_list",
    "airflow_task_get",
    "airflow_connection_list",
    "airflow_connection_get",
    "airflow_variable_list",
    "airflow_variable_get",
    "airflow_pool_list",
    "airflow_pool_get",
    "airflow_xcom_get",
    "airflow_import_error_list",
    "airflow_dataset_list",
    "airflow_dataset_get",
    "airflow_provider_list",
    "airflow_plugin_list",
    "airflow_tools_list",
    "airflow_tool_get",
    "airflow_health_check",
    "airflow_system_health",
    "airflow_dag_diagnose",
}

# Tool examples: tool_name -> example params
TOOL_EXAMPLES = {
    "airflow_dag_list": {"limit": 10, "offset": 0},
    "airflow_dag_get": {"dag_id": "my_etl_dag"},
    "airflow_dag_trigger": {"dag_id": "my_etl_dag", "conf": {}},
    "airflow_dag_pause": {"dag_id": "my_etl_dag"},
    "airflow_dag_unpause": {"dag_id": "my_etl_dag"},
    "airflow_dag_run_list": {"dag_id": "my_etl_dag", "limit": 10},
    "airflow_dag_source": {"dag_id": "my_etl_dag"},
    "airflow_dag_diagnose": {"dag_id": "my_etl_dag", "run_id": "manual__2026-01-01T00:00:00+00:00"},
    "airflow_task_list_instances": {"dag_id": "my_etl_dag", "run_id": "manual__2026-01-01T00:00:00+00:00"},
    "airflow_task_retry": {"dag_id": "my_etl_dag", "run_id": "manual__2026-01-01T00:00:00+00:00", "task_id": "extract"},
    "airflow_task_logs": {"dag_id": "my_etl_dag", "run_id": "manual__2026-01-01T00:00:00+00:00", "task_id": "extract", "try_number": 1},
    "airflow_connection_list": {"limit": 10},
    "airflow_connection_get": {"conn_id": "my_http_conn"},
    "airflow_connection_delete": {"conn_id": "my_http_conn"},
    "airflow_connection_create": {"conn_id": "my_http_conn", "type": "http", "host": "example.com"},
    "airflow_variable_list": {"limit": 10},
    "airflow_variable_get": {"key": "my_var"},
    "airflow_variable_set": {"key": "my_var", "value": "value123"},
    "airflow_variable_delete": {"key": "my_var"},
    "airflow_pool_list": {"limit": 10},
    "airflow_pool_get": {"pool_name": "default_pool"},
    "airflow_pool_set": {"pool_name": "my_pool", "slots": 5},
    "airflow_xcom_get": {"dag_id": "my_etl_dag", "run_id": "manual__2026-01-01T00:00:00+00:00", "task_id": "extract", "key": "result"},
    "airflow_import_error_list": {"limit": 10},
    "airflow_dataset_list": {"limit": 10},
    "airflow_dataset_get": {"dataset_uri": "s3://my-bucket/data"},
    "airflow_provider_list": {"limit": 10},
    "airflow_plugin_list": {"limit": 10},
    "airflow_tools_list": {},
    "airflow_tool_get": {"tool_name": "airflow_dag_list"},
    "airflow_system_health": {},
    "airflow_health_check": {},
    "airflow_dag_run_get": {"dag_id": "my_etl_dag", "run_id": "manual__2026-01-01T00:00:00+00:00"},
    "airflow_dag_run_clear": {"dag_id": "my_etl_dag", "run_id": "manual__2026-01-01T00:00:00+00:00", "only_failed": True},
    "airflow_dag_run_cancel": {"dag_id": "my_etl_dag", "run_id": "manual__2026-01-01T00:00:00+00:00"},
    "airflow_dag_run_set_state": {"dag_id": "my_etl_dag", "run_id": "manual__2026-01-01T00:00:00+00:00", "state": "success"},
    "airflow_task_list": {"dag_id": "my_etl_dag"},
    "airflow_task_get": {"dag_id": "my_etl_dag", "task_id": "extract"},
    "airflow_task_set_state": {"dag_id": "my_etl_dag", "run_id": "manual__2026-01-01T00:00:00+00:00", "task_id": "extract", "state": "success"},
    "airflow_task_clear": {"dag_id": "my_etl_dag", "run_id": "manual__2026-01-01T00:00:00+00:00", "task_id": "extract"},
    "airflow_event_log_list": {"limit": 50, "dag_id": "my_etl_dag", "event": "trigger"},
    "airflow_event_log_get": {"event_log_id": 123},
    "airflow_config_get": {"section": "core"},
    "airflow_version_get": {},
    "airflow_dag_warning_list": {"dag_id": "my_etl_dag", "limit": 10},
}


def _get_tool_info(tool_name: str, handler: Any, module_name: str) -> Dict[str, Any]:
    """Extract metadata for a tool: schema, description, category, etc.

    Args:
        tool_name: The tool name (e.g., 'airflow_dag_list').
        handler: The async handler function.
        module_name: The handler module name (e.g., 'dags').

    Returns:
        A dict with tool metadata including input_schema, category, etc.
    """
    info: Dict[str, Any] = {
        "tool_name": tool_name,
        "module": module_name,
        "category": TOOL_CATEGORIES.get(module_name, "other"),
        "read_only": tool_name in READ_ONLY_TOOLS,
    }

    # Extract description from docstring (first line)
    doc = (handler.__doc__ or "").strip() if hasattr(handler, "__doc__") else ""
    first_line = doc.split("\n")[0] if doc else ""
    info["description"] = first_line

    # Add input schema if tool has a Pydantic model
    if tool_name in TOOL_INPUT_MODELS:
        model = TOOL_INPUT_MODELS[tool_name]
        info["input_schema"] = model.model_json_schema()
    else:
        info["input_schema"] = {"type": "object", "properties": {}, "required": []}

    # Add example(s)
    if tool_name in TOOL_EXAMPLES:
        info["examples"] = [TOOL_EXAMPLES[tool_name]]
    else:
        info["examples"] = [{}]

    return info


async def list_tools(params: dict) -> ToolResponse:
    """Return a list of available MCP tools with full metadata.

    For each tool, includes: name, module, category, read_only flag, description,
    input_schema (JSON Schema), and example invocations.

    Args:
        params: Empty dictionary (no parameters).

    Returns:
        {"success": True, "data": [{"tool_name": str, "category": str, "input_schema": dict, ...}], "error": None}

    Raises:
        AirflowConnectionError: If unable to load handlers (generally should not happen).
    """
    tools: List[Dict[str, Any]] = []
    try:
        import airflow_mcp_server.handlers as handlers_pkg
    except Exception:
        return ToolResponse(success=True, data=[], error=None).model_dump()

    for _finder, name, _ispkg in pkgutil.iter_modules(handlers_pkg.__path__):
        try:
            mod = importlib.import_module(f"airflow_mcp_server.handlers.{name}")
        except Exception:
            continue
        mod_tools = getattr(mod, "TOOLS", {}) or {}
        for tname, handler in mod_tools.items():
            info = _get_tool_info(tname, handler, name)
            tools.append(info)

    return ToolResponse(success=True, data=tools, error=None).model_dump()


async def get_tool(params: dict) -> ToolResponse:
    """Fetch full schema and metadata for a single tool.

    Faster than parsing all of list_tools when you only need one tool's schema.

    Args:
        params: Dictionary containing:
            - tool_name (str): Name of the tool to fetch (e.g., 'airflow_dag_list').

    Returns:
        {"success": True, "data": {"tool_name": str, "category": str, "input_schema": dict, ...}, "error": None}

    Raises:
        ValueError: If tool_name is empty.
        AirflowNotFoundError: If the tool does not exist.
    """
    from airflow_mcp_server.schemas import ToolGetParams

    validated = ToolGetParams.model_validate(params or {})
    tool_name = validated.tool_name

    try:
        import airflow_mcp_server.handlers as handlers_pkg
    except Exception:
        raise ValueError(f"Tool '{tool_name}' not found")

    for _finder, name, _ispkg in pkgutil.iter_modules(handlers_pkg.__path__):
        try:
            mod = importlib.import_module(f"airflow_mcp_server.handlers.{name}")
        except Exception:
            continue
        mod_tools = getattr(mod, "TOOLS", {}) or {}
        if tool_name in mod_tools:
            handler = mod_tools[tool_name]
            info = _get_tool_info(tool_name, handler, name)
            return ToolResponse(success=True, data=info, error=None).model_dump()

    raise ValueError(f"Tool '{tool_name}' not found")


TOOLS = {
    "airflow_tools_list": list_tools,
    "airflow_tool_get": get_tool,
}
