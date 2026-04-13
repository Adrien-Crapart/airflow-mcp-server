from typing import Any
from airflow_mcp_server.schemas import ToolResponse


async def health_check(params: dict) -> dict:
    """Check the health status of the MCP server.

    This is a lightweight health endpoint that does not require Airflow connectivity.

    Args:
        params: Empty dictionary (no parameters).

    Returns:
        {"success": True, "data": {"status": "ok"}, "error": None}

    Raises:
        None
    """
    # Lightweight health endpoint for the MCP server
    return ToolResponse(success=True, data={"status": "ok"}, error=None).model_dump()


TOOLS = {
    "airflow_health_check": health_check,
}
