# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

An MCP (Model Context Protocol) server that exposes Apache Airflow operations as tools, allowing AI clients (Claude, etc.) to manage Airflow workflows via HTTP. Targets Airflow 3.x exclusively (REST API `/api/v2`).

## Commands

This project uses `just` as a task runner and `uv` for Python dependency management.

```bash
uv sync                          # Install dependencies
just run                         # Start dev server (--dev mode)
just test                        # Unit tests only (excludes integration)
just lint                        # Lint and auto-fix with ruff
just format                      # Format with ruff
```

Direct equivalents:
```bash
uv run pytest -k "not integration" -v          # Unit tests
uv run pytest tests/unit/test_dags.py -v       # Single test file
uv run pytest tests/unit/test_dags.py::test_list_dags -v  # Single test
uv run pytest tests/integration -v             # Integration tests (requires live Airflow)
uv run mypy airflow_mcp_server/                # Type checking
uv run ruff check . --fix && uv run ruff format .
```

Debug server: `LOG_LEVEL=DEBUG uv run uvicorn airflow_mcp_server.server:create_app --factory --reload`

## Architecture

```
MCP Client → POST /tool/{tool_name} → FastAPI (server.py)
                                          ↓
                              handlers/{domain}.py   (validates params via Pydantic)
                                          ↓
                              airflow_client.py      (async HTTP, retry, Airflow 3.x /api/v2)
                                          ↓
                              Airflow REST API       (Basic Auth)
```

**Key files:**
- [airflow_mcp_server/server.py](airflow_mcp_server/server.py) — FastAPI factory, dynamic tool loading via `pkgutil`, exception-to-HTTP-status mapping
- [airflow_mcp_server/airflow_client.py](airflow_mcp_server/airflow_client.py) — `AirflowClient` singleton: retry with exponential backoff (3×), targets Airflow 3.x `/api/v2`, 30s timeout
- [airflow_mcp_server/handlers/](airflow_mcp_server/handlers/) — One file per domain (`dags`, `tasks`, `logs`, `connections`, `health`); each exports `TOOLS: dict[str, AsyncCallable]`
- [airflow_mcp_server/schemas.py](airflow_mcp_server/schemas.py) — Pydantic input models; `TOOL_INPUT_MODELS` maps tool name → model
- [airflow_mcp_server/config.py](airflow_mcp_server/config.py) — All config from environment variables

**Tool discovery:** `server.py:load_tools()` uses `pkgutil.iter_modules()` to auto-discover handler modules — adding a new handler file automatically registers its tools.

**Response format** (all tools):
```python
{"success": bool, "data": Any | None, "error": str | None}
```

**Error mapping:** `AirflowAuthError→401`, `AirflowPermissionError→403`, `AirflowNotFoundError→404`, `AirflowConflictError→409`, `AirflowConnectionError→503`, `ValueError→400`

## Environment Variables

```env
AIRFLOW_BASE_URL=http://localhost:8080   # required
AIRFLOW_USERNAME=airflow
AIRFLOW_PASSWORD=airflow
AIRFLOW_API_TOKEN=                       # optional Bearer token, takes precedence over BasicAuth
MCP_SERVER_HOST=127.0.0.1
MCP_SERVER_PORT=8000
LOG_LEVEL=INFO
```

Copy `.env.example` to `.env` before running locally. For Docker, use `http://host.docker.internal:8080` to reach a host Airflow instance.

## Specs workflow

Feature documentation lives in `specs/` — one file per branch, named `SPEC-{id}-{slug}.md`.

| Folder | Purpose |
| --- | --- |
| `specs/_templates/` | Copy `spec-template.md` to start a new spec |
| `specs/active/` | Specs currently in development |
| `specs/domain/` | Stable domain reference docs not tied to a branch |
| `specs/done/` | Completed specs (auto-moved by the `post-merge` hook) |
| `specs/wireframes/` | Flow diagrams and mockups |

**Lifecycle:** copy template → fill in `specs/active/SPEC-{id}-{slug}.md` → set `status: active` → work → set `status: done` → merge → hook moves file to `specs/done/`.

## Git hooks

Hooks live in `hooks/` and must be installed once per clone:

```bash
just hooks
```

| Hook | What it does |
| --- | --- |
| `prepare-commit-msg` | Prepends `SPEC-XXX` + title from branch name to commit draft |
| `commit-msg` | Validates Conventional Commits format — fails on bad messages |
| `post-merge` | Moves specs with `status: done` from `active/` to `done/` |
| `pre-push` | Runs lint + unit tests; warns if spec file is missing |

Branch convention that hooks rely on: `feature/SPEC-{id}-{slug}` or `fix/SPEC-{id}-{slug}`.

## Development Conventions

- **Tool naming:** `airflow_<domain>_<action>` (e.g., `airflow_dag_trigger`)
- **Type hints** required on all public functions; **Google-style docstrings** (Args, Returns, Raises)
- **Handlers** are async functions; validate params, delegate to `AirflowClient`, return consistent response dict
- **Adding a tool:** define async handler → add to `TOOLS` dict in the relevant handler module → add Pydantic input model to `schemas.py` → write unit tests
- **Tests:** unit tests mock `AirflowClient` via `monkeypatch`; async tests use `@pytest.mark.asyncio`; integration tests marked `@pytest.mark.integration`
- **Commit messages:** Conventional Commits format (`feat:`, `fix:`, `refactor:`, `test:`, `chore:`)
