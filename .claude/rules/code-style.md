---
name: code-style
description: Python code style rules for this project — type hints, docstrings, naming, imports.
---

# Code Style Rules

## Type hints

Required on all public functions:

```python
# ✅
async def list_dags(params: dict) -> dict: ...

# ❌
async def list_dags(params): ...
```

## Docstrings (Google-style)

```python
async def trigger_dag(params: dict) -> dict:
    """Trigger a DAG run.

    Args:
        params: Dictionary containing:
            - dag_id (str): ID of the DAG to trigger.
            - conf (dict, optional): Run configuration.

    Returns:
        {"success": bool, "data": {"dag_run_id": str, ...}, "error": str | None}

    Raises:
        ValueError: If dag_id is empty.
        AirflowConnectionError: If Airflow is unreachable.
    """
```

## Naming

| Element | Convention | Example |
|---------|-----------|---------|
| Functions / methods | snake_case | `trigger_dag()` |
| Classes | PascalCase | `AirflowClient` |
| Constants | UPPER_SNAKE_CASE | `MAX_RETRIES = 3` |
| Private methods | `_underscore` | `_validate_params()` |
| MCP tools | `airflow_<domain>_<action>` | `airflow_dag_trigger` |

## Imports (3 groups separated by a blank line)

```python
# 1. Standard library
import logging
from typing import Any

# 2. Third-party
from fastapi import FastAPI
from pydantic import BaseModel

# 3. Local
from airflow_mcp_server.config import settings
```

## Response format (all handlers)

```python
{"success": True,  "data": <result>, "error": None}
{"success": False, "data": None,     "error": "error message"}
```

Never return a different structure from a handler.
