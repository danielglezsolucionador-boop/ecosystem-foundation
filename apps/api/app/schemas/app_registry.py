from enum import StrEnum

from pydantic import BaseModel, Field


class AppStatus(StrEnum):
    planned = "planned"
    internal = "internal"
    external = "external"
    blocked = "blocked"
    unknown = "unknown"


class EcosystemApp(BaseModel):
    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    type: str = Field(min_length=1)
    status: AppStatus
    depends_on: list[str] = Field(default_factory=list)
    description: str = Field(min_length=1)
    touch_policy: str = Field(min_length=1)


class AppRegistrySummary(BaseModel):
    total: int
    by_status: dict[str, int]
    app_ids: list[str]
    source: str
    external_connections_enabled: bool
