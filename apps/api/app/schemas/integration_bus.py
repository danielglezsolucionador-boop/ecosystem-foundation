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
    source_service: str
    target_service: str
    event_type: str
    channel: str
    status: str
    retry_policy: str
    dead_letter_enabled: bool
    external_connection_enabled: bool
    created_at: str


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
    route_to_dead_letter: bool = False


class IntegrationDispatchResult(BaseModel):
    id: str
    route_id: str
    status: str
    event_id: str | None
    dead_letter_routed: bool
    audit_event_id: str | None
    created_at: str


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
    services: int
    dependencies: int
    audit_events: int
    external_connections_enabled: bool


class IntegrationBusOverview(BaseModel):
    status: str
    routes: list[IntegrationBusRoute]
    services: list[IntegrationBusService]
    dependencies: list[IntegrationBusDependency]
    external_connections_enabled: bool
