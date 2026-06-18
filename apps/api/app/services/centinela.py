from datetime import UTC, datetime
from uuid import uuid4

from app.schemas.centinela import CentinelaReportAnalysis, CentinelaStatus
from app.schemas.cerebro import SombraInboxMessageCreate


def utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _clean_text(value: object, max_length: int = 800) -> str:
    text = " ".join(str(value or "").replace("\n", " ").split())
    sensitive_tokens = (
        "token",
        "secret",
        "password",
        "passwd",
        "credential",
        "credencial",
        "api_key",
        "apikey",
        "authorization",
        "bearer",
    )
    for token in sensitive_tokens:
        text = text.replace(token, "[redacted]")
        text = text.replace(token.upper(), "[redacted]")
    return (text or "Reporte operativo defensivo recibido por CENTINELA.")[:max_length]


def _blob(message: SombraInboxMessageCreate) -> str:
    payload_hint = ""
    if isinstance(message.payload, dict):
        payload_hint = " ".join(str(key) for key in message.payload.keys())
    elif isinstance(message.payload, str):
        payload_hint = message.payload[:400]
    return " ".join([message.title, message.summary, payload_hint]).lower()


def _impact_for_severity(severity: str) -> str:
    return {
        "critical": "critico",
        "high": "riesgo alto",
        "medium": "riesgo medio",
        "low": "riesgo bajo",
        "info": "riesgo bajo",
    }.get(str(severity), "riesgo medio")


def analyze_operational_report(message: SombraInboxMessageCreate) -> CentinelaReportAnalysis:
    blob = _blob(message)
    metadata = message.metadata or {}
    requires_api = bool(metadata.get("requires_api")) or "api" in blob
    requires_skill = bool(metadata.get("requires_skill")) or "skill" in blob
    requires_tool = bool(metadata.get("requires_tool")) or "herramienta" in blob or "tool" in blob
    requires_update = (
        bool(metadata.get("requires_update"))
        or any(token in blob for token in ("patch", "parche", "update", "actualizacion", "vulnerab", "hardening"))
    )
    requires_defensive_rule = (
        message.severity.value in {"high", "critical"}
        or bool(metadata.get("requires_defensive_rule"))
        or any(token in blob for token in ("credential", "credencial", "ransomware", "cve", "regla", "rule"))
    )
    requires_forja_task = any(
        [
            requires_update,
            requires_api,
            requires_skill,
            requires_tool,
            requires_defensive_rule,
            bool(metadata.get("requires_forja_task")),
        ]
    )
    may_affect_clients = bool(
        message.client_context.company
        or message.client_context.domain
        or metadata.get("may_affect_clients")
        or message.severity.value in {"high", "critical"}
    )
    affects_ecosystem = bool(
        metadata.get("affects_ecosystem", True)
        or message.severity.value in {"medium", "high", "critical"}
    )
    recommendation = (
        "Crear tarea FORJA y registrar capacidad defensiva reutilizable."
        if requires_forja_task
        else "Mantener seguimiento CENTINELA sin construccion tecnica."
    )
    return CentinelaReportAnalysis(
        id=f"centinela-analysis-{uuid4()}",
        report_id=message.message_id,
        impact=_impact_for_severity(message.severity.value),
        affects_ecosystem=affects_ecosystem,
        may_affect_clients=may_affect_clients,
        requires_update=requires_update,
        requires_defensive_rule=requires_defensive_rule,
        requires_api=requires_api,
        requires_skill=requires_skill,
        requires_tool=requires_tool,
        requires_forja_task=requires_forja_task,
        safe_summary=_clean_text(message.summary),
        recommendation=recommendation,
        generated_at=utc_now(),
    )


def build_centinela_status(metrics: dict[str, object]) -> CentinelaStatus:
    external_messages = int(metrics.get("external_intel_messages", 0) or 0)
    threat_level = str(metrics.get("threat_level") or "unknown")
    sombra_connected = bool(metrics.get("sombra_connected", False))
    status = "operational_internal" if sombra_connected and external_messages else "prepared"
    ceo_codes = list(metrics.get("ceo_codes_pending", []) or [])
    return CentinelaStatus(
        status=status,
        risk_level=threat_level if threat_level != "unknown" else "internal_watch",
        readiness="ready_for_internal_ceo_queries",
        message=(
            "CENTINELA lee inteligencia externa recibida por CEREBRO en modo interno. "
            "No consulta servidor SOMBRA real ni expone payload sensible."
        ),
        sombra_connected=sombra_connected,
        external_intel_messages=external_messages,
        critical_alerts=int(metrics.get("critical_alerts", 0) or 0),
        high_alerts=int(metrics.get("high_alerts", 0) or 0),
        lead_signals=int(metrics.get("lead_signals", 0) or 0),
        threat_level=threat_level,
        last_intel_at=metrics.get("last_intel_at"),
        last_heartbeat_at=metrics.get("last_heartbeat_at"),
        ceo_codes_pending=[str(code) for code in ceo_codes],
        source="internal_control_center",
        generated_at=utc_now(),
    )


def get_centinela_status() -> CentinelaStatus:
    try:
        from app.services.cerebro import get_sombra_inbox_metrics

        metrics = get_sombra_inbox_metrics()
    except Exception:
        metrics = {
            "external_intel_messages": 0,
            "critical_alerts": 0,
            "high_alerts": 0,
            "lead_signals": 0,
            "threat_level": "unknown",
            "last_intel_at": None,
            "last_heartbeat_at": None,
            "ceo_codes_pending": [],
            "sombra_connected": False,
        }
    return build_centinela_status(metrics)
