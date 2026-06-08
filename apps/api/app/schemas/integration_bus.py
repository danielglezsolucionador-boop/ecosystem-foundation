from typing import Any

from pydantic import BaseModel, Field


class IntegrationBusService(BaseModel):
    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    category: str = Field(min_length=1)
    status: str = Field(min_length=1)
    external_connection_enabled: bool


class IntegrationBusRouteCreate(BaseModel):
    source_service: str = Field(min_length=1)
    target_service: str = Field(min_length=1)
    event_type: str = Field(min_length=1)
    channel: str = Field(default="internal", min_length=1)
    retry_policy: str = Field(default="standard", min_length=1)
    dead_letter_enabled: bool = True


class IntegrationBusRoute(BaseModel):
    id: str
    route_id: str | None = None
    source: str | None = None
    target: str | None = None
    action_type: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)
    source_service: str
    target_service: str
    event_type: str
    channel: str
    status: str
    allowed: bool = True
    requires_ceo_approval: bool = False
    retry_policy: str
    dead_letter_enabled: bool
    external_connection_enabled: bool
    runtime_connected: bool = False
    audit_event_id: str | None = None
    handler_result: dict[str, Any] = Field(default_factory=dict)
    blocked_reason: str | None = None
    created_at: str
    updated_at: str | None = None


class IntegrationBusPreparedRoute(BaseModel):
    id: str = Field(min_length=1)
    source: str = Field(min_length=1)
    target: str = Field(min_length=1)
    purpose: list[str] = Field(default_factory=list)
    status: str = Field(min_length=1)
    blocked_reason: str = Field(min_length=1)
    requires_ceo_approval: bool = True
    external_connection_enabled: bool = False
    runtime_connected: bool = False


class IntegrationBusDependency(BaseModel):
    id: str
    name: str
    dependency_type: str
    status: str
    required: bool
    external_dependency: bool


class IntegrationDispatchRequest(BaseModel):
    route_id: str = Field(min_length=1)
    subject: str = Field(min_length=1)
    payload: dict[str, Any]
    metadata: dict[str, Any] = Field(default_factory=dict)
    action_type: str | None = Field(default=None, min_length=1)
    route_to_dead_letter: bool = False


class IntegrationDispatchResult(BaseModel):
    id: str
    route_id: str
    status: str
    event_id: str | None
    target_service: str | None = None
    action_type: str | None = None
    allowed: bool = True
    blocked: bool = False
    blocked_reason: str | None = None
    handler_result: dict[str, Any] = Field(default_factory=dict)
    dead_letter_routed: bool
    audit_event_id: str | None
    external_connection_enabled: bool = False
    runtime_connected: bool = False
    created_at: str


class IntegrationBusRouteStateUpdate(BaseModel):
    status: str = Field(min_length=1)
    reason: str = Field(min_length=1)


class IntegrationBusAuditEvent(BaseModel):
    id: str
    action: str
    status: str
    detail: str
    route_id: str | None
    event_id: str | None
    created_at: str


class IntegrationBusStatus(BaseModel):
    status: str
    routes: int
    prepared_routes: int = 0
    services: int
    dependencies: int
    audit_events: int
    external_connections_enabled: bool


class IntegrationBusOverview(BaseModel):
    status: str
    routes: list[IntegrationBusRoute]
    prepared_routes: list[IntegrationBusPreparedRoute] = Field(default_factory=list)
    services: list[IntegrationBusService]
    dependencies: list[IntegrationBusDependency]
    external_connections_enabled: bool
