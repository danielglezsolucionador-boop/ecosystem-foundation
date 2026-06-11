from __future__ import annotations

import os
from typing import Any

from ..base_agent import SombraCollectorAgent
from ..intel_package import IntelPackage


class SombraPasteAgent(SombraCollectorAgent):
    SEARCH_URLS = (
        "https://psbdmp.ws/api/v3/search/password",
        "https://psbdmp.ws/api/v3/search/credentials",
    )

    def __init__(self, max_items: int = 20, client_domains: list[str] | None = None) -> None:
        super().__init__(agent_id="sombra-paste-agent", source_type="PASTE_SEARCH", priority=40)
        self.max_items = max_items
        self.client_domains = client_domains if client_domains is not None else self._client_domains_from_env()

    async def collect(self) -> list[IntelPackage]:
        packages: list[IntelPackage] = []
        for url in self.SEARCH_URLS:
            try:
                payload = await self._fetch_json(url, timeout_seconds=30)
                packages.extend(self._packages_from_payload(url, payload))
            except Exception as error:
                await self.report_failure({"source": url, "error": repr(error)})
        return packages if await self.validate(packages) else []

    def _packages_from_payload(self, url: str, payload: dict[str, Any]) -> list[IntelPackage]:
        records = self._extract_records(payload)
        packages: list[IntelPackage] = []
        for record in records[: self.max_items]:
            raw = self._compact_json(record)
            indicators = self._extract_indicators(record)
            packages.append(
                IntelPackage(
                    collector_agent=self.agent_id,
                    source_category="CREDENTIAL",
                    raw_content=raw,
                    source_reference=str(record.get("url") or record.get("id") or url),
                    source_reliability=0.6,
                    suspected_severity="MEDIUM",
                    suspected_threat_type="CREDENTIAL_EXPOSURE",
                    target_indicators=indicators,
                    language_detected="unknown",
                    requires_ceo_review=self._matches_client_domain(raw),
                )
            )
        return packages

    def _extract_records(self, payload: dict[str, Any]) -> list[dict[str, Any]]:
        for key in ("data", "results", "pastes", "items"):
            records = payload.get(key)
            if isinstance(records, list):
                return [record for record in records if isinstance(record, dict)]
        return [payload] if payload else []

    @staticmethod
    def _extract_indicators(record: dict[str, Any]) -> list[str]:
        indicators: list[str] = []
        for key in ("id", "url", "domain", "email", "source"):
            value = record.get(key)
            if value:
                indicators.append(str(value))
        return list(dict.fromkeys(indicators))[:20]

    def _matches_client_domain(self, content: str) -> bool:
        normalized = content.lower()
        return any(domain and domain.lower() in normalized for domain in self.client_domains)

    @staticmethod
    def _client_domains_from_env() -> list[str]:
        value = os.getenv("SOMBRA_CLIENT_DOMAINS", "")
        return [domain.strip() for domain in value.split(",") if domain.strip()]
