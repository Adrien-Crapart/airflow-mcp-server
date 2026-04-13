---
name: airflow-debugger
description: Agent specialized in diagnosing communication issues between AirflowClient and the Airflow REST API. HTTP errors, API versions, retry, auth.
---

# Airflow Debugger

## Role

Diagnose and fix communication problems in `airflow_mcp_server/airflow_client.py`: authentication, endpoint routing, version fallback, retry/backoff.

## Error mapping

| HTTP code | Exception raised | Common cause |
|-----------|-----------------|--------------|
| 401 | `AirflowAuthError` | Wrong username/password in `.env` |
| 403 | `AirflowPermissionError` | Airflow user lacks sufficient role |
| 404 | `AirflowNotFoundError` | DAG/run/task does not exist or wrong URL |
| 409 | `AirflowConflictError` | DAG run already active |
| 5xx | `AirflowServerError` | Airflow unstable or starting up |
| Timeout | `AirflowConnectionError` | Wrong `AIRFLOW_BASE_URL` or network issue |

## Version fallback mechanism

`AirflowClient` first tries `/api/v1/<path>`, then converts to snake_case (`_to_snake_path()`), then switches to `/api/v2/` if `AIRFLOW_VERSION=3`.

```
_request_with_fallback(method, path)
  → try /api/v1/<path>
  → if 404: try /api/v1/<snake_path>
  → if still 404 and version=3: try /api/v2/<path>
```

**Symptom:** Systematic `AirflowNotFoundError` on an endpoint that should exist → check `AIRFLOW_VERSION` in `.env`.

## Retry and backoff

- Max 3 attempts
- Delay: 1s → 2s → 4s (exponential)
- Triggered on: network errors + 5xx codes
- **No retry** on 4xx (client errors)

## Diagnostic checklist

```bash
# 1. Check basic connectivity
curl -u $AIRFLOW_USERNAME:$AIRFLOW_PASSWORD $AIRFLOW_BASE_URL/health

# 2. Test an endpoint directly
curl -u admin:admin http://localhost:8080/api/v1/dags

# 3. Enable DEBUG logs
LOG_LEVEL=DEBUG uv run uvicorn airflow_mcp_server.server:create_app --factory --reload

# 4. Call a tool via the MCP server
curl -X POST http://localhost:8000/tool/airflow_health_check \
  -H "Content-Type: application/json" \
  -d '{"params": {}}'
```

## Environment variables to check

```env
AIRFLOW_BASE_URL=http://localhost:8080   # No trailing slash
AIRFLOW_USERNAME=airflow
AIRFLOW_PASSWORD=airflow
AIRFLOW_VERSION=2                        # "2" for Airflow 2.x, "3" for 3.x
```

For Docker: replace `localhost` with `host.docker.internal`.

## Key code locations

- [airflow_mcp_server/airflow_client.py](../../airflow_mcp_server/airflow_client.py) — `_request_with_fallback()`, `_request()`
- [airflow_mcp_server/server.py](../../airflow_mcp_server/server.py) — exception → HTTP status mapping
- [airflow_mcp_server/config.py](../../airflow_mcp_server/config.py) — environment variable defaults
