import pkgutil
import importlib
import logging
import inspect
from typing import Dict, Callable, Any, Optional

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

# Define write-only tools (operations that modify Airflow state)
WRITE_ONLY_TOOLS = {
    "airflow_dag_trigger",
    "airflow_dag_pause",
    "airflow_dag_unpause",
    "airflow_dag_run_clear",
    "airflow_dag_run_cancel",
    "airflow_dag_run_set_state",
    "airflow_task_retry",
    "airflow_task_set_state",
    "airflow_task_clear",
    "airflow_connection_create",
    "airflow_connection_delete",
    "airflow_variable_set",
    "airflow_variable_delete",
    "airflow_pool_set",
}

# Global MCP server instance (initialized lazily)
_mcp_server: Optional[Any] = None


def load_tools() -> Dict[str, Callable[[dict], Any]]:
    """Load all tools from handler modules."""
    from airflow_mcp_server.config import cfg

    tools: Dict[str, Callable[[dict], Any]] = {}
    try:
        import airflow_mcp_server.handlers as handlers_pkg
    except Exception:
        return tools
    for _finder, name, _ispkg in pkgutil.iter_modules(handlers_pkg.__path__):
        try:
            mod = importlib.import_module(f"airflow_mcp_server.handlers.{name}")
        except Exception:
            continue
        module_tools = getattr(mod, "TOOLS", {})
        # If read-only mode is enabled, filter out write-only tools
        if cfg.MCP_READ_ONLY:
            module_tools = {k: v for k, v in module_tools.items() if k not in WRITE_ONLY_TOOLS}
        tools.update(module_tools)
    return tools


def _get_mcp_server() -> Any:
    """Lazy-initialize and return the MCP server instance."""
    global _mcp_server
    if _mcp_server is None:
        try:
            from mcp.server.fastmcp import FastMCP
            _mcp_server = FastMCP("Airflow MCP Server")
            _register_tools_with_mcp(_mcp_server, load_tools())
        except ImportError:
            logger.warning("MCP SDK not available, proceeding without MCP protocol support")
            return None
    return _mcp_server


def _register_tools_with_mcp(mcp: Any, tools: Dict[str, Callable]) -> None:
    """Register all discovered tools with the MCP server."""
    try:
        from airflow_mcp_server import schemas as _schemas
    except Exception:
        _schemas = None

    for tool_name, handler in tools.items():
        model = _schemas.TOOL_INPUT_MODELS.get(tool_name) if _schemas else None
        description = (handler.__doc__ or "").split("\n")[0].strip() or tool_name

        if model:
            # Create tool with Pydantic model
            def _make_mcp_tool(h, m, name, desc):
                async def _tool_impl(**kwargs):
                    try:
                        validated = m(**kwargs)
                        params = validated.model_dump()
                    except Exception as e:
                        return {"success": False, "data": None, "error": f"Invalid params: {str(e)}"}
                    try:
                        result = h(params)
                        if inspect.iscoroutine(result):
                            result = await result
                        return result if isinstance(result, dict) else {"success": True, "data": result, "error": None}
                    except Exception as e:
                        return {"success": False, "data": None, "error": str(e)}

                _tool_impl.__doc__ = desc
                return _tool_impl

            tool_func = _make_mcp_tool(handler, model, tool_name, description)
            mcp.tool(name=tool_name, description=description)(tool_func)
        else:
            # Create tool without model
            async def _tool_no_schema():
                try:
                    result = handler({})
                    if inspect.iscoroutine(result):
                        result = await result
                    return result if isinstance(result, dict) else {"success": True, "data": result, "error": None}
                except Exception as e:
                    return {"success": False, "data": None, "error": str(e)}

            _tool_no_schema.__doc__ = description
            mcp.tool(name=tool_name, description=description)(_tool_no_schema)

    logger.info("Registered %d tools with MCP server", len(tools))


