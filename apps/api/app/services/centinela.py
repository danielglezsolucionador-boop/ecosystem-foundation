from datetime import UTC, datetime

from app.schemas.centinela import CentinelaStatus


def utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def get_centinela_status() -> CentinelaStatus:
    return CentinelaStatus(
        status="prepared",
        risk_level="internal_watch",
        readiness="ready_for_internal_ceo_queries",
        message=(
            "CENTINELA responde estado y riesgo interno desde Control Center. "
            "Puente externo no conectado; SOMBRA no fue consultado."
        ),
        sombra_connected=False,
        source="internal_control_center",
        generated_at=utc_now(),
    )
