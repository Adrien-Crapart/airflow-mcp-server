---
id: SPEC-013
title: "MCP Prompts — Workflow Templates for Common Airflow Operations"
status: done
domain: "server.py, handlers/prompts.py"
created: 2026-04-13
updated: 2026-04-13
branch: feature/SPEC-013-mcp-prompts
---

# SPEC-013: MCP Prompts & Workflow Templates

## Context

MCP Prompts are reusable workflow templates that guide LLMs through complex multi-step
operations. Instead of each LLM re-discovering "how do I troubleshoot a failed DAG?",
a prompt provides a structured starting point — with the right tools pre-identified
and the right questions asked.

This makes the server model-agnostic: the same troubleshooting workflow works for
Claude, GPT-4o, Gemini, and Grok because the prompt encodes Airflow expertise directly.

**Requires SPEC-011 (MCP SDK) to be completed first.**

## Goal

Provide pre-built workflow templates that encode Airflow operational expertise for
any LLM, eliminating model-specific prompt engineering.

## Acceptance criteria

- [ ] `troubleshoot_failed_dag` — guide LLM through diagnosing a failed DAG run
- [ ] `daily_health_check` — structured morning health audit for Airflow
- [ ] `onboard_new_dag` — checklist for deploying and validating a new DAG
- [ ] `optimize_pool_usage` — guide for reviewing and adjusting Airflow pools
- [ ] `connection_audit` — security review of all connections
- [ ] Prompts registered via `@mcp.prompt()` decorators
- [ ] Each prompt returns a structured message list (user role message)
- [ ] Unit tests verify prompt structure and argument handling

## Technical approach

### New File (`airflow_mcp_server/handlers/prompts.py`)

Five prompts, each returning a `list[dict]` with `role` + `content`:

```python
@mcp.prompt(name="troubleshoot_failed_dag")
async def troubleshoot_failed_dag(dag_id: str, run_id: str) -> list:
    return [{
        "role": "user",
        "content": f"""Troubleshoot DAG '{dag_id}', run '{run_id}':
1. airflow_dag_diagnose dag_id="{dag_id}" run_id="{run_id}"
2. Identify which tasks failed and why
3. Fetch logs from failed tasks
4. Recommend: retry tasks / clear full run / fix issue first
5. Summarize root cause and action plan"""
    }]

@mcp.prompt(name="daily_health_check")
async def daily_health_check() -> list:
    return [{
        "role": "user",
        "content": """Daily Airflow health check:
1. airflow_health_check
2. airflow_system_health (health + import errors + pool usage)
3. airflow_import_error_list
4. airflow_dag_warning_list
5. airflow_pool_list — flag pools >80% full
Report: system status, issues, bottlenecks, urgent actions."""
    }]

@mcp.prompt(name="onboard_new_dag")
async def onboard_new_dag(dag_id: str) -> list:
    return [{
        "role": "user",
        "content": f"""Validate new DAG '{dag_id}':
1. airflow_dag_get dag_id="{dag_id}" — confirm registered
2. airflow_task_list dag_id="{dag_id}" — review task structure
3. airflow_dag_source dag_id="{dag_id}" — inspect source
4. airflow_import_error_list — any parse errors?
5. airflow_dag_trigger dag_id="{dag_id}" — trigger test run
6. airflow_task_list_instances — monitor progress
Report: structure, issues, test run status, prod readiness."""
    }]

@mcp.prompt(name="optimize_pool_usage")
async def optimize_pool_usage() -> list:
    return [{
        "role": "user",
        "content": """Review Airflow pool usage:
1. airflow_pool_list — slots usage per pool
2. airflow_system_health — overall load
3. Identify bottlenecks (>80%) and underused pools (<20%)
Recommend: slot adjustments (airflow_pool_set), new pools, scheduling changes."""
    }]

@mcp.prompt(name="connection_audit")
async def connection_audit() -> list:
    return [{
        "role": "user",
        "content": """Security audit of Airflow connections:
1. airflow_connection_list — all connections
2. Flag: duplicate hosts, missing fields, unexpected types
3. Suggest cleanup (airflow_connection_delete for stale ones)
Report by type: total count, suspicious entries, recommended actions."""
    }]
```

### Tests (`tests/unit/test_prompts.py`)

- `test_troubleshoot_prompt_returns_message_list`
- `test_troubleshoot_prompt_includes_dag_id`
- `test_daily_health_check_no_args`
- `test_onboard_dag_includes_dag_id`
- `test_all_prompts_have_valid_role_content_structure`

## MCP tools affected

No new tools. Prompts expose via `prompts/list` + `prompts/get` MCP endpoints.

In Claude Desktop they appear as slash commands:
- `/troubleshoot_failed_dag` (args: `dag_id`, `run_id`)
- `/daily_health_check`
- `/onboard_new_dag` (arg: `dag_id`)
- `/optimize_pool_usage`
- `/connection_audit`

## Related

- SPEC-011: MCP Protocol (prerequisite)
- SPEC-012: MCP Resources (prompts reference resource URIs)
- SPEC-009: DAG Run Lifecycle (prompts reference clear/cancel tools)
