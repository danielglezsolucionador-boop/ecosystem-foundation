from pydantic import BaseModel, Field


class ControlCenterMetric(BaseModel):
    id: str = Field(min_length=1)
    label: str = Field(min_length=1)
    value: int | str
    status: str = Field(min_length=1)


class ControlCenterAction(BaseModel):
    id: str = Field(min_length=1)
    label: str = Field(min_length=1)
    priority: str = Field(min_length=1)
    blocked: bool


class ControlCenterOverview(BaseModel):
    status: str
    registry_source: str
    external_connections_enabled: bool
    metrics: list[ControlCenterMetric]
    next_actions: list[ControlCenterAction]
    risks: list[str]

