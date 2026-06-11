from __future__ import annotations

import re
from typing import Any

from .models import ClassifiedIntel


THREAT_TYPES: dict[str, dict[str, Any]] = {
    "CREDENTIAL_EXPOSURE": {
        "default_severity": "HIGH",
        "auto_route": ["CEREBRO", "SENTINELA"],
        "time_sensitive": True,
    },
    "ACTIVE_ATTACK_CAMPAIGN": {
        "default_severity": "CRITICAL",
        "auto_route": ["CEREBRO", "SENTINELA", "FORJA"],
        "time_sensitive": True,
    },
    "ZERO_DAY_EXPLOIT": {
        "default_severity": "CRITICAL",
        "auto_route": ["CEREBRO", "SENTINELA", "FORJA"],
        "time_sensitive": True,
    },
    "RANSOMWARE_CAMPAIGN": {
        "default_severity": "CRITICAL",
        "auto_route": ["CEREBRO", "SENTINELA"],
        "time_sensitive": True,
    },
    "BRAND_IMPERSONATION": {
        "default_severity": "HIGH",
        "auto_route": ["CEREBRO", "SENTINELA"],
        "time_sensitive": True,
    },
    "EXECUTIVE_EXPOSURE": {
        "default_severity": "HIGH",
        "auto_route": ["CEREBRO", "SENTINELA"],
        "time_sensitive": True,
    },
    "EMERGING_EXPLOIT": {
        "default_severity": "HIGH",
        "auto_route": ["CEREBRO", "SENTINELA", "FORJA"],
        "time_sensitive": True,
    },
    "SECTOR_THREAT_TREND": {
        "default_severity": "MEDIUM",
        "auto_route": ["CEREBRO", "SENTINELA"],
        "time_sensitive": False,
    },
    "VULNERABILITY_PUBLISHED": {
        "default_severity": "HIGH",
        "auto_route": ["CEREBRO", "SENTINELA"],
        "time_sensitive": False,
    },
    "INTELLIGENCE_TREND": {
        "default_severity": "MEDIUM",
        "auto_route": ["CEREBRO"],
        "time_sensitive": False,
    },
}


KEYWORD_RULES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("ZERO_DAY_EXPLOIT", ("zero-day", "0-day", "actively exploited", "in the wild")),
    ("RANSOMWARE_CAMPAIGN", ("ransomware", "double extortion", "encryptor", "lockbit", "black basta")),
    ("CREDENTIAL_EXPOSURE", ("credential", "password", "token leak", "api key", "stealer log")),
    ("ACTIVE_ATTACK_CAMPAIGN", ("campaign", "mass exploitation", "botnet", "phishing kit", "malware campaign")),
    ("BRAND_IMPERSONATION", ("impersonation", "fake login", "lookalike domain", "typosquat", "brand abuse")),
    ("EXECUTIVE_EXPOSURE", ("executive", "ceo", "founder", "board", "personal email")),
    ("EMERGING_EXPLOIT", ("exploit", "poc", "proof-of-concept", "weaponized")),
    ("SECTOR_THREAT_TREND", ("sector", "industry", "financial services", "healthcare", "retail")),
    ("VULNERABILITY_PUBLISHED", ("cve-", "cvss", "vulnerability", "nvd")),
    ("INTELLIGENCE_TREND", ("trend", "observed", "researchers", "threat actor")),
)


