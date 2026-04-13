from typing import Optional, Any, Dict
from pydantic import BaseModel, Field, ValidationError


class ToolResponse(BaseModel):
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None


# Per-tool parameter models
class ListDagsParams(BaseModel):
    limit: int = Field(100, ge=1, description="Maximum number of DAGs to return. Default 100.")
    offset: int = Field(0, ge=0, description="Pagination offset. Default 0.")


class TriggerDagParams(BaseModel):
    dag_id: str = Field(..., description="The unique identifier of the DAG to trigger (e.g. 'my_etl_dag')")
    conf: Optional[Dict[str, Any]] = Field(None, description="Optional run configuration JSON dict")


class DagIdParams(BaseModel):
    dag_id: str = Field(..., description="The unique identifier of the DAG (e.g. 'my_etl_dag')")


class TaskRunParams(BaseModel):
    dag_id: str = Field(..., description="The unique identifier of the DAG")
    run_id: str = Field(..., description="The run identifier (e.g. 'manual__2026-01-01T00:00:00+00:00')")


class RetryTaskParams(BaseModel):
    dag_id: str = Field(..., description="The unique identifier of the DAG")
    run_id: str = Field(..., description="The run identifier")
    task_id: str = Field(..., description="The task identifier within the DAG")


class FetchLogsParams(BaseModel):
    dag_id: str = Field(..., description="The unique identifier of the DAG")
    task_id: str = Field(..., description="The task identifier within the DAG")
    run_id: str = Field(..., description="The run identifier")
    try_number: int = Field(1, ge=1, description="Attempt number (1 = first try, 2 = first retry, etc.)")


class CreateConnectionParams(BaseModel):
    conn_id: str = Field(..., description="Unique connection identifier")
    type: str = Field("", description="Connection type (e.g. 'http', 'postgres', 'aws')")
    host: str = Field("", description="Connection host")
    login: Optional[str] = Field(None, description="Login/username")
    password: Optional[str] = Field(None, description="Password")
    port: Optional[int] = Field(None, description="Connection port")
    extra: Optional[Dict[str, Any]] = Field(None, description="Extra configuration JSON")


class DagRunListParams(BaseModel):
    dag_id: str = Field(..., description="The unique identifier of the DAG")
    limit: int = Field(100, ge=1, description="Maximum number of runs to return. Default 100.")


class ConnectionIdParams(BaseModel):
    conn_id: str = Field(..., description="Unique connection identifier")


class ListConnectionsParams(BaseModel):
    limit: int = Field(100, ge=1, description="Maximum number of connections to return. Default 100.")


class VariableKeyParams(BaseModel):
    key: str = Field(..., description="Variable key name")


class SetVariableParams(BaseModel):
    key: str = Field(..., description="Variable key name")
    value: str = Field(..., description="Variable value (JSON string or plain text)")


class ListVariablesParams(BaseModel):
    limit: int = Field(100, ge=1, description="Maximum number of variables to return. Default 100.")


class PoolNameParams(BaseModel):
    pool_name: str = Field(..., description="Pool name identifier")


class SetPoolParams(BaseModel):
    pool_name: str = Field(..., description="Pool name identifier")
    slots: int = Field(..., ge=1, description="Number of slots in the pool")
    description: Optional[str] = Field(None, description="Pool description")


class ListPoolsParams(BaseModel):
    limit: int = Field(100, ge=1, description="Maximum number of pools to return. Default 100.")


class XcomGetParams(BaseModel):
    dag_id: str = Field(..., description="The unique identifier of the DAG")
    run_id: str = Field(..., description="The run identifier")
    task_id: str = Field(..., description="The task identifier within the DAG")
    key: str = Field(..., description="XCom key name")


class ListImportErrorsParams(BaseModel):
    limit: int = Field(100, ge=1, description="Maximum number of import errors to return. Default 100.")


class DiagnoseDagRunParams(BaseModel):
    dag_id: str = Field(..., description="The unique identifier of the DAG")
    run_id: str = Field(..., description="The run identifier")


class SystemHealthParams(BaseModel):
    pass  # No parameters needed


class ListDatasetsParams(BaseModel):
    limit: int = Field(100, ge=1, description="Maximum number of datasets to return. Default 100.")


class DatasetUriParams(BaseModel):
    dataset_uri: str = Field(..., description="Dataset URI identifier")


class ListProvidersParams(BaseModel):
    limit: int = Field(100, ge=1, description="Maximum number of providers to return. Default 100.")


class ListPluginsParams(BaseModel):
    limit: int = Field(100, ge=1, description="Maximum number of plugins to return. Default 100.")


class ToolGetParams(BaseModel):
    tool_name: str = Field(..., description="The name of the tool to fetch (e.g. 'airflow_dag_list')")


