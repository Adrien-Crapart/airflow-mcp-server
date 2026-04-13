from typing import Any
from airflow_mcp_server.schemas import ToolResponse


async def health_check(params: dict) -> dict:
    # Lightweight health endpoint for the MCP server
    return ToolResponse(success=True, data={"status": "ok"}, error=None).model_dump()


TOOLS = {
    "airflow_health_check": health_check,
}
