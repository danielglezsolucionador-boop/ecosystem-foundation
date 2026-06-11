from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from apps.sombra.memory import DatabaseConnection
from apps.sombra.memory.database import LOG_DIR


METRICS_SCHEMA = """
CREATE TABLE IF NOT EXISTS sombra_metrics (
  metric_name TEXT,
  metric_value REAL,
  timestamp_utc TEXT
);

CREATE INDEX IF NOT EXISTS idx_sombra_metrics_name_time
  ON sombra_metrics(metric_name, timestamp_utc);
"""


class SombraMetrics:
    def __init__(self, database: DatabaseConnection | None = None) -> None:
        self.database = database if database is not None else DatabaseConnection()
        self._schema_ready = False
        self._owns_connection = database is None

    async def disconnect(self) -> None:
        if self._owns_connection:
            await self.database.disconnect()

    async def record(self, metric_name: str, value: float) -> None:
        await self._ensure_ready()
        await self.database.execute(
            """
            INSERT INTO sombra_metrics (metric_name, metric_value, timestamp_utc)
            VALUES ($1, $2, $3)
            """,
            metric_name,
            float(value),
            self._now(),
        )

    async def get_metric_history(self, metric_name: str, hours: int = 24) -> list[dict[str, Any]]:
        await self._ensure_ready()
        rows = await self.database.fetch(
            """
            SELECT metric_name, metric_value, timestamp_utc
            FROM sombra_metrics
            WHERE metric_name = $1
              AND datetime(timestamp_utc) >= datetime('now', $2)
            ORDER BY timestamp_utc ASC
            """,
            metric_name,
            f"-{int(hours)} hours",
        )
        return rows

    async def get_daily_summary(self) -> dict[str, Any]:
        await self._ensure_ready()
        intel_processed_today = await self._safe_count(
            "SELECT COUNT(*) AS count FROM sombra_intel_global WHERE date(timestamp_utc) = date('now')"
        )
        alerts_generated_today = await self._safe_count(
            "SELECT COUNT(*) AS count FROM sombra_alerts WHERE date(timestamp_utc) = date('now')"
        )
        critical_alerts_today = await self._safe_count(
            "SELECT COUNT(*) AS count FROM sombra_alerts WHERE date(timestamp_utc) = date('now') AND severity = 'CRITICAL'"
        )
        proactive_alerts_today = await self._safe_count(
            "SELECT COUNT(*) AS count FROM sombra_alerts WHERE date(timestamp_utc) = date('now') AND order_origin = 'PROACTIVE'"
        )
        average_row = await self._safe_fetchrow(
            "SELECT AVG(threat_score) AS average FROM sombra_alerts WHERE date(timestamp_utc) = date('now')"
        )
        return {
            "intel_processed_today": intel_processed_today,
            "alerts_generated_today": alerts_generated_today,
            "critical_alerts_today": critical_alerts_today,
            "proactive_alerts_today": proactive_alerts_today,
            "collection_cycles_today": self._collection_cycles_today(),
            "average_threat_score_today": round(float((average_row or {}).get("average") or 0.0), 2),
        }

    async def _ensure_ready(self) -> None:
        if self.database.connection is None:
            await self.database.connect()
        if self._schema_ready:
            return
        if self.database.backend == "sqlite":
            async with self.database._sqlite_lock:
                await self.database.connection.executescript(METRICS_SCHEMA)
                await self.database.connection.commit()
        else:
            statements = [statement.strip() for statement in METRICS_SCHEMA.split(";") if statement.strip()]
            for statement in statements:
                await self.database.execute(statement)
        self._schema_ready = True

    async def _safe_count(self, query: str) -> int:
        row = await self._safe_fetchrow(query)
        return int((row or {}).get("count") or 0)

    async def _safe_fetchrow(self, query: str) -> dict[str, Any] | None:
        try:
            return await self.database.fetchrow(query)
        except Exception:
            return None

    @staticmethod
    def _collection_cycles_today() -> int:
        scheduler_log = LOG_DIR / "scheduler.log"
        if not scheduler_log.exists():
            return 0
        today = datetime.now(UTC).date().isoformat()
        return sum(
            1
            for line in scheduler_log.read_text(encoding="utf-8", errors="replace").splitlines()
            if line.startswith(today) and "cycle_complete" in line
        )

    @staticmethod
    def _now() -> str:
        return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
