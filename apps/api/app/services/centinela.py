from datetime import UTC, datetime

from app.schemas.centinela import CentinelaStatus


def utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


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
