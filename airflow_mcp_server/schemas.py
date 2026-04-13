from typing import Optional, Any, Dict
from pydantic import BaseModel, Field, ValidationError


class ToolResponse(BaseModel):
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None


# Per-tool parameter models
class ListDagsParams(BaseModel):
    limit: int = Field(100, ge=1)
    offset: int = Field(0, ge=0)


class TriggerDagParams(BaseModel):
    dag_id: str
    conf: Optional[Dict[str, Any]] = None


class DagIdParams(BaseModel):
    dag_id: str


class TaskRunParams(BaseModel):
    dag_id: str
    run_id: str


class RetryTaskParams(BaseModel):
    dag_id: str
    run_id: str
    task_id: str


class FetchLogsParams(BaseModel):
    dag_id: str
    task_id: str
    run_id: str
    try_number: int = Field(1, ge=1)


class CreateConnectionParams(BaseModel):
    conn_id: str
    type: str = ""
    host: str = ""
    login: Optional[str] = None
    password: Optional[str] = None
    port: Optional[int] = None
    extra: Optional[Dict[str, Any]] = None


class DagRunListParams(BaseModel):
    dag_id: str
    limit: int = Field(100, ge=1)


class ConnectionIdParams(BaseModel):
    conn_id: str


class ListConnectionsParams(BaseModel):
    limit: int = Field(100, ge=1)


class VariableKeyParams(BaseModel):
    key: str


class SetVariableParams(BaseModel):
    key: str
    value: str


class ListVariablesParams(BaseModel):
    limit: int = Field(100, ge=1)


class PoolNameParams(BaseModel):
    pool_name: str


class SetPoolParams(BaseModel):
    pool_name: str
    slots: int = Field(ge=1)
    description: Optional[str] = None


class ListPoolsParams(BaseModel):
    limit: int = Field(100, ge=1)


class XcomGetParams(BaseModel):
    dag_id: str
    run_id: str
    task_id: str
    key: str


class ListImportErrorsParams(BaseModel):
    limit: int = Field(100, ge=1)


class DiagnoseDagRunParams(BaseModel):
    dag_id: str
    run_id: str


class SystemHealthParams(BaseModel):
    pass  # No parameters needed


class ListDatasetsParams(BaseModel):
    limit: int = Field(100, ge=1)


class DatasetUriParams(BaseModel):
    dataset_uri: str


class ListProvidersParams(BaseModel):
    limit: int = Field(100, ge=1)


class ListPluginsParams(BaseModel):
    limit: int = Field(100, ge=1)


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
}
