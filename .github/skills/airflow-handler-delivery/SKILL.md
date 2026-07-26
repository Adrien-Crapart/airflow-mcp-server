---
name: airflow-handler-delivery
description: "Build or modify Airflow MCP handlers end-to-end with schema validation, registration, tests, and quality gates. Use when adding tools, extending handler domains, or refactoring handlers safely."
argument-hint: "Provide domain, action, Airflow endpoint, expected params, and whether the operation is read-only or mutating."
user-invocable: true
---

# Airflow Handler Delivery

## Outcome
Deliver a production-ready MCP handler change with:
- consistent response contract
- validated inputs
- correct registration
- tests for critical paths
- updated documentation

## When to Use
Use this skill when you need to:
- add a new tool in airflow_mcp_server/handlers
- extend an existing handler action
- add missing schema/client wiring for a handler
- harden a handler against security or reliability regressions

## Related Agents
- handler-developer
- test-writer

## Procedure
1. Define scope and risk
- Confirm tool name format: airflow_<domain>_<action>
- Classify operation as read-only or mutating
- Identify sensitive fields in inputs and outputs

2. Implement or update Airflow client method if needed
- Add method in airflow_mcp_server/airflow_client.py
- Use _request_with_fallback and api_prefix (/api/v2)
- Keep HTTP to exception mapping consistent

3. Implement handler function
- Validate params with Pydantic model_validate
- Call airflow_client singleton
- Return ToolResponse(success=..., data=..., error=...).model_dump()
- Keep handler return structure strictly consistent

4. Wire registration and schema
- Register function in module TOOLS dict
- Add input model to airflow_mcp_server/schemas.py
- Register in TOOL_INPUT_MODELS

5. Apply mutating tool controls
- If mutating, add tool name to WRITE_ONLY_TOOLS in airflow_mcp_server/server.py
- Verify MCP_READ_ONLY mode hides mutating tool

6. Add tests
- Add or update tests/unit/test_<domain>.py
- Cover at minimum: success, missing required param, 404, 503, 401
- For sensitive data paths, add masking/assertion tests

7. Validate and document
- Prefer just test and just lint
- If unavailable in environment, use direct .venv commands
- Update docs/mcp_capabilities.md when tool behavior changes

## Decision Points
- If operation mutates Airflow state:
  - enforce WRITE_ONLY_TOOLS entry
  - add read-only mode test
- If output may expose secrets:
  - mask or deny by default
  - add explicit regression test
- If integration evidence is requested:
  - distinguish real integration from mock fallback

## Completion Checklist
- [ ] Handler implemented with type hints and clear docstring
- [ ] Params validated via Pydantic
- [ ] TOOL_INPUT_MODELS updated
- [ ] TOOLS registration updated
- [ ] WRITE_ONLY_TOOLS updated when needed
- [ ] Unit tests added for required scenarios
- [ ] Sensitive data handling verified
- [ ] Commands/tests executed with captured evidence
- [ ] docs/mcp_capabilities.md updated when required
