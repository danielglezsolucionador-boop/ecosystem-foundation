from pydantic import BaseModel


class ObservabilityMetric(BaseModel):
    id: str
    value: int | str | bool
    status: str


class ObservabilityStatus(BaseModel):
    status: str
    service: str
    environment: str
    metrics: list[ObservabilityMetric]

