import sys
import types
import pytest


def test_main_uses_app_start_when_present(monkeypatch):
    # Create fake app with start method
    started = {}

    class FakeApp:
        def start(self, host=None, port=None):
            started['host'] = host
            started['port'] = port

    fake_app = FakeApp()

    monkeypatch.setattr('airflow_mcp_server.main.create_app', lambda: fake_app)
    monkeypatch.setattr(sys, 'argv', ['prog'])

    # Import and run main
    from airflow_mcp_server.main import main

    main()

    assert started.get('host') == '127.0.0.1'
    assert started.get('port') == 8000


def test_main_dev_uses_uvicorn(monkeypatch):
    called = {}

    class FakeApp:
        pass

    fake_app = FakeApp()

    def fake_uvicorn_run(app, host=None, port=None, reload=None):
        called['host'] = host
        called['port'] = port
        called['reload'] = reload

    monkeypatch.setattr('airflow_mcp_server.main.create_app', lambda: fake_app)
    # override global uvicorn.run so the local import in main() calls our fake
    monkeypatch.setattr('uvicorn.run', fake_uvicorn_run, raising=False)
    monkeypatch.setattr(sys, 'argv', ['prog', '--dev'])

    from airflow_mcp_server.main import main

    main()

    assert called.get('reload') is True
