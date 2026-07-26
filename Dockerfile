FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install build deps (kept minimal)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY . /app

RUN pip install --upgrade pip
RUN pip install --no-cache-dir .

EXPOSE 8000

ENV AIRFLOW_BASE_URL=http://airflow-webserver:8080

# Start the unified launcher so MCP_TRANSPORT (stdio/http/both) is honored.
CMD ["python", "-m", "airflow_mcp_server.main"]
