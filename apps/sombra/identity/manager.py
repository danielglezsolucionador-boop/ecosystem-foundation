from __future__ import annotations

import json
from typing import Any

from apps.sombra.memory import BlackBoxAuditCore, DatabaseConnection

from .models import OperationalIdentity, utc_now_iso


IDENTITY_SCHEMA = """
CREATE TABLE IF NOT EXISTS sombra_identities (
  identity_id TEXT PRIMARY KEY,
  codename TEXT,
  username TEXT,
  creation_date TEXT,
  status TEXT,
  nationality TEXT,
  apparent_skill_level TEXT,
  language_primary TEXT,
  writing_style TEXT,
  timezone_apparent TEXT,
  activity_hours TEXT,
  community TEXT,
  current_phase TEXT,
  reputation_score REAL,
  risk_score INTEGER,
  last_active TEXT,
  requires_ceo_authorization INTEGER,
  ceo_authorized INTEGER,
  ceo_authorization_date TEXT,
  cooling_period_days INTEGER
);

CREATE INDEX IF NOT EXISTS idx_sombra_identities_status
  ON sombra_identities(status);

CREATE INDEX IF NOT EXISTS idx_sombra_identities_community
  ON sombra_identities(community);
"""


IDENTITY_FIELDS = (
    "identity_id",
    "codename",
    "username",
    "creation_date",
    "status",
    "nationality",
    "apparent_skill_level",
    "language_primary",
    "writing_style",
    "timezone_apparent",
    "activity_hours",
    "community",
    "current_phase",
    "reputation_score",
    "risk_score",
    "last_active",
    "requires_ceo_authorization",
    "ceo_authorized",
    "ceo_authorization_date",
    "cooling_period_days",
)


