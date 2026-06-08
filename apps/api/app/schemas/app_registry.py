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
    role: str | None = None
    commercial_role: str | None = None
    controlled_state: str | None = None
    external_connection_enabled: bool = False
    runtime_connected: bool = False
    sunat_enabled: bool = False
    requires_ceo_approval: bool = True
    governance_execution_blocked: bool = True
    secrets_required: bool = False
    human_cabin_complete: bool = True


class AppRegistrySummary(BaseModel):
    total: int
    by_status: dict[str, int]
    app_ids: list[str]
    source: str
    external_connections_enabled: bool
