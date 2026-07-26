import sys

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


def test_main_stdio_success(monkeypatch):
    """Stdio transport: create_stdio_server().run() is invoked and main() returns normally."""
    calls = {}

    class FakeMcpServer:
        def run(self):
            calls['ran'] = True

    monkeypatch.setattr('airflow_mcp_server.main.create_stdio_server', lambda: FakeMcpServer())
    monkeypatch.setattr(sys, 'argv', ['prog', '--transport', 'stdio'])

    from airflow_mcp_server.main import main

    main()

    assert calls.get('ran') is True


def test_main_stdio_failure_exits(monkeypatch):
    """Stdio transport: any exception during startup logs an error and exits via sys.exit(1)."""

    def fake_create_stdio_server():
        raise RuntimeError("boom")

    monkeypatch.setattr('airflow_mcp_server.main.create_stdio_server', fake_create_stdio_server)
    monkeypatch.setattr(sys, 'argv', ['prog', '--transport', 'stdio'])

    from airflow_mcp_server.main import main

    with pytest.raises(SystemExit):
        main()


def test_main_dev_uvicorn_failure_falls_through_to_generic_block(monkeypatch):
    """When dev-mode uvicorn.run() raises, execution falls through (no exit) to the
    final generic uvicorn.run() block, which is attempted afterwards."""
    call_count = {'n': 0}
    calls = []

    class FakeApp:
        pass  # no `.start` attribute, so the generic block is reached too

    fake_app = FakeApp()

    def fake_uvicorn_run(app, host=None, port=None, reload=None):
        call_count['n'] += 1
        calls.append({'host': host, 'port': port, 'reload': reload})
        if call_count['n'] == 1:
            raise RuntimeError("dev uvicorn failed")
        # second call (generic block) succeeds

    monkeypatch.setattr('airflow_mcp_server.main.create_app', lambda: fake_app)
    monkeypatch.setattr('uvicorn.run', fake_uvicorn_run, raising=False)
    monkeypatch.setattr(sys, 'argv', ['prog', '--dev'])

    from airflow_mcp_server.main import main

    main()

    assert call_count['n'] == 2
    assert calls[0]['reload'] is True
    assert calls[1]['reload'] is False


def test_main_app_start_failure_falls_through_to_uvicorn(monkeypatch):
    """When app.start() raises, execution falls through silently to the final
    generic uvicorn.run() block."""
    called = {}

    class FakeApp:
        def start(self, host=None, port=None):
            raise RuntimeError("start failed")

    fake_app = FakeApp()

    def fake_uvicorn_run(app, host=None, port=None, reload=None):
        called['ran'] = True
        called['reload'] = reload

    monkeypatch.setattr('airflow_mcp_server.main.create_app', lambda: fake_app)
    monkeypatch.setattr('uvicorn.run', fake_uvicorn_run, raising=False)
    monkeypatch.setattr(sys, 'argv', ['prog'])

    from airflow_mcp_server.main import main

    main()

    assert called.get('ran') is True
    assert called.get('reload') is False


def test_main_generic_uvicorn_success(monkeypatch):
    """No --dev flag and no `.start` attribute: the generic block runs
    uvicorn.run(app, host, port, reload=False)."""
    called = {}

    class FakeApp:
        pass  # no `.start` attribute

    fake_app = FakeApp()

    def fake_uvicorn_run(app, host=None, port=None, reload=None):
        called['host'] = host
        called['port'] = port
        called['reload'] = reload

    monkeypatch.setattr('airflow_mcp_server.main.create_app', lambda: fake_app)
    monkeypatch.setattr('uvicorn.run', fake_uvicorn_run, raising=False)
    monkeypatch.setattr(sys, 'argv', ['prog'])

    from airflow_mcp_server.main import main

    main()

    assert called.get('reload') is False
    assert called.get('host') == '127.0.0.1'
    assert called.get('port') == 8000


def test_main_generic_uvicorn_failure_exits(monkeypatch):
    """No --dev flag and no `.start` attribute: if the generic uvicorn.run() call
    raises, main() exits via sys.exit(1)."""

    class FakeApp:
        pass  # no `.start` attribute

    fake_app = FakeApp()

    def fake_uvicorn_run(app, host=None, port=None, reload=None):
        raise RuntimeError("generic uvicorn failed")

    monkeypatch.setattr('airflow_mcp_server.main.create_app', lambda: fake_app)
    monkeypatch.setattr('uvicorn.run', fake_uvicorn_run, raising=False)
    monkeypatch.setattr(sys, 'argv', ['prog'])

    from airflow_mcp_server.main import main

    with pytest.raises(SystemExit):
        main()
