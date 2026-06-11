from __future__ import annotations

import asyncio
from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Any

from apps.sombra.communication import CEOEmergencyChannel
from apps.sombra.memory import BlackBoxAuditCore, DatabaseConnection
from apps.sombra.memory.database import LOG_DIR
from apps.sombra.security import LockdownProtocol

from .health_monitor import SombraHealthMonitor


HEARTBEAT_LOG = LOG_DIR / "heartbeat.log"
WATCHDOG_ERROR_LOG = LOG_DIR / "watchdog_errors.log"


class SombraWatchdog:
    def __init__(self, database: DatabaseConnection | None = None) -> None:
        self.database = database if database is not None else DatabaseConnection()
        self.blackbox = BlackBoxAuditCore(self.database)
        self.health_monitor = SombraHealthMonitor()
        self.lockdown = LockdownProtocol(self.database, self.blackbox)
        self.emergency = CEOEmergencyChannel(self.database, self.blackbox)
        self._owns_connection = database is None

    async def disconnect(self) -> None:
        if self._owns_connection:
            await self.database.disconnect()

    async def run_once(self) -> dict[str, Any]:
        await self._ensure_ready()
        modules = await self.health_monitor.check_all_modules()
        overall_status = self._overall_status_from_matrix(modules)
        heartbeat = {
            "timestamp_utc": self._now(),
            "overall_status": overall_status,
            "modules": modules,
            "lockdown_level": self.lockdown.get_current_level(),
            "active_alerts_today": await self._count_active_alerts_today(),
            "intel_processed_today": await self._count_intel_processed_today(),
        }
        await asyncio.to_thread(self._write_heartbeat, heartbeat)
        if overall_status == "CRITICAL":
            await self.emergency.activate(
                "CRITICAL_COMPROMISE",
                "Watchdog detected CRITICAL module health.",
                {"overall_status": overall_status},
                ["nonessential_operations"],
            )
        return heartbeat

    async def run_forever(self, interval_seconds: int = 30) -> None:
        while True:
            try:
                await self.run_once()
            except Exception as error:
                await asyncio.to_thread(self._append_error_log, error)
            await asyncio.sleep(max(1, int(interval_seconds)))

    async def _ensure_ready(self) -> None:
        if self.database.connection is None:
            await self.database.connect()

    async def _count_active_alerts_today(self) -> int:
        row = await self._safe_fetchrow(
            "SELECT COUNT(*) AS count FROM sombra_alerts WHERE date(timestamp_utc) = date('now')"
        )
        return int((row or {}).get("count") or 0)

    async def _count_intel_processed_today(self) -> int:
        row = await self._safe_fetchrow(
            "SELECT COUNT(*) AS count FROM sombra_intel_global WHERE date(timestamp_utc) = date('now')"
        )
        return int((row or {}).get("count") or 0)

    async def _safe_fetchrow(self, query: str) -> dict[str, Any] | None:
        try:
            return await self.database.fetchrow(query)
        except Exception:
            return None

    @staticmethod
    def _overall_status_from_matrix(modules: dict[str, dict[str, Any]]) -> str:
        statuses = [row["status"] for row in modules.values()]
        if "DOWN" in statuses:
            return "CRITICAL"
        if "DEGRADED" in statuses:
            return "DEGRADED"
        return "FULLY_OPERATIONAL"

    @staticmethod
    def _write_heartbeat(heartbeat: dict[str, Any]) -> None:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        Path(HEARTBEAT_LOG).write_text(json.dumps(heartbeat, indent=2, sort_keys=True, default=str), encoding="utf-8")

    @staticmethod
    def _append_error_log(error: Exception) -> None:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        with Path(WATCHDOG_ERROR_LOG).open("a", encoding="utf-8") as log_file:
            log_file.write(f"{SombraWatchdog._now()} error={error!r}\n")

    @staticmethod
    def _now() -> str:
        return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
