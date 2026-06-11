from __future__ import annotations

import asyncio
from collections import Counter
from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Any

from apps.sombra.memory import DatabaseConnection, GlobalMemoryLayer, MemoryQueryEngine
from apps.sombra.memory.database import LOG_DIR
from apps.sombra.security.output_sanitizer import OutputSanitizer

from .generator import AlertGenerationEngine


SECTOR_KEYWORDS = {
    "finance": ("bank", "payment", "fintech", "invoice", "credit"),
    "healthcare": ("hospital", "clinic", "patient", "medical"),
    "retail": ("ecommerce", "amazon", "checkout", "store"),
    "government": ("government", "public sector", "tax", "sunat"),
    "technology": ("api", "cloud", "database", "software", "saas"),
}


class DailyIntelligenceBriefing:
    def __init__(self, database: DatabaseConnection | None = None) -> None:
        self.database = database if database is not None else DatabaseConnection()
        self.memory = GlobalMemoryLayer(self.database)
        self.query = MemoryQueryEngine(self.database)
        self.alerts = AlertGenerationEngine(self.database)
        self._owns_connection = database is None

    async def disconnect(self) -> None:
        if self._owns_connection:
            await self.database.disconnect()

    async def generate(self) -> dict[str, Any]:
        await self._ensure_ready()
        recent_threats = await self.memory.get_recent_threats(hours=24)
        all_alerts = await self.alerts.get_recent_alerts(hours=24)
        memory_summary = await self.query.get_threat_summary()
        critical_alerts = [alert for alert in all_alerts if alert.get("severity") == "CRITICAL"]
        high_alerts = [alert for alert in all_alerts if alert.get("severity") == "HIGH"]
        threat_type_counts = Counter(str(row.get("threat_type", "UNKNOWN")) for row in recent_threats)
        severity_counts = Counter(str(alert.get("severity", "UNKNOWN")) for alert in all_alerts)
        sector_counts = self._sector_counts(recent_threats)
        briefing = {
            "generated_at_utc": self._now(),
            "executive_summary": {
                "critical_alert_count": int(severity_counts.get("CRITICAL", 0)),
                "high_alert_count": int(severity_counts.get("HIGH", 0)),
                "most_severe_threat_type_today": self._most_severe_threat_type(all_alerts, recent_threats),
                "total_intel_packages_processed": len(recent_threats),
            },
            "threat_landscape": {
                "top_5_threat_types_by_count": threat_type_counts.most_common(5),
                "top_3_most_targeted_sectors": sector_counts.most_common(3),
            },
            "alert_summary": {
                "critical_alerts_today": self._brief_alerts(critical_alerts),
                "high_alerts_today": self._brief_alerts(high_alerts),
            },
            "operational_status": {
                "total_intel_stored_in_memory": memory_summary["total_intel_stored"],
                "collector_agents_status": self._collector_status(),
                "alert_engine_status": {
                    "status": "ACTIVE",
                    "alerts_last_24h": len(all_alerts),
                    "database_backend": self.database.backend,
                },
            },
        }
        briefing = OutputSanitizer.sanitize_external(briefing)
        await asyncio.to_thread(self._write_briefing_file, briefing)
        return briefing

    async def _ensure_ready(self) -> None:
        if self.database.connection is None:
            await self.database.connect()

    @staticmethod
    def _sector_counts(recent_threats: list[dict[str, Any]]) -> Counter[str]:
        counts: Counter[str] = Counter()
        for threat in recent_threats:
            text = json.dumps(threat, ensure_ascii=True).lower()
            for sector, keywords in SECTOR_KEYWORDS.items():
                if any(keyword in text for keyword in keywords):
                    counts[sector] += 1
        return counts

    @staticmethod
    def _most_severe_threat_type(all_alerts: list[dict[str, Any]], recent_threats: list[dict[str, Any]]) -> str:
        severity_rank = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}
        candidates = all_alerts or recent_threats
        if not candidates:
            return "NONE"
        ordered = sorted(
            candidates,
            key=lambda item: (
                severity_rank.get(str(item.get("severity", "")).upper(), 0),
                int(item.get("threat_score") or 0),
            ),
            reverse=True,
        )
        return str(ordered[0].get("threat_type", "UNKNOWN"))

    @staticmethod
    def _brief_alerts(alerts: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [
            {
                "alert_id": alert.get("alert_id"),
                "threat_type": alert.get("threat_type"),
                "threat_score": alert.get("threat_score"),
                "target_client": alert.get("target_client"),
                "recommended_action": alert.get("recommended_action"),
            }
            for alert in alerts
        ]

    @staticmethod
    def _collector_status() -> dict[str, Any]:
        scheduler_log = LOG_DIR / "scheduler.log"
        collector_log = LOG_DIR / "sombra_collector.log"
        status = {
            "scheduler_log_present": scheduler_log.exists(),
            "collector_startup_log_present": collector_log.exists(),
            "status": "LOG_PRESENT" if scheduler_log.exists() or collector_log.exists() else "NO_RECENT_LOG",
        }
        if scheduler_log.exists():
            lines = scheduler_log.read_text(encoding="utf-8", errors="replace").splitlines()
            status["recent_scheduler_events"] = lines[-6:]
        return status

    @staticmethod
    def _write_briefing_file(briefing: dict[str, Any]) -> None:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        today = datetime.now(UTC).date().isoformat()
        path = LOG_DIR / f"daily_briefing_{today}.json"
        path.write_text(json.dumps(briefing, indent=2, sort_keys=True, default=str), encoding="utf-8")

    @staticmethod
    def _now() -> str:
        return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
