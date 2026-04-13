from typing import Any

from airflow_mcp_server.airflow_client import client as airflow_client
from airflow_mcp_server.schemas import (
    ToolResponse,
    ListDatasetsParams,
    DatasetUriParams,
)


async def list_datasets(params: dict) -> ToolResponse:
    """List all Airflow datasets (data lineage assets).

    In Airflow 3.x, datasets are called "assets". The client handles
    the naming difference automatically.

    Args:
        params: Dictionary containing:
            - limit (int, optional): Maximum number of datasets to return (default: 100).

    Returns:
        {"success": bool, "data": list[dict], "error": str | None}

    Raises:
        AirflowConnectionError: If Airflow is unreachable.
    """
    validated = ListDatasetsParams.model_validate(params or {})
    datasets = await airflow_client.list_datasets(limit=validated.limit)
    return ToolResponse(success=True, data=datasets, error=None).model_dump()


async def get_dataset(params: dict) -> ToolResponse:
    """Retrieve a dataset by URI.

    Args:
        params: Dictionary containing:
            - dataset_uri (str): The dataset URI (e.g., "s3://my-bucket/data").

    Returns:
        {"success": bool, "data": dict, "error": str | None}

    Raises:
        ValueError: If dataset_uri is empty.
        AirflowNotFoundError: If the dataset does not exist.
        AirflowConnectionError: If Airflow is unreachable.
    """
    validated = DatasetUriParams.model_validate(params or {})
    dataset = await airflow_client.get_dataset(validated.dataset_uri)
    return ToolResponse(success=True, data=dataset, error=None).model_dump()


TOOLS = {
    "airflow_dataset_list": list_datasets,
    "airflow_dataset_get": get_dataset,
}
