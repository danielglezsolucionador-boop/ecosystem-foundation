from __future__ import annotations

from datetime import UTC, datetime
import json
import os
from pathlib import Path
from typing import Any
import uuid

from apps.sombra.communication.emergency_channel import CEOEmergencyChannel
from apps.sombra.communication.outbound import OutboundTransmissionEngine
from apps.sombra.memory import BlackBoxAuditCore, DatabaseConnection
from apps.sombra.memory.database import LOG_DIR

from .model_router import ModelRouter


AI_COST_LOG = LOG_DIR / "ai_cost_monitor.log"

COST_PER_MILLION_TOKENS = {
    "claude-haiku-4-5": {"input": 1.00, "output": 5.00, "cached_input": 0.10},
    "claude-sonnet-4-6": {"input": 3.00, "output": 15.00, "cached_input": 0.30},
    "claude-opus-4-7": {"input": 5.00, "output": 25.00, "cached_input": 0.50},
    "ollama_llama3": {"input": 0.00, "output": 0.00, "cached_input": 0.00},
}

WARNING_THRESHOLD = 0.80
CRITICAL_THRESHOLD = 0.95

AI_COST_SCHEMA = """
CREATE TABLE IF NOT EXISTS sombra_ai_costs (
  id TEXT PRIMARY KEY,
  timestamp_utc TEXT,
  model_used TEXT,
  input_tokens INTEGER,
  output_tokens INTEGER,
  cost_usd REAL,
  task_type TEXT,
  cached INTEGER
);

CREATE INDEX IF NOT EXISTS idx_sombra_ai_costs_timestamp
  ON sombra_ai_costs(timestamp_utc);

CREATE INDEX IF NOT EXISTS idx_sombra_ai_costs_model
  ON sombra_ai_costs(model_used);
"""


