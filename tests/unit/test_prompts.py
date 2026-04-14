import pytest

from airflow_mcp_server.handlers import prompts


@pytest.mark.asyncio
async def test_troubleshoot_prompt_returns_message_list():
    result = await prompts.troubleshoot_failed_dag("my_dag", "run_20240101")
    assert isinstance(result, list)
    assert len(result) == 1


@pytest.mark.asyncio
async def test_troubleshoot_prompt_includes_dag_id():
    result = await prompts.troubleshoot_failed_dag("my_dag", "run_20240101")
    content = result[0]["content"]
    assert "my_dag" in content
    assert "run_20240101" in content


@pytest.mark.asyncio
async def test_troubleshoot_prompt_has_valid_role():
    result = await prompts.troubleshoot_failed_dag("my_dag", "run_20240101")
    assert result[0]["role"] == "user"


@pytest.mark.asyncio
async def test_daily_health_check_no_args():
    result = await prompts.daily_health_check()
    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0]["role"] == "user"
    assert "airflow_health_check" in result[0]["content"]


@pytest.mark.asyncio
async def test_onboard_dag_includes_dag_id():
    result = await prompts.onboard_new_dag("etl_pipeline")
    assert isinstance(result, list)
    content = result[0]["content"]
    assert "etl_pipeline" in content
    assert "airflow_dag_get" in content


@pytest.mark.asyncio
async def test_optimize_pool_usage_returns_list():
    result = await prompts.optimize_pool_usage()
    assert isinstance(result, list)
    assert result[0]["role"] == "user"
    assert "airflow_pool_list" in result[0]["content"]


@pytest.mark.asyncio
async def test_connection_audit_returns_list():
    result = await prompts.connection_audit()
    assert isinstance(result, list)
    assert result[0]["role"] == "user"
    assert "airflow_connection_list" in result[0]["content"]


@pytest.mark.asyncio
async def test_all_prompts_have_valid_role_content_structure():
    """All prompts must return a list of dicts with 'role' and 'content'."""
    results = [
        await prompts.troubleshoot_failed_dag("dag1", "run1"),
        await prompts.daily_health_check(),
        await prompts.onboard_new_dag("dag1"),
        await prompts.optimize_pool_usage(),
        await prompts.connection_audit(),
    ]
    for result in results:
        assert isinstance(result, list)
        assert len(result) >= 1
        for msg in result:
            assert "role" in msg
            assert "content" in msg
            assert msg["role"] in ("user", "assistant", "system")
            assert isinstance(msg["content"], str)
            assert len(msg["content"]) > 0


def test_register_all_graceful_on_bad_mcp():
    """register_all must not raise even when mcp.prompt() fails."""

    class BadMcp:
        def prompt(self, *args, **kwargs):
            raise RuntimeError("mcp unavailable")

    # Should not raise
    prompts.register_all(BadMcp())
