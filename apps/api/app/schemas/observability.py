from typing import Any

from pydantic import BaseModel, Field


class ObservabilityMetricCreate(BaseModel):
    id: str = Field(min_length=1)
    value: int | float | str | bool
    status: str = Field(default="ok", min_length=1)
    source: str = Field(min_length=1)
    unit: str | None = None
    request_id: str | None = Field(default=None, min_length=1)
    trace_id: str | None = Field(default=None, min_length=1)


class ObservabilityMetric(BaseModel):
    id: str
    value: int | float | str | bool
    status: str
    source: str
    unit: str | None = None
    request_id: str | None = None
    trace_id: str | None = None
    created_at: str | None = None


class ObservabilityLogCreate(BaseModel):
    level: str = Field(min_length=1)
    message: str = Field(min_length=1)
    source: str = Field(min_length=1)
    request_id: str | None = Field(default=None, min_length=1)
    trace_id: str | None = Field(default=None, min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ObservabilityLog(BaseModel):
    id: str
    level: str
    message: str
    source: str
    request_id: str | None
    trace_id: str | None
    metadata: dict[str, Any]
    created_at: str


class ObservabilityTraceCreate(BaseModel):
    trace_id: str | None = Field(default=None, min_length=1)
    span_id: str = Field(min_length=1)
    parent_span_id: str | None = Field(default=None, min_length=1)
    operation: str = Field(min_length=1)
    status: str = Field(default="ok", min_length=1)
    duration_ms: int = Field(ge=0)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ObservabilityTrace(BaseModel):
    id: str
    trace_id: str
    span_id: str
    parent_span_id: str | None
    operation: str
    status: str
    duration_ms: int
    metadata: dict[str, Any]
    created_at: str


class ObservabilityIncidentCreate(BaseModel):
    title: str = Field(min_length=1)
    severity: str = Field(min_length=1)
    status: str = Field(default="open", min_length=1)
    description: str = Field(min_length=1)
    source: str = Field(min_length=1)
    trace_id: str | None = Field(default=None, min_length=1)


class ObservabilityIncident(BaseModel):
    id: str
    title: str
    severity: str
    status: str
    description: str
    source: str
    trace_id: str | None
    created_at: str


class ObservabilityHealthService(BaseModel):
    id: str
    status: str
    detail: str


class ObservabilityObjective(BaseModel):
    id: str
    label: str
    target: str
    status: str


class ObservabilityStatus(BaseModel):
    status: str
    service: str
    environment: str
    metrics: list[ObservabilityMetric]
    logs: int = 0
    traces: int = 0
    incidents: int = 0
    external_monitor_connected: bool = False


class ObservabilityOverview(BaseModel):
    status: str
    service: str
    environment: str
    health: list[ObservabilityHealthService]
    metrics: list[ObservabilityMetric]
    logs: int
    traces: int
    incidents: int
    sla: list[ObservabilityObjective]
    slo: list[ObservabilityObjective]
    external_monitor_connected: bool
