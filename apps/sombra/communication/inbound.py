from __future__ import annotations

import asyncio
from pathlib import Path
import json
from typing import Any

from apps.sombra.memory import BlackBoxAuditCore, DatabaseConnection
from apps.sombra.memory.database import LOG_DIR

from .models import InboundOrder


INBOUND_LOG = LOG_DIR / "inbound.log"
VALID_ORDER_TYPES = {
    "INTELLIGENCE_MISSION",
    "CLIENT_CHECK",
    "GLOBAL_THREAT_ANALYSIS",
    "CREDENTIAL_EXPOSURE_CHECK",
    "DOMAIN_MONITORING",
    "EXECUTIVE_PROTECTION",
    "MISSION_STATUS",
    "EMERGENCY_FREEZE",
    "INVESTIGATE",
}


class InboundOrderProcessor:
    def __init__(self, database: DatabaseConnection | None = None, blackbox: BlackBoxAuditCore | None = None) -> None:
        self.database = database if database is not None else DatabaseConnection()
        self.blackbox = blackbox if blackbox is not None else BlackBoxAuditCore(self.database)
        self._owns_connection = database is None

    async def disconnect(self) -> None:
        if self._owns_connection:
            await self.database.disconnect()

    async def process_order(self, raw_order: dict[str, Any]) -> dict[str, Any]:
        await self._ensure_ready()
        if not await self.validate_structure(raw_order):
            await self.blackbox.log(
                "ORDER_REJECTED",
                str(raw_order.get("target", "UNKNOWN")),
                {"reason": "invalid_structure", "raw": self._safe_raw(raw_order)},
                order_origin="COMMUNICATION_LAYER",
            )
            await asyncio.to_thread(self._append_inbound_log, {"status": "rejected", "reason": "invalid_structure"})
            return {"accepted": False, "reason": "invalid_structure"}
        is_ceo_order = raw_order.get("tag") == "[CEO]"
        priority = self._assign_priority(str(raw_order.get("priority", "STANDARD")), is_ceo_order)
        order = InboundOrder(
            sender=str(raw_order.get("sender", "UNKNOWN")),
            order_type=str(raw_order["order_type"]),
            target=str(raw_order["target"]),
            priority=priority,
            is_ceo_order=is_ceo_order,
            raw=self._safe_raw(raw_order),
        )
        await self.blackbox.log(
            "ORDER_RECEIVED",
            order.order_id,
            {
                "sender": order.sender,
                "order_type": order.order_type,
                "target": order.target,
                "priority": order.priority,
                "is_ceo_order": order.is_ceo_order,
            },
            order_origin="CEO" if order.is_ceo_order else "CEREBRO",
        )
        processed = order.to_dict()
        processed["accepted"] = True
        await asyncio.to_thread(self._append_inbound_log, processed)
        return processed

    async def validate_structure(self, order: dict[str, Any]) -> bool:
        required = ("order_type", "target", "priority")
        if not isinstance(order, dict) or any(not order.get(field) for field in required):
            return False
        return str(order["order_type"]).upper() in VALID_ORDER_TYPES

    async def _ensure_ready(self) -> None:
        if self.database.connection is None:
            await self.database.connect()

    @staticmethod
    def _assign_priority(priority: str, is_ceo_order: bool) -> str:
        if is_ceo_order:
            return "SUPREME"
        normalized = priority.upper()
        if normalized == "CRITICAL":
            return "CRITICAL"
        return "STANDARD"

    @staticmethod
    def _safe_raw(raw_order: dict[str, Any]) -> dict[str, Any]:
        blocked_terms = ("password", "secret", "token", "api_key")
        clean: dict[str, Any] = {}
        for key, value in raw_order.items():
            if any(term in str(key).lower() for term in blocked_terms):
                clean[str(key)] = "[REDACTED]"
            else:
                clean[str(key)] = value
        return clean

    @staticmethod
    def _append_inbound_log(payload: dict[str, Any]) -> None:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        with Path(INBOUND_LOG).open("a", encoding="utf-8") as log_file:
            log_file.write(json.dumps(payload, sort_keys=True, default=str) + "\n")
