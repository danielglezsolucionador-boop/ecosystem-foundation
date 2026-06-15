from __future__ import annotations

from datetime import UTC, datetime, timedelta
import json
from typing import Any
import uuid

from apps.sombra.memory.blackbox import BlackBoxAuditCore
from apps.sombra.memory.database import DatabaseConnection

from .emergency_channel import CEOEmergencyChannel
from .outbound import OutboundTransmissionEngine
from .telegram_channel import TelegramCEOChannel


CEO_ID = "1"

ALERT_CODES = {
    "A1-PARA-1": {
        "level": "CRITICAL",
        "meaning": "Immediate CEO action required",
        "response_window": "NOW - minutes",
        "examples": [
            "CEO credentials being sold now",
            "Active attack on ecosystem",
            "Legal risk extreme - operations frozen",
            "Hierarchy compromise detected",
        ],
        "cerebro_instruction": "DROP EVERYTHING. SMS CEO NOW.",
        "sms_prefix": "A1-PARA-1:",
    },
    "A2-PARA-1": {
        "level": "URGENT",
        "meaning": "CEO action required today",
        "response_window": "Hours",
        "examples": [
            "Client credentials exposed",
            "Directed attack on ecosystem detected",
            "Zero day affecting client systems",
            "Executive data found underground",
        ],
        "cerebro_instruction": "Alert CEO within 1 hour.",
        "sms_prefix": "A2-PARA-1:",
    },
    "A3-PARA-1": {
        "level": "IMPORTANT",
        "meaning": "CEO should review soon",
        "response_window": "24 hours",
        "examples": [
            "New vulnerability affects clients",
            "Threat actor targeting our sector",
            "Budget threshold reached",
            "Identity at risk",
        ],
        "cerebro_instruction": "Notify CEO in next report.",
        "sms_prefix": "A3-PARA-1:",
    },
    "INFO-PARA-1": {
        "level": "INFORMATIONAL",
        "meaning": "CEO awareness only",
        "response_window": "When available",
        "examples": [
            "Weekly intelligence summary",
            "New threat trend emerging",
            "Ecosystem health report",
            "Monthly cost report",
        ],
        "cerebro_instruction": "Include in weekly CEO briefing.",
        "sms_prefix": "INFO-PARA-1:",
    },
}

ALERT_PRIORITIES = {
    "A1-PARA-1": "SUPREME",
    "A2-PARA-1": "CRITICAL",
    "A3-PARA-1": "HIGH",
    "INFO-PARA-1": "STANDARD",
}

CEO_ALERT_SCHEMA = """
CREATE TABLE IF NOT EXISTS sombra_ceo_alerts (
  alert_id TEXT PRIMARY KEY,
  timestamp_utc TEXT,
  alert_code TEXT,
  to_entity TEXT,
  from_entity TEXT,
  level TEXT,
  message TEXT,
  cerebro_instruction TEXT,
  sms_text TEXT,
  response_window TEXT,
  intel_reference TEXT,
  priority TEXT,
  requires_acknowledgement INTEGER,
  acknowledged INTEGER DEFAULT 0,
  last_sent_at TEXT,
  resend_count INTEGER DEFAULT 0,
  payload TEXT
);

CREATE INDEX IF NOT EXISTS idx_sombra_ceo_alerts_code_ack
  ON sombra_ceo_alerts(alert_code, acknowledged);
"""


