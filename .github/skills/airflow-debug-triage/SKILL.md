---
name: airflow-debug-triage
description: "Diagnose Airflow MCP communication failures and quality regressions across auth, transport, endpoint mapping, and server-side behavior. Use for 401/403/404/5xx, timeouts, and inconsistent tool outcomes."
argument-hint: "Provide failing tool, exact error, timestamp, environment variables used, and whether failure is local, CI, or integration."
user-invocable: true
---

# Airflow Debug Triage

## Outcome
Find and verify root cause for Airflow MCP failures, then propose a minimal and testable fix.

## When to Use
Use this skill when you see:
- AirflowAuthError, AirflowPermissionError, AirflowNotFoundError
- AirflowConnectionError or AirflowServerError
- tool endpoint failures in /tool/{tool_name} or /tool
- inconsistent behavior between local, CI, and integration runs

## Related Agent
- airflow-debugger

## Procedure
1. Capture failure context
- tool name, payload, error text, status code
- command or test that reproduced the issue
- branch/commit and environment variables

2. Check connectivity and auth assumptions
- verify AIRFLOW_BASE_URL and credentials/token
- verify target Airflow supports /api/v2
- reproduce with direct API call if needed

3. Reproduce through MCP surfaces
- reproduce via /tool/{tool_name} and fallback /tool
- compare behavior with direct airflow_client call

4. Map error to expected contract
- 401 -> AirflowAuthError
- 403 -> AirflowPermissionError
- 404 -> AirflowNotFoundError
- 409 -> AirflowConflictError
- 5xx -> AirflowServerError
- network/request errors -> AirflowConnectionError

5. Evaluate repository quality gates
- endpoint access control on tool execution surfaces
- sensitive admin/config exposure
- masking of sensitive variable/resource outputs
- 4xx logging behavior (avoid stacktrace noise)
- read-only mode behavior for mutating tools

6. Confirm integration evidence quality
- if integration passes with fallback mock, label as contract/mock evidence
- keep real end-to-end evidence separate

7. Propose and verify fix
- implement smallest safe change
- add or update regression tests
- rerun relevant checks and summarize outcomes

## Decision Points
- If 404 occurs:
  - check path construction and dag/run/task ids
  - verify endpoint exists in Airflow /api/v2
- If 401/403 occurs:
  - check token vs basic auth mode
  - verify permission model in Airflow
- If timeout/network errors occur:
  - check base URL reachability and retry behavior
- If tests pass unexpectedly:
  - inspect integration fixture fallback behavior

## Completion Checklist
- [ ] Reproduction path documented
- [ ] Root cause identified and categorized
- [ ] Fix proposal is minimal and testable
- [ ] Relevant tests updated or added
- [ ] Quality gates reviewed
- [ ] Evidence clearly marks real integration vs mock fallback
