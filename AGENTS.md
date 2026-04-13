# AGENTS.md

This file describes the available agents for working in this repository, their roles, and when to use them.

## Overview

This project is an **MCP (Model Context Protocol) server** for Apache Airflow. The agents below cover recurring development tasks: adding new MCP tools, debugging the HTTP client, and writing tests.

---

## Available agents

### `handler-developer`
**File:** [.claude/agents/handler-developer.md](.claude/agents/handler-developer.md)

Specialized in adding new MCP tools (handlers). Knows the exact handler structure, the associated Pydantic schema, and how to register entries in `TOOLS`.

**When to use:**

- Adding a new Airflow domain (e.g., variables, pools, XComs)
- Extending an existing handler with a new action
- Refactoring handlers without breaking the response contract

---

### `test-writer`
**File:** [.claude/agents/test-writer.md](.claude/agents/test-writer.md)

Specialized in writing unit and integration tests. Uses `AsyncMock` + `monkeypatch`, knows the shared fixtures in `conftest.py`.

**When to use:**

- Adding tests for a newly created handler
- Increasing code coverage (target: 80%+)
- Writing integration tests that require a real Airflow instance

---

### `airflow-debugger`
**File:** [.claude/agents/airflow-debugger.md](.claude/agents/airflow-debugger.md)

Specialized in diagnosing communication issues with the Airflow REST API: authentication, API version (v1/v2), retry, timeouts.

**When to use:**

- Unexpected 401 / 403 / 404 errors from `AirflowClient`
- Different behavior between Airflow 2.x and 3.x
- Debugging the retry or version fallback mechanism

---

## Conventions for all agents

- Always return `{"success": bool, "data": ..., "error": str | None}`
- Name MCP tools: `airflow_<domain>_<action>`
- Type hints required on all public functions
- Google-style docstrings (Args, Returns, Raises)
- Commits in Conventional Commits format (`feat:`, `fix:`, `test:`, etc.)
