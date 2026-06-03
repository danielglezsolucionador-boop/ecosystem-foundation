from fastapi import APIRouter, status

from app.schemas.memory import MemoryEntry, MemoryEntryCreate, MemoryStatus
from app.services.memory import (
    create_memory_entry,
    get_memory_status,
    list_memory_entries,
)

router = APIRouter(prefix="/api/v1/memory", tags=["memory"])


@router.get("/status", response_model=MemoryStatus)
def read_memory_status() -> MemoryStatus:
    return get_memory_status()


@router.get("/entries", response_model=list[MemoryEntry])
def read_memory_entries() -> list[MemoryEntry]:
    return list_memory_entries()


@router.post("/entries", response_model=MemoryEntry, status_code=status.HTTP_201_CREATED)
def write_memory_entry(entry: MemoryEntryCreate) -> MemoryEntry:
    return create_memory_entry(entry)

