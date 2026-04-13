import os
import pytest

pytestmark = pytest.mark.integration

TEST_DAG_ID = os.getenv("TEST_DAG_ID", "example_bash_operator")


@pytest.mark.asyncio
async def test_trigger_dag_against_airflow(airflow_client):
    client = airflow_client

    dags = await client.list_dags()

    # Support different Airflow response shapes
    dag_ids = []
    if isinstance(dags, list):
        dag_ids = [d.get("dag_id") for d in dags if isinstance(d, dict)]
    elif isinstance(dags, dict):
        dag_ids = [d.get("dag_id") for d in dags.get("dags", []) if isinstance(d, dict)]

    if not dag_ids:
        pytest.skip("No DAGs found in Airflow; ensure Airflow is running and accessible")

    # If the requested TEST_DAG_ID is not present, fall back to the
    # first available DAG to force the test to exercise a trigger
    # against the running Airflow instance.
    dag_to_use = TEST_DAG_ID if TEST_DAG_ID in dag_ids else dag_ids[0]

    tr = await client.trigger_dag(dag_to_use, conf={})
    assert tr and ("dag_run_id" in tr or "dag_run_id" in tr.values())
