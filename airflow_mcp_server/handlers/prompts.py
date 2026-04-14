"""MCP Prompts — reusable workflow templates for common Airflow operations."""

from typing import Any


async def troubleshoot_failed_dag(dag_id: str, run_id: str) -> list:
    """Guide an LLM through diagnosing a failed DAG run step by step.

    Args:
        dag_id: ID of the failed DAG.
        run_id: ID of the failed DAG run.

    Returns:
        A list with a single user-role message containing the troubleshooting workflow.
    """
    return [
        {
            "role": "user",
            "content": (
                f"Troubleshoot DAG '{dag_id}', run '{run_id}':\n"
                f"1. airflow_dag_diagnose dag_id=\"{dag_id}\" run_id=\"{run_id}\"\n"
                "2. Identify which tasks failed and why\n"
                "3. Fetch logs from failed tasks\n"
                "4. Recommend: retry tasks / clear full run / fix issue first\n"
                "5. Summarize root cause and action plan"
            ),
        }
    ]


async def daily_health_check() -> list:
    """Structured morning health audit for the Airflow cluster.

    Returns:
        A list with a single user-role message containing the daily health check workflow.
    """
    return [
        {
            "role": "user",
            "content": (
                "Daily Airflow health check:\n"
                "1. airflow_health_check\n"
                "2. airflow_system_health (health + import errors + pool usage)\n"
                "3. airflow_import_error_list\n"
                "4. airflow_dag_warning_list\n"
                "5. airflow_pool_list — flag pools >80% full\n"
                "Report: system status, issues, bottlenecks, urgent actions."
            ),
        }
    ]


async def onboard_new_dag(dag_id: str) -> list:
    """Checklist for deploying and validating a new DAG in production.

    Args:
        dag_id: ID of the new DAG to validate.

    Returns:
        A list with a single user-role message containing the onboarding checklist.
    """
    return [
        {
            "role": "user",
            "content": (
                f"Validate new DAG '{dag_id}':\n"
                f"1. airflow_dag_get dag_id=\"{dag_id}\" — confirm registered\n"
                f"2. airflow_task_list dag_id=\"{dag_id}\" — review task structure\n"
                f"3. airflow_dag_source dag_id=\"{dag_id}\" — inspect source\n"
                "4. airflow_import_error_list — any parse errors?\n"
                f"5. airflow_dag_trigger dag_id=\"{dag_id}\" — trigger test run\n"
                "6. airflow_task_list_instances — monitor progress\n"
                "Report: structure, issues, test run status, prod readiness."
            ),
        }
    ]


async def optimize_pool_usage() -> list:
    """Guide for reviewing and adjusting Airflow pool slot allocation.

    Returns:
        A list with a single user-role message containing the pool optimization workflow.
    """
    return [
        {
            "role": "user",
            "content": (
                "Review Airflow pool usage:\n"
                "1. airflow_pool_list — slots usage per pool\n"
                "2. airflow_system_health — overall load\n"
                "3. Identify bottlenecks (>80%) and underused pools (<20%)\n"
                "Recommend: slot adjustments (airflow_pool_set), new pools, scheduling changes."
            ),
        }
    ]


async def connection_audit() -> list:
    """Security review of all Airflow connections.

    Returns:
        A list with a single user-role message containing the connection audit workflow.
    """
    return [
        {
            "role": "user",
            "content": (
                "Security audit of Airflow connections:\n"
                "1. airflow_connection_list — all connections\n"
                "2. Flag: duplicate hosts, missing fields, unexpected types\n"
                "3. Suggest cleanup (airflow_connection_delete for stale ones)\n"
                "Report by type: total count, suspicious entries, recommended actions."
            ),
        }
    ]


def register_all(mcp: Any) -> None:
    """Register all MCP prompts with the MCP server.

    Args:
        mcp: FastMCP server instance.
    """
    import logging

    logger = logging.getLogger(__name__)
    try:
        mcp.prompt(name="troubleshoot_failed_dag", description="Diagnose a failed DAG run step by step")(
            troubleshoot_failed_dag
        )
        mcp.prompt(name="daily_health_check", description="Structured morning health audit for Airflow")(
            daily_health_check
        )
        mcp.prompt(name="onboard_new_dag", description="Checklist for deploying and validating a new DAG")(
            onboard_new_dag
        )
        mcp.prompt(name="optimize_pool_usage", description="Review and adjust Airflow pool slot allocation")(
            optimize_pool_usage
        )
        mcp.prompt(name="connection_audit", description="Security review of all Airflow connections")(
            connection_audit
        )
        logger.info("Registered 5 MCP prompts")
    except Exception as e:
        logger.warning("Failed to register MCP prompts: %s", e)
