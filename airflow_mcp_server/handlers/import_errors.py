
from airflow_mcp_server.airflow_client import client as airflow_client
from airflow_mcp_server.schemas import (
    ToolResponse,
    ListImportErrorsParams,
)


async def list_import_errors(params: dict) -> dict:
    """List all DAG import errors.

    Useful for debugging DAGs that failed to parse or import.

    Args:
        params: Dictionary containing:
            - limit (int, optional): Maximum number of errors to return (default: 100).

    Returns:
        {"success": bool, "data": list[dict], "error": str | None}

    Raises:
        AirflowConnectionError: If Airflow is unreachable.
    """
    validated = ListImportErrorsParams.model_validate(params or {})
    errors = await airflow_client.list_import_errors(limit=validated.limit)
    return ToolResponse(success=True, data=errors, error=None).model_dump()


TOOLS = {
    "airflow_import_error_list": list_import_errors,
}
