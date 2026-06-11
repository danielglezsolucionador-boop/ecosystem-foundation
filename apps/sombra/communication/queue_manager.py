from __future__ import annotations

import asyncio
from datetime import UTC, datetime
import json
import os
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
import uuid

from apps.sombra.memory import BlackBoxAuditCore, DatabaseConnection


QUEUE_SCHEMA = """
CREATE TABLE IF NOT EXISTS sombra_message_queue (
  queue_id TEXT PRIMARY KEY,
  message_id TEXT,
  recipient TEXT,
  priority TEXT,
  classification TEXT,
  payload TEXT,
  delivered INTEGER DEFAULT 0,
  delivery_attempts INTEGER DEFAULT 0,
  last_attempt TEXT,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_sombra_message_queue_priority
  ON sombra_message_queue(priority);

CREATE INDEX IF NOT EXISTS idx_sombra_message_queue_delivered
  ON sombra_message_queue(delivered);
"""


PRIORITY_ORDER = {
    "SUPREME": 0,
    "CRITICAL": 1,
    "HIGH": 2,
    "STANDARD": 3,
    "MEDIUM": 3,
    "LOW": 4,
}


class MessageQueueManager:
    def __init__(self, database: DatabaseConnection | None = None, blackbox: BlackBoxAuditCore | None = None) -> None:
        self.database = database if database is not None else DatabaseConnection()
        self.blackbox = blackbox if blackbox is not None else BlackBoxAuditCore(self.database)
        self._schema_ready = False
        self._owns_connection = database is None

    async def disconnect(self) -> None:
        if self._owns_connection:
            await self.database.disconnect()

    async def enqueue(self, message: Any, priority: str) -> str:
        await self._ensure_ready()
        queue_id = str(uuid.uuid4())
        message_dict = message.to_dict() if hasattr(message, "to_dict") else dict(message)
        await self.database.execute(
            """
            INSERT INTO sombra_message_queue (
              queue_id, message_id, recipient, priority, classification,
              payload, delivered, delivery_attempts, last_attempt
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            """,
            queue_id,
            str(message_dict.get("message_id", queue_id)),
            str(message_dict.get("recipient", "UNKNOWN")).upper(),
            self._normalize_priority(priority),
            str(message_dict.get("classification", "INTERNAL")).upper(),
            json.dumps(message_dict, ensure_ascii=True, sort_keys=True),
            int(bool(message_dict.get("delivered", False))),
            int(message_dict.get("delivery_attempts", 0)),
            str(message_dict.get("last_attempt", "")),
        )
        await self.blackbox.log(
            "MESSAGE_QUEUED",
            queue_id,
            {
                "message_id": message_dict.get("message_id"),
                "recipient": message_dict.get("recipient"),
                "priority": self._normalize_priority(priority),
            },
            order_origin="COMMUNICATION_QUEUE",
        )
        return queue_id

    async def dequeue_by_priority(self) -> list[dict[str, Any]]:
        await self._ensure_ready()
        rows = await self.database.fetch(
            """
            SELECT * FROM sombra_message_queue
            WHERE delivered = 0
            ORDER BY
              CASE priority
                WHEN 'SUPREME' THEN 0
                WHEN 'CRITICAL' THEN 1
                WHEN 'HIGH' THEN 2
                WHEN 'STANDARD' THEN 3
                WHEN 'MEDIUM' THEN 3
                ELSE 4
              END,
              created_at ASC
            """
        )
        return [self._decode_row(row) for row in rows]

    async def retry_failed(self, max_attempts: int = 3) -> list[dict[str, Any]]:
        await self._ensure_ready()
        rows = await self.database.fetch(
            """
            SELECT * FROM sombra_message_queue
            WHERE delivered = 0 AND delivery_attempts < $1
            ORDER BY created_at ASC
            """,
            int(max_attempts),
        )
        retried: list[dict[str, Any]] = []
        for row in rows:
            decoded = self._decode_row(row)
            attempts = int(decoded.get("delivery_attempts") or 0) + 1
            now = self._now()
            delivered = await self._attempt_delivery(decoded)
            await self.database.execute(
                """
                UPDATE sombra_message_queue
                SET delivery_attempts = $1, last_attempt = $2, delivered = $3
                WHERE queue_id = $4
                """,
                attempts,
                now,
                int(delivered),
                decoded["queue_id"],
            )
            await self.blackbox.log(
                "MESSAGE_RETRY_DELIVERED" if delivered else "MESSAGE_RETRY_SCHEDULED",
                decoded["queue_id"],
                {"message_id": decoded.get("message_id"), "attempts": attempts, "delivered": delivered},
                order_origin="COMMUNICATION_QUEUE",
            )
            decoded["delivery_attempts"] = attempts
            decoded["last_attempt"] = now
            decoded["delivered"] = int(delivered)
            retried.append(decoded)
        return retried

    async def get_queue_stats(self) -> dict[str, Any]:
        await self._ensure_ready()
        total_pending = await self.database.fetchrow(
            "SELECT COUNT(*) AS count FROM sombra_message_queue WHERE delivered = 0"
        )
        priority_rows = await self.database.fetch(
            """
            SELECT priority, COUNT(*) AS count
            FROM sombra_message_queue
            WHERE delivered = 0
            GROUP BY priority
            """
        )
        failed = await self.database.fetchrow(
            """
            SELECT COUNT(*) AS count
            FROM sombra_message_queue
            WHERE delivered = 0 AND delivery_attempts >= 3
            """
        )
        delivered_today = await self.database.fetchrow(
            """
            SELECT COUNT(*) AS count
            FROM sombra_message_queue
            WHERE delivered = 1 AND date(last_attempt) = date('now')
            """
        )
        return {
            "total_pending_count": int((total_pending or {}).get("count") or 0),
            "count_by_priority": {row["priority"]: int(row["count"]) for row in priority_rows},
            "failed_count": int((failed or {}).get("count") or 0),
            "delivered_today_count": int((delivered_today or {}).get("count") or 0),
        }

    async def _ensure_ready(self) -> None:
        if self.database.connection is None:
            await self.database.connect()
        if self._schema_ready:
            return
        if self.database.backend == "sqlite":
            async with self.database._sqlite_lock:
                await self.database.connection.executescript(QUEUE_SCHEMA)
                await self.database.connection.commit()
        else:
            statements = [statement.strip() for statement in QUEUE_SCHEMA.split(";") if statement.strip()]
            for statement in statements:
                await self.database.execute(statement)
        self._schema_ready = True

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
    def _normalize_priority(priority: str) -> str:
        normalized = str(priority or "STANDARD").upper()
        return normalized if normalized in PRIORITY_ORDER else "STANDARD"

    async def _attempt_delivery(self, queued_message: dict[str, Any]) -> bool:
        webhook_url = self._webhook_for_recipient(str(queued_message.get("recipient", "")))
        if not webhook_url:
            return False
        try:
            await asyncio.to_thread(self._post_webhook, webhook_url, queued_message.get("payload", {}))
        except Exception:
            return False
        return True

    @staticmethod
    def _webhook_for_recipient(recipient: str) -> str | None:
        env_map = {
            "CEREBRO": "CEREBRO_WEBHOOK_URL",
            "SENTINELA": "SENTINELA_WEBHOOK_URL",
            "FORJA": "FORJA_WEBHOOK_URL",
        }
        key = env_map.get(recipient.upper())
        return os.getenv(key) if key else None

    @staticmethod
    def _post_webhook(url: str, payload: Any) -> None:
        body = json.dumps(payload, ensure_ascii=True).encode("utf-8")
        request = Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST")
        try:
            with urlopen(request, timeout=15) as response:
                if response.status >= 300:
                    raise RuntimeError(f"queue webhook returned status {response.status}")
        except HTTPError as error:
            raise RuntimeError(f"queue webhook HTTP {error.code}") from error
        except URLError as error:
            raise RuntimeError(f"queue webhook network error: {error.reason}") from error

    @staticmethod
    def _now() -> str:
        return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