class ThreatClassificationEngine:
    def __init__(self, threat_types: dict[str, dict[str, Any]] | None = None) -> None:
        self.threat_types = threat_types if threat_types is not None else THREAT_TYPES

    def classify(self, package: Any) -> ClassifiedIntel:
        self._validate_package(package)
        raw_content = str(package.raw_content)
        normalized_content = raw_content.lower()
        threat_type = self._resolve_threat_type(package, normalized_content)
        config = self.threat_types[threat_type]
        severity = self._resolve_severity(package, config)
        routing = list(config["auto_route"])
        if bool(getattr(package, "requires_ceo_review", False)) and "CEREBRO" not in routing:
            routing.insert(0, "CEREBRO")
        indicators = [str(item) for item in getattr(package, "target_indicators", []) if str(item).strip()]
        evidence = self._build_evidence(package, raw_content)
        return ClassifiedIntel(
            intel_id=str(package.intel_id),
            timestamp_utc=str(package.timestamp_utc),
            threat_type=threat_type,
            severity=severity,
            confidence=self._confidence_from_reliability(float(package.source_reliability), threat_type, normalized_content),
            affected_clients=self._extract_clients(raw_content, indicators),
            legal_risk_flag=bool(getattr(package, "requires_ceo_review", False)),
            routing=routing,
            findings=self._build_findings(threat_type, severity, indicators),
            evidence=evidence,
            time_window=self._time_window(threat_type, severity, bool(config["time_sensitive"])),
            order_origin="COLLECTOR",
            source_mission=str(getattr(package, "collector_agent", "unknown")),
            primary_client=self._extract_primary_client(raw_content, indicators),
            affected_assets=indicators,
        )

    def _resolve_threat_type(self, package: Any, normalized_content: str) -> str:
        suspected = str(getattr(package, "suspected_threat_type", "")).upper()
        if suspected in self.threat_types:
            return suspected
        for threat_type, keywords in KEYWORD_RULES:
            if any(keyword in normalized_content for keyword in keywords):
                return threat_type
        return "INTELLIGENCE_TREND"

    def _resolve_severity(self, package: Any, config: dict[str, Any]) -> str:
        severity = str(getattr(package, "suspected_severity", "")).upper()
        if severity in {"CRITICAL", "HIGH", "MEDIUM", "LOW", "INFORMATIONAL"}:
            return severity
        return str(config["default_severity"]).upper()

    @staticmethod
    def _confidence_from_reliability(reliability: float, threat_type: str, content: str) -> float:
        confidence = max(0.05, min(0.99, reliability))
        if threat_type in {"ZERO_DAY_EXPLOIT", "ACTIVE_ATTACK_CAMPAIGN"} and any(
            keyword in content for keyword in ("confirmed", "actively exploited", "observed")
        ):
            confidence += 0.05
        if len(content) < 80:
            confidence -= 0.15
        return max(0.05, min(0.99, round(confidence, 3)))

    @staticmethod
    def _extract_clients(raw_content: str, indicators: list[str]) -> list[str]:
        candidates = re.findall(r"\bclient[:=]\s*([A-Za-z0-9_.-]+)", raw_content, flags=re.IGNORECASE)
        domains = [item for item in indicators if "." in item and not item.startswith("http")]
        return list(dict.fromkeys(candidates + domains))[:10]

    @staticmethod
    def _extract_primary_client(raw_content: str, indicators: list[str]) -> str:
        clients = ThreatClassificationEngine._extract_clients(raw_content, indicators)
        return clients[0] if clients else "UNASSIGNED"

    @staticmethod
    def _build_findings(threat_type: str, severity: str, indicators: list[str]) -> str:
        indicator_note = f"{len(indicators)} target indicator(s)" if indicators else "no explicit target indicators"
        return f"{severity} {threat_type} classified with {indicator_note}."

    @staticmethod
    def _build_evidence(package: Any, raw_content: str) -> str:
        reference = str(getattr(package, "source_reference", "unknown"))
        digest = str(getattr(package, "hash_sha256", ""))[:16]
        excerpt = raw_content.replace("\n", " ")[:280]
        return f"source={reference}; hash_prefix={digest}; excerpt={excerpt}"

    @staticmethod
    def _time_window(threat_type: str, severity: str, time_sensitive: bool) -> str:
        if severity == "CRITICAL" or threat_type in {"ZERO_DAY_EXPLOIT", "ACTIVE_ATTACK_CAMPAIGN"}:
            return "0-24h"
        if time_sensitive or severity == "HIGH":
            return "24-72h"
        if severity == "MEDIUM":
            return "3-7d"
        return "monitor"

    @staticmethod
    def _validate_package(package: Any) -> None:
        required = (
            "intel_id",
            "timestamp_utc",
            "raw_content",
            "source_reference",
            "source_reliability",
            "suspected_severity",
            "suspected_threat_type",
        )
        missing = [field for field in required if not hasattr(package, field)]
        if missing:
            raise ValueError(f"invalid IntelPackage: missing {', '.join(missing)}")
        if not str(package.raw_content).strip():
            raise ValueError("invalid IntelPackage: raw_content is empty")
