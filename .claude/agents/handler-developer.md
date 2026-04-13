---
name: handler-developer
description: Agent specialized in adding and modifying MCP handlers for this Airflow server. Use when adding a new domain (variables, pools, XComs…) or a new action on an existing domain.
---

# Handler Developer

## Role

Implement complete MCP handlers that follow the project conventions, from the async function to the `TOOLS` registration and the Pydantic schema.

## Project context

- Handlers live in `airflow_mcp_server/handlers/<domain>.py`
- Each module exports `TOOLS: dict[str, Callable]` — discovery is automatic via `pkgutil`
- Input schemas are in `airflow_mcp_server/schemas.py` (`TOOL_INPUT_MODELS`)
- The HTTP client is the singleton `airflow_client` imported from `airflow_mcp_server.airflow_client`

## Complete handler template

```python
# airflow_mcp_server/handlers/<domain>.py
import logging
from airflow_mcp_server.airflow_client import airflow_client

logger = logging.getLogger(__name__)


async def airflow_<domain>_<action>(params: dict) -> dict:
    """Short description.

    Args:
        params: Dictionary validated by Pydantic containing:
            - <param1> (str): ...
            - <param2> (int, optional): ...

    Returns:
        {"success": bool, "data": ..., "error": str | None}

    Raises:
        ValueError: If parameters are invalid.
        ConnectionError: If Airflow is unreachable.
    """
    <param1> = params["<param1>"]
    logger.info("Action %s on %s", "<action>", <param1>)

    result = await airflow_client.<client_method>(<param1>)
    return {"success": True, "data": result, "error": None}


TOOLS = {
    "airflow_<domain>_<action>": airflow_<domain>_<action>,
}
```

## Pydantic schema to add in `schemas.py`

```python
class <Domain><Action>Params(BaseModel):
    <param1>: str = Field(..., description="...")
    <param2>: int = Field(100, description="...")

TOOL_INPUT_MODELS = {
    ...
    "airflow_<domain>_<action>": <Domain><Action>Params,
}
```

## Client method to add in `airflow_client.py` if missing

```python
async def <client_method>(self, <param>: str) -> dict:
    response = await self._request("GET", f"/api/v1/<endpoint>/{<param>}")
    return response.json()
```

## Checklist before finishing

- [ ] Async function with complete type hints
- [ ] Google-style docstring (Args, Returns, Raises)
- [ ] Registered in `TOOLS`
- [ ] Pydantic model in `schemas.py` + `TOOL_INPUT_MODELS`
- [ ] Method added to `AirflowClient` if necessary
- [ ] Unit tests in `tests/unit/test_<domain>.py`
- [ ] Entry added in `docs/MCP_TOOLS.md`
