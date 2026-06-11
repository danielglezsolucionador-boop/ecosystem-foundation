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

from .sentinela_mask_validator import SentinelaMaskValidator


SENTINELA_OUTBOUND_LOG = LOG_DIR / "sentinela_outbound.log"
SENTINELA_OUTBOX = Path(__file__).resolve().parents[1] / "outbox" / "sentinela"


class SentinelaConnector:
    def __init__(
        self,
        database: DatabaseConnection | None = None,
        blackbox: BlackBoxAuditCore | None = None,
        mask_validator: SentinelaMaskValidator | None = None,
    ) -> None:
        self.database = database if database is not None else DatabaseConnection()
        self.blackbox = blackbox if blackbox is not None else BlackBoxAuditCore(self.database)
        self.mask_validator = (
            mask_validator
            if mask_validator is not None
            else SentinelaMaskValidator(self.database, self.blackbox)
        )
        self.webhook_url = os.getenv("SENTINELA_WEBHOOK_URL", "").strip()
        self.api_key = os.getenv("SENTINELA_API_KEY", "").strip()
        self._owns_connection = database is None

    async def disconnect(self) -> None:
        if self._owns_connection:
            await self.database.disconnect()

    async def deliver_intel(self, alert: Any) -> bool:
        await self._ensure_ready()
        payload = {
            "intel_id": str(getattr(alert, "alert_id", "")),
            "timestamp": self._now(),
            "source": "THREAT_INTELLIGENCE_ENGINE",
            "severity": str(getattr(alert, "severity", "")).upper(),
            "threat_type": str(getattr(alert, "threat_type", "")).upper(),
            "threat_score": int(getattr(alert, "threat_score", 0) or 0),
            "target_assets": list(getattr(alert, "target_assets", []) or []),
            "findings": str(getattr(alert, "findings", "")),
            "time_window": str(getattr(alert, "time_window", "")),
            "recommended_defense": str(getattr(alert, "recommended_action", "")),
            "forja_action_needed": bool(getattr(alert, "forja_construction_needed", False)),
            "source_classification": "CLASSIFIED",
            "intelligence_confidence": float(getattr(alert, "confidence_level", 0.0) or 0.0),
        }
        payload = OutputSanitizer.sanitize_external(payload)
        return await self._validated_delivery(
            payload,
            event_type="INTEL_DELIVERED_TO_SENTINELA",
            entity=str(getattr(alert, "alert_id", "UNKNOWN")),
            message_type="intel",
        )

    async def deliver_credential_alert(self, client_id: str, exposure_data: Any) -> bool:
        await self._ensure_ready()
        payload = {
            "alert_type": "CREDENTIAL_EXPOSURE",
            "severity": "CRITICAL",
            "client_id": str(client_id),
            "affected_assets": self._exposure_assets(exposure_data),
            "exposure_detected": self._now(),
            "recommended_action": "Force password reset immediately",
            "time_window": "0-2 hours",
            "source": "MONITORING_ENGINE",
            "source_classification": "CLASSIFIED",
        }
        payload = OutputSanitizer.sanitize_external(payload)
        return await self._validated_delivery(
            payload,
            event_type="CREDENTIAL_ALERT_DELIVERED_TO_SENTINELA",
            entity=str(client_id),
            message_type="credential_alert",
        )

    async def _validated_delivery(self, payload: dict[str, Any], event_type: str, entity: str, message_type: str) -> bool:
        validation = await self.mask_validator.validate(payload)
        if not validation.valid:
            await self.blackbox.log(
                "SENTINELA_DELIVERY_ABORTED",
                entity,
                {"reason": "mask_validation_failed", "violations": validation.violations},
                order_origin="SENTINELA_INTEGRATION",
            )
            await asyncio.to_thread(
                self._append_outbound_log,
                {
                    "timestamp_utc": self._now(),
                    "message_type": message_type,
                    "delivered": False,
                    "aborted": True,
                    "reason": "mask_validation_failed",
                    "violations": validation.violations,
                },
            )
            return False

        delivered = await self._deliver_or_outbox(payload, message_type)
        await self.blackbox.log(
            event_type,
            entity,
            {
                "delivered": delivered,
                "delivery_target": "webhook" if self.webhook_url else "file_outbox",
                "source": payload.get("source"),
            },
            order_origin="SENTINELA_INTEGRATION",
        )
        return delivered

    async def _deliver_or_outbox(self, payload: dict[str, Any], message_type: str) -> bool:
        if self.webhook_url:
            delivered = await self._post_with_retry(payload, message_type)
            if delivered:
                return True
        await asyncio.to_thread(self._write_outbox, payload, message_type)
        await asyncio.to_thread(
            self._append_outbound_log,
            {
                "timestamp_utc": self._now(),
                "message_type": message_type,
                "delivered": True,
                "delivery_target": "file_outbox",
                "webhook_configured": bool(self.webhook_url),
            },
        )
        return True

    async def _post_with_retry(self, payload: dict[str, Any], message_type: str) -> bool:
        if not self._safe_transport(self.webhook_url):
            await asyncio.to_thread(
                self._append_outbound_log,
                {
                    "timestamp_utc": self._now(),
                    "message_type": message_type,
                    "delivered": False,
                    "error": "unsafe_transport_blocked",
                    "url_host": urlparse(self.webhook_url).netloc,
                },
            )
            return False
        for attempt in range(1, 4):
            try:
                await asyncio.to_thread(self._post_json, payload)
                await asyncio.to_thread(
                    self._append_outbound_log,
                    {
                        "timestamp_utc": self._now(),
                        "message_type": message_type,
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
                        "message_type": message_type,
                        "delivered": False,
                        "attempt": attempt,
                        "url_host": urlparse(self.webhook_url).netloc,
                        "error": repr(error),
                    },
                )
                await asyncio.sleep(0.25 * attempt)
        return False

    def _post_json(self, payload: dict[str, Any]) -> None:
        body = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "X-Intel-Source": "CLASSIFIED",
        }
        if self.api_key:
            headers["X-Sentinela-Key"] = self.api_key
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
    def _write_outbox(payload: dict[str, Any], message_type: str) -> None:
        SENTINELA_OUTBOX.mkdir(parents=True, exist_ok=True)
        safe_timestamp = datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
        safe_timestamp = safe_timestamp.replace(":", "").replace("-", "")
        outbox_path = SENTINELA_OUTBOX / f"{safe_timestamp}_{message_type}_{uuid.uuid4().hex}.json"
        payload = OutputSanitizer.sanitize_external(payload)
        outbox_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

    @staticmethod
    def _append_outbound_log(row: dict[str, Any]) -> None:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        with Path(SENTINELA_OUTBOUND_LOG).open("a", encoding="utf-8") as log_file:
            log_file.write(json.dumps(row, sort_keys=True, default=str) + "\n")

    async def _ensure_ready(self) -> None:
        if self.database.connection is None:
            await self.database.connect()

    @staticmethod
    def _exposure_assets(exposure_data: Any) -> list[str]:
        if isinstance(exposure_data, dict):
            assets = exposure_data.get("assets", [])
        else:
            assets = getattr(exposure_data, "assets", [])
        if isinstance(assets, str):
            return [assets]
        return [str(asset) for asset in assets if str(asset).strip()]

    @staticmethod
    def _safe_transport(url: str) -> bool:
        parsed = urlparse(url)
        if parsed.scheme == "https":
            return True
        if parsed.scheme == "http" and parsed.hostname in {"127.0.0.1", "localhost"}:
            return True
        return False

    @staticmethod
    def _now() -> str:
        return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
