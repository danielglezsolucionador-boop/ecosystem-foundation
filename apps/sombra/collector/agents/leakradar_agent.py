from __future__ import annotations

import json
import re
from typing import Any

from ..base_agent import SombraCollectorAgent
from ..intel_package import IntelPackage


class SombraLeakRadarAgent(SombraCollectorAgent):
    BASE_URL = "https://leakradar.io/api/v1/search"
    API_BASE_URL = "https://api.leakradar.io"

    def __init__(self, domains: list[str] | None = None, timeout_seconds: int = 25) -> None:
        super().__init__(agent_id="sombra-leakradar-agent", source_type="LEAKRADAR", priority=5)
        self.domains = [self._clean_domain(domain) for domain in domains or [] if str(domain).strip()]
        self.timeout_seconds = timeout_seconds

    async def collect(self) -> list[IntelPackage]:
        packages: list[IntelPackage] = []
        for domain in self.domains:
            result = await self.search_domain(domain)
            if result.get("hits", 0) <= 0:
                continue
            packages.append(self._package_from_result(domain, result))
        return packages if await self.validate(packages) else []

    async def search_domain(self, domain: str) -> dict[str, Any]:
        clean_domain = self._clean_domain(domain)
        try:
            payload, source_reference = await self._fetch_payload(clean_domain)
            results = self._extract_results(payload)
            hits = self._count_hits(payload, results)
            if hits == 0:
                results = []
            return {
                "source": "LeakRadar",
                "query": clean_domain,
                "source_reference": source_reference,
                "source_reliability": 0.85,
                "source_category": "CREDENTIAL",
                "status": "ok" if results else "empty",
                "hits": hits,
                "results": results,
            }
        except Exception as error:
            await self.report_failure({"domain": clean_domain, "error": repr(error)})
            return {
                "source": "LeakRadar",
                "query": clean_domain,
                "source_reference": self.BASE_URL,
                "source_reliability": 0.85,
                "source_category": "CREDENTIAL",
                "status": "error",
                "hits": 0,
                "results": [],
                "error": str(error),
            }

    async def _fetch_payload(self, domain: str) -> tuple[Any, str]:
        attempts = [
            (self.BASE_URL, {"q": domain, "type": "domain"}),
            (f"{self.API_BASE_URL}/search/domain/{domain}", {"light": "true"}),
        ]
        last_error: Exception | None = None
        for url, params in attempts:
            try:
                text = await self._fetch_text(url, params=params, timeout_seconds=self.timeout_seconds)
                if not text.strip():
                    return {}, url
                return json.loads(text), url
            except Exception as error:
                last_error = error
        if last_error is not None:
            raise last_error
        return {}, self.BASE_URL

    def _package_from_result(self, domain: str, result: dict[str, Any]) -> IntelPackage:
        raw = self._compact_json(result)
        return IntelPackage(
            collector_agent=self.agent_id,
            source_category="CREDENTIAL",
            raw_content=raw,
            source_reference=str(result.get("source_reference") or f"{self.BASE_URL}?q={domain}&type=domain"),
            source_reliability=0.85,
            suspected_severity="HIGH",
            suspected_threat_type="CREDENTIAL_EXPOSURE",
            target_indicators=[domain],
            language_detected="en",
            requires_ceo_review=True,
        )

    @staticmethod
    def _extract_results(payload: Any) -> list[dict[str, Any]]:
        if isinstance(payload, list):
            values = payload
        elif isinstance(payload, dict):
            for key in ("results", "data", "hits", "items"):
                value = payload.get(key)
                if isinstance(value, list):
                    values = value
                    break
            else:
                values = [payload] if payload and not payload.get("error") else []
        else:
            values = []

        results: list[dict[str, Any]] = []
        for item in values:
            if isinstance(item, dict):
                results.append(item)
            else:
                results.append({"value": str(item)})
        return results

    @staticmethod
    def _count_hits(payload: Any, results: list[dict[str, Any]]) -> int:
        if isinstance(payload, dict):
            count_fields = ("employees_compromised", "third_parties_compromised", "customers_compromised")
            if any(field in payload for field in count_fields):
                total = 0
                for field in count_fields:
                    try:
                        total += int(payload.get(field) or 0)
                    except (TypeError, ValueError):
                        continue
                return total
            for field in ("total", "count", "hits"):
                try:
                    if field in payload:
                        return int(payload.get(field) or 0)
                except (TypeError, ValueError):
                    continue
        return len(results)

    @staticmethod
    def _clean_domain(domain: str) -> str:
        clean = str(domain or "").strip().lower()
        clean = re.sub(r"^https?://", "", clean).split("/")[0].strip(".")
        if not clean or "." not in clean:
            raise ValueError("domain must be a valid DNS domain")
        return clean
