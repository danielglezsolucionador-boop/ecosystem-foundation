from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class MemoryType(StrEnum):
    global_memory = "global"
    application = "application"
    service = "service"
    context = "context"
    execution = "execution"
    decision = "decision"
    knowledge = "knowledge"


class MemoryRecordStatus(StrEnum):
    active = "active"
    draft = "draft"
    archived = "archived"
    superseded = "superseded"


class MemoryEntryCreate(BaseModel):
    title: str = Field(min_length=1)
    content: str = Field(min_length=1)
    type: MemoryType = MemoryType.global_memory
    status: MemoryRecordStatus = MemoryRecordStatus.active
    source: str = Field(default="local", min_length=1)
    app_id: str | None = Field(default=None, min_length=1)
    service_id: str | None = Field(default=None, min_length=1)
    tags: list[str] = Field(default_factory=list)
    retention_policy: str = Field(default="standard", min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)


class MemoryEntryUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1)
    content: str | None = Field(default=None, min_length=1)
    type: MemoryType | None = None
    status: MemoryRecordStatus | None = None
    source: str | None = Field(default=None, min_length=1)
    app_id: str | None = Field(default=None, min_length=1)
    service_id: str | None = Field(default=None, min_length=1)
    tags: list[str] | None = None
    retention_policy: str | None = Field(default=None, min_length=1)
    metadata: dict[str, Any] | None = None
    change_reason: str = Field(default="memory_update", min_length=1)


class MemoryEntry(BaseModel):
    id: str
    title: str
    content: str
    type: MemoryType
    status: MemoryRecordStatus
    source: str
    app_id: str | None
    service_id: str | None
    tags: list[str]
    retention_policy: str
    metadata: dict[str, Any]
    version: int
    external_source_connected: bool
    created_at: str
    updated_at: str


class MemoryVersion(BaseModel):
    id: str
    memory_id: str
    version: int
    action: str
    payload: MemoryEntry
    created_at: str


class MemoryAuditEvent(BaseModel):
    id: str
    memory_id: str
    action: str
    version: int
    status: str
    created_at: str


class MemoryStatus(BaseModel):
    status: str
    backend: str
    entries: int
    versions: int
    audit_events: int
    supported_types: list[MemoryType]
    external_sources_connected: bool
