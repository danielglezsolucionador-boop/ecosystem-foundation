from __future__ import annotations

import asyncio
from datetime import UTC, datetime
import json
import os
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen

from apps.sombra.memory import BlackBoxAuditCore, DatabaseConnection
from apps.sombra.memory.database import LOG_DIR


CEO_EMERGENCY_LOG = LOG_DIR / "CEO_EMERGENCY.log"
HEALTH_LOG = LOG_DIR / "communication_health.log"
CASE_TYPES = {"LEGAL_RISK", "HIERARCHY_CONFLICT", "CEREBRO_UNRESPONSIVE", "CRITICAL_COMPROMISE"}


class CEOEmergencyChannel:
    def __init__(self, database: DatabaseConnection | None = None, blackbox: BlackBoxAuditCore | None = None) -> None:
        self.database = database if database is not None else DatabaseConnection()
        self.blackbox = blackbox if blackbox is not None else BlackBoxAuditCore(self.database)
        self._owns_connection = database is None

    async def disconnect(self) -> None:
        if self._owns_connection:
            await self.database.disconnect()

    async def activate(
        self,
        case_type: str,
        situation: str,
        risk_assessment: dict[str, Any],
        frozen_operations: list[str],
    ) -> dict[str, Any]:
        await self._ensure_ready()
        normalized_case = case_type.upper()
        if normalized_case not in CASE_TYPES:
            raise ValueError(f"unsupported emergency case type: {case_type}")
        message = {
            "timestamp_utc": self._now(),
            "case_type": normalized_case,
            "situation": situation,
            "risk_assessment": dict(risk_assessment),
            "frozen_operations": list(frozen_operations),
            "status": "AWAITING_CEO_INSTRUCTION",
        }
        await asyncio.to_thread(self._append_emergency_log, message)
        delivery = await self._send_if_configured(message)
        await self.blackbox.log(
            "CEO_EMERGENCY_ACTIVATED",
            normalized_case,
            {**message, "webhook_delivered": delivery["delivered"], "webhook_error": delivery.get("error")},
            order_origin="EMERGENCY_CHANNEL",
        )
        print("[CEO EMERGENCY CHANNEL ACTIVATED]")
        print(f"[CASE: {normalized_case}]")
        print(f"[SITUATION: {situation}]")
        print("[AWAITING CEO INSTRUCTION]")
        return {**message, "webhook_delivered": delivery["delivered"], "webhook_error": delivery.get("error")}

    async def is_ready(self) -> bool:
        await asyncio.to_thread(self._append_health_log)
        return True

    async def _ensure_ready(self) -> None:
        if self.database.connection is None:
            await self.database.connect()

    async def _send_if_configured(self, message: dict[str, Any]) -> dict[str, Any]:
        webhook_url = os.getenv("CEO_EMERGENCY_WEBHOOK_URL")
        if not webhook_url:
            return {"delivered": False, "error": "webhook_not_configured"}
        try:
            await asyncio.to_thread(self._post_webhook, webhook_url, message)
        except Exception as error:
            return {"delivered": False, "error": repr(error)}
        return {"delivered": True}

    @staticmethod
    def _post_webhook(url: str, payload: dict[str, Any]) -> None:
        body = json.dumps(payload, ensure_ascii=True).encode("utf-8")
        request = Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST")
        with urlopen(request, timeout=10) as response:
            if response.status >= 300:
                raise RuntimeError(f"emergency webhook returned status {response.status}")

    @staticmethod
    def _append_emergency_log(message: dict[str, Any]) -> None:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        with Path(CEO_EMERGENCY_LOG).open("a", encoding="utf-8") as log_file:
            log_file.write(json.dumps(message, sort_keys=True, default=str) + "\n")

    @staticmethod
    def _append_health_log() -> None:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        with Path(HEALTH_LOG).open("a", encoding="utf-8") as log_file:
            log_file.write(f"{CEOEmergencyChannel._now()} CEO emergency channel readiness=True\n")

    @staticmethod
    def _now() -> str:
        return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