class CEOAlertCodeSystem:
    def __init__(self, database: DatabaseConnection | None = None, blackbox: BlackBoxAuditCore | None = None) -> None:
        self.database = database if database is not None else DatabaseConnection()
        self.blackbox = blackbox if blackbox is not None else BlackBoxAuditCore(self.database)
        self.outbound = OutboundTransmissionEngine(self.database, self.blackbox)
        self.emergency_channel = CEOEmergencyChannel(self.database, self.blackbox)
        self.telegram_channel = TelegramCEOChannel()
        self._schema_ready = False
        self._owns_connection = database is None

    async def disconnect(self) -> None:
        if self._owns_connection:
            await self.database.disconnect()

    async def send_ceo_alert(self, code: str, message: str, intel_reference: str | None = None) -> dict[str, Any]:
        await self._ensure_ready()
        normalized_code = str(code or "").upper()
        if normalized_code not in ALERT_CODES:
            await self.blackbox.log(
                "CEO_ALERT_REJECTED",
                "CEO_ALERT_CODE_SYSTEM",
                {"reason": "invalid_code", "code": code},
                order_origin="CEO_ALERT_CODES",
            )
            return {"accepted": False, "reason": "invalid_alert_code", "alert_code": code}
        config = ALERT_CODES[normalized_code]
        priority = ALERT_PRIORITIES[normalized_code]
        alert_package = {
            "alert_id": str(uuid.uuid4()),
            "alert_code": normalized_code,
            "to": "CEO-1",
            "from": "SOMBRA",
            "level": config["level"],
            "message": str(message),
            "cerebro_instruction": config["cerebro_instruction"],
            "sms_text": f"{config['sms_prefix']} {message}",
            "response_window": config["response_window"],
            "intel_reference": intel_reference,
            "timestamp_utc": self._now(),
            "requires_acknowledgement": normalized_code in {"A1-PARA-1", "A2-PARA-1"},
            "priority": priority,
        }
        await self._store_alert(alert_package)
        await self.blackbox.log(
            "CEO_ALERT_SENT",
            alert_package["alert_id"],
            {
                "alert_code": normalized_code,
                "level": config["level"],
                "priority": priority,
                "requires_acknowledgement": alert_package["requires_acknowledgement"],
            },
            order_origin="CEO_ALERT_CODES",
        )
        telegram_configured = await self.telegram_channel.is_configured()
        telegram_delivered = False
        if telegram_configured:
            telegram_delivered = await self.telegram_channel.send_alert(normalized_code, str(message))
            await self.blackbox.log(
                "CEO_ALERT_TELEGRAM_ATTEMPT",
                alert_package["alert_id"],
                {
                    "alert_code": normalized_code,
                    "configured": telegram_configured,
                    "delivered": telegram_delivered,
                },
                order_origin="CEO_ALERT_CODES",
            )
        if not telegram_delivered:
            await self.outbound.transmit_to_cerebro(alert_package, priority)
        if normalized_code == "A1-PARA-1":
            await self.emergency_channel.activate(
                "CRITICAL_COMPROMISE",
                str(message),
                {"alert_code": normalized_code, "intel_reference": intel_reference, "priority": priority},
                ["await_ceo_instruction"],
            )
        return alert_package

    async def check_unacknowledged(self) -> list[dict[str, Any]]:
        await self._ensure_ready()
        rows = await self.database.fetch(
            """
            SELECT *
            FROM sombra_ceo_alerts
            WHERE acknowledged = 0
              AND alert_code IN ('A1-PARA-1', 'A2-PARA-1')
            ORDER BY timestamp_utc ASC
            """
        )
        resent: list[dict[str, Any]] = []
        now = datetime.now(UTC)
        for row in rows:
            last_sent = self._parse_time(str(row.get("last_sent_at") or row.get("timestamp_utc") or ""))
            code = str(row["alert_code"])
            threshold = timedelta(minutes=10 if code == "A1-PARA-1" else 60)
            if now - last_sent < threshold:
                continue
            payload = self._decode_payload(row)
            payload["resend"] = True
            payload["resend_count"] = int(row.get("resend_count") or 0) + 1
            priority = str(row.get("priority") or ALERT_PRIORITIES[code])
            await self.outbound.transmit_to_cerebro(payload, priority)
            await self.database.execute(
                """
                UPDATE sombra_ceo_alerts
                SET last_sent_at = $1, resend_count = resend_count + 1
                WHERE alert_id = $2
                """,
                self._now(),
                row["alert_id"],
            )
            await self.blackbox.log(
                "CEO_ALERT_RESENT",
                str(row["alert_id"]),
                {"alert_code": code, "priority": priority, "resend_count": payload["resend_count"]},
                order_origin="CEO_ALERT_CODES",
            )
            resent.append(payload)
        return resent

    async def acknowledge_alert(self, alert_id: str) -> bool:
        await self._ensure_ready()
        await self.database.execute(
            """
            UPDATE sombra_ceo_alerts
            SET acknowledged = 1
            WHERE alert_id = $1
            """,
            alert_id,
        )
        await self.blackbox.log(
            "CEO_ALERT_ACKNOWLEDGED",
            alert_id,
            {"alert_id": alert_id},
            order_origin="CEO_ALERT_CODES",
        )
        return True

    async def _store_alert(self, alert_package: dict[str, Any]) -> None:
        await self.database.execute(
            """
            INSERT INTO sombra_ceo_alerts (
              alert_id, timestamp_utc, alert_code, to_entity, from_entity,
              level, message, cerebro_instruction, sms_text, response_window,
              intel_reference, priority, requires_acknowledgement, acknowledged,
              last_sent_at, resend_count, payload
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12,
                    $13, $14, $15, $16, $17)
            """,
            alert_package["alert_id"],
            alert_package["timestamp_utc"],
            alert_package["alert_code"],
            alert_package["to"],
            alert_package["from"],
            alert_package["level"],
            alert_package["message"],
            alert_package["cerebro_instruction"],
            alert_package["sms_text"],
            alert_package["response_window"],
            alert_package.get("intel_reference"),
            alert_package["priority"],
            int(bool(alert_package["requires_acknowledgement"])),
            0,
            alert_package["timestamp_utc"],
            0,
            json.dumps(alert_package, ensure_ascii=True, sort_keys=True),
        )

    async def _ensure_ready(self) -> None:
        if self.database.connection is None:
            await self.database.connect()
        if self._schema_ready:
            return
        if self.database.backend == "sqlite":
            async with self.database._sqlite_lock:
                await self.database.connection.executescript(CEO_ALERT_SCHEMA)
                await self.database.connection.commit()
        else:
            statements = [statement.strip() for statement in CEO_ALERT_SCHEMA.split(";") if statement.strip()]
            for statement in statements:
                await self.database.execute(statement)
        self._schema_ready = True

    @staticmethod
    def _decode_payload(row: dict[str, Any]) -> dict[str, Any]:
        payload = row.get("payload")
        if isinstance(payload, str):
            try:
                return json.loads(payload)
            except json.JSONDecodeError:
                pass
        return dict(row)

    @staticmethod
    def _parse_time(value: str) -> datetime:
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return datetime.now(UTC)

    @staticmethod
    def _now() -> str:
        return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
