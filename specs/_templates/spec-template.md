---
id: SPEC-000
title: ""
status: draft
domain: ""
created: YYYY-MM-DD
updated: YYYY-MM-DD
branch: feature/SPEC-000-slug
---

# SPEC-000: Title

## Context

Why this feature or change is needed. What problem it solves.

## Goal

What we want to achieve. One or two sentences, no implementation details.

## Acceptance criteria

- [ ] ...
- [ ] ...

## Technical approach

### Handler

Which file in `airflow_mcp_server/handlers/` is affected or created.  
New tool name: `airflow_<domain>_<action>`

### Schema

New or updated Pydantic model in `schemas.py`.

### Client

New or updated method in `AirflowClient` (endpoint, HTTP verb, response shape).

### Tests

Unit test file: `tests/unit/test_<domain>.py`  
Scenarios: success, missing param, not found, connection error.

## Wireframes

See [wireframes/SPEC-000-*.png](../wireframes/) or describe flow inline.

## MCP tool(s) affected

- `airflow_<domain>_<action>` — short description

## Related

- Issue: #
- PR: #
- Docs: [docs/MCP_TOOLS.md](../../docs/MCP_TOOLS.md)
