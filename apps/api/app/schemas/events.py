from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class EventStatus(StrEnum):
    created = "created"
    published = "published"
    consumed = "consumed"
    failed = "failed"
    replayed = "replayed"
    dead_letter = "dead_letter"


class EventCatalogItem(BaseModel):
    id: str = Field(min_length=1)
    description: str = Field(min_length=1)
    required_payload_fields: list[str] = Field(default_factory=list)
    status: str = Field(min_length=1)


class EventConsumer(BaseModel):
    id: str = Field(min_length=1)
    event_type: str = Field(min_length=1)
    service: str = Field(min_length=1)
    status: str = Field(min_length=1)
    external_connection_enabled: bool


class EventCreate(BaseModel):
    type: str = Field(min_length=1)
    source: str = Field(min_length=1)
    subject: str = Field(min_length=1)
    payload: dict[str, Any]
    metadata: dict[str, Any] = Field(default_factory=dict)
    route_to_dead_letter: bool = False


class EventReplayRequest(BaseModel):
    reason: str = Field(default="manual_replay", min_length=1)


class EventRecord(BaseModel):
    id: str
    type: str
    source: str
    subject: str
    status: EventStatus
    payload: dict[str, Any]
    metadata: dict[str, Any]
    replay_count: int
    external_queue_connected: bool
    created_at: str
    updated_at: str


class EventAuditEvent(BaseModel):
    id: str
    event_id: str
    action: str
    status: EventStatus
    detail: str
    created_at: str


class EventReplayResult(BaseModel):
    original_event_id: str
    replayed_event: EventRecord
    audit_event_id: str | None


class EventStatusSummary(BaseModel):
    status: str
    events: int
    dead_letter_events: int
    catalog_items: int
    consumers: int
    external_queue_connected: bool
