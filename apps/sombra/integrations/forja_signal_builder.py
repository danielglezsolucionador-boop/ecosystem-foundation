from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
import uuid

from apps.sombra.security.output_sanitizer import OutputSanitizer


THREAT_CONSTRUCTION_MAP = {
    "ZERO_DAY_EXPLOIT": {
        "construction": "Compensating control rule",
        "priority": "URGENT",
        "description": "Build detection rule for exploit pattern: {findings}",
    },
    "RANSOMWARE_CAMPAIGN": {
        "construction": "Backup isolation protocol",
        "priority": "URGENT",
        "description": "Build automated backup isolation trigger for ransomware indicators",
    },
    "ACTIVE_ATTACK_CAMPAIGN": {
        "construction": "Attack pattern firewall rule",
        "priority": "URGENT",
        "description": "Build blocking rule for attack campaign indicators",
    },
    "CREDENTIAL_EXPOSURE": {
        "construction": "Forced authentication reset",
        "priority": "HIGH",
        "description": "Build automated password reset trigger for affected accounts",
    },
    "BRAND_IMPERSONATION": {
        "construction": "Domain monitoring alert",
        "priority": "HIGH",
        "description": "Build lookalike domain detection and alert system",
    },
    "EMERGING_EXPLOIT": {
        "construction": "Vulnerability detection rule",
        "priority": "STANDARD",
        "description": "Build detection for emerging exploit pattern",
    },
}


class ForjaSignalBuilder:
    def build_construction_signal(self, alert: Any, threat_type: str) -> dict[str, Any]:
        normalized_threat = str(threat_type).upper()
        mapping = THREAT_CONSTRUCTION_MAP.get(
            normalized_threat,
            {
                "construction": "Defensive review package",
                "priority": "STANDARD",
                "description": "Prepare defensive review package for observed threat pattern",
            },
        )
        findings = str(getattr(alert, "findings", ""))[:200]
        description = str(mapping["description"]).format(findings=findings)
        signal = {
            "signal_id": str(uuid.uuid4()),
            "timestamp": self._utc_now(),
            "origin": "THREAT_INTELLIGENCE_ENGINE",
            "pattern_detected": normalized_threat,
            "construction_needed": mapping["construction"],
            "priority": mapping["priority"],
            "description": description,
            "technical_context": str(getattr(alert, "findings", ""))[:500],
            "deadline_estimate": self._deadline_for_alert(alert),
            "indicators": list(getattr(alert, "target_assets", []) or []),
        }
        return OutputSanitizer.sanitize_external(signal)

    @staticmethod
    def supported_threat_types() -> list[str]:
        return list(THREAT_CONSTRUCTION_MAP)

    @staticmethod
    def _deadline_for_alert(alert: Any) -> str:
        severity = str(getattr(alert, "severity", "LOW")).upper()
        if severity == "CRITICAL":
            return "NOW"
        if severity == "HIGH":
            return "24 hours"
        if severity == "MEDIUM":
            return "72 hours"
        return "next planning cycle"

    @staticmethod
    def _utc_now() -> str:
        return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
