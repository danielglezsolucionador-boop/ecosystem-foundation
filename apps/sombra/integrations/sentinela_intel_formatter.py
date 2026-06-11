from __future__ import annotations

import re
from typing import Any


SOMBRA_FORBIDDEN_WORDS = [
    "sombra",
    "SOMBRA",
    "Sombra",
    "shadow_agent",
    "covert",
    "infiltration",
    "underground_identity",
]

SEVERITY_MAP = {
    "CRITICAL": "Immediate Action Required",
    "HIGH": "Urgent Attention Needed",
    "MEDIUM": "Review Recommended",
    "LOW": "For Awareness",
}


class SentinelaIntelFormatter:
    @staticmethod
    def format_threat_alert(alert: Any) -> dict[str, Any]:
        severity = str(getattr(alert, "severity", "LOW")).upper()
        confidence = float(getattr(alert, "confidence_level", 0.0) or 0.0)
        findings = SentinelaIntelFormatter._business_language(str(getattr(alert, "findings", "")))
        recommended_action = SentinelaIntelFormatter._business_language(str(getattr(alert, "recommended_action", "")))
        payload = {
            "alert_level": SEVERITY_MAP.get(severity, "For Awareness"),
            "what_is_happening": findings,
            "your_systems_at_risk": list(getattr(alert, "target_assets", []) or []),
            "how_long_you_have": str(getattr(alert, "time_window", "")),
            "what_to_do_now": recommended_action,
            "intelligence_source": "Advanced Monitoring",
            "confidence": f"{round(max(0.0, min(1.0, confidence)) * 100)}%",
        }
        return SentinelaIntelFormatter._remove_forbidden_words(payload)

    @staticmethod
    def format_sector_warning(sector: str, threat_type: str) -> dict[str, Any]:
        payload = {
            "warning_type": "SECTOR_THREAT",
            "your_sector": sector,
            "emerging_threat": threat_type,
            "risk_to_you": "ELEVATED",
            "recommended_posture": "Increase monitoring and review access controls",
            "source": "Threat Intelligence Feed",
        }
        return SentinelaIntelFormatter._remove_forbidden_words(payload)

    @staticmethod
    def _business_language(text: str) -> str:
        replacements = {
            "classified": "identified",
            "threat_score": "risk level",
            "indicator": "signal",
            "indicators": "signals",
            "exploit": "attack method",
            "payload": "evidence package",
            "vector": "attack path",
            "privileged access": "administrator access",
            "lateral movement": "spread inside systems",
        }
        cleaned = text
        for technical, plain in replacements.items():
            cleaned = re.sub(re.escape(technical), plain, cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\b[A-Z_]{4,}\b", lambda match: match.group(0).replace("_", " ").title(), cleaned)
        return cleaned.strip()

    @staticmethod
    def _remove_forbidden_words(value: Any) -> Any:
        if isinstance(value, dict):
            return {key: SentinelaIntelFormatter._remove_forbidden_words(item) for key, item in value.items()}
        if isinstance(value, list):
            return [SentinelaIntelFormatter._remove_forbidden_words(item) for item in value]
        if isinstance(value, str):
            cleaned = value
            for word in SOMBRA_FORBIDDEN_WORDS:
                cleaned = cleaned.replace(word, "classified monitoring")
            return cleaned
        return value
