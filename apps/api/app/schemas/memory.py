from pydantic import BaseModel, Field


class MemoryEntryCreate(BaseModel):
    title: str = Field(min_length=1)
    content: str = Field(min_length=1)
    source: str = Field(default="local", min_length=1)
    tags: list[str] = Field(default_factory=list)


class MemoryEntry(BaseModel):
    id: str
    title: str
    content: str
    source: str
    tags: list[str]
    created_at: str


class MemoryStatus(BaseModel):
    status: str
    backend: str
    entries: int
    external_sources_connected: bool

