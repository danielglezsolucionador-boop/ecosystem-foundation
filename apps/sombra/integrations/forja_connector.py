from __future__ import annotations

import asyncio
from datetime import UTC, datetime
import json
import os
from pathlib import Path
from typing import Any
import uuid
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from apps.sombra.memory import BlackBoxAuditCore, DatabaseConnection
from apps.sombra.memory.database import LOG_DIR
from apps.sombra.security.output_sanitizer import OutputSanitizer


FORJA_OUTBOUND_LOG = LOG_DIR / "forja_outbound.log"
FORJA_OUTBOX = Path(__file__).resolve().parents[1] / "outbox" / "forja"
REQUIRED_SIGNAL_FIELDS = {
    "signal_id",
    "timestamp",
    "origin",
    "pattern_detected",
    "construction_needed",
    "priority",
    "description",
    "technical_context",
    "deadline_estimate",
    "indicators",
}


class ForjaConnector:
    def __init__(self, database: DatabaseConnection | None = None, blackbox: BlackBoxAuditCore | None = None) -> None:
        self.database = database if database is not None else DatabaseConnection()
        self.blackbox = blackbox if blackbox is not None else BlackBoxAuditCore(self.database)
        self.webhook_url = os.getenv("FORJA_WEBHOOK_URL", "").strip()
        self.api_key = os.getenv("FORJA_API_KEY", "").strip()
        self._owns_connection = database is None

    async def disconnect(self) -> None:
        if self._owns_connection:
            await self.database.disconnect()

    async def send_construction_signal(self, signal: dict[str, Any]) -> bool:
        await self._ensure_ready()
        signal = OutputSanitizer.sanitize_external(signal)
        validation = self._validate_signal(signal)
        if not validation["valid"]:
            await self.blackbox.log(
                "CONSTRUCTION_SIGNAL_REJECTED_FORJA",
                str(signal.get("signal_id", "UNKNOWN")),
                validation,
                order_origin="FORJA_INTEGRATION",
            )
            await asyncio.to_thread(self._append_outbound_log, {**validation, "delivered": False})
            return False

        delivered = await self._deliver_or_outbox(signal)
        await self.blackbox.log(
            "CONSTRUCTION_SIGNAL_SENT_TO_FORJA",
            str(signal["signal_id"]),
            {
                "delivered": delivered,
                "priority": signal["priority"],
                "pattern_detected": signal["pattern_detected"],
                "delivery_target": "webhook" if self.webhook_url else "file_outbox",
            },
            order_origin="FORJA_INTEGRATION",
        )
        return delivered

    async def get_pending_signals(self) -> list[dict[str, Any]]:
        await self._ensure_ready()
        if not FORJA_OUTBOX.exists():
            return []
        signals: list[dict[str, Any]] = []
        for path in sorted(FORJA_OUTBOX.glob("*.json")):
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                continue
            signals.append({"file": path.name, "signal": payload})
        return signals

    async def _deliver_or_outbox(self, signal: dict[str, Any]) -> bool:
        if self.webhook_url:
            delivered = await self._post_with_retry(signal)
            if delivered:
                return True
        await asyncio.to_thread(self._write_outbox, signal)
        await asyncio.to_thread(
            self._append_outbound_log,
            {
                "timestamp_utc": self._now(),
                "signal_id": signal["signal_id"],
                "priority": signal["priority"],
                "pattern_detected": signal["pattern_detected"],
                "delivered": True,
                "delivery_target": "file_outbox",
                "webhook_configured": bool(self.webhook_url),
            },
        )
        return True

    async def _post_with_retry(self, signal: dict[str, Any]) -> bool:
        if not self._safe_transport(self.webhook_url):
            await asyncio.to_thread(
                self._append_outbound_log,
                {
                    "timestamp_utc": self._now(),
                    "signal_id": signal["signal_id"],
                    "delivered": False,
                    "error": "unsafe_transport_blocked",
                    "url_host": urlparse(self.webhook_url).netloc,
                },
            )
            return False
        for attempt in range(1, 4):
            try:
                await asyncio.to_thread(self._post_json, signal)
                await asyncio.to_thread(
                    self._append_outbound_log,
                    {
                        "timestamp_utc": self._now(),
                        "signal_id": signal["signal_id"],
                        "delivered": True,
                        "attempt": attempt,
                        "url_host": urlparse(self.webhook_url).netloc,
                    },
                )
                return True
            except Exception as error:
                await asyncio.to_thread(
                    self._append_outbound_log,
                    {
                        "timestamp_utc": self._now(),
                        "signal_id": signal["signal_id"],
                        "delivered": False,
                        "attempt": attempt,
                        "url_host": urlparse(self.webhook_url).netloc,
                        "error": repr(error),
                    },
                )
                await asyncio.sleep(0.25 * attempt)
        return False

    def _post_json(self, signal: dict[str, Any]) -> None:
        body = json.dumps(signal, sort_keys=True, separators=(",", ":")).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "X-Signal-Source": "INTEL_ENGINE",
        }
        if self.api_key:
            headers["X-Forja-Key"] = self.api_key
        request = Request(self.webhook_url, data=body, headers=headers, method="POST")
        try:
            with urlopen(request, timeout=10) as response:
                if response.status >= 400:
                    raise RuntimeError(f"HTTP {response.status}")
        except HTTPError as error:
            detail = error.read().decode("utf-8", errors="replace")[:300]
            raise RuntimeError(f"HTTP {error.code}: {detail}") from error
        except URLError as error:
            raise RuntimeError(f"network error: {error.reason}") from error

    @staticmethod
    def _write_outbox(signal: dict[str, Any]) -> None:
        FORJA_OUTBOX.mkdir(parents=True, exist_ok=True)
        safe_timestamp = datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
        safe_timestamp = safe_timestamp.replace(":", "").replace("-", "")
        outbox_path = FORJA_OUTBOX / f"{safe_timestamp}_signal_{uuid.uuid4().hex}.json"
        outbox_path.write_text(json.dumps(signal, indent=2, sort_keys=True), encoding="utf-8")

    @staticmethod
    def _validate_signal(signal: dict[str, Any]) -> dict[str, Any]:
        missing = sorted(REQUIRED_SIGNAL_FIELDS - set(signal))
        payload_text = json.dumps(signal, sort_keys=True, default=str)
        forbidden_found = OutputSanitizer.contains_forbidden_external_reference(payload_text)
        if missing or forbidden_found:
            return {
                "valid": False,
                "missing_fields": missing,
                "forbidden_source_reference": forbidden_found,
                "timestamp_utc": ForjaConnector._now(),
            }
        return {"valid": True, "timestamp_utc": ForjaConnector._now()}

    async def _ensure_ready(self) -> None:
        if self.database.connection is None:
            await self.database.connect()

    @staticmethod
    def _safe_transport(url: str) -> bool:
        parsed = urlparse(url)
        if parsed.scheme == "https":
            return True
        if parsed.scheme == "http" and parsed.hostname in {"127.0.0.1", "localhost"}:
            return True
        return False

    @staticmethod
    def _append_outbound_log(row: dict[str, Any]) -> None:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        with Path(FORJA_OUTBOUND_LOG).open("a", encoding="utf-8") as log_file:
            log_file.write(json.dumps(row, sort_keys=True, default=str) + "\n")

    @staticmethod
    def _now() -> str:
        return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
