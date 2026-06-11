from __future__ import annotations

import asyncio
from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Any

from apps.sombra.communication import CEOEmergencyChannel
from apps.sombra.memory import BlackBoxAuditCore, DatabaseConnection
from apps.sombra.memory.database import LOG_DIR


SECURITY_LOG = LOG_DIR / "security.log"
CAPACITIES = {0: 100, 1: 90, 2: 70, 3: 30, 4: 10}


class LockdownProtocol:
    current_level: int = 0

    def __init__(self, database: DatabaseConnection | None = None, blackbox: BlackBoxAuditCore | None = None) -> None:
        self.database = database if database is not None else DatabaseConnection()
        self.blackbox = blackbox if blackbox is not None else BlackBoxAuditCore(self.database)
        self._owns_connection = database is None

    async def disconnect(self) -> None:
        if self._owns_connection:
            await self.database.disconnect()

    async def activate(self, level: int, reason: str) -> dict[str, Any]:
        await self._ensure_ready()
        normalized_level = max(0, min(4, int(level)))
        LockdownProtocol.current_level = normalized_level
        event = {
            "timestamp_utc": self._now(),
            "event": "LOCKDOWN_ACTIVATED",
            "level": normalized_level,
            "reason": reason,
            "operational_capacity": self.get_operational_capacity(),
        }
        await self.blackbox.log(
            "LOCKDOWN_ACTIVATED",
            "SOMBRA_SECURITY",
            event,
            order_origin="SECURITY",
        )
        await asyncio.to_thread(self._append_security_log, event)
        print(f"[SOMBRA LOCKDOWN LEVEL {normalized_level} ACTIVATED]")
        print(f"[REASON: {reason}]")
        if normalized_level >= 3:
            emergency = CEOEmergencyChannel(self.database, self.blackbox)
            await emergency.activate(
                "CRITICAL_COMPROMISE",
                reason,
                {"lockdown_level": normalized_level, "operational_capacity": self.get_operational_capacity()},
                ["external_transmission", "identity_activity", "nonessential_collection"],
            )
        return event

    async def deactivate(self, authorized_by: str) -> bool:
        await self._ensure_ready()
        if authorized_by != "CEO":
            await self.blackbox.log(
                "LOCKDOWN_DEACTIVATE_REJECTED",
                "SOMBRA_SECURITY",
                {"authorized_by": authorized_by, "current_level": LockdownProtocol.current_level},
                order_origin="SECURITY",
            )
            await asyncio.to_thread(
                self._append_security_log,
                {
                    "timestamp_utc": self._now(),
                    "event": "LOCKDOWN_DEACTIVATE_REJECTED",
                    "authorized_by": authorized_by,
                    "current_level": LockdownProtocol.current_level,
                },
            )
            return False
        previous_level = LockdownProtocol.current_level
        LockdownProtocol.current_level = 0
        await self.blackbox.log(
            "LOCKDOWN_DEACTIVATED",
            "SOMBRA_SECURITY",
            {"authorized_by": authorized_by, "previous_level": previous_level},
            order_origin="CEO",
        )
        await asyncio.to_thread(
            self._append_security_log,
            {
                "timestamp_utc": self._now(),
                "event": "LOCKDOWN_DEACTIVATED",
                "authorized_by": authorized_by,
                "previous_level": previous_level,
            },
        )
        return True

    def get_current_level(self) -> int:
        return LockdownProtocol.current_level

    def get_operational_capacity(self) -> int:
        return CAPACITIES.get(LockdownProtocol.current_level, 0)

    async def _ensure_ready(self) -> None:
        if self.database.connection is None:
            await self.database.connect()

    @staticmethod
    def _append_security_log(event: dict[str, Any]) -> None:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        with Path(SECURITY_LOG).open("a", encoding="utf-8") as log_file:
            log_file.write(json.dumps(event, sort_keys=True, default=str) + "\n")

    @staticmethod
    def _now() -> str:
        return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
