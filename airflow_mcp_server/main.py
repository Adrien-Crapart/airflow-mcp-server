import argparse
import sys
import logging

from .server import create_app, create_stdio_server

logger = logging.getLogger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dev", action="store_true", help="Run server with reload")
    parser.add_argument("--host", default=None)
    parser.add_argument("--port", type=int, default=None)
    parser.add_argument("--transport", default=None, help="MCP transport: stdio, http, or both")
    args = parser.parse_args()

    from .config import cfg

    # Determine transport mode
    transport = args.transport or cfg.MCP_TRANSPORT
    host = args.host or cfg.MCP_SERVER_HOST
    port = args.port or cfg.MCP_SERVER_PORT

    # Stdio transport (Claude Desktop / MCP CLI)
    if transport == "stdio":
        try:
            logger.info("Starting MCP server in stdio mode")
            mcp_server = create_stdio_server()
            mcp_server.run()
            return
        except Exception as e:
            logger.error("Failed to start MCP stdio server: %s", e)
            sys.exit(1)

    # HTTP transport (FastAPI + optional MCP Streamable HTTP)
    app = create_app()

    if args.dev:
        try:
            import uvicorn

            logger.info("Starting server in development mode on %s:%d", host, port)
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

        logger.info("Starting server on %s:%d (transport: %s)", host, port, transport)
        uvicorn.run(app, host=host, port=port, reload=False)
    except Exception:
        print("Failed to start server with Uvicorn", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
