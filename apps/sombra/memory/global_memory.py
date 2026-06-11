from __future__ import annotations

from datetime import UTC, datetime
import hashlib
import json
import uuid
from typing import Any

from .database import DatabaseConnection


class GlobalMemoryLayer:
    def __init__(self, database: DatabaseConnection) -> None:
        self.database = database

    async def store_intel(self, classified_intel: Any, score: Any, prediction: Any) -> str:
        record_id = str(uuid.uuid4())
        prediction_payload = self._to_dict(prediction)
        prediction_payload["memory_hash_sha256"] = self._hash_record(classified_intel, score, prediction_payload)
        indicators = list(getattr(classified_intel, "affected_assets", []))
        routing = list(getattr(classified_intel, "routing", []))
        args = (
            record_id,
            self._timestamp(getattr(classified_intel, "timestamp_utc", None)),
            str(getattr(classified_intel, "threat_type", "INTELLIGENCE_TREND")).upper(),
            str(getattr(classified_intel, "severity", "MEDIUM")).upper(),
            float(getattr(classified_intel, "confidence", 0.0)),
            str(getattr(classified_intel, "findings", "")),
            str(getattr(classified_intel, "source_category", "ANALYSIS")),
            float(getattr(classified_intel, "source_reliability", getattr(classified_intel, "confidence", 0.0))),
            json.dumps(indicators, sort_keys=True),
            json.dumps(routing, sort_keys=True),
            int(getattr(score, "final", 0)),
            json.dumps(prediction_payload, sort_keys=True),
        )
        if self.database.backend == "postgresql":
            query = """
            INSERT INTO sombra_intel_global (
              id, timestamp_utc, threat_type, severity, confidence, findings,
              source_category, source_reliability, indicators, routing,
              threat_score, prediction
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9::jsonb, $10::jsonb, $11, $12::jsonb)
            """
        else:
            query = """
            INSERT INTO sombra_intel_global (
              id, timestamp_utc, threat_type, severity, confidence, findings,
              source_category, source_reliability, indicators, routing,
              threat_score, prediction
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
            """
        await self.database.execute(query, *args)
        return record_id

    async def get_recent_threats(self, hours: int = 24) -> list[dict[str, Any]]:
        if self.database.backend == "postgresql":
            rows = await self.database.fetch(
                """
                SELECT * FROM sombra_intel_global
                WHERE timestamp_utc >= NOW() - ($1 * INTERVAL '1 hour')
                ORDER BY threat_score DESC
                """,
                int(hours),
            )
        else:
            rows = await self.database.fetch(
                """
                SELECT * FROM sombra_intel_global
                WHERE datetime(timestamp_utc) >= datetime('now', $1)
                ORDER BY threat_score DESC
                """,
                f"-{int(hours)} hours",
            )
        return [self._decode_row(row) for row in rows]

    async def get_by_threat_type(self, threat_type: str) -> list[dict[str, Any]]:
        rows = await self.database.fetch(
            """
            SELECT * FROM sombra_intel_global
            WHERE threat_type = $1
            ORDER BY threat_score DESC, timestamp_utc DESC
            """,
            threat_type.upper(),
        )
        return [self._decode_row(row) for row in rows]

    async def update_aging_flags(self) -> None:
        if self.database.backend == "postgresql":
            await self.database.execute(
                """
                UPDATE sombra_intel_global
                SET aging_status = 'HISTORICAL'
                WHERE created_at < NOW() - INTERVAL '180 days'
                """
            )
            await self.database.execute(
                """
                UPDATE sombra_intel_global
                SET aging_status = 'AGING'
                WHERE created_at < NOW() - INTERVAL '90 days'
                  AND created_at >= NOW() - INTERVAL '180 days'
                """
            )
            return
        await self.database.execute(
            """
            UPDATE sombra_intel_global
            SET aging_status = 'HISTORICAL'
            WHERE datetime(created_at) < datetime('now', '-180 days')
            """
        )
        await self.database.execute(
            """
            UPDATE sombra_intel_global
            SET aging_status = 'AGING'
            WHERE datetime(created_at) < datetime('now', '-90 days')
              AND datetime(created_at) >= datetime('now', '-180 days')
            """
        )

    async def get_pattern_history(self, threat_type: str) -> list[dict[str, Any]]:
        rows = await self.database.fetch(
            """
            SELECT * FROM sombra_intel_global
            WHERE threat_type = $1
            ORDER BY timestamp_utc DESC
            LIMIT 200
            """,
            threat_type.upper(),
        )
        return [self._decode_row(row) for row in rows]

    @staticmethod
    def _hash_record(classified_intel: Any, score: Any, prediction_payload: dict[str, Any]) -> str:
        payload = {
            "intel_id": getattr(classified_intel, "intel_id", ""),
            "threat_type": getattr(classified_intel, "threat_type", ""),
            "severity": getattr(classified_intel, "severity", ""),
            "findings": getattr(classified_intel, "findings", ""),
            "score": getattr(score, "final", 0),
            "prediction": prediction_payload,
        }
        return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()

    @staticmethod
    def _timestamp(value: Any) -> str:
        if value:
            return str(value)
        return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    @staticmethod
    def _to_dict(value: Any) -> dict[str, Any]:
        if hasattr(value, "to_dict"):
            return value.to_dict()
        if isinstance(value, dict):
            return dict(value)
        return {"value": str(value)}

    @staticmethod
    def _decode_row(row: dict[str, Any]) -> dict[str, Any]:
        decoded = dict(row)
        for key in ("indicators", "routing", "prediction"):
            value = decoded.get(key)
            if isinstance(value, str):
                try:
                    decoded[key] = json.loads(value)
                except json.JSONDecodeError:
                    decoded[key] = value
        return decoded
