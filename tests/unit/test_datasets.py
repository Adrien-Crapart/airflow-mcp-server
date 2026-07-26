import pytest

import airflow_mcp_server.airflow_client as _client
from airflow_mcp_server.airflow_client import (
    AirflowConnectionError,
    AirflowNotFoundError,
)
from airflow_mcp_server.handlers import datasets


@pytest.mark.asyncio
async def test_list_datasets_success(monkeypatch):
    async def _fake_list(limit=100):
        return [
            {"uri": "s3://my-bucket/data", "extra": {}},
            {"uri": "s3://my-bucket/other", "extra": {}},
        ]

    monkeypatch.setattr(_client.client, "list_datasets", _fake_list)

    res = await datasets.list_datasets({})

    assert res["success"] is True
    assert isinstance(res["data"], list)
    assert len(res["data"]) == 2
    assert res["data"][0]["uri"] == "s3://my-bucket/data"
    assert res["error"] is None


@pytest.mark.asyncio
async def test_list_datasets_connection_error(monkeypatch):
    async def _fake_list(limit=100):
        raise AirflowConnectionError("unreachable")

    monkeypatch.setattr(_client.client, "list_datasets", _fake_list)

    with pytest.raises(AirflowConnectionError):
        await datasets.list_datasets({})


@pytest.mark.asyncio
async def test_get_dataset_success(monkeypatch):
    async def _fake_get(dataset_uri):
        return {"uri": dataset_uri, "extra": {}}

    monkeypatch.setattr(_client.client, "get_dataset", _fake_get)

    res = await datasets.get_dataset({"dataset_uri": "s3://my-bucket/data"})

    assert res["success"] is True
    assert res["data"]["uri"] == "s3://my-bucket/data"
    assert res["error"] is None


@pytest.mark.asyncio
async def test_get_dataset_missing_uri():
    with pytest.raises(Exception):
        await datasets.get_dataset({})


@pytest.mark.asyncio
async def test_get_dataset_not_found(monkeypatch):
    async def _fake_get(dataset_uri):
        raise AirflowNotFoundError("dataset not found")

    monkeypatch.setattr(_client.client, "get_dataset", _fake_get)

    with pytest.raises(AirflowNotFoundError):
        await datasets.get_dataset({"dataset_uri": "s3://missing/data"})


@pytest.mark.asyncio
async def test_get_dataset_connection_error(monkeypatch):
    async def _fake_get(dataset_uri):
        raise AirflowConnectionError("unreachable")

    monkeypatch.setattr(_client.client, "get_dataset", _fake_get)

    with pytest.raises(AirflowConnectionError):
        await datasets.get_dataset({"dataset_uri": "s3://my-bucket/data"})
