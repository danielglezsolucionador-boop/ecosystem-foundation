from __future__ import annotations

import os
import re
from typing import Any

from .models import EnrichedIntel


SECTOR_KEYWORDS = {
    "finance": ("bank", "payment", "fintech", "credit", "loan", "invoice"),
    "healthcare": ("hospital", "clinic", "patient", "healthcare", "medical"),
    "retail": ("ecommerce", "retail", "amazon", "storefront", "checkout"),
    "government": ("government", "municipal", "public sector", "tax", "sunat"),
    "technology": ("saas", "api", "cloud", "devops", "software", "database"),
}


class ThreatEnrichmentEngine:
    def __init__(self, client_domains: list[str] | None = None) -> None:
        self.client_domains = client_domains if client_domains is not None else self._client_domains_from_env()

    def enrich(self, package: Any) -> EnrichedIntel:
        raw_content = str(getattr(package, "raw_content", ""))
        indicators = self._extract_indicators(raw_content, getattr(package, "target_indicators", []))
        clients = self._match_clients(raw_content, indicators)
        assets = self._extract_assets(indicators)
        sectors = self._detect_sectors(raw_content)
        time_window = self._time_window_from_content(raw_content, str(getattr(package, "suspected_severity", "")))
        return EnrichedIntel(
            clients=clients,
            assets=assets,
            indicators=indicators,
            sectors=sectors,
            time_window=time_window,
            source_mission=str(getattr(package, "collector_agent", "unknown")),
            primary_client=clients[0] if clients else "UNASSIGNED",
            evidence_summary=self._evidence_summary(package, raw_content, indicators),
        )

    def _match_clients(self, raw_content: str, indicators: list[str]) -> list[str]:
        normalized = raw_content.lower()
        clients = [domain for domain in self.client_domains if domain.lower() in normalized]
        for indicator in indicators:
            for domain in self.client_domains:
                if domain.lower() in indicator.lower() and domain not in clients:
                    clients.append(domain)
        explicit = re.findall(r"\bclient[:=]\s*([A-Za-z0-9_.-]+)", raw_content, flags=re.IGNORECASE)
        return list(dict.fromkeys(clients + explicit))[:10]

    @staticmethod
    def _extract_indicators(raw_content: str, target_indicators: Any) -> list[str]:
        indicators = [str(item).strip() for item in target_indicators if str(item).strip()]
        indicators.extend(re.findall(r"CVE-\d{4}-\d{4,7}", raw_content, flags=re.IGNORECASE))
        indicators.extend(re.findall(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", raw_content))
        indicators.extend(re.findall(r"https?://[^\s<>'\"]+", raw_content))
        indicators.extend(re.findall(r"\b[a-fA-F0-9]{64}\b", raw_content))
        indicators.extend(re.findall(r"\b[A-Za-z0-9_.+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b", raw_content))
        return list(dict.fromkeys(indicators))[:80]

    @staticmethod
    def _extract_assets(indicators: list[str]) -> list[str]:
        assets: list[str] = []
        for indicator in indicators:
            if indicator.lower().startswith("cpe:"):
                assets.append(indicator)
            elif indicator.startswith("http://") or indicator.startswith("https://"):
                assets.append(indicator.split("/")[2])
            elif "@" in indicator:
                assets.append(indicator.split("@", 1)[1])
            elif re.match(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", indicator):
                assets.append(indicator)
        return list(dict.fromkeys(assets))[:40]

    @staticmethod
    def _detect_sectors(raw_content: str) -> list[str]:
        normalized = raw_content.lower()
        sectors: list[str] = []
        for sector, keywords in SECTOR_KEYWORDS.items():
            if any(keyword in normalized for keyword in keywords):
                sectors.append(sector)
        return sectors

    @staticmethod
    def _time_window_from_content(raw_content: str, severity: str) -> str:
        normalized = raw_content.lower()
        if severity.upper() == "CRITICAL" or "actively exploited" in normalized or "zero-day" in normalized:
            return "0-24h"
        if severity.upper() == "HIGH" or "ransomware" in normalized or "credential" in normalized:
            return "24-72h"
        if severity.upper() == "MEDIUM":
            return "3-7d"
        return "monitor"

    @staticmethod
    def _evidence_summary(package: Any, raw_content: str, indicators: list[str]) -> str:
        reference = str(getattr(package, "source_reference", "unknown"))
        source = str(getattr(package, "source_category", "unknown"))
        excerpt = raw_content.replace("\n", " ")[:220]
        return f"{source} evidence from {reference}; indicators={len(indicators)}; excerpt={excerpt}"

    @staticmethod
    def _client_domains_from_env() -> list[str]:
        value = os.getenv("SOMBRA_CLIENT_DOMAINS", "")
        return [domain.strip() for domain in value.split(",") if domain.strip()]
