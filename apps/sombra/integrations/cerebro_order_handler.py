from __future__ import annotations

from typing import Any

from apps.sombra.communication import InboundOrderProcessor
from apps.sombra.memory import BlackBoxAuditCore, DatabaseConnection


class CerebroOrderHandler:
    def __init__(
        self,
        database: DatabaseConnection | None = None,
        blackbox: BlackBoxAuditCore | None = None,
        inbound_processor: InboundOrderProcessor | None = None,
    ) -> None:
        self.database = database if database is not None else DatabaseConnection()
        self.blackbox = blackbox if blackbox is not None else BlackBoxAuditCore(self.database)
        self.inbound_processor = (
            inbound_processor
            if inbound_processor is not None
            else InboundOrderProcessor(self.database, self.blackbox)
        )
        self._owns_connection = database is None

    async def disconnect(self) -> None:
        if self._owns_connection:
            await self.database.disconnect()

    async def handle_order(self, raw_order: dict[str, Any]) -> dict[str, Any]:
        await self._ensure_ready()
        normalized_order = self._normalize_cerebro_order(raw_order)
        processed = await self.inbound_processor.process_order(normalized_order)
        await self.blackbox.log(
            "CEREBRO_ORDER_HANDLED",
            str(processed.get("order_id", processed.get("target", "UNKNOWN"))),
            {
                "accepted": bool(processed.get("accepted")),
                "order_type": processed.get("order_type"),
                "target": processed.get("target"),
                "priority": processed.get("priority"),
                "is_ceo_order": bool(processed.get("is_ceo_order")),
            },
            order_origin="CEREBRO",
        )
        return processed

    async def _ensure_ready(self) -> None:
        if self.database.connection is None:
            await self.database.connect()

    @staticmethod
    def _normalize_cerebro_order(raw_order: dict[str, Any]) -> dict[str, Any]:
        normalized = dict(raw_order)
        normalized.setdefault("sender", "CEREBRO")
        if normalized.get("tag") == "[CEO]":
            normalized["sender"] = "CEREBRO"
        elif normalized.get("tag") not in {"[CEREBRO]", "[CEO]"}:
            normalized["tag"] = "[CEREBRO]"
        if "order_type" in normalized:
            normalized["order_type"] = str(normalized["order_type"]).upper()
        if "priority" in normalized:
            normalized["priority"] = str(normalized["priority"]).upper()
        return normalized
