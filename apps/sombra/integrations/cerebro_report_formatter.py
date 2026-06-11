from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from apps.sombra.security.output_sanitizer import OutputSanitizer


class CerebroReportFormatter:
    @staticmethod
    def format_intel_report(alert: Any) -> dict[str, Any]:
        return OutputSanitizer.sanitize_external({
            "source": "THREAT_INTELLIGENCE_ENGINE",
            "timestamp": CerebroReportFormatter.utc_now(),
            "classification": str(getattr(alert, "severity", "")).upper(),
            "threat_type": str(getattr(alert, "threat_type", "")).upper(),
            "threat_score": int(getattr(alert, "threat_score", 0) or 0),
            "findings": str(getattr(alert, "findings", "")),
            "recommended_action": str(getattr(alert, "recommended_action", "")),
            "route_to": list(getattr(alert, "route_to", []) or []),
            "time_window": str(getattr(alert, "time_window", "")),
            "blast_radius": str(getattr(alert, "blast_radius", "")),
            "forja_needed": bool(getattr(alert, "forja_construction_needed", False)),
            "forja_spec": str(getattr(alert, "forja_specification", "")),
            "source_classification": "CLASSIFIED",
        })

    @staticmethod
    def format_heartbeat(
        *,
        status: str,
        intel_processed_today: int,
        alerts_sent_today: int,
        lockdown_level: int,
        current_ai_cost_today_usd: float = 0.0,
        budget_mode: str = "NORMAL",
        ceo_risk_score: int = 0,
    ) -> dict[str, Any]:
        return OutputSanitizer.sanitize_external({
            "type": "INTELLIGENCE_ENGINE_HEARTBEAT",
            "timestamp": CerebroReportFormatter.utc_now(),
            "status": status,
            "intel_processed_today": int(intel_processed_today),
            "alerts_sent_today": int(alerts_sent_today),
            "lockdown_level": int(lockdown_level),
            "current_ai_cost_today_usd": round(float(current_ai_cost_today_usd), 8),
            "budget_mode": str(budget_mode).upper(),
            "ceo_risk_score": int(ceo_risk_score),
        })

    @staticmethod
    def utc_now() -> str:
        return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
