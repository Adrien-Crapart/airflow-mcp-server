import asyncio
import logging
import re
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


class AirflowConnectionError(ConnectionError):
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
        # Airflow major version (string), e.g. '2' or '3'
        self.version = str(getattr(cfg, "AIRFLOW_VERSION", "2"))
        # Map Airflow major version to the API prefix used by the REST API.
        # Airflow 2.x typically exposes /api/v1, while Airflow 3.x upgrades
        # to /api/v2.
        if self.version and str(self.version).startswith("3"):
            self.api_prefix = "/api/v2"
        else:
            self.api_prefix = "/api/v1"
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
                if self.username and self.password:
                    auth = httpx.BasicAuth(self.username, self.password)
                self._client = httpx.AsyncClient(
                    base_url=self.base_url,
                    auth=auth,
                    timeout=30.0,
                )
        else:
            auth = None
            if self.username and self.password:
                auth = httpx.BasicAuth(self.username, self.password)
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                auth=auth,
                timeout=30.0,
            )

    def _to_snake_path(self, path: str) -> str:
        """Return a snake_case variant of a REST path by converting camelCase
        segments to snake_case. Placeholders like `{dag_id}` are left intact.
        This helps support API differences between Airflow major versions.
        """
        parts = path.split("/")
        new_parts = []
        for p in parts:
            if not p or p.startswith("{"):
                new_parts.append(p)
                continue
            s = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", p)
            new_parts.append(s.lower())
        return "/".join(new_parts)

    async def _request_with_fallback(self, method: str, path: str, params: Optional[dict] = None, json: Optional[dict] = None, retries: int = 3, allow_api_switch: bool = True, allow_auth_switch: bool = True) -> Any:
        """Try the primary path, then a snake_case variant if available.

        If a 404 (AirflowNotFoundError) occurs for the primary path, the
        snake_case variant is attempted. Other exceptions are raised
        immediately.
        """
        # Keep the original path for potential api-prefix switching logic below
        original_path = path

        candidates = [path]
        snake = self._to_snake_path(path)
        if snake != path:
            candidates.append(snake)

        last_not_found = None
        for p in candidates:
            try:
                return await self._request(method, p, params=params, json=json, retries=retries)
            except AirflowNotFoundError as exc:
                last_not_found = exc
                continue
            except AirflowAuthError as exc:
                # Try a single auth-switch attempt: if we had auth, retry without it;
                # if we had no auth but credentials are configured, retry with BasicAuth.
                if allow_auth_switch:
                    curr_auth = None
                    try:
                        curr_auth = getattr(self._client, "auth", None)
                    except Exception:
                        curr_auth = None

                    # If the current client sent auth, retry once without auth
                    if curr_auth:
                        try:
                            return await self._request(method, p, params=params, json=json, retries=retries, override_auth=None)
                        except AirflowAuthError:
                            # fall through to raise original
                            pass

                    # If no auth was sent but we have configured credentials, try with BasicAuth
                    if (not curr_auth) and self.username and self.password:
                        try:
                            return await self._request(method, p, params=params, json=json, retries=retries, override_auth=httpx.BasicAuth(self.username, self.password))
                        except AirflowAuthError:
                            pass
                # If fallback didn't succeed, re-raise the original auth error
                raise
            except AirflowError:
                # propagate other Airflow-related errors immediately
                raise
        if last_not_found:
            # If Airflow indicates the v1 API was removed (Airflow 3+), switch
            # to the v2 API prefix once and retry the same request. This makes
            # the client resilient when the user did not configure
            # AIRFLOW_VERSION correctly.
            if allow_api_switch:
                try:
                    msg = str(last_not_found)
                except Exception:
                    msg = ""
                if "/api/v1" in msg and "/api/v2" in msg and self.api_prefix != "/api/v2":
                    logger.info("Airflow indicates /api/v1 removed; switching api_prefix to /api/v2 and retrying")
                    self.api_prefix = "/api/v2"
                    # Replace first occurrence of /api/v1 with /api/v2 in the original path
                    if original_path.startswith("/api/v1"):
                        new_path = original_path.replace("/api/v1", "/api/v2", 1)
                    else:
                        new_path = original_path.replace("/api/v1", "/api/v2")
                    return await self._request_with_fallback(method, new_path, params=params, json=json, retries=retries, allow_api_switch=False, allow_auth_switch=True)
            raise last_not_found
        # Fallback: try the original path which will raise an appropriate error
        return await self._request(method, path, params=params, json=json, retries=retries)

    async def _request(
        self,
        method: str,
        path: str,
        params: Optional[dict] = None,
        json: Optional[dict] = None,
        retries: int = 3,
        override_auth: object = _UNSET,
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
        payload: dict = {}
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
        path = f"{self.api_prefix}/dags/{dag_id}/dagRuns/{run_id}/taskInstances/{task_id}/logs"
        resp = await self._request_with_fallback("GET", path, params={"try_number": try_number})
        if isinstance(resp, dict):
            return resp.get("content") or resp.get("logs") or ""
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
        payload: dict = {"connection_id": conn_id, "type": conn_type, "host": host}
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

        Note: behavior depends on Airflow version; this uses the `setState` taskInstance endpoint.
        """
        # Try both camelCase and snake_case setState endpoints to support
        # Airflow API variations across major versions.
        path = f"{self.api_prefix}/dags/{dag_id}/dagRuns/{run_id}/taskInstances/{task_id}/setState"
        return await self._request_with_fallback("POST", path, json={"state": "queued"})

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

    async def close(self) -> None:
        await self._client.aclose()


# module-level client convenience instance
client = AirflowClient()
