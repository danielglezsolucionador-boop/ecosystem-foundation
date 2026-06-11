from __future__ import annotations

from datetime import UTC, datetime
import hashlib
import json
import uuid
from typing import Any

from .database import DatabaseConnection


class BlackBoxAuditCore:
    def __init__(self, database: DatabaseConnection) -> None:
        self.database = database

    async def log(self, event_type: str, entity: str, detail: dict[str, Any], **kwargs: Any) -> str:
        record_id = str(uuid.uuid4())
        timestamp = self._now()
        order_origin = str(kwargs.get("order_origin", "SYSTEM"))
        rule_suspended = str(kwargs.get("rule_suspended", "")) or None
        detail_payload = dict(detail)
        detail_payload.setdefault("immutable", True)
        detail_json = json.dumps(detail_payload, ensure_ascii=True, sort_keys=True)
        hash_sha256 = self._hash_event(record_id, timestamp, event_type, entity, detail_payload, order_origin)
        if self.database.backend == "postgresql":
            query = """
            INSERT INTO sombra_blackbox (
              id, timestamp_utc, event_type, entity, detail,
              order_origin, rule_suspended, hash_sha256
            )
            VALUES ($1, $2, $3, $4, $5::jsonb, $6, $7, $8)
            """
        else:
            query = """
            INSERT INTO sombra_blackbox (
              id, timestamp_utc, event_type, entity, detail,
              order_origin, rule_suspended, hash_sha256
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            """
        await self.database.execute(
            query,
            record_id,
            timestamp,
            event_type.upper(),
            entity,
            detail_json,
            order_origin.upper(),
            rule_suspended,
            hash_sha256,
        )
        return record_id

    async def get_ceo_audit_trail(self, limit: int = 100) -> list[dict[str, Any]]:
        rows = await self.database.fetch(
            """
            SELECT * FROM sombra_blackbox
            ORDER BY timestamp_utc DESC
            LIMIT $1
            """,
            max(1, min(1000, int(limit))),
        )
        return [self._decode_row(row) for row in rows]

    @staticmethod
    def _hash_event(
        record_id: str,
        timestamp: str,
        event_type: str,
        entity: str,
        detail: dict[str, Any],
        order_origin: str,
    ) -> str:
        payload = {
            "id": record_id,
            "timestamp_utc": timestamp,
            "event_type": event_type,
            "entity": entity,
            "detail": detail,
            "order_origin": order_origin,
        }
        return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()

    @staticmethod
    def _decode_row(row: dict[str, Any]) -> dict[str, Any]:
        decoded = dict(row)
        detail = decoded.get("detail")
        if isinstance(detail, str):
            try:
                decoded["detail"] = json.loads(detail)
            except json.JSONDecodeError:
                decoded["detail"] = detail
        return decoded

    @staticmethod
    def _now() -> str:
        return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
