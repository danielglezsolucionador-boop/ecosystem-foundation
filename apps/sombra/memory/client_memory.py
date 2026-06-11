from __future__ import annotations

from datetime import UTC, datetime
import json
import uuid
from typing import Any

from .database import DatabaseConnection


class ClientMemoryLayer:
    def __init__(self, database: DatabaseConnection) -> None:
        self.database = database

    async def create_client(self, client_data: dict[str, Any]) -> str:
        client_id = str(client_data.get("client_id") or uuid.uuid4())
        payload = {
            "client_name": str(client_data.get("client_name", "UNNAMED_CLIENT")),
            "industry_sector": str(client_data.get("industry_sector", "UNKNOWN")),
            "geography": str(client_data.get("geography", "UNKNOWN")),
            "risk_score": int(client_data.get("risk_score", 0)),
            "risk_trend": str(client_data.get("risk_trend", "STABLE")).upper(),
            "digital_assets": self._json(client_data.get("digital_assets", [])),
            "executive_registry": self._json(client_data.get("executive_registry", [])),
            "threat_history": self._json(client_data.get("threat_history", [])),
            "credential_history": self._json(client_data.get("credential_history", [])),
            "brand_registry": self._json(client_data.get("brand_registry", [])),
        }
        if self.database.backend == "postgresql":
            query = """
            INSERT INTO sombra_client_profiles (
              client_id, client_name, industry_sector, geography, risk_score,
              risk_trend, digital_assets, executive_registry, threat_history,
              credential_history, brand_registry
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7::jsonb, $8::jsonb, $9::jsonb, $10::jsonb, $11::jsonb)
            """
        else:
            query = """
            INSERT INTO sombra_client_profiles (
              client_id, client_name, industry_sector, geography, risk_score,
              risk_trend, digital_assets, executive_registry, threat_history,
              credential_history, brand_registry
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
            """
        await self.database.execute(
            query,
            client_id,
            payload["client_name"],
            payload["industry_sector"],
            payload["geography"],
            payload["risk_score"],
            payload["risk_trend"],
            payload["digital_assets"],
            payload["executive_registry"],
            payload["threat_history"],
            payload["credential_history"],
            payload["brand_registry"],
        )
        return client_id

    async def get_client(self, client_id: str) -> dict[str, Any]:
        row = await self.database.fetchrow(
            "SELECT * FROM sombra_client_profiles WHERE client_id = $1",
            client_id,
        )
        if row is None:
            return {}
        return self._decode_client(row)

    async def update_risk_score(self, client_id: str, score: int, trend: str) -> None:
        await self.database.execute(
            """
            UPDATE sombra_client_profiles
            SET risk_score = $1, risk_trend = $2, updated_at = $3
            WHERE client_id = $4
            """,
            self._clamp_score(score),
            trend.upper(),
            self._now(),
            client_id,
        )

    async def add_threat_to_history(self, client_id: str, threat: dict[str, Any]) -> None:
        await self._append_history(client_id, "threat_history", threat)

    async def add_credential_exposure(self, client_id: str, exposure: dict[str, Any]) -> None:
        await self._append_history(client_id, "credential_history", exposure)

    async def get_all_clients(self) -> list[dict[str, Any]]:
        rows = await self.database.fetch(
            "SELECT * FROM sombra_client_profiles ORDER BY client_name ASC"
        )
        return [self._decode_client(row) for row in rows]

    async def find_clients_by_sector(self, sector: str) -> list[dict[str, Any]]:
        rows = await self.database.fetch(
            """
            SELECT * FROM sombra_client_profiles
            WHERE LOWER(industry_sector) = LOWER($1)
            ORDER BY risk_score DESC, client_name ASC
            """,
            sector,
        )
        return [self._decode_client(row) for row in rows]

    async def _append_history(self, client_id: str, field_name: str, item: dict[str, Any]) -> None:
        if field_name not in {"threat_history", "credential_history"}:
            raise ValueError(f"unsupported history field: {field_name}")
        client = await self.get_client(client_id)
        if not client:
            raise ValueError(f"client not found: {client_id}")
        history = client.get(field_name, [])
        if not isinstance(history, list):
            history = []
        entry = dict(item)
        entry.setdefault("timestamp_utc", self._now())
        history.append(entry)
        cast = "::jsonb" if self.database.backend == "postgresql" else ""
        await self.database.execute(
            f"""
            UPDATE sombra_client_profiles
            SET {field_name} = $1{cast}, updated_at = $2
            WHERE client_id = $3
            """,
            self._json(history),
            self._now(),
            client_id,
        )

    @staticmethod
    def _json(value: Any) -> str:
        return json.dumps(value, ensure_ascii=True, sort_keys=True)

    @staticmethod
    def _decode_client(row: dict[str, Any]) -> dict[str, Any]:
        decoded = dict(row)
        for key in (
            "digital_assets",
            "executive_registry",
            "threat_history",
            "credential_history",
            "brand_registry",
        ):
            value = decoded.get(key)
            if isinstance(value, str):
                try:
                    decoded[key] = json.loads(value)
                except json.JSONDecodeError:
                    decoded[key] = value
        return decoded

    @staticmethod
    def _now() -> str:
        return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    @staticmethod
    def _clamp_score(score: int) -> int:
        return max(0, min(100, int(score)))
