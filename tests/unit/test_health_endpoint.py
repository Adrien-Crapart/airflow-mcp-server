import pytest

from airflow_mcp_server.server import create_app


@pytest.mark.asyncio
async def test_http_health():
    app = create_app()
    # ASGI test utilities may not be available; call the app via an ASGI test client.
    # We'll start the app in an ASGI test client using httpx.AsyncClient and asgi-lifespan if available.
    try:
        from asgi_lifespan import LifespanManager
        import httpx
    except Exception:
        pytest.skip("Lifespan or httpx not installed in this environment")

    async with LifespanManager(app):
        async with httpx.AsyncClient(app=app, base_url="http://testserver") as client:
            r = await client.get("/health")
            assert r.status_code == 200
            assert r.json() == {"status": "ok"}
