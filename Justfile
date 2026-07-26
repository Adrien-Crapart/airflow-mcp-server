# Justfile — common dev tasks for Airflow MCP Server
# Requires: just (https://github.com/casey/just)

set windows-shell := ["powershell.exe", "-NoLogo", "-NoProfile", "-Command"]

uv_sync:
	uv sync

run:
	uv run python -m airflow_mcp_server.main --dev

test:
	uv run pytest -k "not integration" -v

lint:
	uv run ruff check . --fix

format:
	uv run ruff format .

lock:
	uv lock

hooks:
	sh hooks/install.sh

help:
	echo "Commands: uv_sync, run, test, lint, format, lock, hooks"
