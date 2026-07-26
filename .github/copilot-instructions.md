# Airflow MCP Server — Copilot Instructions

**Project**: Airflow MCP Server  
**Language**: Python (FastAPI)  
**Purpose**: High-performance MCP (Model Context Protocol) server for Apache Airflow management  
**Users**: Claude AI, developers, automation tools  
**License**: Apache 2.0

---

## Quick Start

### Development Setup
```bash
# Clone and navigate
cd airflow-mcp-server

# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh  # On Windows: powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# Create virtual environment and install dependencies (Python 3.10+)
uv sync

# Activate virtual environment
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Run development server
uv run uvicorn airflow_mcp_server.server:create_app --factory --reload --host 127.0.0.1 --port 8000

# Run tests
uv run pytest tests/ -v

# Format and lint
uv run ruff format .
uv run ruff check . --fix
```

### Project Structure
```
airflow-mcp-server/
├── airflow_mcp_server/
│   ├── __init__.py
│   ├── server.py               # FastAPI app factory / MCP server implementation
│   ├── handlers/               # MCP tool/resource handlers
│   │   ├── dags.py            # DAG management (create, list, trigger)
│   │   ├── tasks.py           # Task execution and monitoring
│   │   ├── connections.py     # Connection and Variable management
│   │   ├── logs.py            # Log retrieval
│   │   └── health.py          # Health checks
│   ├── airflow_client.py       # Airflow REST API client
│   ├── models.py               # Response/Request schemas (TypedDict, dataclasses)
│   └── config.py               # Configuration management
├── tests/
│   ├── unit/                   # Unit tests (mocked Airflow)
│   ├── integration/            # Integration tests (real Airflow connection)
│   └── conftest.py             # Pytest fixtures
├── docs/
│   ├── architecture.md         # System design and data flow
│   └── mcp_tools.md            # Exposed tools and resources
├── pyproject.toml              # Project config, tool settings, dependencies
├── .env.example                # Example environment variables
├── README.md
├── CONTRIBUTING.md
└── LICENSE
```

---

## Architecture Overview

### Core Concepts

**MCP Server**: Implements the Model Context Protocol to expose Airflow operations as:
- **Tools**: Actions (trigger DAG, update connection, pause task)
- **Resources**: Data (DAG definitions, task logs, execution history)
- **Prompts**: Contextual templates for Claude

**FastAPI**: Modern, fast (high-performance) web framework for building APIs with Python 3.7+; integrates with Pydantic for validation and generates OpenAPI documentation automatically.
- Handles HTTP requests from MCP clients
- Routes to handler functions (one handler per Airflow domain)
- Returns structured JSON responses with OpenAPI support

**Airflow Integration**: Communicates via REST API to Airflow webserver
- No direct database access (respects Airflow architecture)
- Connection pooling for performance
- Graceful degradation if Airflow is unavailable

### Data Flow
```
MCP Client (Claude/Agent)
    ↓ HTTP PUT/POST (JSON)
FastAPI App (airflow_mcp_server/server.py)
    ↓ Route → Handler
Handler (handlers/*.py)
    ↓ Call via AirflowClient
AirflowClient (airflow_client.py)
    ↓ HTTP → Airflow REST API
Airflow Webserver
    ↓ Response (JSON)
AirflowClient
    ↓ Parse & return
Handler → FastAPI → MCP Client
```

---

## Development Conventions

### Code Organization

**Handlers** (`handlers/` directory):
- One file per Airflow domain (dags.py, tasks.py, connections.py, logs.py, health.py)
- Each handler file exports a dict of `{"tool_name": handler_func}`
- Handler functions are async: `async def handler(params: dict) -> dict`
- Return consistent response format: `{"success": bool, "data": Any, "error": str | None}`

**Type Safety**:
- Use Python 3.10+ type hints (PEP 604 unions, pattern matching)
- Use `TypedDict` from `typing` for request schemas
- Use `dataclasses.dataclass` for response models
- All public functions must have complete type annotations

**Error Handling**:
- Raise `ValueError` for bad parameters (caught by handler wrapper)
- Raise `ConnectionError` for Airflow unavailable (returns 503 to client)
- All exceptions include descriptive messages for MCP client
- Never silently fail; always log errors

### MCP Tool Naming

Tools are named using snake_case pattern:
```
airflow_<domain>_<action>

Examples:
- airflow_dag_list
- airflow_dag_trigger
- airflow_task_logs
- airflow_connection_create
- airflow_health_check
```

### Testing

**Unit Tests** (`tests/unit/`):
- Mock `AirflowClient` entirely
- Test handler logic and error cases
- Use `pytest` with fixtures in `conftest.py`
- Target: 80%+ coverage

**Integration Tests** (`tests/integration/`):
- Require running Airflow instance
- Test full flow: MCP → FastAPI → AirflowClient → Airflow
- Conditionally skip if Airflow unreachable
- Use pytest markers: `@pytest.mark.integration`

**Run tests**:
```bash
uv run pytest tests/unit -v              # Unit tests only
uv run pytest tests/integration -v       # Integration (requires Airflow)
uv run pytest -k "not integration" -v    # Skip integration
```

