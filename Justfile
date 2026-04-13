# Justfile — common dev tasks for Airflow MCP Server
# Requires: just (https://github.com/casey/just)

# Use bash so commands behave consistently on CI
set shell := ["bash", "-cu"]

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
	bash hooks/install.sh

help:
	echo "Commands: uv_sync, run, test, lint, format, lock, hooks"
