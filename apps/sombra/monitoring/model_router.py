from __future__ import annotations

from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Any

from apps.sombra.memory import BlackBoxAuditCore, DatabaseConnection
from apps.sombra.memory.database import LOG_DIR


MODEL_ROUTER_LOG = LOG_DIR / "model_router.log"

NORMAL_MODE_ROUTING = {
    "bulk_classification": "claude-haiku-4-5",
    "credential_triage": "claude-haiku-4-5",
    "routine_scoring": "claude-haiku-4-5",
    "standard_analysis": "claude-sonnet-4-6",
    "pattern_detection": "claude-sonnet-4-6",
    "report_generation": "claude-sonnet-4-6",
    "deep_analysis": "claude-opus-4-7",
    "ceo_briefing": "claude-opus-4-7",
    "critical_prediction": "claude-opus-4-7",
    "honeypot_design": "claude-opus-4-7",
    "offline_fallback": "ollama_llama3",
}

ECONOMY_MODE_ROUTING = {
    "bulk_classification": "claude-haiku-4-5",
    "credential_triage": "claude-haiku-4-5",
    "routine_scoring": "claude-haiku-4-5",
    "standard_analysis": "claude-haiku-4-5",
    "pattern_detection": "claude-haiku-4-5",
    "report_generation": "claude-sonnet-4-6",
    "deep_analysis": "claude-sonnet-4-6",
    "ceo_briefing": "claude-sonnet-4-6",
    "critical_prediction": "claude-sonnet-4-6",
    "honeypot_design": "claude-sonnet-4-6",
    "offline_fallback": "ollama_llama3",
}

EMERGENCY_MODE_ROUTING = {
    "default": "claude-haiku-4-5",
    "ceo_order": "claude-sonnet-4-6",
    "offline_fallback": "ollama_llama3",
}

VALID_MODES = {"NORMAL", "ECONOMY", "EMERGENCY"}


class ModelRouter:
    def __init__(self, database: DatabaseConnection | None = None, blackbox: BlackBoxAuditCore | None = None) -> None:
        self.database = database if database is not None else DatabaseConnection()
        self.blackbox = blackbox if blackbox is not None else BlackBoxAuditCore(self.database)
        self.mode = "NORMAL"
        self._owns_connection = database is None

    async def disconnect(self) -> None:
        if self._owns_connection:
            await self.database.disconnect()

    def get_model(self, task_type: str) -> str:
        normalized_task = str(task_type or "standard_analysis").strip() or "standard_analysis"
        if self.mode == "EMERGENCY":
            model = EMERGENCY_MODE_ROUTING.get(normalized_task, EMERGENCY_MODE_ROUTING["default"])
        elif self.mode == "ECONOMY":
            model = ECONOMY_MODE_ROUTING.get(normalized_task, ECONOMY_MODE_ROUTING["standard_analysis"])
        else:
            model = NORMAL_MODE_ROUTING.get(normalized_task, NORMAL_MODE_ROUTING["standard_analysis"])
        self._append_router_log(
            {
                "timestamp_utc": self._now(),
                "event": "MODEL_ROUTED",
                "mode": self.mode,
                "task_type": normalized_task,
                "model": model,
            }
        )
        return model

    def set_mode(self, mode: str) -> None:
        normalized_mode = str(mode or "").upper()
        if normalized_mode not in VALID_MODES:
            raise ValueError(f"unsupported model routing mode: {mode}")
        previous = self.mode
        self.mode = normalized_mode
        self._append_router_log(
            {
                "timestamp_utc": self._now(),
                "event": "MODEL_ROUTER_MODE_CHANGED",
                "previous_mode": previous,
                "new_mode": self.mode,
            }
        )

    async def set_mode_async(self, mode: str, reason: str = "manual") -> None:
        previous = self.mode
        self.set_mode(mode)
        await self._ensure_database()
        await self.blackbox.log(
            "MODEL_ROUTER_MODE_CHANGED",
            "MODEL_ROUTER",
            {"previous_mode": previous, "new_mode": self.mode, "reason": reason},
            order_origin="AI_COST_CONTROL",
        )

    async def _ensure_database(self) -> None:
        if self.database.connection is None:
            await self.database.connect()

    @staticmethod
    def _append_router_log(row: dict[str, Any]) -> None:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        with Path(MODEL_ROUTER_LOG).open("a", encoding="utf-8") as log_file:
            log_file.write(json.dumps(row, sort_keys=True, default=str) + "\n")

    @staticmethod
    def _now() -> str:
        return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
