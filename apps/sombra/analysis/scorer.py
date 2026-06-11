from __future__ import annotations

from .models import ClassifiedIntel, ThreatScore


SEVERITY_BASE = {
    "CRITICAL": 90,
    "HIGH": 72,
    "MEDIUM": 48,
    "LOW": 24,
    "INFORMATIONAL": 10,
}


class ThreatScoringEngine:
    def calculate_score(self, intel: ClassifiedIntel) -> ThreatScore:
        base = SEVERITY_BASE.get(intel.severity.upper(), 35)
        time_multiplier = self._time_multiplier(intel.time_window)
        client_impact = self._client_impact(intel)
        pattern_boost = self._pattern_boost(intel)
        raw_score = (base * time_multiplier) + client_impact + pattern_boost
        confidence_adjusted = raw_score * intel.confidence
        final = int(round(min(100.0, confidence_adjusted)))
        return ThreatScore(
            base=base,
            time_multiplier=time_multiplier,
            client_impact=client_impact,
            confidence_adjusted=round(confidence_adjusted, 2),
            pattern_boost=pattern_boost,
            final=final,
        )

    @staticmethod
    def _time_multiplier(time_window: str) -> float:
        normalized = time_window.lower()
        if normalized == "0-24h":
            return 1.25
        if normalized == "24-72h":
            return 1.1
        if normalized == "3-7d":
            return 0.95
        return 0.75

    @staticmethod
    def _client_impact(intel: ClassifiedIntel) -> int:
        impact = 0
        if intel.primary_client != "UNASSIGNED":
            impact += 12
        if intel.legal_risk_flag:
            impact += 8
        impact += min(15, len(intel.affected_clients) * 3)
        impact += min(10, len(intel.affected_assets) * 2)
        return min(35, impact)

    @staticmethod
    def _pattern_boost(intel: ClassifiedIntel) -> int:
        boost = 0
        if intel.threat_type in {"ZERO_DAY_EXPLOIT", "ACTIVE_ATTACK_CAMPAIGN", "RANSOMWARE_CAMPAIGN"}:
            boost += 12
        if "FORJA" in intel.routing:
            boost += 5
        if intel.confidence >= 0.9:
            boost += 4
        return min(25, boost)
