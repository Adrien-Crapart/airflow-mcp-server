import asyncio
from datetime import datetime, timezone
import logging
from typing import Any, Optional

import httpx

from .config import cfg

logger = logging.getLogger(__name__)

# Sentinel used to detect when no auth-override was passed to a helper
_UNSET = object()


class AirflowError(Exception):
    """Base exception for Airflow client errors."""


class AirflowAuthError(AirflowError):
    pass


class AirflowPermissionError(AirflowError):
    pass


class AirflowNotFoundError(AirflowError):
    pass


class AirflowConflictError(AirflowError):
    pass


class AirflowServerError(AirflowError):
    pass


class AirflowConnectionError(AirflowError):
    pass


class AirflowClient:
    """Async Airflow REST client with retry/backoff and HTTP->exception mapping."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        http_client: Optional[httpx.AsyncClient] = None,
    ) -> None:
        self.base_url = base_url or cfg.AIRFLOW_BASE_URL
        # Prefer explicitly passed credentials; fall back to config (may be empty).
        self.username = username if username is not None else cfg.AIRFLOW_USERNAME
        self.password = password if password is not None else cfg.AIRFLOW_PASSWORD
        # Support Bearer token authentication via `AIRFLOW_API_TOKEN`.
        # If present, prefer token over BasicAuth.
        self.token = cfg.AIRFLOW_API_TOKEN
        # This client targets Airflow 3.x exclusively, which exposes /api/v2.
        self.api_prefix = "/api/v2"
        if http_client is not None:
            # If a client was provided without a base_url, create a client
            # bound to the configured base_url so relative paths work.
            client_base = None
            try:
                client_base = getattr(http_client, "base_url", None)
            except Exception:
                client_base = None
            if client_base and str(client_base).strip():
                self._client = http_client
            else:
                auth = None
                headers = None
                # If token present, use Bearer header and ignore BasicAuth
                if self.token:
                    headers = {"Authorization": f"Bearer {self.token}"}
                else:
                    if self.username and self.password:
                        auth = httpx.BasicAuth(self.username, self.password)

                self._client = httpx.AsyncClient(
                    base_url=self.base_url,
                    auth=auth if not headers else None,
                    headers=headers,
                    timeout=30.0,
                )
        else:
            auth = None
            headers = None
            if self.token:
                headers = {"Authorization": f"Bearer {self.token}"}
            else:
                if self.username and self.password:
                    auth = httpx.BasicAuth(self.username, self.password)

            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                auth=auth if not headers else None,
                headers=headers,
                timeout=30.0,
            )

    async def _request_with_fallback(self, method: str, path: str, params: Optional[dict] = None, json: Optional[dict] = None, retries: int = 3, allow_auth_switch: bool = True) -> Any:
        """Call the Airflow v2 REST API, retrying once on an auth failure.

        On `AirflowAuthError`, a single auth-switch attempt is made: if we
        sent auth, retry once without it; if we sent no auth but credentials
        are configured, retry once with BasicAuth. Other exceptions propagate
        immediately.
        """
        try:
            return await self._request(method, path, params=params, json=json, retries=retries)
        except AirflowAuthError:
            if not allow_auth_switch:
                raise
            curr_auth = None
            try:
                curr_auth = getattr(self._client, "auth", None)
            except Exception:
                curr_auth = None

            # If the current client sent auth, retry once without auth
            if curr_auth:
                try:
                    return await self._request(method, path, params=params, json=json, retries=retries, override_auth=None)
                except AirflowAuthError:
                    pass

            # If no auth was sent but we have configured credentials, try with BasicAuth
            if (not curr_auth) and self.username and self.password:
                try:
                    return await self._request(method, path, params=params, json=json, retries=retries, override_auth=httpx.BasicAuth(self.username, self.password))
                except AirflowAuthError:
                    pass
            # Fallback didn't succeed; re-raise the original auth error
            raise

    async def _request(
        self,
        method: str,
        path: str,
        params: Optional[dict] = None,
        json: Optional[dict] = None,
        retries: int = 3,
        override_auth: Any = _UNSET,
    ) -> Any:
        attempt = 0
        backoff = 1
        while True:
            tmp_client = None
            try:
                # If a fully-qualified URL was provided, use it as-is. If a
                # relative path is used but the provided client lacks a
                # configured base_url, prefix with the configured base_url.
                request_target = path
                if not (path.startswith("http://") or path.startswith("https://")):
                    client_base = None
                    try:
                        client_base = getattr(self._client, "base_url", None)
                    except Exception:
                        client_base = None
                    if not client_base:
                        # ensure exactly one slash between base and path
                        request_target = self.base_url.rstrip("/") + "/" + path.lstrip("/")

                # If an auth override was requested (including explicit None),
                # create a short-lived client for this request so we don't
                # mutate the primary client state.
                if override_auth is _UNSET:
                    resp = await self._client.request(method, request_target, params=params, json=json)
                else:
                    base = None
                    try:
                        base = getattr(self._client, "base_url", None)
                    except Exception:
                        base = None
                    if not base:
                        base = self.base_url
                    timeout = getattr(self._client, "timeout", 30.0)
                    # Preserve Bearer token header when creating temporary client
                    if getattr(self, "token", None):
                        tmp_client = httpx.AsyncClient(base_url=base, auth=override_auth, timeout=timeout, headers={"Authorization": f"Bearer {self.token}"})
                    else:
                        tmp_client = httpx.AsyncClient(base_url=base, auth=override_auth, timeout=timeout)
                    resp = await tmp_client.request(method, request_target, params=params, json=json)
            except httpx.RequestError as exc:
                # network-level error
                if attempt < retries:
                    await asyncio.sleep(backoff)
                    attempt += 1
                    backoff *= 2
                    continue
                raise AirflowConnectionError(str(exc))
            finally:
                if tmp_client is not None:
                    await tmp_client.aclose()

            status = resp.status_code
            text = resp.text
            # success
            if 200 <= status < 300:
                try:
                    return resp.json()
                except Exception:
                    return text

            # server errors: retry a few times for 5xx
            if 500 <= status < 600:
                if attempt < retries:
                    await asyncio.sleep(backoff)
                    attempt += 1
                    backoff *= 2
                    continue
                raise AirflowServerError(f"Airflow server error: {status} {text}")

            # client errors mapping
            if status == 401:
                raise AirflowAuthError(f"Authentication failed: {text}")
            if status == 403:
                raise AirflowPermissionError(f"Permission denied: {text}")
            if status == 404:
                raise AirflowNotFoundError(f"Not found: {text}")
            if status == 409:
                raise AirflowConflictError(f"Conflict: {text}")

            # Other 4xx
            raise AirflowError(f"HTTP {status}: {text}")

    async def list_dags(self, limit: int = 100, offset: int = 0) -> list:
        resp = await self._request_with_fallback("GET", f"{self.api_prefix}/dags", params={"limit": limit, "offset": offset})
        if isinstance(resp, dict):
            return resp.get("dags") or resp.get("data") or []
        return []

    async def get_dag(self, dag_id: str) -> Any:
        return await self._request_with_fallback("GET", f"{self.api_prefix}/dags/{dag_id}")

    async def trigger_dag(self, dag_id: str, conf: Optional[dict] = None) -> Any:
        payload: dict[str, Any] = {
            # Airflow 3 requires `logical_date` in DAG run creation payload.
            "logical_date": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
        }
        if conf is not None:
            payload["conf"] = conf
        return await self._request_with_fallback("POST", f"{self.api_prefix}/dags/{dag_id}/dagRuns", json=payload)

    async def list_dag_runs(self, dag_id: str, limit: int = 100) -> list:
        resp = await self._request_with_fallback("GET", f"{self.api_prefix}/dags/{dag_id}/dagRuns", params={"limit": limit})
        if isinstance(resp, dict):
            return resp.get("dag_runs") or resp.get("dagRuns") or []
        return []

    async def get_task_instances(self, dag_id: str, run_id: str) -> list:
        resp = await self._request_with_fallback("GET", f"{self.api_prefix}/dags/{dag_id}/dagRuns/{run_id}/taskInstances")
        if isinstance(resp, dict):
            return resp.get("task_instances") or resp.get("taskInstances") or []
        return []

    async def get_task_logs(self, dag_id: str, run_id: str, task_id: str, try_number: int = 1) -> str:
        airflow3_path = f"{self.api_prefix}/dags/{dag_id}/dagRuns/{run_id}/taskInstances/{task_id}/logs/{try_number}"
        legacy_path = f"{self.api_prefix}/dags/{dag_id}/dagRuns/{run_id}/taskInstances/{task_id}/logs"

        try:
            resp = await self._request_with_fallback("GET", airflow3_path)
        except AirflowError as exc:
            # Older API variants use `/logs?try_number=...`.
            message = str(exc).lower()
            if (
                "http 404" not in message
                and "http 405" not in message
                and "http 422" not in message
                and "not found" not in message
            ):
                raise
            resp = await self._request_with_fallback("GET", legacy_path, params={"try_number": try_number})

        if isinstance(resp, dict):
            content = resp.get("content")
            if isinstance(content, str):
                return content
            if isinstance(content, list):
                lines: list[str] = []
                for entry in content:
                    if isinstance(entry, dict) and entry.get("event") is not None:
                        lines.append(str(entry.get("event")))
                    else:
                        lines.append(str(entry))
                return "\n".join(lines)

            logs = resp.get("logs")
            if isinstance(logs, str):
                return logs
            if isinstance(logs, list):
                return "\n".join(str(item) for item in logs)
            return ""
        return str(resp)

    async def list_connections(self, limit: int = 100) -> list:
        resp = await self._request_with_fallback("GET", f"{self.api_prefix}/connections", params={"limit": limit})
        if isinstance(resp, dict):
            return resp.get("connections") or []
        return []

    async def get_connection(self, conn_id: str) -> Any:
        return await self._request_with_fallback("GET", f"{self.api_prefix}/connections/{conn_id}")

    async def delete_connection(self, conn_id: str) -> Any:
        return await self._request_with_fallback("DELETE", f"{self.api_prefix}/connections/{conn_id}")

    async def create_connection(
        self,
        conn_id: str,
        conn_type: str,
        host: str,
        login: Optional[str] = None,
        password: Optional[str] = None,
        port: Optional[int] = None,
        extra: Optional[dict] = None,
    ) -> Any:
        # Airflow 3 expects `conn_type` (not `type`) in the request body.
        payload: dict[str, Any] = {"connection_id": conn_id, "conn_type": conn_type, "host": host}
        if login is not None:
            payload["login"] = login
        if password is not None:
            payload["password"] = password
        if port is not None:
            payload["port"] = port
        if extra is not None:
            payload["extra"] = extra
        return await self._request_with_fallback("POST", f"{self.api_prefix}/connections", json=payload)

    async def pause_dag(self, dag_id: str) -> Any:
        """Pause a DAG via the Airflow REST API (sets `is_paused = true`)."""
        return await self._request_with_fallback("PATCH", f"{self.api_prefix}/dags/{dag_id}", json={"is_paused": True})

    async def unpause_dag(self, dag_id: str) -> Any:
        """Unpause a DAG via the Airflow REST API (sets `is_paused = false`)."""
        return await self._request_with_fallback("PATCH", f"{self.api_prefix}/dags/{dag_id}", json={"is_paused": False})

    async def retry_task(self, dag_id: str, run_id: str, task_id: str) -> Any:
        """Retry a task by setting its state to `queued` via the REST API.

        Airflow 3 favors `clearTaskInstances`, while older variants expose
        `.../taskInstances/{task_id}/setState`.
        """
        legacy_path = f"{self.api_prefix}/dags/{dag_id}/dagRuns/{run_id}/taskInstances/{task_id}/setState"
        try:
            return await self._request_with_fallback("POST", legacy_path, json={"state": "queued"})
        except AirflowError as exc:
            # Endpoint-level incompatibility on newer API shapes (404/405)
            # should fall back to Airflow 3 clearTaskInstances.
            message = str(exc).lower()
            if "http 404" not in message and "http 405" not in message and "not found" not in message:
                raise

        payload = {"dag_run_id": run_id, "task_ids": [task_id], "dry_run": False}
        return await self._request_with_fallback("POST", f"{self.api_prefix}/dags/{dag_id}/clearTaskInstances", json=payload)

    async def list_variables(self, limit: int = 100) -> list:
        resp = await self._request_with_fallback("GET", f"{self.api_prefix}/variables", params={"limit": limit})
        if isinstance(resp, dict):
            return resp.get("variables") or []
        return []

    async def get_variable(self, key: str) -> Any:
        return await self._request_with_fallback("GET", f"{self.api_prefix}/variables/{key}")

    async def set_variable(self, key: str, value: str) -> Any:
        payload = {"key": key, "value": value}
        return await self._request_with_fallback("POST", f"{self.api_prefix}/variables", json=payload)

    async def delete_variable(self, key: str) -> Any:
        return await self._request_with_fallback("DELETE", f"{self.api_prefix}/variables/{key}")

    async def list_pools(self, limit: int = 100) -> list:
        resp = await self._request_with_fallback("GET", f"{self.api_prefix}/pools", params={"limit": limit})
        if isinstance(resp, dict):
            return resp.get("pools") or []
        return []

    async def get_pool(self, pool_name: str) -> Any:
        return await self._request_with_fallback("GET", f"{self.api_prefix}/pools/{pool_name}")

    async def set_pool(self, pool_name: str, slots: int, description: Optional[str] = None) -> Any:
        payload = {"name": pool_name, "slots": slots}
        if description is not None:
            payload["description"] = description
        return await self._request_with_fallback("POST", f"{self.api_prefix}/pools", json=payload)

    async def get_xcom(self, dag_id: str, run_id: str, task_id: str, key: str) -> Any:
        return await self._request_with_fallback("GET", f"{self.api_prefix}/dags/{dag_id}/dagRuns/{run_id}/taskInstances/{task_id}/xcomEntries/{key}")

    async def list_import_errors(self, limit: int = 100) -> list:
        resp = await self._request_with_fallback("GET", f"{self.api_prefix}/importErrors", params={"limit": limit})
        if isinstance(resp, dict):
            return resp.get("import_errors") or resp.get("importErrors") or []
        return []

    async def get_dag_source(self, file_token: str) -> Any:
        return await self._request_with_fallback("GET", f"{self.api_prefix}/dagSources/{file_token}")

    async def list_datasets(self, limit: int = 100) -> list:
        resp = await self._request_with_fallback("GET", f"{self.api_prefix}/datasets", params={"limit": limit})
        if isinstance(resp, dict):
            return resp.get("datasets") or resp.get("assets") or []
        return []

    async def get_dataset(self, dataset_uri: str) -> Any:
        import urllib.parse
        encoded_uri = urllib.parse.quote(dataset_uri, safe="")
        return await self._request_with_fallback("GET", f"{self.api_prefix}/datasets/{encoded_uri}")

    async def list_providers(self, limit: int = 100) -> list:
        resp = await self._request_with_fallback("GET", f"{self.api_prefix}/providers", params={"limit": limit})
        if isinstance(resp, dict):
            return resp.get("providers") or []
        return []

    async def list_plugins(self, limit: int = 100) -> list:
        resp = await self._request_with_fallback("GET", f"{self.api_prefix}/plugins", params={"limit": limit})
        if isinstance(resp, dict):
            return resp.get("plugins") or []
        return []

    # DAG Run lifecycle methods
    async def get_dag_run(self, dag_id: str, run_id: str) -> Any:
        """GET /dags/{dag_id}/dagRuns/{run_id}"""
        return await self._request_with_fallback("GET", f"{self.api_prefix}/dags/{dag_id}/dagRuns/{run_id}")

    async def clear_dag_run(self, dag_id: str, run_id: str, only_failed: bool = True) -> Any:
        """POST /dags/{dag_id}/dagRuns/{run_id}/clear"""
        payload = {"dry_run": False, "only_failed": only_failed, "reset_dag_runs": True}
        return await self._request_with_fallback("POST", f"{self.api_prefix}/dags/{dag_id}/dagRuns/{run_id}/clear", json=payload)

    async def delete_dag_run(self, dag_id: str, run_id: str) -> Any:
        """DELETE /dags/{dag_id}/dagRuns/{run_id}"""
        return await self._request_with_fallback("DELETE", f"{self.api_prefix}/dags/{dag_id}/dagRuns/{run_id}")

    async def update_dag_run_state(self, dag_id: str, run_id: str, state: str) -> Any:
        """PATCH /dags/{dag_id}/dagRuns/{run_id}"""
        payload = {"state": state}
        return await self._request_with_fallback("PATCH", f"{self.api_prefix}/dags/{dag_id}/dagRuns/{run_id}", json=payload)

    # Task definition and instance management methods
    async def list_tasks(self, dag_id: str) -> list:
        """GET /dags/{dag_id}/tasks"""
        resp = await self._request_with_fallback("GET", f"{self.api_prefix}/dags/{dag_id}/tasks")
        if isinstance(resp, dict):
            return resp.get("tasks") or []
        return []

    async def get_task(self, dag_id: str, task_id: str) -> Any:
        """GET /dags/{dag_id}/tasks/{task_id}"""
        return await self._request_with_fallback("GET", f"{self.api_prefix}/dags/{dag_id}/tasks/{task_id}")

    async def set_task_instance_state(self, dag_id: str, run_id: str, task_id: str, state: str) -> Any:
        """PATCH /dags/{dag_id}/dagRuns/{run_id}/taskInstances/{task_id}"""
        payload = {"state": state, "include_upstream": False, "include_downstream": False}
        return await self._request_with_fallback("PATCH", f"{self.api_prefix}/dags/{dag_id}/dagRuns/{run_id}/taskInstances/{task_id}", json=payload)

    async def clear_task_instance(self, dag_id: str, run_id: str, task_id: str) -> Any:
        """POST /dags/{dag_id}/dagRuns/{run_id}/taskInstances/{task_id}/clear"""
        return await self._request_with_fallback("POST", f"{self.api_prefix}/dags/{dag_id}/dagRuns/{run_id}/taskInstances/{task_id}/clear")

    # Audit and config methods
    async def list_event_logs(self, limit: int = 100, dag_id: Optional[str] = None, event: Optional[str] = None) -> Any:
        """GET /eventLogs — Airflow audit trail."""
        params: dict[str, Any] = {"limit": limit}
        if dag_id:
            params["dag_id"] = dag_id
        if event:
            params["event"] = event
        resp = await self._request_with_fallback("GET", f"{self.api_prefix}/eventLogs", params=params)
        if isinstance(resp, dict):
            return resp.get("entries") or resp.get("events") or []
        return []

    async def get_event_log(self, event_log_id: int) -> Any:
        """GET /eventLogs/{event_log_id}"""
        return await self._request_with_fallback("GET", f"{self.api_prefix}/eventLogs/{event_log_id}")

    async def get_config(self, section: Optional[str] = None) -> Any:
        """GET /config — Airflow configuration (may require admin permissions)."""
        resp = await self._request_with_fallback("GET", f"{self.api_prefix}/config")
        if section and isinstance(resp, dict):
            return resp.get(section, {})
        return resp

    async def get_version(self) -> Any:
        """GET /version — Airflow version metadata."""
        return await self._request_with_fallback("GET", f"{self.api_prefix}/version")

    async def list_dag_warnings(self, dag_id: Optional[str] = None, limit: int = 100) -> Any:
        """GET /dagWarnings"""
        params: dict[str, Any] = {"limit": limit}
        if dag_id:
            params["dag_id"] = dag_id
        resp = await self._request_with_fallback("GET", f"{self.api_prefix}/dagWarnings", params=params)
        if isinstance(resp, dict):
            return resp.get("dag_warnings") or resp.get("warnings") or []
        return []

    async def close(self) -> None:
        await self._client.aclose()


# module-level client convenience instance
client = AirflowClient()
