from fastapi import APIRouter, HTTPException, status

from app.schemas.memory import (
    MemoryAuditEvent,
    MemoryEntry,
    MemoryEntryCreate,
    MemoryEntryUpdate,
    MemoryRecordStatus,
    MemoryStatus,
    MemoryType,
    MemoryVersion,
)
from app.services.memory import (
    create_memory_entry,
    get_memory_entry,
    get_memory_status,
    list_memory_audit_events,
    list_memory_by_app,
    list_memory_entries,
    list_memory_versions,
    update_memory_entry,
)

router = APIRouter(prefix="/api/v1/memory", tags=["memory"])


@router.get("/status", response_model=MemoryStatus)
def read_memory_status() -> MemoryStatus:
    return get_memory_status()


@router.get("", response_model=list[MemoryEntry])
def read_memory(
    app_id: str | None = None,
    type: MemoryType | None = None,
    status: MemoryRecordStatus | None = None,
) -> list[MemoryEntry]:
    return list_memory_entries(app_id=app_id, type=type, status=status)


@router.post("", response_model=MemoryEntry, status_code=status.HTTP_201_CREATED)
def write_memory(entry: MemoryEntryCreate) -> MemoryEntry:
    return create_memory_entry(entry)


@router.get("/entries", response_model=list[MemoryEntry])
def read_memory_entries() -> list[MemoryEntry]:
    return list_memory_entries()


@router.post("/entries", response_model=MemoryEntry, status_code=status.HTTP_201_CREATED)
def write_memory_entry(entry: MemoryEntryCreate) -> MemoryEntry:
    return create_memory_entry(entry)


@router.get("/apps/{app_id}", response_model=list[MemoryEntry])
def read_memory_for_app(app_id: str) -> list[MemoryEntry]:
    return list_memory_by_app(app_id)


@router.get("/audit", response_model=list[MemoryAuditEvent])
def read_memory_audit() -> list[MemoryAuditEvent]:
    return list_memory_audit_events()


@router.get("/{memory_id}", response_model=MemoryEntry)
def read_memory_entry(memory_id: str) -> MemoryEntry:
    entry = get_memory_entry(memory_id)

    if entry is None:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "memory_not_found",
                "memory_id": memory_id,
            },
        )

    return entry


@router.put("/{memory_id}", response_model=MemoryEntry)
def replace_memory_entry(
    memory_id: str,
    update: MemoryEntryUpdate,
) -> MemoryEntry:
    entry = update_memory_entry(memory_id, update)

    if entry is None:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "memory_not_found",
                "memory_id": memory_id,
            },
        )

    return entry


@router.get("/{memory_id}/versions", response_model=list[MemoryVersion])
def read_memory_versions(memory_id: str) -> list[MemoryVersion]:
    if get_memory_entry(memory_id) is None:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "memory_not_found",
                "memory_id": memory_id,
            },
        )

    return list_memory_versions(memory_id)