def create_app() -> FastAPI:
    """Create a FastAPI app with MCP protocol and legacy HTTP support."""
    from airflow_mcp_server.config import cfg
    from airflow_mcp_server.airflow_client import (
        AirflowAuthError,
        AirflowPermissionError,
        AirflowNotFoundError,
        AirflowConflictError,
        AirflowServerError,
        AirflowConnectionError,
    )

    app = FastAPI(title="Airflow MCP Server")
    tools = load_tools()

    # Try to mount MCP server at /mcp if available
    try:
        mcp = _get_mcp_server()
        if mcp is not None and cfg.MCP_TRANSPORT in ("http", "both"):
            app.mount("/mcp", mcp.streamable_http_app())
            logger.info("MCP HTTP transport mounted at /mcp")
    except Exception as e:
        logger.warning("Failed to mount MCP HTTP transport: %s", e)

    # Import validation models
    try:
        from airflow_mcp_server import schemas as _schemas
    except Exception:
        _schemas = None

    def _make_response(body: dict, status: int = 200) -> JSONResponse:
        return JSONResponse(content=body, status_code=status)

    @app.post("/tool/{tool_name}")
    async def invoke_tool(tool_name: str, request: Request):
        """Legacy HTTP endpoint for tool invocation."""
        logger.info("invoke_tool called for tool: %s", tool_name)
        try:
            payload = await request.json()
        except Exception as e:
            logger.exception("Failed to parse JSON for tool %s: %s", tool_name, e)
            payload = {}

        params = payload.get("params", {}) or {}

        # Validate params against schema if available
        if _schemas is not None:
            model = _schemas.TOOL_INPUT_MODELS.get(tool_name)
            if model is not None:
                try:
                    validated = model.model_validate(params)
                    params = validated.model_dump()
                except Exception as exc:
                    return _make_response({"success": False, "data": None, "error": f"Invalid params: {exc}"}, 400)

        handler = tools.get(tool_name)
        if handler is None:
            logger.warning("Tool not found: %s", tool_name)
            return _make_response({"success": False, "data": None, "error": "Tool not found"}, 404)

        try:
            result = handler(params)
            if inspect.iscoroutine(result):
                result = await result

            if isinstance(result, dict):
                return _make_response(result, 200)
            return _make_response({"success": True, "data": result, "error": None}, 200)
        except ValueError as exc:
            logger.exception("Bad request for tool %s: %s", tool_name, exc)
            return _make_response({"success": False, "data": None, "error": str(exc)}, 400)
        except AirflowAuthError as exc:
            logger.exception("Auth error for tool %s: %s", tool_name, exc)
            return _make_response({"success": False, "data": None, "error": str(exc)}, 401)
        except AirflowPermissionError as exc:
            logger.exception("Permission error for tool %s: %s", tool_name, exc)
            return _make_response({"success": False, "data": None, "error": str(exc)}, 403)
        except AirflowNotFoundError as exc:
            logger.exception("Not found for tool %s: %s", tool_name, exc)
            return _make_response({"success": False, "data": None, "error": str(exc)}, 404)
        except AirflowConflictError as exc:
            logger.exception("Conflict for tool %s: %s", tool_name, exc)
            return _make_response({"success": False, "data": None, "error": str(exc)}, 409)
        except AirflowConnectionError as exc:
            logger.exception("Connection error for tool %s: %s", tool_name, exc)
            return _make_response({"success": False, "data": None, "error": str(exc)}, 503)
        except AirflowServerError as exc:
            logger.exception("Server error for tool %s: %s", tool_name, exc)
            return _make_response({"success": False, "data": None, "error": str(exc)}, 502)
        except Exception as exc:
            logger.exception("Unexpected error for tool %s: %s", tool_name, exc)
            return _make_response({"success": False, "data": None, "error": str(exc)}, 500)

    @app.post("/tool")
    async def invoke_tool_body(request: Request):
        """Legacy HTTP endpoint: alternative body format."""
        logger.info("invoke_tool_body called")
        try:
            payload = await request.json()
        except Exception as e:
            logger.exception("Failed to parse JSON in fallback /tool: %s", e)
            payload = {}

        tool_name = payload.get("tool_name") or payload.get("tool")
        params = payload.get("params", {}) or {}

        # Validate params against schema if available
        if _schemas is not None and tool_name:
            model = _schemas.TOOL_INPUT_MODELS.get(tool_name)
            if model is not None:
                try:
                    validated = model.model_validate(params)
                    params = validated.model_dump()
                except Exception as exc:
                    return _make_response({"success": False, "data": None, "error": f"Invalid params: {exc}"}, 400)

        if not tool_name:
            return _make_response({"success": False, "data": None, "error": "Missing 'tool_name' in body"}, 400)

        handler = tools.get(tool_name)
        if handler is None:
            logger.warning("Tool not found (body): %s", tool_name)
            return _make_response({"success": False, "data": None, "error": "Tool not found"}, 404)

        try:
            result = handler(params)
            if inspect.iscoroutine(result):
                result = await result

            if isinstance(result, dict):
                return _make_response(result, 200)
            return _make_response({"success": True, "data": result, "error": None}, 200)
        except ValueError as exc:
            logger.exception("Bad request for tool %s: %s", tool_name, exc)
            return _make_response({"success": False, "data": None, "error": str(exc)}, 400)
        except AirflowAuthError as exc:
            logger.exception("Auth error for tool %s: %s", tool_name, exc)
            return _make_response({"success": False, "data": None, "error": str(exc)}, 401)
        except AirflowPermissionError as exc:
            logger.exception("Permission error for tool %s: %s", tool_name, exc)
            return _make_response({"success": False, "data": None, "error": str(exc)}, 403)
        except AirflowNotFoundError as exc:
            logger.exception("Not found for tool %s: %s", tool_name, exc)
            return _make_response({"success": False, "data": None, "error": str(exc)}, 404)
        except AirflowConflictError as exc:
            logger.exception("Conflict for tool %s: %s", tool_name, exc)
            return _make_response({"success": False, "data": None, "error": str(exc)}, 409)
        except AirflowConnectionError as exc:
            logger.exception("Connection error for tool %s: %s", tool_name, exc)
            return _make_response({"success": False, "data": None, "error": str(exc)}, 503)
        except AirflowServerError as exc:
            logger.exception("Server error for tool %s: %s", tool_name, exc)
            return _make_response({"success": False, "data": None, "error": str(exc)}, 502)
        except Exception as exc:
            logger.exception("Unexpected error for tool %s: %s", tool_name, exc)
            return _make_response({"success": False, "data": None, "error": str(exc)}, 500)

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    logger.info("Loaded tools: %s", sorted(list(tools.keys())))
    return app


def create_stdio_server() -> Any:
    """Create an MCP server for stdio transport (Claude Desktop)."""
    mcp = _get_mcp_server()
    if mcp is None:
        raise RuntimeError("MCP SDK not available")
    return mcp
