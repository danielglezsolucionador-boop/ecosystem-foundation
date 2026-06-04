from fastapi import APIRouter, status

from app.schemas.observability import (
    ObservabilityHealthService,
    ObservabilityIncident,
    ObservabilityIncidentCreate,
    ObservabilityLog,
    ObservabilityLogCreate,
    ObservabilityMetric,
    ObservabilityMetricCreate,
    ObservabilityObjective,
    ObservabilityOverview,
    ObservabilityStatus,
    ObservabilityTrace,
    ObservabilityTraceCreate,
)
from app.services.observability import (
    create_incident,
    create_log,
    create_metric,
    create_trace,
    get_health_aggregation,
    get_observability_overview,
    get_observability_status,
    get_sla_registry,
    get_slo_registry,
    list_error_logs,
    list_incidents,
    list_logs,
    list_metrics,
    list_traces,
)

router = APIRouter(prefix="/api/v1/observability", tags=["observability"])


@router.get("", response_model=ObservabilityOverview)
def read_observability() -> ObservabilityOverview:
    return get_observability_overview()


@router.get("/status", response_model=ObservabilityStatus)
def read_observability_status() -> ObservabilityStatus:
    return get_observability_status()


@router.get("/metrics", response_model=list[ObservabilityMetric])
def read_metrics() -> list[ObservabilityMetric]:
    return list_metrics()


@router.post(
    "/metrics",
    response_model=ObservabilityMetric,
    status_code=status.HTTP_201_CREATED,
)
def write_metric(metric: ObservabilityMetricCreate) -> ObservabilityMetric:
    return create_metric(metric)


@router.get("/logs", response_model=list[ObservabilityLog])
def read_logs(level: str | None = None) -> list[ObservabilityLog]:
    return list_logs(level=level)


@router.post(
    "/logs",
    response_model=ObservabilityLog,
    status_code=status.HTTP_201_CREATED,
)
def write_log(log: ObservabilityLogCreate) -> ObservabilityLog:
    return create_log(log)


@router.get("/traces", response_model=list[ObservabilityTrace])
def read_traces(trace_id: str | None = None) -> list[ObservabilityTrace]:
    return list_traces(trace_id=trace_id)


@router.post(
    "/traces",
    response_model=ObservabilityTrace,
    status_code=status.HTTP_201_CREATED,
)
def write_trace(trace: ObservabilityTraceCreate) -> ObservabilityTrace:
    return create_trace(trace)


@router.get("/health", response_model=list[ObservabilityHealthService])
def read_health() -> list[ObservabilityHealthService]:
    return get_health_aggregation()


@router.get("/errors", response_model=list[ObservabilityLog])
def read_errors() -> list[ObservabilityLog]:
    return list_error_logs()


@router.get("/incidents", response_model=list[ObservabilityIncident])
def read_incidents() -> list[ObservabilityIncident]:
    return list_incidents()


@router.post(
    "/incidents",
    response_model=ObservabilityIncident,
    status_code=status.HTTP_201_CREATED,
)
def write_incident(
    incident: ObservabilityIncidentCreate,
) -> ObservabilityIncident:
    return create_incident(incident)


@router.get("/sla", response_model=list[ObservabilityObjective])
def read_sla() -> list[ObservabilityObjective]:
    return get_sla_registry()


@router.get("/slo", response_model=list[ObservabilityObjective])
def read_slo() -> list[ObservabilityObjective]:
    return get_slo_registry()
