from __future__ import annotations

import asyncio
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Any

from apps.sombra.memory import BlackBoxAuditCore, DatabaseConnection
from apps.sombra.memory.database import LOG_DIR
from apps.sombra.security.output_sanitizer import OutputSanitizer


SENTINELA_MASK_LOG = LOG_DIR / "sentinela_mask.log"
FORBIDDEN_WORDS = [
    "sombra",
    "SOMBRA",
    "Sombra",
    "covert_agent",
    "infiltration",
    "dark_web_identity",
    "fake_profile",
    "underground_forum_access",
    "dark_web",
    "underground",
    "covert",
    "operational_identity",
]
ALLOWED_SOURCES = {
    "THREAT_INTELLIGENCE_ENGINE",
    "MONITORING_ENGINE",
    "ADVANCED_MONITORING",
    "CLASSIFIED",
}


@dataclass(slots=True)
class ValidationResult:
    valid: bool
    violations: list[str] = field(default_factory=list)
    reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class SentinelaMaskValidator:
    def __init__(self, database: DatabaseConnection | None = None, blackbox: BlackBoxAuditCore | None = None) -> None:
        self.database = database if database is not None else DatabaseConnection()
        self.blackbox = blackbox if blackbox is not None else BlackBoxAuditCore(self.database)
        self._owns_connection = database is None

    async def disconnect(self) -> None:
        if self._owns_connection:
            await self.database.disconnect()

    async def validate(self, payload: dict[str, Any]) -> ValidationResult:
        await self._ensure_ready()
        payload_text = json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str)
        violations = [word for word in FORBIDDEN_WORDS if word in payload_text]
        if OutputSanitizer.contains_forbidden_external_reference(payload_text):
            violations.append("classified_reference_pattern")
        if violations:
            result = ValidationResult(valid=False, violations=violations, reason="forbidden_word_detected")
            await self._log_failure(result, payload)
            return result

        source = payload.get("source")
        if source is not None and str(source) not in ALLOWED_SOURCES:
            result = ValidationResult(valid=False, violations=[str(source)], reason="invalid_source_field")
            await self._log_failure(result, payload)
            return result

        return ValidationResult(valid=True)

    async def _log_failure(self, result: ValidationResult, payload: dict[str, Any]) -> None:
        payload_keys = sorted(str(key) for key in payload)
        log_row = {
            "timestamp_utc": self._now(),
            "event": "MASK_VIOLATION_DETECTED",
            "reason": result.reason,
            "violations": result.violations,
            "payload_keys": payload_keys,
        }
        await self.blackbox.log(
            "SENTINELA_MASK_FAILURE",
            "MASK_VALIDATOR",
            log_row,
            order_origin="SENTINELA_INTEGRATION",
        )
        await asyncio.to_thread(self._append_mask_log, log_row)

    async def _ensure_ready(self) -> None:
        if self.database.connection is None:
            await self.database.connect()

    @staticmethod
    def _append_mask_log(row: dict[str, Any]) -> None:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        with Path(SENTINELA_MASK_LOG).open("a", encoding="utf-8") as log_file:
            log_file.write(json.dumps(row, sort_keys=True, default=str) + "\n")

    @staticmethod
    def _now() -> str:
        return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
