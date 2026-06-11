from __future__ import annotations

import asyncio
import csv
from io import StringIO
from typing import Any

from ..base_agent import SombraCollectorAgent
from ..intel_package import IntelPackage


class SombraAbuseAgent(SombraCollectorAgent):
    URLHAUS_RECENT_URL = "https://urlhaus-api.abuse.ch/v1/urls/recent/"
    MALWARE_BAZAAR_RECENT_CSV = "https://bazaar.abuse.ch/export/csv/recent/"

    def __init__(self, max_items: int = 25) -> None:
        super().__init__(agent_id="sombra-abuse-agent", source_type="ABUSE_CH", priority=30)
        self.max_items = max_items

    async def collect(self) -> list[IntelPackage]:
        packages: list[IntelPackage] = []
        packages.extend(await self._collect_urlhaus())
        packages.extend(await self._collect_malware_bazaar())
        return packages if await self.validate(packages) else []

    async def _collect_urlhaus(self) -> list[IntelPackage]:
        try:
            payload = await self._fetch_json(self.URLHAUS_RECENT_URL, timeout_seconds=45)
            urls = payload.get("urls", [])
            return [self._package_from_urlhaus(item) for item in urls[: self.max_items] if isinstance(item, dict)]
        except Exception as error:
            await self.report_failure({"source": self.URLHAUS_RECENT_URL, "error": repr(error)})
            return []

    async def _collect_malware_bazaar(self) -> list[IntelPackage]:
        try:
            csv_text = await self._fetch_text(self.MALWARE_BAZAAR_RECENT_CSV, timeout_seconds=45)
            rows = await asyncio.to_thread(self._parse_csv_rows, csv_text)
            return [self._package_from_bazaar(row) for row in rows[: self.max_items]]
        except Exception as error:
            await self.report_failure({"source": self.MALWARE_BAZAAR_RECENT_CSV, "error": repr(error)})
            return []

    def _package_from_urlhaus(self, item: dict[str, Any]) -> IntelPackage:
        raw = self._compact_json(item)
        indicators = [str(value) for value in (item.get("url"), item.get("host"), item.get("threat")) if value]
        indicators.extend(str(tag) for tag in item.get("tags", []) if tag)
        return IntelPackage(
            collector_agent=self.agent_id,
            source_category="THREAT_INTELLIGENCE",
            raw_content=raw,
            source_reference=str(item.get("urlhaus_reference") or item.get("url") or self.URLHAUS_RECENT_URL),
            source_reliability=0.9,
            suspected_severity="HIGH",
            suspected_threat_type="MALICIOUS_URL_OBSERVED",
            target_indicators=list(dict.fromkeys(indicators))[:20],
            language_detected="en",
            requires_ceo_review=False,
        )

    def _package_from_bazaar(self, row: dict[str, str]) -> IntelPackage:
        raw = self._compact_json(row)
        indicators = [
            row.get("sha256_hash", ""),
            row.get("sha1_hash", ""),
            row.get("md5_hash", ""),
            row.get("signature", ""),
            row.get("file_type_guess", ""),
        ]
        sha256 = row.get("sha256_hash") or "unknown"
        return IntelPackage(
            collector_agent=self.agent_id,
            source_category="THREAT_INTELLIGENCE",
            raw_content=raw,
            source_reference=f"https://bazaar.abuse.ch/sample/{sha256}/",
            source_reliability=0.9,
            suspected_severity="HIGH",
            suspected_threat_type="MALWARE_SAMPLE_OBSERVED",
            target_indicators=[indicator for indicator in indicators if indicator],
            language_detected="en",
            requires_ceo_review=False,
        )

    @staticmethod
    def _parse_csv_rows(csv_text: str) -> list[dict[str, str]]:
        lines = [line for line in csv_text.splitlines() if line and not line.startswith("#")]
        if not lines:
            return []
        reader = csv.DictReader(StringIO("\n".join(lines)))
        return [dict(row) for row in reader if row]
