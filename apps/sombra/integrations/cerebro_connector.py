from __future__ import annotations

import asyncio
import base64
from datetime import UTC, datetime
import hashlib
import hmac
import json
import os
from pathlib import Path
from typing import Any
import uuid
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from cryptography.fernet import Fernet

from apps.sombra.memory import BlackBoxAuditCore, DatabaseConnection
from apps.sombra.memory.database import LOG_DIR
from apps.sombra.monitoring import SombraHealthMonitor, SombraMetrics
from apps.sombra.security import LockdownProtocol

from .cerebro_report_formatter import CerebroReportFormatter


CEREBRO_OUTBOUND_LOG = LOG_DIR / "cerebro_outbound.log"
CEREBRO_OUTBOX = Path(__file__).resolve().parents[1] / "outbox" / "cerebro"


class CerebroConnector:
    def __init__(
        self,
        database: DatabaseConnection | None = None,
        blackbox: BlackBoxAuditCore | None = None,
        health_monitor: SombraHealthMonitor | None = None,
        metrics: SombraMetrics | None = None,
        lockdown: LockdownProtocol | None = None,
    ) -> None:
        self.database = database if database is not None else DatabaseConnection()
        self.blackbox = blackbox if blackbox is not None else BlackBoxAuditCore(self.database)
        self.health_monitor = health_monitor if health_monitor is not None else SombraHealthMonitor()
        self.metrics = metrics if metrics is not None else SombraMetrics(self.database)
        self.lockdown = lockdown if lockdown is not None else LockdownProtocol(self.database, self.blackbox)
        self.webhook_url = os.getenv("CEREBRO_WEBHOOK_URL", "").strip()
        self.cerebro_api_key = os.getenv("CEREBRO_API_KEY", "").strip()
        self.sombra_api_key = os.getenv("SOMBRA_API_KEY", "").strip()
        self._owns_connection = database is None

    async def disconnect(self) -> None:
        if self._owns_connection:
            await self.database.disconnect()

    async def send_intel_report(self, alert: Any) -> bool:
        await self._ensure_ready()
        payload = CerebroReportFormatter.format_intel_report(alert)
        destination = self.webhook_url
        delivered = await self._deliver_or_outbox(payload, destination, "intel")
        await self.blackbox.log(
            "INTEL_TRANSMITTED_TO_CEREBRO",
            str(getattr(alert, "alert_id", "UNKNOWN")),
            {
                "delivered": delivered,
                "classification": payload["classification"],
                "threat_type": payload["threat_type"],
                "outbox_fallback": not bool(destination),
            },
            order_origin="CEREBRO_INTEGRATION",
        )
        return delivered

    async def send_heartbeat(self) -> bool:
        await self._ensure_ready()
        modules_health = await self.health_monitor.check_all_modules()
        status = self._overall_status_from_health(modules_health)
        daily_summary = await self.metrics.get_daily_summary()
        payload = CerebroReportFormatter.format_heartbeat(
            status=status,
            intel_processed_today=daily_summary["intel_processed_today"],
            alerts_sent_today=daily_summary["alerts_generated_today"],
            lockdown_level=self.lockdown.get_current_level(),
        )
        destination = self._join_webhook_path(self.webhook_url, "heartbeat") if self.webhook_url else ""
        delivered = await self._deliver_or_outbox(payload, destination, "heartbeat")
        await self.blackbox.log(
            "HEARTBEAT_TRANSMITTED_TO_CEREBRO",
            "CEREBRO_HEARTBEAT",
            {
                "delivered": delivered,
                "status": status,
                "outbox_fallback": not bool(destination),
            },
            order_origin="CEREBRO_INTEGRATION",
        )
        return delivered

    async def _deliver_or_outbox(self, payload: dict[str, Any], destination: str, message_type: str) -> bool:
        if destination:
            delivered = await self._post_with_retry(destination, payload, message_type)
            if delivered:
                return True
        await self._write_outbox(payload, message_type, "CEREBRO_WEBHOOK_NOT_CONFIGURED" if not destination else "CEREBRO_DELIVERY_FAILED")
        return False

    async def _post_with_retry(self, url: str, payload: dict[str, Any], message_type: str) -> bool:
        if not self._safe_transport(url):
            await asyncio.to_thread(
                self._append_outbound_log,
                {
                    "timestamp_utc": self._now(),
                    "message_type": message_type,
                    "delivered": False,
                    "error": "unsafe_transport_blocked",
                    "url_host": urlparse(url).netloc,
                },
            )
            return False
        for attempt in range(1, 4):
            try:
                await asyncio.to_thread(self._post_json, url, payload)
                await asyncio.to_thread(
                    self._append_outbound_log,
                    {
                        "timestamp_utc": self._now(),
                        "message_type": message_type,
                        "delivered": True,
                        "attempt": attempt,
                        "url_host": urlparse(url).netloc,
                    },
                )
                return True
            except Exception as error:
                await asyncio.to_thread(
                    self._append_outbound_log,
                    {
                        "timestamp_utc": self._now(),
                        "message_type": message_type,
                        "delivered": False,
                        "attempt": attempt,
                        "url_host": urlparse(url).netloc,
                        "error": repr(error),
                    },
                )
                await asyncio.sleep(0.25 * attempt)
        return False

    def _post_json(self, url: str, payload: dict[str, Any]) -> None:
        body = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "X-Sombra-Key": self.sombra_api_key,
            "X-Cerebro-Signature": self._signature(body),
        }
        if self.cerebro_api_key:
            headers["X-Cerebro-Key"] = self.cerebro_api_key
        request = Request(url, data=body, headers=headers, method="POST")
        try:
            with urlopen(request, timeout=10) as response:
                if response.status >= 400:
                    raise RuntimeError(f"HTTP {response.status}")
        except HTTPError as error:
            detail = error.read().decode("utf-8", errors="replace")[:300]
            raise RuntimeError(f"HTTP {error.code}: {detail}") from error
        except URLError as error:
            raise RuntimeError(f"network error: {error.reason}") from error

    async def _write_outbox(self, payload: dict[str, Any], message_type: str, reason: str) -> None:
        encrypted_payload = self._encrypted_outbox_payload(payload)
        row = {
            "timestamp_utc": self._now(),
            "message_type": message_type,
            "reason": reason,
            **encrypted_payload,
        }
        await asyncio.to_thread(self._write_outbox_sync, row, message_type)
        await asyncio.to_thread(
            self._append_outbound_log,
            {
                "timestamp_utc": row["timestamp_utc"],
                "message_type": message_type,
                "delivered": False,
                "fallback": "file_outbox",
                "reason": reason,
            },
        )

    @staticmethod
    def _write_outbox_sync(row: dict[str, Any], message_type: str) -> None:
        CEREBRO_OUTBOX.mkdir(parents=True, exist_ok=True)
        safe_timestamp = str(row["timestamp_utc"]).replace(":", "").replace("-", "")
        outbox_path = CEREBRO_OUTBOX / f"{safe_timestamp}_{message_type}_{uuid.uuid4().hex}.json"
        outbox_path.write_text(json.dumps(row, indent=2, sort_keys=True), encoding="utf-8")

    def _signature(self, body: bytes) -> str:
        key = self.sombra_api_key or self.cerebro_api_key
        if not key:
            return ""
        return hmac.new(key.encode("utf-8"), body, hashlib.sha256).hexdigest()

    def _encrypted_outbox_payload(self, payload: dict[str, Any]) -> dict[str, Any]:
        payload_bytes = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        payload_hash = hashlib.sha256(payload_bytes).hexdigest()
        key_material = self.sombra_api_key or self.cerebro_api_key
        if not key_material:
            return {
                "encrypted": False,
                "payload_redacted": True,
                "payload_sha256": payload_hash,
                "encryption_error": "missing_encryption_key",
            }
        fernet_key = base64.urlsafe_b64encode(hashlib.sha256(key_material.encode("utf-8")).digest())
        encrypted_payload = Fernet(fernet_key).encrypt(payload_bytes).decode("utf-8")
        return {
            "encrypted": True,
            "encryption": "fernet_sha256_derived_key",
            "payload_sha256": payload_hash,
            "encrypted_payload": encrypted_payload,
        }

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
    def _join_webhook_path(base_url: str, path: str) -> str:
        return f"{base_url.rstrip('/')}/{path.lstrip('/')}"

    @staticmethod
    def _overall_status_from_health(modules_health: dict[str, dict[str, Any]]) -> str:
        statuses = [row["status"] for row in modules_health.values()]
        if "DOWN" in statuses:
            return "CRITICAL"
        if "DEGRADED" in statuses:
            return "DEGRADED"
        return "OPERATIONAL"

    @staticmethod
    def _append_outbound_log(row: dict[str, Any]) -> None:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        with Path(CEREBRO_OUTBOUND_LOG).open("a", encoding="utf-8") as log_file:
            log_file.write(json.dumps(row, sort_keys=True, default=str) + "\n")

    @staticmethod
    def _now() -> str:
        return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
