from __future__ import annotations

from datetime import UTC, datetime
import json
import os
from pathlib import Path
from typing import Any

from apps.sombra.memory.database import LOG_DIR

from .outbox_monitor import OUTBOX_DIRS, REPO_ROOT


DELIVERY_REPORT_PATH = LOG_DIR / "delivery_report.json"


class DeliveryReportGenerator:
    def generate_report(self) -> dict[str, Any]:
        report: dict[str, Any] = {
            "report_timestamp": self._now(),
            "webhooks_configured": {
                "cerebro": bool(os.getenv("CEREBRO_WEBHOOK_URL")),
                "sentinela": bool(os.getenv("SENTINELA_WEBHOOK_URL")),
                "forja": bool(os.getenv("FORJA_WEBHOOK_URL")),
            },
        }
        total_pending = 0
        for destination in OUTBOX_DIRS:
            section = self._destination_report(destination)
            report[destination] = section
            total_pending += section["pending"]
        report["total_pending"] = total_pending
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        DELIVERY_REPORT_PATH.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
        return report

    @staticmethod
    def _destination_report(destination: str) -> dict[str, Any]:
        outbox_path = REPO_ROOT / OUTBOX_DIRS[destination]
        delivered_path = outbox_path / "delivered"
        outbox_path.mkdir(parents=True, exist_ok=True)
        delivered_path.mkdir(parents=True, exist_ok=True)
        pending_files = sorted(path for path in outbox_path.glob("*.json") if path.is_file())
        delivered_files = sorted(path for path in delivered_path.glob("*.json") if path.is_file())
        oldest_pending = None
        if pending_files:
            oldest_pending = DeliveryReportGenerator._timestamp_from_mtime(
                min(path.stat().st_mtime for path in pending_files)
            )
        return {
            "pending": len(pending_files),
            "delivered": len(delivered_files),
            "oldest_pending": oldest_pending,
        }

    @staticmethod
    def _timestamp_from_mtime(mtime: float) -> str:
        return datetime.fromtimestamp(mtime, UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    @staticmethod
    def _now() -> str:
        return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