class IdentityManager:
    def __init__(self, database: DatabaseConnection | None = None, blackbox: BlackBoxAuditCore | None = None) -> None:
        self.database = database if database is not None else DatabaseConnection()
        self.blackbox = blackbox if blackbox is not None else BlackBoxAuditCore(self.database)
        self._schema_ready = False
        self._owns_connection = database is None

    async def disconnect(self) -> None:
        if self._owns_connection:
            await self.database.disconnect()

    async def create_identity(self, identity_data: dict[str, Any]) -> str | None:
        await self._ensure_ready()
        identity = OperationalIdentity(**identity_data)
        if identity.requires_ceo_authorization and not identity.ceo_authorized:
            await self.blackbox.log(
                "CEO_AUTH_REQUIRED",
                identity.codename,
                {
                    "identity_id": identity.identity_id,
                    "username": identity.username,
                    "community": identity.community,
                    "status": "CREATION_BLOCKED",
                },
                order_origin="IDENTITY_MANAGER",
            )
            return None
        await self.database.execute(self._insert_query(), *self._identity_values(identity))
        await self.blackbox.log(
            "IDENTITY_CREATED",
            identity.identity_id,
            {
                "codename": identity.codename,
                "username": identity.username,
                "community": identity.community,
                "status": identity.status,
                "ceo_authorized": identity.ceo_authorized,
            },
            order_origin="IDENTITY_MANAGER",
        )
        return identity.identity_id

    async def get_identity(self, identity_id: str) -> OperationalIdentity:
        await self._ensure_ready()
        row = await self.database.fetchrow(
            "SELECT * FROM sombra_identities WHERE identity_id = $1",
            identity_id,
        )
        if row is None:
            raise ValueError(f"identity not found: {identity_id}")
        return self._row_to_identity(row)

    async def get_all_active(self) -> list[OperationalIdentity]:
        await self._ensure_ready()
        rows = await self.database.fetch(
            """
            SELECT * FROM sombra_identities
            WHERE status IN ('ACTIVE', 'BUILDING')
            ORDER BY risk_score DESC, last_active ASC
            """
        )
        return [self._row_to_identity(row) for row in rows]

    async def update_status(self, identity_id: str, status: str) -> None:
        await self._ensure_ready()
        identity = await self.get_identity(identity_id)
        new_status = status.upper()
        await self.database.execute(
            "UPDATE sombra_identities SET status = $1 WHERE identity_id = $2",
            new_status,
            identity_id,
        )
        await self.blackbox.log(
            "IDENTITY_STATUS_CHANGE",
            identity_id,
            {"previous_status": identity.status, "new_status": new_status},
            order_origin="IDENTITY_MANAGER",
        )

    async def update_risk_score(self, identity_id: str, score: int) -> None:
        await self._ensure_ready()
        clamped = self._clamp_score(score)
        identity = await self.get_identity(identity_id)
        await self.database.execute(
            "UPDATE sombra_identities SET risk_score = $1 WHERE identity_id = $2",
            clamped,
            identity_id,
        )
        await self.blackbox.log(
            "IDENTITY_RISK_UPDATE",
            identity_id,
            {"previous_risk_score": identity.risk_score, "new_risk_score": clamped},
            order_origin="IDENTITY_MANAGER",
        )
        if clamped >= 80 and identity.status != "RETIRED":
            await self.retire_identity(identity_id, "AUTO_RETIRE_RISK_SCORE_80_PLUS")

    async def retire_identity(self, identity_id: str, reason: str) -> None:
        await self._ensure_ready()
        identity = await self.get_identity(identity_id)
        cooling_period = self._cooling_period(identity.risk_score)
        await self.database.execute(
            """
            UPDATE sombra_identities
            SET status = 'RETIRED', cooling_period_days = $1, last_active = $2
            WHERE identity_id = $3
            """,
            cooling_period,
            utc_now_iso(),
            identity_id,
        )
        await self.blackbox.log(
            "IDENTITY_RETIRED",
            identity_id,
            {
                "reason": reason,
                "previous_status": identity.status,
                "risk_score": identity.risk_score,
                "cooling_period_days": cooling_period,
            },
            order_origin="IDENTITY_MANAGER",
        )

    async def _ensure_ready(self) -> None:
        if self.database.connection is None:
            await self.database.connect()
        if self._schema_ready:
            return
        if self.database.backend == "sqlite":
            async with self.database._sqlite_lock:
                await self.database.connection.executescript(IDENTITY_SCHEMA)
                await self.database.connection.commit()
        else:
            statements = [statement.strip() for statement in IDENTITY_SCHEMA.split(";") if statement.strip()]
            for statement in statements:
                await self.database.execute(statement)
        self._schema_ready = True

    @staticmethod
    def _insert_query() -> str:
        columns = ", ".join(IDENTITY_FIELDS)
        markers = ", ".join(f"${index}" for index in range(1, len(IDENTITY_FIELDS) + 1))
        return f"INSERT INTO sombra_identities ({columns}) VALUES ({markers})"

    @staticmethod
    def _identity_values(identity: OperationalIdentity) -> tuple[Any, ...]:
        return (
            identity.identity_id,
            identity.codename,
            identity.username,
            identity.creation_date,
            identity.status,
            identity.nationality,
            identity.apparent_skill_level,
            identity.language_primary,
            json.dumps(identity.writing_style, ensure_ascii=True, sort_keys=True),
            identity.timezone_apparent,
            json.dumps(identity.activity_hours, ensure_ascii=True, sort_keys=True),
            identity.community,
            identity.current_phase,
            identity.reputation_score,
            identity.risk_score,
            identity.last_active,
            int(identity.requires_ceo_authorization),
            int(identity.ceo_authorized),
            identity.ceo_authorization_date,
            identity.cooling_period_days,
        )

    @staticmethod
    def _row_to_identity(row: dict[str, Any]) -> OperationalIdentity:
        data = dict(row)
        data["writing_style"] = IdentityManager._decode_json(data.get("writing_style"), {})
        data["activity_hours"] = IdentityManager._decode_json(data.get("activity_hours"), {})
        data["requires_ceo_authorization"] = bool(data.get("requires_ceo_authorization"))
        data["ceo_authorized"] = bool(data.get("ceo_authorized"))
        return OperationalIdentity(**data)

    @staticmethod
    def _decode_json(value: Any, fallback: Any) -> Any:
        if not isinstance(value, str):
            return value if value is not None else fallback
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return fallback

    @staticmethod
    def _clamp_score(score: int) -> int:
        return max(0, min(100, int(score)))

    @staticmethod
    def _cooling_period(score: int) -> int:
        if score >= 80:
            return 90
        if score >= 60:
            return 45
        return 30
