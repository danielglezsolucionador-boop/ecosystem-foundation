from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
import json
from pathlib import Path
import re
from typing import Any

from apps.sombra.memory import BlackBoxAuditCore, DatabaseConnection
from apps.sombra.memory.database import LOG_DIR

from .lockdown import LockdownProtocol


SECURITY_LOG = LOG_DIR / "security.log"
INJECTION_PATTERNS = (
    r"\bDROP\b",
    r"\bDELETE\b",
    r"\bUPDATE\b",
    r"\bINSERT\b",
    r"--",
    r"\bOR\s+1\s*=\s*1\b",
    r"\bUNION\s+SELECT\b",
)


class IntrusionDetectionSystem:
    failed_auth_attempts: dict[str, list[datetime]] = {}
    suspicious_queries: list[dict[str, Any]] = []
    anomaly_log: list[dict[str, Any]] = []
    blocked_ips: set[str] = set()

    def __init__(self, database: DatabaseConnection | None = None, blackbox: BlackBoxAuditCore | None = None) -> None:
        self.database = database if database is not None else DatabaseConnection()
        self.blackbox = blackbox if blackbox is not None else BlackBoxAuditCore(self.database)
        self.lockdown = LockdownProtocol(self.database, self.blackbox)
        self._owns_connection = database is None

    async def disconnect(self) -> None:
        if self._owns_connection:
            await self.database.disconnect()

    async def record_failed_auth(self, source_ip: str) -> bool:
        await self._ensure_ready()
        now = datetime.now(UTC)
        window_start = now - timedelta(seconds=60)
        attempts = [item for item in self.failed_auth_attempts.get(source_ip, []) if item >= window_start]
        attempts.append(now)
        self.failed_auth_attempts[source_ip] = attempts
        blocked = len(attempts) >= 5
        event = {
            "timestamp_utc": self._now(),
            "event": "FAILED_AUTH",
            "source_ip": source_ip,
            "attempts_last_60s": len(attempts),
            "blocked": blocked,
        }
        if blocked:
            self.blocked_ips.add(source_ip)
            await self.blackbox.log(
                "BRUTE_FORCE_DETECTED",
                source_ip,
                event,
                order_origin="SECURITY",
            )
            event["event"] = "BRUTE_FORCE_DETECTED"
        await asyncio.to_thread(self._append_security_log, event)
        return blocked

    async def detect_injection_attempt(self, query: str) -> bool:
        await self._ensure_ready()
        detected = any(re.search(pattern, query, flags=re.IGNORECASE) for pattern in INJECTION_PATTERNS)
        if not detected:
            return False
        event = {
            "timestamp_utc": self._now(),
            "event": "INJECTION_ATTEMPT",
            "query_excerpt": query[:250],
        }
        self.suspicious_queries.append(event)
        await self.blackbox.log(
            "INJECTION_ATTEMPT",
            "QUERY_INPUT",
            event,
            order_origin="SECURITY",
        )
        await asyncio.to_thread(self._append_security_log, event)
        return True

    async def record_anomaly(self, anomaly_type: str, detail: dict[str, Any]) -> None:
        await self._ensure_ready()
        normalized_type = anomaly_type.upper()
        event = {
            "timestamp_utc": self._now(),
            "event": "ANOMALY_RECORDED",
            "anomaly_type": normalized_type,
            "detail": dict(detail),
        }
        self.anomaly_log.append(event)
        await asyncio.to_thread(self._append_security_log, event)
        await self.blackbox.log(
            "SECURITY_ANOMALY_RECORDED",
            normalized_type,
            event,
            order_origin="SECURITY",
        )
        if normalized_type == "CRITICAL":
            await self.lockdown.activate(2, "Critical anomaly recorded by intrusion detector")

    async def get_security_summary(self) -> dict[str, Any]:
        today = datetime.now(UTC).date()
        anomalies_today = [
            item
            for item in self.anomaly_log
            if self._date_from_timestamp(str(item.get("timestamp_utc", ""))) == today
        ]
        return {
            "blocked_ips_count": len(self.blocked_ips),
            "injection_attempts_count": len(self.suspicious_queries),
            "anomalies_today_count": len(anomalies_today),
            "current_lockdown_level": self.lockdown.get_current_level(),
        }

    async def _ensure_ready(self) -> None:
        if self.database.connection is None:
            await self.database.connect()

    @staticmethod
    def _append_security_log(event: dict[str, Any]) -> None:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        with Path(SECURITY_LOG).open("a", encoding="utf-8") as log_file:
            log_file.write(json.dumps(event, sort_keys=True, default=str) + "\n")

    @staticmethod
    def _date_from_timestamp(value: str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).date()
        except ValueError:
            return None

    @staticmethod
    def _now() -> str:
        return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
