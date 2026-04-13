import pkgutil
import importlib
import inspect
from typing import Any, Dict, List

from airflow_mcp_server.schemas import ToolResponse, TOOL_INPUT_MODELS


async def list_tools(params: dict) -> ToolResponse:
    """Return a list of available MCP tools with basic metadata.

    The result is a list of dicts describing each tool: name, module,
    whether it has a structured input model, a short docstring and the
    Python signature when available.
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
            info: Dict[str, Any] = {
                "tool_name": tname,
                "module": name,
                "has_input_model": tname in TOOL_INPUT_MODELS,
                "callable": callable(handler),
                "doc": (handler.__doc__ or "").strip() if hasattr(handler, "__doc__") else "",
            }
            try:
                info["signature"] = str(inspect.signature(handler))
            except Exception:
                info["signature"] = None
            tools.append(info)

    return ToolResponse(success=True, data=tools, error=None).model_dump()


TOOLS = {
    "airflow_tools_list": list_tools,
}
