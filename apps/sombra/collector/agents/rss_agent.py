from __future__ import annotations

import asyncio
import re
from typing import Any
from xml.etree import ElementTree

from ..base_agent import SombraCollectorAgent
from ..intel_package import IntelPackage


class SombraRSSAgent(SombraCollectorAgent):
    FEEDS = (
        "https://feeds.feedburner.com/TheHackersNews",
        "https://www.bleepingcomputer.com/feed",
        "https://krebsonsecurity.com/feed",
    )

    def __init__(self, feeds: tuple[str, ...] = FEEDS, max_items_per_feed: int = 10) -> None:
        super().__init__(agent_id="sombra-rss-agent", source_type="SECURITY_RSS", priority=20)
        self.feeds = feeds
        self.max_items_per_feed = max_items_per_feed

    async def collect(self) -> list[IntelPackage]:
        packages: list[IntelPackage] = []
        for feed_url in self.feeds:
            try:
                text = await self._fetch_text(feed_url, timeout_seconds=30)
                parsed = await self._parse_feed(text)
                for entry in parsed.get("entries", [])[: self.max_items_per_feed]:
                    package = self._package_from_entry(feed_url, entry)
                    if package is not None:
                        packages.append(package)
            except Exception as error:
                await self.report_failure({"feed": feed_url, "error": repr(error)})
        return packages if await self.validate(packages) else []

    async def _parse_feed(self, text: str) -> dict[str, Any]:
        try:
            import feedparser
        except ImportError:
            return await asyncio.to_thread(self._parse_basic_feed, text)

        parsed = await asyncio.to_thread(feedparser.parse, text)
        return dict(parsed)

    def _parse_basic_feed(self, text: str) -> dict[str, Any]:
        root = ElementTree.fromstring(text.encode("utf-8"))
        entries: list[dict[str, str | None]] = []
        channel = root.find("channel")
        items = channel.findall("item") if channel is not None else root.findall(".//item")
        if items:
            for item in items:
                entries.append(
                    {
                        "title": self._child_text(item, "title"),
                        "link": self._child_text(item, "link"),
                        "summary": self._child_text(item, "description"),
                        "published": self._child_text(item, "pubDate"),
                    }
                )
            return {"entries": entries}

        namespace = {"atom": "http://www.w3.org/2005/Atom"}
        for entry in root.findall(".//atom:entry", namespace):
            link_node = entry.find("atom:link", namespace)
            entries.append(
                {
                    "title": self._child_text(entry, "atom:title", namespace),
                    "link": link_node.get("href") if link_node is not None else None,
                    "summary": self._child_text(entry, "atom:summary", namespace)
                    or self._child_text(entry, "atom:content", namespace),
                    "published": self._child_text(entry, "atom:published", namespace)
                    or self._child_text(entry, "atom:updated", namespace),
                }
            )
        return {"entries": entries}

    @staticmethod
    def _child_text(node: ElementTree.Element, path: str, namespace: dict[str, str] | None = None) -> str | None:
        child = node.find(path, namespace or {})
        if child is None or child.text is None:
            return None
        return child.text.strip()

    def _package_from_entry(self, feed_url: str, entry: Any) -> IntelPackage | None:
        title = str(entry.get("title", "")).strip()
        link = str(entry.get("link", feed_url)).strip() or feed_url
        summary = str(entry.get("summary", entry.get("description", ""))).strip()
        if not title and not summary:
            return None
        content = self._compact_json(
            {
                "feed": feed_url,
                "title": title,
                "link": link,
                "published": entry.get("published") or entry.get("updated"),
                "summary": summary[:1200],
            }
        )
        severity = self._severity_from_text(f"{title} {summary}")
        return IntelPackage(
            collector_agent=self.agent_id,
            source_category="OSINT",
            raw_content=content,
            source_reference=link,
            source_reliability=0.8,
            suspected_severity=severity,
            suspected_threat_type="SECURITY_NEWS_SIGNAL",
            target_indicators=self._extract_indicators(f"{title} {summary} {link}"),
            language_detected="en",
            requires_ceo_review=severity in {"CRITICAL", "HIGH"},
        )

    @staticmethod
    def _severity_from_text(text: str) -> str:
        value = text.lower()
        critical_terms = ("zero-day", "0-day", "actively exploited", "mass exploitation", "critical vulnerability")
        high_terms = ("ransomware", "data breach", "credential theft", "malware", "botnet", "supply chain")
        if any(term in value for term in critical_terms):
            return "CRITICAL"
        if any(term in value for term in high_terms):
            return "HIGH"
        return "MEDIUM"

    @staticmethod
    def _extract_indicators(text: str) -> list[str]:
        cves = re.findall(r"CVE-\d{4}-\d{4,7}", text, flags=re.IGNORECASE)
        urls = re.findall(r"https?://[^\s<>\"]+", text)
        return list(dict.fromkeys([item.upper() if item.lower().startswith("cve-") else item for item in cves + urls]))[:20]
