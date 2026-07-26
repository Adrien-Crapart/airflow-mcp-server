
from airflow_mcp_server.airflow_client import client as airflow_client
from airflow_mcp_server.schemas import (
    ToolResponse,
    ListPoolsParams,
    PoolNameParams,
    SetPoolParams,
)


async def list_pools(params: dict) -> dict:
    """List all Airflow pools.

    Args:
        params: Dictionary containing:
            - limit (int, optional): Maximum number of pools to return (default: 100).

    Returns:
        {"success": bool, "data": list[dict], "error": str | None}

    Raises:
        AirflowConnectionError: If Airflow is unreachable.
    """
    validated = ListPoolsParams.model_validate(params or {})
    pools = await airflow_client.list_pools(limit=validated.limit)
    return ToolResponse(success=True, data=pools, error=None).model_dump()


async def get_pool(params: dict) -> dict:
    """Retrieve an Airflow pool by name.

    Args:
        params: Dictionary containing:
            - pool_name (str): The pool name.

    Returns:
        {"success": bool, "data": dict, "error": str | None}

    Raises:
        ValueError: If pool_name is empty.
        AirflowNotFoundError: If pool not found.
        AirflowConnectionError: If Airflow is unreachable.
    """
    validated = PoolNameParams.model_validate(params or {})
    pool = await airflow_client.get_pool(validated.pool_name)
    return ToolResponse(success=True, data=pool, error=None).model_dump()


async def set_pool(params: dict) -> dict:
    """Create or update an Airflow pool.

    Args:
        params: Dictionary containing:
            - pool_name (str): The pool name.
            - slots (int): Number of slots in the pool (must be >= 1).
            - description (str, optional): Pool description.

    Returns:
        {"success": bool, "data": dict, "error": str | None}

    Raises:
        ValueError: If pool_name or slots is invalid.
        AirflowConnectionError: If Airflow is unreachable.
    """
    validated = SetPoolParams.model_validate(params or {})
    pool = await airflow_client.set_pool(
        validated.pool_name,
        validated.slots,
        description=validated.description,
    )
    return ToolResponse(success=True, data=pool, error=None).model_dump()


TOOLS = {
    "airflow_pool_list": list_pools,
    "airflow_pool_get": get_pool,
    "airflow_pool_set": set_pool,
}
