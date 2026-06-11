from __future__ import annotations

import asyncio
from datetime import UTC, datetime
import os
from pathlib import Path
import re
from typing import Any


SOMBRA_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = SOMBRA_ROOT / "data"
LOG_DIR = SOMBRA_ROOT / "logs"
DATABASE_LOG = LOG_DIR / "memory_database.log"
SCHEMA_PATH = Path(__file__).with_name("schema.sql")


SQLITE_SCHEMA = """
CREATE TABLE IF NOT EXISTS sombra_intel_global (
  id TEXT PRIMARY KEY,
  timestamp_utc TEXT,
  threat_type TEXT,
  severity TEXT,
  confidence REAL,
  findings TEXT,
  source_category TEXT,
  source_reliability REAL,
  indicators TEXT,
  routing TEXT,
  threat_score INTEGER,
  prediction TEXT,
  aging_status TEXT DEFAULT 'ACTIVE',
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS sombra_client_profiles (
  client_id TEXT PRIMARY KEY,
  client_name TEXT,
  industry_sector TEXT,
  geography TEXT,
  risk_score INTEGER DEFAULT 0,
  risk_trend TEXT DEFAULT 'STABLE',
  digital_assets TEXT,
  executive_registry TEXT,
  threat_history TEXT,
  credential_history TEXT,
  brand_registry TEXT,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS sombra_blackbox (
  id TEXT PRIMARY KEY,
  timestamp_utc TEXT DEFAULT CURRENT_TIMESTAMP,
  event_type TEXT,
  entity TEXT,
  detail TEXT,
  order_origin TEXT,
  rule_suspended TEXT,
  hash_sha256 TEXT
);

CREATE INDEX IF NOT EXISTS idx_sombra_intel_global_threat_type
  ON sombra_intel_global(threat_type);
CREATE INDEX IF NOT EXISTS idx_sombra_intel_global_severity
  ON sombra_intel_global(severity);
CREATE INDEX IF NOT EXISTS idx_sombra_intel_global_timestamp_utc
  ON sombra_intel_global(timestamp_utc);
CREATE INDEX IF NOT EXISTS idx_sombra_blackbox_event_type
  ON sombra_blackbox(event_type);

CREATE TRIGGER IF NOT EXISTS trg_sombra_blackbox_no_update
BEFORE UPDATE ON sombra_blackbox
BEGIN
  SELECT RAISE(ABORT, 'sombra_blackbox is append-only');
END;

CREATE TRIGGER IF NOT EXISTS trg_sombra_blackbox_no_delete
BEFORE DELETE ON sombra_blackbox
BEGIN
  SELECT RAISE(ABORT, 'sombra_blackbox is append-only');
END;
"""


class DatabaseConnection:
    def __init__(self, database_url: str | None = None, sqlite_path: Path | None = None) -> None:
        self.database_url = database_url if database_url is not None else os.getenv("DATABASE_URL")
        self.sqlite_path = sqlite_path if sqlite_path is not None else DATA_DIR / "sombra.db"
        self.backend = "postgresql" if self.database_url else "sqlite"
        self.connection: Any | None = None
        self._sqlite_lock = asyncio.Lock()

    async def connect(self) -> None:
        if self.backend == "postgresql":
            await self._connect_postgresql()
        else:
            await self._connect_sqlite()
        await self.initialize_schema()
        await asyncio.to_thread(self._log_database_backend)

    async def disconnect(self) -> None:
        if self.connection is None:
            return
        if self.backend == "postgresql":
            await self.connection.close()
        else:
            await self.connection.close()
        self.connection = None

    async def initialize_schema(self) -> None:
        self._require_connection()
        if self.backend == "postgresql":
            await self.connection.execute(SCHEMA_PATH.read_text(encoding="utf-8"))
            return
        async with self._sqlite_lock:
            await self.connection.executescript(SQLITE_SCHEMA)
            await self.connection.commit()

    async def execute(self, query: str, *args: Any) -> Any:
        self._require_connection()
        if self.backend == "postgresql":
            return await self.connection.execute(query, *args)
        sqlite_query, sqlite_args = self._adapt_query_for_sqlite(query, args)
        async with self._sqlite_lock:
            try:
                cursor = await self.connection.execute(sqlite_query, sqlite_args)
                await self.connection.commit()
                return cursor.rowcount
            except Exception:
                await self.connection.rollback()
                raise

    async def fetch(self, query: str, *args: Any) -> list[dict[str, Any]]:
        self._require_connection()
        if self.backend == "postgresql":
            rows = await self.connection.fetch(query, *args)
            return [dict(row) for row in rows]
        sqlite_query, sqlite_args = self._adapt_query_for_sqlite(query, args)
        async with self._sqlite_lock:
            cursor = await self.connection.execute(sqlite_query, sqlite_args)
            rows = await cursor.fetchall()
        return [dict(row) for row in rows]

    async def fetchrow(self, query: str, *args: Any) -> dict[str, Any] | None:
        self._require_connection()
        if self.backend == "postgresql":
            row = await self.connection.fetchrow(query, *args)
            return dict(row) if row is not None else None
        sqlite_query, sqlite_args = self._adapt_query_for_sqlite(query, args)
        async with self._sqlite_lock:
            cursor = await self.connection.execute(sqlite_query, sqlite_args)
            row = await cursor.fetchone()
        return dict(row) if row is not None else None

    async def _connect_postgresql(self) -> None:
        import asyncpg

        self.connection = await asyncpg.connect(self.database_url)

    async def _connect_sqlite(self) -> None:
        import aiosqlite

        DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.connection = await aiosqlite.connect(self.sqlite_path)
        self.connection.row_factory = aiosqlite.Row

    def _log_database_backend(self) -> None:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
        target = "DATABASE_URL" if self.backend == "postgresql" else str(self.sqlite_path)
        with DATABASE_LOG.open("a", encoding="utf-8") as log_file:
            log_file.write(f"{timestamp} backend={self.backend} target={target}\n")

    def _require_connection(self) -> None:
        if self.connection is None:
            raise RuntimeError("database is not connected")

    @staticmethod
    def _adapt_query_for_sqlite(query: str, args: tuple[Any, ...]) -> tuple[str, tuple[Any, ...]]:
        expanded_args: list[Any] = []

        def replace(match: re.Match[str]) -> str:
            position = int(match.group()[1:]) - 1
            if position < 0 or position >= len(args):
                raise ValueError(f"missing SQLite argument for marker {match.group()}")
            expanded_args.append(args[position])
            return "?"

        sqlite_query = re.sub(r"\$\d+", replace, query)
        return sqlite_query, tuple(expanded_args)
