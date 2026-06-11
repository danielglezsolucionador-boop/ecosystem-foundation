from __future__ import annotations

import asyncio
from datetime import UTC, datetime
import json
import os
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from apps.sombra.memory import BlackBoxAuditCore, DatabaseConnection
from apps.sombra.memory.database import LOG_DIR

from .models import OutboundMessage
from .queue_manager import MessageQueueManager


OUTBOUND_LOG = LOG_DIR / "outbound.log"

OUTBOUND_SCHEMA = """
CREATE TABLE IF NOT EXISTS sombra_outbound_queue (
  message_id TEXT PRIMARY KEY,
  timestamp_utc TEXT,
  sender TEXT,
  recipient TEXT,
  priority TEXT,
  classification TEXT,
  payload TEXT,
  hash_sha256 TEXT,
  delivered INTEGER DEFAULT 0,
  delivery_attempts INTEGER DEFAULT 0,
  last_attempt TEXT
);

CREATE INDEX IF NOT EXISTS idx_sombra_outbound_queue_delivered
  ON sombra_outbound_queue(delivered);
"""


class OutboundTransmissionEngine:
    def __init__(self, database: DatabaseConnection | None = None, blackbox: BlackBoxAuditCore | None = None) -> None:
        self.database = database if database is not None else DatabaseConnection()
        self.blackbox = blackbox if blackbox is not None else BlackBoxAuditCore(self.database)
        self.queue = MessageQueueManager(self.database, self.blackbox)
        self._schema_ready = False
        self._owns_connection = database is None

    async def disconnect(self) -> None:
        if self._owns_connection:
            await self.database.disconnect()

    async def transmit_to_cerebro(self, payload: dict[str, Any], priority: str) -> OutboundMessage:
        message = OutboundMessage(
            recipient="CEREBRO",
            priority=priority,
            classification="INTERNAL_COMMAND_INTELLIGENCE",
            payload=self._mask_payload(payload, preserve_sombra=True),
        )
        await self._persist_and_attempt(message, os.getenv("CEREBRO_WEBHOOK_URL"))
        return message

    async def transmit_to_sentinela(self, intel: dict[str, Any]) -> OutboundMessage:
        clean_payload = self._strip_sombra_references(intel)
        clean_payload["source"] = "THREAT_INTELLIGENCE_ENGINE"
        message = OutboundMessage(
            recipient="SENTINELA",
            priority=str(clean_payload.get("priority", "HIGH")),
            classification="ACTIONABLE_THREAT_INTELLIGENCE",
            payload=clean_payload,
        )
        await self._persist_and_attempt(message, os.getenv("SENTINELA_WEBHOOK_URL"))
        return message

    async def transmit_to_forja(self, signal: dict[str, Any]) -> OutboundMessage:
        clean_payload = self._strip_sombra_references(signal)
        clean_payload["source"] = "THREAT_INTELLIGENCE_ENGINE"
        message = OutboundMessage(
            recipient="FORJA",
            priority=str(clean_payload.get("priority", "STANDARD")),
            classification="CONSTRUCTION_SIGNAL",
            payload=clean_payload,
        )
        await self._persist_and_attempt(message, os.getenv("FORJA_WEBHOOK_URL"))
        return message

    async def get_pending_messages(self) -> list[dict[str, Any]]:
        await self._ensure_ready()
        rows = await self.database.fetch(
            """
            SELECT * FROM sombra_outbound_queue
            WHERE delivered = 0
            ORDER BY timestamp_utc ASC
            """
        )
        return [self._decode_row(row) for row in rows]

    async def mark_delivered(self, message_id: str) -> None:
        await self._ensure_ready()
        await self.database.execute(
            """
            UPDATE sombra_outbound_queue
            SET delivered = 1, last_attempt = $1
            WHERE message_id = $2
            """,
            self._now(),
            message_id,
        )
        await self.database.execute(
            """
            UPDATE sombra_message_queue
            SET delivered = 1, last_attempt = $1
            WHERE message_id = $2
            """,
            self._now(),
            message_id,
        )
        await self.blackbox.log(
            "OUTBOUND_MARKED_DELIVERED",
            message_id,
            {"message_id": message_id},
            order_origin="COMMUNICATION_LAYER",
        )

    async def _persist_and_attempt(self, message: OutboundMessage, webhook_url: str | None) -> None:
        await self._ensure_ready()
        await self._insert_outbound(message)
        await self.queue.enqueue(message, message.priority)
        delivery = await self._attempt_delivery(message, webhook_url)
        await self.blackbox.log(
            "OUTBOUND_TRANSMISSION",
            message.message_id,
            {
                "recipient": message.recipient,
                "priority": message.priority,
                "delivered": delivery["delivered"],
                "webhook_configured": bool(webhook_url),
                "delivery_error": delivery.get("error"),
            },
            order_origin="COMMUNICATION_LAYER",
        )
        await asyncio.to_thread(self._append_outbound_log, message, delivery)

    async def _insert_outbound(self, message: OutboundMessage) -> None:
        await self.database.execute(
            """
            INSERT INTO sombra_outbound_queue (
              message_id, timestamp_utc, sender, recipient, priority,
              classification, payload, hash_sha256, delivered,
              delivery_attempts, last_attempt
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
            """,
            message.message_id,
            message.timestamp_utc,
            message.sender,
            message.recipient,
            message.priority,
            message.classification,
            json.dumps(message.payload, ensure_ascii=True, sort_keys=True),
            message.hash_sha256,
            int(message.delivered),
            message.delivery_attempts,
            message.last_attempt,
        )

    async def _attempt_delivery(self, message: OutboundMessage, webhook_url: str | None) -> dict[str, Any]:
        if not webhook_url:
            return {"delivered": False, "error": "webhook_not_configured"}
        message.delivery_attempts += 1
        message.last_attempt = self._now()
        try:
            await asyncio.to_thread(self._post_webhook, webhook_url, message.to_dict())
        except Exception as error:
            await self._update_delivery_attempt(message, delivered=False)
            return {"delivered": False, "error": repr(error)}
        message.delivered = True
        await self._update_delivery_attempt(message, delivered=True)
        return {"delivered": True}

    async def _update_delivery_attempt(self, message: OutboundMessage, delivered: bool) -> None:
        await self.database.execute(
            """
            UPDATE sombra_outbound_queue
            SET delivered = $1, delivery_attempts = $2, last_attempt = $3
            WHERE message_id = $4
            """,
            int(delivered),
            message.delivery_attempts,
            message.last_attempt,
            message.message_id,
        )
        await self.database.execute(
            """
            UPDATE sombra_message_queue
            SET delivered = $1, delivery_attempts = $2, last_attempt = $3
            WHERE message_id = $4
            """,
            int(delivered),
            message.delivery_attempts,
            message.last_attempt,
            message.message_id,
        )

    async def _ensure_ready(self) -> None:
        if self.database.connection is None:
            await self.database.connect()
        if self._schema_ready:
            return
        if self.database.backend == "sqlite":
            async with self.database._sqlite_lock:
                await self.database.connection.executescript(OUTBOUND_SCHEMA)
                await self.database.connection.commit()
        else:
            statements = [statement.strip() for statement in OUTBOUND_SCHEMA.split(";") if statement.strip()]
            for statement in statements:
                await self.database.execute(statement)
        self._schema_ready = True

    @staticmethod
    def _post_webhook(url: str, payload: dict[str, Any]) -> None:
        body = json.dumps(payload, ensure_ascii=True).encode("utf-8")
        request = Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST")
        try:
            with urlopen(request, timeout=15) as response:
                if response.status >= 300:
                    raise RuntimeError(f"webhook returned status {response.status}")
        except HTTPError as error:
            raise RuntimeError(f"webhook HTTP {error.code}") from error
        except URLError as error:
            raise RuntimeError(f"webhook network error: {error.reason}") from error

    @staticmethod
    def _strip_sombra_references(value: Any) -> Any:
        if isinstance(value, dict):
            cleaned: dict[str, Any] = {}
            for key, item in value.items():
                key_text = str(key)
                if "sombra" in key_text.lower() or key_text.lower() in {"source_visibility"}:
                    continue
                cleaned[key_text] = OutboundTransmissionEngine._strip_sombra_references(item)
            return cleaned
        if isinstance(value, list):
            return [OutboundTransmissionEngine._strip_sombra_references(item) for item in value]
        if isinstance(value, str):
            return value.replace("SOMBRA", "THREAT_INTELLIGENCE_ENGINE").replace("sombra", "threat_intelligence_engine")
        return value

    @staticmethod
    def _mask_payload(payload: dict[str, Any], preserve_sombra: bool) -> dict[str, Any]:
        copied = dict(payload)
        if not preserve_sombra:
            return OutboundTransmissionEngine._strip_sombra_references(copied)
        return copied

    @staticmethod
    def _decode_row(row: dict[str, Any]) -> dict[str, Any]:
        decoded = dict(row)
        payload = decoded.get("payload")
        if isinstance(payload, str):
            try:
                decoded["payload"] = json.loads(payload)
            except json.JSONDecodeError:
                decoded["payload"] = payload
        return decoded

    @staticmethod
    def _append_outbound_log(message: OutboundMessage, delivery: dict[str, Any]) -> None:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        row = {
            "timestamp_utc": OutboundTransmissionEngine._now(),
            "message_id": message.message_id,
            "recipient": message.recipient,
            "priority": message.priority,
            "delivered": delivery["delivered"],
            "error": delivery.get("error"),
        }
        with Path(OUTBOUND_LOG).open("a", encoding="utf-8") as log_file:
            log_file.write(json.dumps(row, sort_keys=True) + "\n")

    @staticmethod
    def _now() -> str:
        return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
