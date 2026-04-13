---
name: error-handling
description: Error handling rules for handlers and the Airflow client — exception hierarchy, logging, HTTP mapping.
---

# Error Handling Rules

## Exception hierarchy (`airflow_client.py`)

```
AirflowError (base)
├── AirflowAuthError          → HTTP 401
├── AirflowPermissionError    → HTTP 403
├── AirflowNotFoundError      → HTTP 404
├── AirflowConflictError      → HTTP 409
├── AirflowConnectionError    → HTTP 503
└── AirflowServerError        → HTTP 502
```

`ValueError` raised in a handler → HTTP 400.  
Uncaught exception → HTTP 500.

## Pattern in a handler

```python
async def airflow_dag_trigger(params: dict) -> dict:
    dag_id = params.get("dag_id")
    if not dag_id:
        raise ValueError("dag_id is required")

    try:
        result = await airflow_client.trigger_dag(dag_id)
        return {"success": True, "data": result, "error": None}
    except AirflowNotFoundError as e:
        logger.warning("DAG not found: %s", dag_id)
        return {"success": False, "data": None, "error": str(e)}
    except AirflowConnectionError:
        raise  # FastAPI maps → 503
```

## Logging levels

| Level | When to use |
|-------|-------------|
| `DEBUG` | Method entry/exit, parameter values |
| `INFO` | Successful important operations (`DAG triggered: X`) |
| `WARNING` | Resource not found, retry in progress |
| `ERROR` | Unexpected recoverable error |
| `CRITICAL` | Cannot start server |

```python
logger = logging.getLogger(__name__)  # One logger per module
```

## What NOT to do

- Do not swallow `AirflowConnectionError` — let it propagate so FastAPI returns 503
- Do not log `exc_info=True` on 4xx errors (too verbose)
- Do not raise generic `Exception` — use the specific subclass
- Do not duplicate the error message in both `data` and `error` fields
