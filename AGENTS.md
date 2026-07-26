# AGENTS.md

This file describes the available agents for working in this repository, their roles, and when to use them.

## Overview

This project is an **MCP (Model Context Protocol) server** for Apache Airflow. The agents below cover recurring development tasks: adding new MCP tools, debugging the HTTP client, and writing tests.

Quality baseline: every development agent now integrates explicit checks for security exposure, error-mapping behavior, and test evidence quality.

---

## Available agents

### `handler-developer`
**File:** [.github/agents/handler-developer.agent.md](.github/agents/handler-developer.agent.md)

Specialized in adding new MCP tools (handlers). Knows the exact handler structure, the associated Pydantic schema, registration in `TOOLS`, and quality gates (read-only filtering, sensitive-data protection, response contract).

**When to use:**

- Adding a new Airflow domain (e.g., variables, pools, XComs)
- Extending an existing handler with a new action
- Refactoring handlers without breaking the response contract

---

### `test-writer`
**File:** [.github/agents/test-writer.agent.md](.github/agents/test-writer.agent.md)

Specialized in writing unit and integration tests. Uses `AsyncMock` + `monkeypatch`, knows shared fixtures, and enforces quality scenarios (error mapping, read-only mode, sensitive masking, real integration evidence).

**When to use:**

- Adding tests for a newly created handler
- Increasing code coverage (target: 80%+)
- Writing integration tests that require a real Airflow instance

---

### `airflow-debugger`
**File:** [.github/agents/airflow-debugger.agent.md](.github/agents/airflow-debugger.agent.md)

Specialized in diagnosing communication issues with the Airflow REST API (`/api/v2`, Airflow 3.x only): authentication, retry, timeouts, and server-side quality risks linked to endpoint exposure/logging behavior.

**When to use:**

- Unexpected 401 / 403 / 404 errors from `AirflowClient`
- Debugging the retry/backoff or auth-switch mechanism

---

## Available prompts

Prompt files are focused slash commands for repeatable tasks. They complement agents by providing pre-structured inputs and expected outputs.

### `review-data`
**File:** [.github/prompts/review-data.prompt.md](.github/prompts/review-data.prompt.md)

Launches a strict data PR review workflow with evidence-based findings and GO/NO-GO output.

**When to use:**

- Running a full compliance-oriented review on a PR
- Producing a standardized review report for reviewers

---

### `rapport-qa`
**File:** [.github/prompts/rapport-qa.prompt.md](.github/prompts/rapport-qa.prompt.md)

Generates a QA validation report structure with mandatory evidence fields and final decision logic.

**When to use:**

- Building a ticket-level QA report before environment promotion
- Consolidating alerts, anomalies, and corrective actions

---

### `handler-delivery`
**File:** [.github/prompts/handler-delivery.prompt.md](.github/prompts/handler-delivery.prompt.md)

Guides end-to-end handler delivery (schema, registration, read-only/mutating checks, tests).

**When to use:**

- Adding a new MCP tool handler
- Extending an existing handler action safely

---

### `debug-airflow`
**File:** [.github/prompts/debug-airflow.prompt.md](.github/prompts/debug-airflow.prompt.md)

Runs a structured incident triage for Airflow MCP failures with root-cause and validation steps.

**When to use:**

- Investigating 401/403/404/5xx and timeout issues
- Producing a minimal, testable fix plan

---

### `write-handler-tests`
**File:** [.github/prompts/write-handler-tests.prompt.md](.github/prompts/write-handler-tests.prompt.md)

Produces or updates handler unit tests with required scenarios and project testing conventions.

**When to use:**

- Backfilling missing tests after handler changes
- Standardizing coverage for error mapping and edge cases

---

### `catalog-hygiene`
**File:** [.github/prompts/catalog-hygiene.prompt.md](.github/prompts/catalog-hygiene.prompt.md)

Diagnoses and fixes customization catalog issues (missing commands, duplicates, naming collisions).

**When to use:**

- Prompt or agent not visible in chat picker
- Duplicate entries in slash command lists

---

## Conventions for all agents

- Always return `{"success": bool, "data": ..., "error": str | None}`
- Name MCP tools: `airflow_<domain>_<action>`
- Type hints required on all public functions
- Google-style docstrings (Args, Returns, Raises)
- Commits in Conventional Commits format (`feat:`, `fix:`, `test:`, etc.)

## Shared quality gates

- Protect endpoints and admin capabilities by default; avoid unauthenticated write surfaces.
- Keep sensitive values masked in resources and config-related outputs.
- For expected 4xx outcomes, prefer warning-level logs over stack traces.
- Distinguish real integration tests from mocked contract tests in QA evidence.
