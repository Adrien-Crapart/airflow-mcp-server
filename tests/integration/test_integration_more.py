import pytest
from uuid import uuid4

pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_list_dag_runs(airflow_client):
    client = airflow_client
    dags = await client.list_dags()
    dag_ids = []
    if isinstance(dags, list):
        dag_ids = [d.get("dag_id") for d in dags if isinstance(d, dict)]
    elif isinstance(dags, dict):
        dag_ids = [d.get("dag_id") for d in dags.get("dags", []) if isinstance(d, dict)]

    if not dag_ids:
        pytest.skip("No DAGs available")

    dag_id = dag_ids[0]
    runs = await client.list_dag_runs(dag_id)
    assert isinstance(runs, list)


@pytest.mark.asyncio
async def test_get_task_logs(airflow_client):
    client = airflow_client
    dags = await client.list_dags()
    dag_ids = []
    if isinstance(dags, list):
        dag_ids = [d.get("dag_id") for d in dags if isinstance(d, dict)]
    elif isinstance(dags, dict):
        dag_ids = [d.get("dag_id") for d in dags.get("dags", []) if isinstance(d, dict)]

    if not dag_ids:
        pytest.skip("No DAGs available")

    dag_id = dag_ids[0]
    runs = await client.list_dag_runs(dag_id)
    if not runs:
        pytest.skip("No DAG runs available")

    run_id = None
    if isinstance(runs, list) and runs:
        first = runs[0]
        if isinstance(first, dict):
            run_id = first.get("dag_run_id") or first.get("run_id")

    if not run_id:
        pytest.skip("No run id found")

    tasks = await client.get_task_instances(dag_id, run_id)
    if not tasks:
        pytest.skip("No task instances")

    task_id = None
    if isinstance(tasks, list) and tasks:
        t0 = tasks[0]
        if isinstance(t0, dict):
            task_id = t0.get("task_id")

    if not task_id:
        pytest.skip("No task id")

    logs = await client.get_task_logs(dag_id, run_id, task_id)
    assert isinstance(logs, str)


@pytest.mark.asyncio
async def test_create_connection(airflow_client):
    client = airflow_client
    conn_id = f"my_conn_{uuid4().hex[:8]}"
    res = await client.create_connection(conn_id, "http", "host", login="u", password="p", port=123)
    assert res is not None
    if isinstance(res, dict):
        assert "connection_id" in res
        assert res["connection_id"] == conn_id


@pytest.mark.asyncio
async def test_pause_unpause_and_retry(airflow_client):
    client = airflow_client
    dags = await client.list_dags()
    dag_ids = []
    if isinstance(dags, list):
        dag_ids = [d.get("dag_id") for d in dags if isinstance(d, dict)]
    elif isinstance(dags, dict):
        dag_ids = [d.get("dag_id") for d in dags.get("dags", []) if isinstance(d, dict)]

    if not dag_ids:
        pytest.skip("No DAGs available")

    dag_id = dag_ids[0]
    res = await client.pause_dag(dag_id)
    assert res is not None
    res2 = await client.unpause_dag(dag_id)
    assert res2 is not None

    runs = await client.list_dag_runs(dag_id)
    if not runs:
        pytest.skip("No DAG runs available for retry test")

    run_id = None
    if isinstance(runs, list) and runs:
        first_run = runs[0]
        if isinstance(first_run, dict):
            run_id = first_run.get("dag_run_id") or first_run.get("run_id")

    if not run_id:
        pytest.skip("No run id found for retry test")

    tasks = await client.get_task_instances(dag_id, run_id)
    if not tasks:
        pytest.skip("No task instances available for retry test")

    task_id = None
    if isinstance(tasks, list) and tasks:
        first_task = tasks[0]
        if isinstance(first_task, dict):
            task_id = first_task.get("task_id")

    if not task_id:
        pytest.skip("No task id found for retry test")

    retry_res = await client.retry_task(dag_id, run_id, task_id)
    assert retry_res is not None
