---
id: SPEC-001
title: "Core Infrastructure — Server, Client, Config, Health"
status: done
domain: "server, airflow_client, config, schemas, health, discovery"
created: 2026-04-13
updated: 2026-04-13
branch: feature/SPEC-001-core-infrastructure
---

# SPEC-001: Core Infrastructure

## Context

The MCP Airflow server requires a robust foundation: a FastAPI server that dynamically
loads and dispatches tools, an async HTTP client that communicates with Airflow's REST API
with retry logic and version fallback, configuration management via environment variables,
and foundational endpoints for health checks and tool discovery.

## Goal

Establish the base HTTP server, Airflow client, and utility infrastructure that all
subsequent tool domains will build upon.

## Acceptance criteria

- [x] FastAPI server with dynamic tool loading via `pkgutil`
- [x] `AirflowClient` singleton with exponential backoff retry (3×), API v1/v2 fallback
- [x] Config module loading all env vars (`AIRFLOW_BASE_URL`, `AIRFLOW_USERNAME`, `AIRFLOW_PASSWORD`, `AIRFLOW_VERSION`, `MCP_READ_ONLY`, etc.)
- [x] Pydantic response model (`ToolResponse`) and parameter base models
- [x] Health check endpoint
- [x] Tool discovery endpoint that introspects loaded tools
- [x] HTTP error mapping (ValueError→400, AirflowAuthError→401, etc.)
- [x] Unit tests for server, client, config, and health endpoints

## Technical approach

### Server (`airflow_mcp_server/server.py`)

- FastAPI factory function `create_app()` that:
  - Initializes the `AirflowClient` singleton
  - Dynamically loads all handler modules via `pkgutil.iter_modules("airflow_mcp_server/handlers")`
  - Registers `POST /tool/{tool_name}` and `POST /tool` endpoints
  - Filters write tools if `cfg.MCP_READ_ONLY` is true
  - Maps exceptions to HTTP status codes

### Client (`airflow_mcp_server/airflow_client.py`)

- Async httpx-based client with:
  - Basic auth (username/password)
  - Auto-detection of API v1 (Airflow 2.x) vs v2 (Airflow 3.x) prefix
  - Exponential backoff retry (max 3 attempts)
  - camelCase→snake_case path fallback for cross-version compatibility
  - Typed exception classes (`AirflowAuthError`, `AirflowConnectionError`, etc.)

### Config (`airflow_mcp_server/config.py`)

- Pydantic `Config` dataclass that:
  - Loads all env vars with defaults
  - Validates required vars (e.g., `AIRFLOW_BASE_URL`)
  - Provides a module-level `settings` singleton

### Schemas (`airflow_mcp_server/schemas.py`)

- `ToolResponse(success: bool, data: Any | None, error: str | None)` — standard response format for all tools
- Base Pydantic models for parameter validation
- `TOOL_INPUT_MODELS` dict mapping tool names to their input parameter models

### Health & Discovery (`airflow_mcp_server/handlers/health.py`, `discovery.py`)

- `health_check()` — returns `{"status": "ok"}` if Airflow is reachable
- `list_tools()` — introspects loaded tools and returns their names + schemas

### Tests

- `tests/unit/test_airflow_client.py` — client methods, retry logic
- `tests/unit/test_airflow_client_errors.py` — error mapping, API version fallback
- `tests/unit/test_client_errors.py` — specific error scenarios
- `tests/unit/test_health_endpoint.py` — health check endpoint
- `tests/unit/test_server_and_handlers.py` — server initialization, tool loading
- `tests/unit/test_main_runner.py` — main.py entry point
- `tests/integration/conftest.py` — integration test fixtures with real/mock Airflow
- `tests/integration/test_integration_airflow.py` — end-to-end integration test

## MCP tools affected

### New tools (2)
- `airflow_health_check` — check Airflow connectivity
- `airflow_tools_list` — list available MCP tools and their schemas

### Infrastructure (not directly user-facing)
- Dynamic tool registration and dispatch
- Error handling and HTTP status mapping
- API version auto-detection and fallback

## Related

- CLAUDE.md — development conventions and commands
- Architecture guide: `specs/domain/architecture.md`
- Configuration: `.env.example`
