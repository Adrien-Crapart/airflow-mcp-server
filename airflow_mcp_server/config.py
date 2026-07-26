from dataclasses import dataclass
import os


@dataclass
class Config:
    AIRFLOW_BASE_URL: str = os.getenv("AIRFLOW_BASE_URL", "http://localhost:8080")
    # By default do not assume credentials; only use BasicAuth when
    # environment variables explicitly provide username/password.
    AIRFLOW_USERNAME: str = os.getenv("AIRFLOW_USERNAME", "")
    AIRFLOW_PASSWORD: str = os.getenv("AIRFLOW_PASSWORD", "")
    # Bearer token; takes precedence over BasicAuth when set.
    AIRFLOW_API_TOKEN: str = os.getenv("AIRFLOW_API_TOKEN", "")
    MCP_SERVER_HOST: str = os.getenv("MCP_SERVER_HOST", "127.0.0.1")
    MCP_SERVER_PORT: int = int(os.getenv("MCP_SERVER_PORT", "8000"))
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    # Require auth on HTTP-exposed MCP/tool surfaces.
    # If enabled and token is empty, only loopback clients are allowed.
    MCP_REQUIRE_AUTH: bool = os.getenv("MCP_REQUIRE_AUTH", "true").lower() == "true"
    # Bearer token (or X-API-Key) for incoming client requests.
    MCP_AUTH_TOKEN: str = os.getenv("MCP_AUTH_TOKEN", "")
    # Read-only mode: when enabled, only read-only tools are exposed
    MCP_READ_ONLY: bool = os.getenv("MCP_READ_ONLY", "false").lower() == "true"
    # Admin/config surfaces are disabled by default to avoid sensitive exposure.
    MCP_ENABLE_ADMIN_ENDPOINTS: bool = os.getenv("MCP_ENABLE_ADMIN_ENDPOINTS", "false").lower() == "true"
    # MCP transport mode: "stdio" (Claude Desktop), "http" (Streamable HTTP), "both" (default)
    MCP_TRANSPORT: str = os.getenv("MCP_TRANSPORT", "both")


cfg = Config()
