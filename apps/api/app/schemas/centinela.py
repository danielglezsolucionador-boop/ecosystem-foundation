from pydantic import BaseModel, Field


class CentinelaStatus(BaseModel):
    status: str = Field(default="prepared", min_length=1)
    risk_level: str = Field(default="internal_watch", min_length=1)
    readiness: str = Field(default="ready_for_internal_ceo_queries", min_length=1)
    message: str = Field(
        default="CENTINELA preparado en modo interno. Puente externo no conectado.",
        min_length=1,
    )
    sombra_connected: bool = False
    source: str = Field(default="internal_control_center", min_length=1)
    generated_at: str = Field(min_length=1)
