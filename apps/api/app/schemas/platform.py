from pydantic import BaseModel


class PlatformPhaseStatus(BaseModel):
    id: str
    name: str
    status: str
    evidence: str


class PlatformStatus(BaseModel):
    status: str
    phases: list[PlatformPhaseStatus]
    local_ready: bool
    external_apps_connected: bool