class DagRunIdParams(BaseModel):
    dag_id: str = Field(..., description="The unique identifier of the DAG")
    run_id: str = Field(..., description="The run identifier")


class ClearDagRunParams(BaseModel):
    dag_id: str = Field(..., description="The unique identifier of the DAG")
    run_id: str = Field(..., description="The DAG run to clear")
    only_failed: bool = Field(True, description="Only clear failed tasks (default: True)")


class SetDagRunStateParams(BaseModel):
    dag_id: str = Field(..., description="The unique identifier of the DAG")
    run_id: str = Field(..., description="The run identifier")
    state: str = Field(..., description="Target state: 'success', 'failed', 'queued', 'running'")


class TaskListParams(BaseModel):
    dag_id: str = Field(..., description="The unique identifier of the DAG")


class TaskGetParams(BaseModel):
    dag_id: str = Field(..., description="The unique identifier of the DAG")
    task_id: str = Field(..., description="The task identifier within the DAG")


class SetTaskStateParams(BaseModel):
    dag_id: str = Field(..., description="The unique identifier of the DAG")
    run_id: str = Field(..., description="The run identifier")
    task_id: str = Field(..., description="The task identifier within the DAG")
    state: str = Field(..., description="Target state: 'success', 'failed', 'skipped', 'up_for_retry'")


class ClearTaskParams(BaseModel):
    dag_id: str = Field(..., description="The unique identifier of the DAG")
    run_id: str = Field(..., description="The run identifier")
    task_id: str = Field(..., description="The task identifier within the DAG")


class ListEventLogsParams(BaseModel):
    limit: int = Field(100, ge=1, description="Maximum number of audit events to return. Default 100.")
    dag_id: Optional[str] = Field(None, description="Filter by DAG ID (optional)")
    event: Optional[str] = Field(None, description="Filter by event type (e.g. 'trigger', 'pause', 'success')")


class EventLogIdParams(BaseModel):
    event_log_id: int = Field(..., description="Numeric ID of the audit event")


class ListDagWarningsParams(BaseModel):
    dag_id: Optional[str] = Field(None, description="Filter by DAG ID (None = all DAGs)")
    limit: int = Field(100, ge=1, description="Maximum number of warnings to return. Default 100.")


class GetConfigParams(BaseModel):
    section: Optional[str] = Field(None, description="Config section to filter (e.g. 'core', 'scheduler')")


# Mapping tool_name -> pydantic model used to validate `params` dict
TOOL_INPUT_MODELS: Dict[str, type] = {
    "airflow_dag_list": ListDagsParams,
    "airflow_dag_get": DagIdParams,
    "airflow_dag_trigger": TriggerDagParams,
    "airflow_dag_pause": DagIdParams,
    "airflow_dag_unpause": DagIdParams,
    "airflow_dag_run_list": DagRunListParams,
    "airflow_task_list_instances": TaskRunParams,
    "airflow_task_retry": RetryTaskParams,
    "airflow_task_logs": FetchLogsParams,
    "airflow_connection_list": ListConnectionsParams,
    "airflow_connection_get": ConnectionIdParams,
    "airflow_connection_delete": ConnectionIdParams,
    "airflow_connection_create": CreateConnectionParams,
    "airflow_variable_list": ListVariablesParams,
    "airflow_variable_get": VariableKeyParams,
    "airflow_variable_set": SetVariableParams,
    "airflow_variable_delete": VariableKeyParams,
    "airflow_pool_list": ListPoolsParams,
    "airflow_pool_get": PoolNameParams,
    "airflow_pool_set": SetPoolParams,
    "airflow_xcom_get": XcomGetParams,
    "airflow_import_error_list": ListImportErrorsParams,
    "airflow_dag_diagnose": DiagnoseDagRunParams,
    "airflow_system_health": SystemHealthParams,
    "airflow_dag_source": DagIdParams,
    "airflow_dataset_list": ListDatasetsParams,
    "airflow_dataset_get": DatasetUriParams,
    "airflow_provider_list": ListProvidersParams,
    "airflow_plugin_list": ListPluginsParams,
    "airflow_tool_get": ToolGetParams,
    "airflow_dag_run_get": DagRunIdParams,
    "airflow_dag_run_clear": ClearDagRunParams,
    "airflow_dag_run_cancel": DagRunIdParams,
    "airflow_dag_run_set_state": SetDagRunStateParams,
    "airflow_task_list": TaskListParams,
    "airflow_task_get": TaskGetParams,
    "airflow_task_set_state": SetTaskStateParams,
    "airflow_task_clear": ClearTaskParams,
    "airflow_event_log_list": ListEventLogsParams,
    "airflow_event_log_get": EventLogIdParams,
    "airflow_dag_warning_list": ListDagWarningsParams,
    "airflow_config_get": GetConfigParams,
}
