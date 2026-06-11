from __future__ import annotations

from typing import Any

from ..base_agent import SombraCollectorAgent
from ..intel_package import IntelPackage


class SombraCVEAgent(SombraCollectorAgent):
    NVD_URL = "https://services.nvd.nist.gov/rest/json/cves/2.0"

    def __init__(self, results_per_page: int = 50) -> None:
        super().__init__(agent_id="sombra-cve-agent", source_type="NVD_CVE", priority=10)
        self.results_per_page = results_per_page

    async def collect(self) -> list[IntelPackage]:
        try:
            payload = await self._fetch_json(
                self.NVD_URL,
                params={"resultsPerPage": str(self.results_per_page)},
                timeout_seconds=45,
            )
            packages = [
                package
                for package in (self._package_from_vulnerability(item) for item in payload.get("vulnerabilities", []))
                if package is not None
            ]
            return packages if await self.validate(packages) else []
        except Exception as error:
            await self.report_failure(error)
            return []

    def _package_from_vulnerability(self, vulnerability: dict[str, Any]) -> IntelPackage | None:
        cve = vulnerability.get("cve", {})
        score = self._extract_cvss_score(cve)
        if score is None or score < 7.0:
            return None
        cve_id = str(cve.get("id", "UNKNOWN-CVE"))
        description = self._extract_description(cve)
        indicators = self._extract_affected_systems(cve)
        raw = self._compact_json(
            {
                "id": cve_id,
                "published": cve.get("published"),
                "lastModified": cve.get("lastModified"),
                "cvss": score,
                "description": description,
                "affected": indicators[:30],
                "references": self._extract_references(cve),
            }
        )
        return IntelPackage(
            collector_agent=self.agent_id,
            source_category="OSINT",
            raw_content=raw,
            source_reference=f"https://nvd.nist.gov/vuln/detail/{cve_id}",
            source_reliability=0.95,
            suspected_severity=self._severity_from_score(score),
            suspected_threat_type="VULNERABILITY_PUBLISHED",
            target_indicators=indicators,
            language_detected="en",
            requires_ceo_review=score >= 9.0,
        )

    @staticmethod
    def _extract_cvss_score(cve: dict[str, Any]) -> float | None:
        metrics = cve.get("metrics", {})
        metric_keys = ("cvssMetricV31", "cvssMetricV30", "cvssMetricV2")
        for key in metric_keys:
            values = metrics.get(key) or []
            if not values:
                continue
            cvss_data = values[0].get("cvssData", {})
            score = cvss_data.get("baseScore")
            if score is not None:
                return float(score)
        return None

    @staticmethod
    def _severity_from_score(score: float) -> str:
        if score >= 9.0:
            return "CRITICAL"
        if score >= 7.0:
            return "HIGH"
        if score >= 4.0:
            return "MEDIUM"
        return "LOW"

    @staticmethod
    def _extract_description(cve: dict[str, Any]) -> str:
        descriptions = cve.get("descriptions", [])
        for description in descriptions:
            if description.get("lang") == "en":
                return str(description.get("value", ""))
        if descriptions:
            return str(descriptions[0].get("value", ""))
        return ""

    def _extract_affected_systems(self, cve: dict[str, Any]) -> list[str]:
        systems: list[str] = []
        configurations = cve.get("configurations") or []
        for configuration in configurations:
            for node in configuration.get("nodes", []):
                self._collect_cpe_matches(node, systems)
        return list(dict.fromkeys(systems))[:40]

    @staticmethod
    def _extract_references(cve: dict[str, Any]) -> list[str]:
        references = cve.get("references") or []
        if isinstance(references, dict):
            references = references.get("referenceData") or []
        if not isinstance(references, list):
            return []
        urls: list[str] = []
        for reference in references[:8]:
            if isinstance(reference, dict) and reference.get("url"):
                urls.append(str(reference["url"]))
        return urls

    def _collect_cpe_matches(self, node: dict[str, Any], systems: list[str]) -> None:
        for match in node.get("cpeMatch", []):
            if match.get("vulnerable") and match.get("criteria"):
                systems.append(str(match["criteria"]))
        for child in node.get("children", []):
            self._collect_cpe_matches(child, systems)
