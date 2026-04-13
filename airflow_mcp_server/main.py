import argparse
import sys

from .server import create_app


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dev", action="store_true", help="Run server with reload")
    parser.add_argument("--host", default=None)
    parser.add_argument("--port", type=int, default=None)
    args = parser.parse_args()

    app = create_app()
    host = args.host or "127.0.0.1"
    port = args.port or 8000

    # In development prefer uvicorn (hot-reload) for easier debugging
    if args.dev:
        try:
            import uvicorn

            uvicorn.run(app, host=host, port=port, reload=True)
            return
        except Exception:
            print("Failed to start server with Uvicorn in dev mode", file=sys.stderr)

    # If the app exposes a `.start()` entrypoint (custom runner), prefer it.
    if hasattr(app, "start"):
        try:
            app.start(host=host, port=port)
            return
        except Exception:
            # fallthrough to uvicorn if app.start fails for some reason
            pass

    # Start generic ASGI apps with Uvicorn
    try:
        import uvicorn

        uvicorn.run(app, host=host, port=port, reload=False)
    except Exception:
        print("Failed to start server with Uvicorn", file=sys.stderr)


if __name__ == "__main__":
    main()