### Configuration

**Environment Variables** (use `.env` file, loaded in `config.py`):
```
AIRFLOW_BASE_URL=http://localhost:8080
AIRFLOW_USERNAME=airflow
AIRFLOW_PASSWORD=airflow
MCP_SERVER_PORT=8000
MCP_SERVER_HOST=127.0.0.1
LOG_LEVEL=INFO
```

**Runtime Config** (`config.py`):
- Load and validate environment variables
- Raise clear errors on missing/invalid config
- Provide sensible defaults where appropriate
- Log config on startup (mask passwords)

---

## Airflow-Specific Patterns

### REST API Client (`airflow_client.py`)

**Connection Management**:
- Single persistent session with connection pooling
- Retry logic with exponential backoff (3 retries default)
- Timeout: 30 seconds for standard requests, 120 for long operations
- Auth: Basic auth (username/password) via `base64` header

**Response Handling**:
- Airflow returns 200 for success, 400-500 for errors
- Parse JSON response; key fields: `dag_id`, `dag_run_id`, `task_id`, `state`
- Always check HTTP status before parsing JSON
- Return structured data (dict/list) or raise with context

**Common Endpoints** (Airflow 3.x only — `/api/v2`):
```
GET  /api/v2/dags                    # List DAGs
GET  /api/v2/dags/{dag_id}          # Get DAG
POST /api/v2/dags/{dag_id}/dagRuns  # Trigger DAG
GET  /api/v2/dags/{dag_id}/dagRuns  # List runs
GET  /api/v2/dags/{dag_id}/dagRuns/{run_id}/taskInstances  # Task instances
POST /api/v2/connections            # Create/update connection
GET  /api/v2/variables              # List variables
```

### Response Schemas (`models.py`)

Always include these fields in tool responses:
```python
{
    "success": True | False,
    "data": {  # Actual result or None
        "dag_id": str,
        "execution_date": datetime | str,
        "state": "queued" | "running" | "success" | "failed",
        ...
    },
    "error": "None | String describing error"
}
```

---

## Common Development Tasks

### Adding a New Tool

1. **Define handler** in appropriate file (e.g., `handlers/dags.py`):
   ```python
   async def trigger_dag(params: dict) -> dict:
       try:
           dag_id = params.get("dag_id")
           # Call AirflowClient
           result = await airflow_client.trigger_dag(dag_id)
           return {"success": True, "data": result, "error": None}
       except Exception as e:
           return {"success": False, "data": None, "error": str(e)}
   ```

2. **Register in MCP server** (`server.py`):
   ```python
   TOOLS = {**DAGS_TOOLS, **TASKS_TOOLS, **CONNECTIONS_TOOLS, ...}
   ```

3. **Write tests** (`tests/unit/test_dags.py`):
   ```python
   @pytest.mark.asyncio
   async def test_trigger_dag():
       mock_client.trigger_dag.return_value = {...}
       result = await trigger_dag({"dag_id": "my_dag"})
       assert result["success"] is True
   ```

4. **Document** in `docs/mcp_tools.md`:
   ```markdown
   #### airflow_dag_trigger
   Trigger a DAG run.
   - **Input**: dag_id (str)
   - **Output**: dag_run_id, execution_date, state
   ```

### Debugging

**Enable verbose logging**:
```bash
LOG_LEVEL=DEBUG uv run uvicorn airflow_mcp_server.server:create_app --factory --reload
```

**Test with curl**:
```bash
curl -X PUT http://localhost:8000/tool/airflow_dag_list \
  -H "Content-Type: application/json" \
  -d '{"params": {}}'
```

**Inspect Airflow REST responses**:
```bash
curl -u airflow:airflow http://localhost:8080/api/v2/dags | jq .
```

---

## Installation & Build

### Production Build
```bash
uv sync --no-dev
uv run python -m airflow_mcp_server.main --port 8000
```

### Docker (if needed)
```dockerfile
FROM python:3.11-slim
WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

COPY pyproject.toml .
RUN uv sync --no-dev --no-cache

COPY airflow_mcp_server/ ./airflow_mcp_server/
CMD [".venv/bin/python", "-m", "airflow_mcp_server.main"]
```

---

## Related Documentation

- **[architecture.md](../docs/architecture.md)** — Detailed system design
- **[mcp_tools.md](../docs/mcp_tools.md)** — Complete tool reference
- **[CONTRIBUTING.md](../CONTRIBUTING.md)** — Contribution guidelines
- **[Apache Airflow REST API](https://airflow.apache.org/docs/apache-airflow/stable/stable-api-ref.html)** — External reference
- **[Model Context Protocol](https://modelcontextprotocol.io/)** — MCP specification

---

## Questions for Implementers

When working with this codebase, keep these in mind:

1. **Is Airflow unreachable?** → Return 503 Service Unavailable, not 500
2. **Can Claude retry this operation safely?** → Use appropriate HTTP status (409 for conflicts)
3. **Does this expose sensitive data?** → Implement access control in auth layer
4. **Are we making multiple Airflow REST calls?** → Consider batching or async execution
5. **Is the response too large for Claude?** → Paginate or summarize
