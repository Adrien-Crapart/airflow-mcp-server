import pkgutil
import importlib
import logging
import inspect
from typing import Dict, Callable, Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

# Define write-only tools (operations that modify Airflow state)
WRITE_ONLY_TOOLS = {
    "airflow_dag_trigger",
    "airflow_dag_pause",
    "airflow_dag_unpause",
    "airflow_task_retry",
    "airflow_connection_create",
    "airflow_connection_delete",
    "airflow_variable_set",
    "airflow_variable_delete",
    "airflow_pool_set",
}


def load_tools() -> Dict[str, Callable[[dict], Any]]:
    from airflow_mcp_server.config import cfg

    tools: Dict[str, Callable[[dict], Any]] = {}
    try:
        import airflow_mcp_server.handlers as handlers_pkg
    except Exception:
        return tools
    for _finder, name, _ispkg in pkgutil.iter_modules(handlers_pkg.__path__):
        mod = importlib.import_module(f"airflow_mcp_server.handlers.{name}")
        module_tools = getattr(mod, "TOOLS", {})
        # If read-only mode is enabled, filter out write-only tools
        if cfg.MCP_READ_ONLY:
            module_tools = {k: v for k, v in module_tools.items() if k not in WRITE_ONLY_TOOLS}
        tools.update(module_tools)
    return tools


def create_app() -> FastAPI:
    """Return a FastAPI ASGI app exposing MCP tool endpoints.

    Loads handlers from `airflow_mcp_server.handlers` and exposes
    `/tool`, `/tool/{tool_name}` and `/health`.
    """
    app = FastAPI(title="Airflow MCP Server")

    tools = load_tools()
    # import validation models
    try:
        from airflow_mcp_server import schemas as _schemas
    except Exception:
        _schemas = None
    # Register explicit typed routes for tools that have Pydantic input models
    if _schemas is not None:
        for _name, _handler in list(tools.items()):
            model = _schemas.TOOL_INPUT_MODELS.get(_name)
            if model is None:
                continue

            def _make_endpoint(handler, model, name):
                async def _endpoint(params):
                    # params is a Pydantic model instance
                    try:
                        params_dict = params.model_dump()
                    except Exception:
                        params_dict = params
                    result = handler(params_dict)
                    if inspect.isawaitable(result):
                        result = await result
                    # If result is a Pydantic model, convert to dict
                    try:
                        from pydantic import BaseModel

                        if isinstance(result, BaseModel):
                            return result.model_dump()
                    except Exception:
                        pass
                    if isinstance(result, dict):
                        return result
                    return {"success": True, "data": result, "error": None}

                _endpoint.__name__ = f"tool_{name}"
                # annotate for FastAPI to pick up the request model and response model
                _endpoint.__annotations__ = {"params": model, "return": _schemas.ToolResponse}
                return _endpoint

            endpoint = _make_endpoint(_handler, model, _name)
            # register a static route for this specific tool name to appear in OpenAPI
            app.post(f"/tool/{_name}", response_model=_schemas.ToolResponse, name=f"tool_{_name}")(endpoint)
    try:
        logger.info("Loaded tools: %s", sorted(list(tools.keys())))
    except Exception:
        pass

    # import Airflow-specific exceptions for mapping
    from airflow_mcp_server.airflow_client import (
        AirflowAuthError,
        AirflowPermissionError,
        AirflowNotFoundError,
        AirflowConflictError,
        AirflowServerError,
        AirflowConnectionError,
    )

    def _make_response(body: dict, status: int = 200) -> JSONResponse:
        return JSONResponse(content=body, status_code=status)

    @app.post("/tool/{tool_name}")
    async def invoke_tool(tool_name: str, request: Request):
        logger.info("invoke_tool called for tool: %s", tool_name)
        try:
            payload = await request.json()
        except Exception as e:
            try:
                raw_body = await request.body()
            except Exception:
                raw_body = b"<unreadable>"
            logger.exception("Failed to parse JSON for tool %s: %s — raw_body=%s headers=%s", tool_name, e, raw_body, getattr(request, "headers", None))
            payload = {}
        params = payload.get("params", {}) or {}
        # validate params against schema if available
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
            if inspect.isawaitable(result):
                result = await result
            logger.info("handler result type: %s", type(result))
            try:
                logger.info("handler result repr: %s", repr(result)[:200])
            except Exception:
                pass
            # If handler returned a Pydantic BaseModel, serialize it to dict
            try:
                from pydantic import BaseModel

                if isinstance(result, BaseModel):
                    return _make_response(result.model_dump(), 200)
            except Exception:
                pass
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
        except Exception as exc:  # pragma: no cover - unexpected
            logger.exception("Unexpected error for tool %s: %s", tool_name, exc)
            return _make_response({"success": False, "data": None, "error": str(exc)}, 500)

    @app.post("/tool")
    async def invoke_tool_body(request: Request):
        logger.info("invoke_tool_body called")
        try:
            payload = await request.json()
        except Exception as e:
            try:
                raw_body = await request.body()
            except Exception:
                raw_body = b"<unreadable>"
            logger.exception("Failed to parse JSON in fallback /tool: %s — raw_body=%s headers=%s", e, raw_body, getattr(request, "headers", None))
            payload = {}
        tool_name = payload.get("tool_name") or payload.get("tool")
        params = payload.get("params", {}) or {}
        # validate params against schema if available
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
            if inspect.isawaitable(result):
                result = await result
            logger.info("handler result type (body): %s", type(result))
            try:
                logger.info("handler result repr (body): %s", repr(result)[:200])
            except Exception:
                pass
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
        except Exception as exc:  # pragma: no cover - unexpected
            logger.exception("Unexpected error for tool %s: %s", tool_name, exc)
            return _make_response({"success": False, "data": None, "error": str(exc)}, 500)

    @app.get("/health")
    async def http_health():
        return {"status": "ok"}

    return app
