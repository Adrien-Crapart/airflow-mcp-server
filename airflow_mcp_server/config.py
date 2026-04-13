from dataclasses import dataclass
import os

@dataclass
class Config:
    AIRFLOW_BASE_URL: str = os.getenv("AIRFLOW_BASE_URL", "http://localhost:8080")
    # By default do not assume credentials; only use BasicAuth when
    # environment variables explicitly provide username/password.
    AIRFLOW_USERNAME: str = os.getenv("AIRFLOW_USERNAME", "")
    AIRFLOW_PASSWORD: str = os.getenv("AIRFLOW_PASSWORD", "")
    # Airflow major version (string) — allows toggling behavior between
    # Airflow 2.x and 3.x where the REST API shapes may differ.
    AIRFLOW_VERSION: str = os.getenv("AIRFLOW_VERSION", "2")
    MCP_SERVER_HOST: str = os.getenv("MCP_SERVER_HOST", "127.0.0.1")
    MCP_SERVER_PORT: int = int(os.getenv("MCP_SERVER_PORT", "8000"))
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    # Read-only mode: when enabled, only read-only tools are exposed
    MCP_READ_ONLY: bool = os.getenv("MCP_READ_ONLY", "false").lower() == "true"

cfg = Config()
