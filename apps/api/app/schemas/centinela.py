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
    external_intel_messages: int = 0
    critical_alerts: int = 0
    high_alerts: int = 0
    lead_signals: int = 0
    threat_level: str = Field(default="unknown", pattern="^(unknown|low|medium|high|critical)$")
    last_intel_at: str | None = None
    last_heartbeat_at: str | None = None
    ceo_codes_pending: list[str] = Field(default_factory=list)
    source: str = Field(default="internal_control_center", min_length=1)
    generated_at: str = Field(min_length=1)
