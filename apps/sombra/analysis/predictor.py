from __future__ import annotations

from .models import ClassifiedIntel, ThreatPrediction, ThreatScore


PREDICTION_RULES = {
    "CREDENTIAL_EXPOSURE": (
        "credential replay or account takeover",
        "0-48h",
        "force credential rotation, revoke sessions, inspect anomalous logins",
    ),
    "ACTIVE_ATTACK_CAMPAIGN": (
        "active intrusion or scanning escalation",
        "0-24h",
        "raise detection thresholds, block indicators, verify exposed services",
    ),
    "ZERO_DAY_EXPLOIT": (
        "rapid exploitation against exposed vulnerable assets",
        "0-24h",
        "identify exposure, apply vendor mitigation, deploy virtual patching",
    ),
    "RANSOMWARE_CAMPAIGN": (
        "lateral movement followed by extortion attempt",
        "0-72h",
        "verify backups, isolate high-value assets, hunt for known tooling",
    ),
    "BRAND_IMPERSONATION": (
        "phishing and customer credential theft",
        "24-72h",
        "monitor domains, request takedown, alert affected audience",
    ),
    "EXECUTIVE_EXPOSURE": (
        "targeted phishing or social engineering",
        "24-72h",
        "protect executive accounts, harden MFA, monitor impersonation",
    ),
    "EMERGING_EXPLOIT": (
        "weaponization of public exploit technique",
        "24-72h",
        "track exploit maturity and prepare defensive rule updates",
    ),
    "SECTOR_THREAT_TREND": (
        "sector-specific targeting increase",
        "3-14d",
        "review sector exposure and prioritize monitoring",
    ),
    "VULNERABILITY_PUBLISHED": (
        "patch window pressure and opportunistic scanning",
        "3-7d",
        "map affected assets and schedule patch or mitigation",
    ),
    "INTELLIGENCE_TREND": (
        "watchlist signal requiring correlation",
        "monitor",
        "continue collection and correlate with client assets",
    ),
}


class ThreatPredictionEngine:
    def predict(self, intel: ClassifiedIntel, score: ThreatScore) -> ThreatPrediction:
        vector, estimate, defense = PREDICTION_RULES.get(
            intel.threat_type,
            PREDICTION_RULES["INTELLIGENCE_TREND"],
        )
        targets = intel.affected_assets or intel.affected_clients or ["UNASSIGNED"]
        confidence = self._prediction_confidence(intel, score)
        basis = (
            f"threat_type={intel.threat_type}; severity={intel.severity}; "
            f"score={score.final}; source_confidence={intel.confidence:.2f}"
        )
        return ThreatPrediction(
            predicted_vector=vector,
            time_estimate=estimate,
            high_risk_targets=targets[:20],
            recommended_defense=defense,
            confidence=confidence,
            data_basis=basis,
        )

    @staticmethod
    def _prediction_confidence(intel: ClassifiedIntel, score: ThreatScore) -> float:
        confidence = intel.confidence
        if score.final >= 85:
            confidence += 0.05
        if intel.affected_assets:
            confidence += 0.04
        if intel.primary_client == "UNASSIGNED":
            confidence -= 0.08
        return max(0.05, min(0.99, round(confidence, 3)))
