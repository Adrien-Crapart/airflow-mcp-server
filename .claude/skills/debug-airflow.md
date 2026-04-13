---
name: debug-airflow
description: Skill for quickly diagnosing connection problems between the MCP server and the Airflow REST API.
---

# Skill: Debug Airflow connection

## Quick diagnostic (in order)

```bash
# 1. Check the .env file
cat .env

# 2. Test direct connectivity
curl -s -u "$AIRFLOW_USERNAME:$AIRFLOW_PASSWORD" "$AIRFLOW_BASE_URL/health"

# 3. Test an API endpoint
curl -s -u "$AIRFLOW_USERNAME:$AIRFLOW_PASSWORD" "$AIRFLOW_BASE_URL/api/v1/dags" | head -50

# 4. Start the server in DEBUG mode
LOG_LEVEL=DEBUG just run

# 5. Call the MCP health check
curl -X POST http://localhost:8000/tool/airflow_health_check \
  -H "Content-Type: application/json" -d '{"params": {}}'
```

## Common errors and solutions

| Symptom | Likely cause | Solution |
| --- | --- | --- |
| `401 Unauthorized` | Wrong credentials | Check `AIRFLOW_USERNAME` / `AIRFLOW_PASSWORD` in `.env` |
| `404` on everything | Wrong API version | Switch `AIRFLOW_VERSION=3` ↔ `2` |
| `Connection refused` | Wrong URL or Airflow stopped | Check `AIRFLOW_BASE_URL`, use `host.docker.internal` in Docker |
| Timeout | Network or Airflow overloaded | Check Airflow logs, increase timeout in `AirflowClient` |
| `409 Conflict` | DAG run already active | Wait for the run to finish or use a unique `dag_run_id` |

## Variables to check

```env
AIRFLOW_BASE_URL=http://localhost:8080   # No trailing slash
AIRFLOW_USERNAME=airflow
AIRFLOW_PASSWORD=airflow
AIRFLOW_VERSION=2                        # "2" or "3" depending on Airflow version
LOG_LEVEL=DEBUG                          # To see detailed HTTP requests
```

## Files to inspect

- [airflow_mcp_server/airflow_client.py](../../airflow_mcp_server/airflow_client.py) — `_request()`, `_request_with_fallback()`
- [airflow_mcp_server/config.py](../../airflow_mcp_server/config.py) — environment variable defaults
- [airflow_mcp_server/server.py](../../airflow_mcp_server/server.py) — exception → HTTP status mapping
