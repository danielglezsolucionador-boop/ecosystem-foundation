from __future__ import annotations

import json
from typing import Any

from .client_memory import ClientMemoryLayer
from .database import DatabaseConnection
from .global_memory import GlobalMemoryLayer


class MemoryQueryEngine:
    def __init__(self, database: DatabaseConnection) -> None:
        self.database = database
        self.clients = ClientMemoryLayer(database)
        self.global_memory = GlobalMemoryLayer(database)

    async def search_by_keyword(self, keyword: str) -> list[dict[str, Any]]:
        pattern = f"%{keyword.strip()}%"
        rows = await self.database.fetch(
            """
            SELECT * FROM sombra_intel_global
            WHERE LOWER(findings) LIKE LOWER($1)
               OR LOWER(threat_type) LIKE LOWER($1)
               OR LOWER(severity) LIKE LOWER($1)
            ORDER BY threat_score DESC, timestamp_utc DESC
            """,
            pattern,
        )
        return [self._decode_intel(row) for row in rows]

    async def get_threat_summary(self) -> dict[str, Any]:
        severity_rows = await self.database.fetch(
            """
            SELECT severity, COUNT(*) AS count
            FROM sombra_intel_global
            GROUP BY severity
            ORDER BY count DESC
            """
        )
        type_rows = await self.database.fetch(
            """
            SELECT threat_type, COUNT(*) AS count
            FROM sombra_intel_global
            GROUP BY threat_type
            ORDER BY count DESC
            """
        )
        total_row = await self.database.fetchrow(
            """
            SELECT COUNT(*) AS total_intel_stored,
                   MIN(timestamp_utc) AS oldest_record,
                   MAX(timestamp_utc) AS newest_record
            FROM sombra_intel_global
            """
        )
        return {
            "counts_by_severity": {row["severity"]: int(row["count"]) for row in severity_rows},
            "counts_by_threat_type": {row["threat_type"]: int(row["count"]) for row in type_rows},
            "total_intel_stored": int((total_row or {}).get("total_intel_stored") or 0),
            "oldest_record": (total_row or {}).get("oldest_record"),
            "newest_record": (total_row or {}).get("newest_record"),
        }

    async def calculate_client_risk(self, client_id: str) -> int:
        client = await self.clients.get_client(client_id)
        if not client:
            raise ValueError(f"client not found: {client_id}")
        threat_history = client.get("threat_history", [])
        credential_history = client.get("credential_history", [])
        digital_assets = client.get("digital_assets", [])
        sector = str(client.get("industry_sector", "UNKNOWN"))
        sector_matches = await self.search_by_keyword(sector) if sector != "UNKNOWN" else []
        recent_threats = await self.global_memory.get_recent_threats(hours=168)
        max_recent_score = max((int(row.get("threat_score") or 0) for row in recent_threats), default=0)
        score = min(
            100,
            (len(threat_history) * 8)
            + (len(credential_history) * 10)
            + (len(digital_assets) * 2)
            + (len(sector_matches) * 6)
            + int(max_recent_score * 0.35),
        )
        previous_score = int(client.get("risk_score") or 0)
        trend = self._trend(previous_score, score)
        await self.clients.update_risk_score(client_id, score, trend)
        return score

    @staticmethod
    def _trend(previous_score: int, new_score: int) -> str:
        if new_score >= previous_score + 10:
            return "RISING"
        if new_score <= previous_score - 10:
            return "FALLING"
        return "STABLE"

    @staticmethod
    def _decode_intel(row: dict[str, Any]) -> dict[str, Any]:
        decoded = dict(row)
        for key in ("indicators", "routing", "prediction"):
            value = decoded.get(key)
            if isinstance(value, str):
                try:
                    decoded[key] = json.loads(value)
                except json.JSONDecodeError:
                    decoded[key] = value
        return decoded