class AICostMonitor:
    def __init__(
        self,
        database: DatabaseConnection | None = None,
        blackbox: BlackBoxAuditCore | None = None,
        model_router: ModelRouter | None = None,
    ) -> None:
        self.database = database if database is not None else DatabaseConnection()
        self.blackbox = blackbox if blackbox is not None else BlackBoxAuditCore(self.database)
        self.model_router = model_router
        self.outbound = OutboundTransmissionEngine(self.database, self.blackbox)
        self.emergency_channel = CEOEmergencyChannel(self.database, self.blackbox)
        self.monthly_budget_usd = float(os.getenv("SOMBRA_AI_BUDGET_USD", "300"))
        self.use_economy_mode = False
        self.use_emergency_mode = False
        self._schema_ready = False
        self._owns_connection = database is None

    async def disconnect(self) -> None:
        if self._owns_connection:
            await self.database.disconnect()

    async def record_usage(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int,
        task_type: str,
        cached: bool = False,
    ) -> dict[str, Any]:
        await self._ensure_ready()
        model_key = str(model or "claude-haiku-4-5")
        rates = COST_PER_MILLION_TOKENS.get(model_key, COST_PER_MILLION_TOKENS["claude-haiku-4-5"])
        input_rate = rates["cached_input"] if cached else rates["input"]
        input_cost = (max(0, int(input_tokens)) / 1_000_000) * input_rate
        output_cost = (max(0, int(output_tokens)) / 1_000_000) * rates["output"]
        total_cost = round(input_cost + output_cost, 8)
        usage_id = str(uuid.uuid4())
        await self.database.execute(
            """
            INSERT INTO sombra_ai_costs (
              id, timestamp_utc, model_used, input_tokens, output_tokens,
              cost_usd, task_type, cached
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            """,
            usage_id,
            self._now(),
            model_key,
            max(0, int(input_tokens)),
            max(0, int(output_tokens)),
            total_cost,
            str(task_type or "unknown"),
            int(bool(cached)),
        )
        await self.blackbox.log(
            "AI_USAGE_RECORDED",
            usage_id,
            {
                "model_used": model_key,
                "input_tokens": max(0, int(input_tokens)),
                "output_tokens": max(0, int(output_tokens)),
                "cost_usd": total_cost,
                "task_type": str(task_type or "unknown"),
                "cached": bool(cached),
            },
            order_origin="AI_COST_CONTROL",
        )
        monthly_total = await self.get_monthly_total()
        percentage = self._budget_percentage(monthly_total)
        if percentage >= CRITICAL_THRESHOLD:
            await self._budget_critical()
        elif percentage >= WARNING_THRESHOLD:
            await self._budget_warning()
        result = {
            "id": usage_id,
            "model_used": model_key,
            "cost_usd": total_cost,
            "monthly_total_usd": monthly_total,
            "percentage_used": percentage,
        }
        await self._append_cost_log({"event": "AI_USAGE_RECORDED", **result})
        return result

    async def get_monthly_total(self) -> float:
        await self._ensure_ready()
        row = await self.database.fetchrow(
            """
            SELECT COALESCE(SUM(cost_usd), 0) AS total
            FROM sombra_ai_costs
            WHERE substr(timestamp_utc, 1, 7) = substr($1, 1, 7)
            """,
            self._now(),
        )
        return round(float((row or {}).get("total") or 0.0), 8)

    async def get_daily_cost(self) -> float:
        await self._ensure_ready()
        row = await self.database.fetchrow(
            """
            SELECT COALESCE(SUM(cost_usd), 0) AS total
            FROM sombra_ai_costs
            WHERE substr(timestamp_utc, 1, 10) = substr($1, 1, 10)
            """,
            self._now(),
        )
        return round(float((row or {}).get("total") or 0.0), 8)

    async def get_cost_by_model(self) -> dict[str, float]:
        await self._ensure_ready()
        rows = await self.database.fetch(
            """
            SELECT model_used, COALESCE(SUM(cost_usd), 0) AS total
            FROM sombra_ai_costs
            WHERE substr(timestamp_utc, 1, 7) = substr($1, 1, 7)
            GROUP BY model_used
            ORDER BY total DESC
            """,
            self._now(),
        )
        return {str(row["model_used"]): round(float(row["total"] or 0.0), 8) for row in rows}

    async def get_monthly_projection(self) -> float:
        daily_cost = await self.get_daily_cost()
        now = datetime.now(UTC)
        days_in_month = self._days_in_month(now.year, now.month)
        elapsed_days = max(1, now.day)
        month_to_date = await self.get_monthly_total()
        daily_average = month_to_date / elapsed_days
        return round(max(daily_cost, daily_average) * days_in_month, 8)

    async def _budget_warning(self) -> None:
        current_total = await self.get_monthly_total()
        percentage = self._budget_percentage(current_total)
        projection = await self.get_monthly_projection()
        self.use_economy_mode = True
        if self.model_router is not None and self.model_router.mode != "ECONOMY":
            await self.model_router.set_mode_async("ECONOMY", reason="AI_BUDGET_WARNING")
        payload = {
            "type": "AI_BUDGET_WARNING",
            "monthly_total": current_total,
            "budget_limit": self.monthly_budget_usd,
            "percentage_used": percentage,
            "projection": projection,
            "action": "Switching non-critical tasks to Haiku model",
        }
        await self.blackbox.log("AI_BUDGET_WARNING", "AI_COST_MONITOR", payload, order_origin="AI_COST_CONTROL")
        await self.outbound.transmit_to_cerebro(payload, "HIGH")
        await self._append_cost_log({"event": "AI_BUDGET_WARNING", **payload})

    async def _budget_critical(self) -> None:
        current_total = await self.get_monthly_total()
        percentage = self._budget_percentage(current_total)
        self.use_economy_mode = True
        self.use_emergency_mode = True
        if self.model_router is not None and self.model_router.mode != "EMERGENCY":
            await self.model_router.set_mode_async("EMERGENCY", reason="AI_BUDGET_CRITICAL")
        payload = {
            "case_type": "AI_BUDGET_CRITICAL",
            "situation": (
                f"AI spend at {round(percentage * 100, 2)}% of monthly budget. "
                "Switching to local models."
            ),
            "monthly_total": current_total,
            "budget_limit": self.monthly_budget_usd,
            "percentage_used": percentage,
        }
        await self.blackbox.log("AI_BUDGET_CRITICAL", "AI_COST_MONITOR", payload, order_origin="AI_COST_CONTROL")
        await self.emergency_channel.activate(
            "AI_BUDGET_CRITICAL",
            payload["situation"],
            payload,
            ["non_critical_paid_ai_tasks"],
        )
        await self._append_cost_log({"event": "AI_BUDGET_CRITICAL", **payload})

    async def _ensure_ready(self) -> None:
        if self.database.connection is None:
            await self.database.connect()
        if self._schema_ready:
            return
        if self.database.backend == "sqlite":
            async with self.database._sqlite_lock:
                await self.database.connection.executescript(AI_COST_SCHEMA)
                await self.database.connection.commit()
        else:
            statements = [statement.strip() for statement in AI_COST_SCHEMA.split(";") if statement.strip()]
            for statement in statements:
                await self.database.execute(statement)
        self._schema_ready = True

    def _budget_percentage(self, monthly_total: float) -> float:
        if self.monthly_budget_usd <= 0:
            return 1.0
        return round(float(monthly_total) / self.monthly_budget_usd, 8)

    @staticmethod
    def _days_in_month(year: int, month: int) -> int:
        if month == 12:
            next_month = datetime(year + 1, 1, 1, tzinfo=UTC)
        else:
            next_month = datetime(year, month + 1, 1, tzinfo=UTC)
        this_month = datetime(year, month, 1, tzinfo=UTC)
        return (next_month - this_month).days

    @staticmethod
    async def _append_cost_log(row: dict[str, Any]) -> None:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        with Path(AI_COST_LOG).open("a", encoding="utf-8") as log_file:
            log_file.write(json.dumps(row, sort_keys=True, default=str) + "\n")

    @staticmethod
    def _now() -> str:
        return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
