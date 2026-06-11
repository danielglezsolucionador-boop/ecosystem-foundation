from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

from apps.sombra.memory import BlackBoxAuditCore, DatabaseConnection, GlobalMemoryLayer
from apps.sombra.memory.database import LOG_DIR

from .models import SombraAlert


ALERTS_LOG = LOG_DIR / "alerts.log"
FORJA_THREAT_TYPES = {"ZERO_DAY_EXPLOIT", "RANSOMWARE_CAMPAIGN", "ACTIVE_ATTACK_CAMPAIGN"}

ALERT_SCHEMA = """
CREATE TABLE IF NOT EXISTS sombra_alerts (
  alert_id TEXT PRIMARY KEY,
  timestamp_utc TEXT,
  mission_id TEXT,
  order_origin TEXT,
  severity TEXT,
  threat_score INTEGER,
  confidence_level REAL,
  threat_type TEXT,
  target_client TEXT,
  target_assets TEXT,
  blast_radius TEXT,
  findings TEXT,
  evidence_summary TEXT,
  time_window TEXT,
  historical_context TEXT,
  recommended_action TEXT,
  route_to TEXT,
  forja_construction_needed INTEGER,
  forja_specification TEXT,
  source TEXT,
  sombra_version TEXT,
  hash_sha256 TEXT,
  audit_logged INTEGER
);

CREATE INDEX IF NOT EXISTS idx_sombra_alerts_severity
  ON sombra_alerts(severity);

CREATE INDEX IF NOT EXISTS idx_sombra_alerts_timestamp
  ON sombra_alerts(timestamp_utc);
"""


class AlertGenerationEngine:
    def __init__(self, database: DatabaseConnection | None = None, blackbox: BlackBoxAuditCore | None = None) -> None:
        self.database = database if database is not None else DatabaseConnection()
        self.blackbox = blackbox if blackbox is not None else BlackBoxAuditCore(self.database)
        self.memory = GlobalMemoryLayer(self.database)
        self._schema_ready = False
        self._owns_connection = database is None

    async def disconnect(self) -> None:
        if self._owns_connection:
            await self.database.disconnect()

    async def generate_alert(self, intel: Any, score: Any, prediction: Any) -> SombraAlert:
        await self._ensure_ready()
        threat_type = str(getattr(intel, "threat_type", "INTELLIGENCE_TREND")).upper()
        severity = str(getattr(intel, "severity", "LOW")).upper()
        affected_clients = list(getattr(intel, "affected_clients", []) or [])
        target_assets = list(getattr(intel, "affected_assets", []) or getattr(prediction, "high_risk_targets", []) or [])
        historical_context = await self._historical_context(threat_type)
        alert = SombraAlert(
            mission_id=str(getattr(intel, "intel_id", "")),
            order_origin=str(getattr(intel, "order_origin", "ANALYSIS")),
            severity=severity,
            threat_score=int(getattr(score, "final", 0)),
            confidence_level=float(getattr(intel, "confidence", getattr(prediction, "confidence", 0.0))),
            threat_type=threat_type,
            target_client=self._target_client(intel, affected_clients),
            target_assets=target_assets,
            blast_radius=self._blast_radius(affected_clients),
            findings=str(getattr(intel, "findings", "")),
            evidence_summary=str(getattr(intel, "evidence", ""))[:1000],
            time_window=str(getattr(intel, "time_window", getattr(prediction, "time_estimate", "monitor"))),
            historical_context=historical_context,
            recommended_action=self._recommended_action(threat_type, severity),
            route_to=list(getattr(intel, "routing", []) or ["CEREBRO"]),
            forja_construction_needed=threat_type in FORJA_THREAT_TYPES,
            forja_specification=self._forja_specification(threat_type, prediction),
        )
        await self._store_alert(alert)
        await self.blackbox.log(
            "ALERT_GENERATED",
            alert.alert_id,
            {
                "mission_id": alert.mission_id,
                "severity": alert.severity,
                "threat_type": alert.threat_type,
                "threat_score": alert.threat_score,
                "route_to": alert.route_to,
            },
            order_origin="ALERT_ENGINE",
        )
        await asyncio.to_thread(self._append_alert_log, alert)
        return alert

    async def get_alerts_by_severity(self, severity: str) -> list[dict[str, Any]]:
        await self._ensure_ready()
        rows = await self.database.fetch(
            """
            SELECT * FROM sombra_alerts
            WHERE severity = $1
            ORDER BY threat_score DESC, timestamp_utc DESC
            """,
            severity.upper(),
        )
        return [self._decode_row(row) for row in rows]

    async def get_recent_alerts(self, hours: int = 24) -> list[dict[str, Any]]:
        await self._ensure_ready()
        if self.database.backend == "postgresql":
            rows = await self.database.fetch(
                """
                SELECT * FROM sombra_alerts
                WHERE timestamp_utc >= NOW() - ($1 * INTERVAL '1 hour')
                ORDER BY threat_score DESC, timestamp_utc DESC
                """,
                int(hours),
            )
        else:
            rows = await self.database.fetch(
                """
                SELECT * FROM sombra_alerts
                WHERE datetime(timestamp_utc) >= datetime('now', $1)
                ORDER BY threat_score DESC, timestamp_utc DESC
                """,
                f"-{int(hours)} hours",
            )
        return [self._decode_row(row) for row in rows]

    async def _store_alert(self, alert: SombraAlert) -> None:
        await self.database.execute(
            """
            INSERT INTO sombra_alerts (
              alert_id, timestamp_utc, mission_id, order_origin, severity,
              threat_score, confidence_level, threat_type, target_client,
              target_assets, blast_radius, findings, evidence_summary,
              time_window, historical_context, recommended_action, route_to,
              forja_construction_needed, forja_specification, source,
              sombra_version, hash_sha256, audit_logged
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12,
                    $13, $14, $15, $16, $17, $18, $19, $20, $21, $22, $23)
            """,
            alert.alert_id,
            alert.timestamp_utc,
            alert.mission_id,
            alert.order_origin,
            alert.severity,
            alert.threat_score,
            alert.confidence_level,
            alert.threat_type,
            alert.target_client,
            json.dumps(alert.target_assets, sort_keys=True),
            alert.blast_radius,
            alert.findings,
            alert.evidence_summary,
            alert.time_window,
            alert.historical_context,
            alert.recommended_action,
            json.dumps(alert.route_to, sort_keys=True),
            int(alert.forja_construction_needed),
            alert.forja_specification,
            alert.source,
            alert.sombra_version,
            alert.hash_sha256,
            int(alert.audit_logged),
        )

    async def _ensure_ready(self) -> None:
        if self.database.connection is None:
            await self.database.connect()
        if self._schema_ready:
            return
        if self.database.backend == "sqlite":
            async with self.database._sqlite_lock:
                await self.database.connection.executescript(ALERT_SCHEMA)
                await self.database.connection.commit()
        else:
            statements = [statement.strip() for statement in ALERT_SCHEMA.split(";") if statement.strip()]
            for statement in statements:
                await self.database.execute(statement)
        self._schema_ready = True

    async def _historical_context(self, threat_type: str) -> str:
        try:
            history = await self.memory.get_pattern_history(threat_type)
        except Exception:
            return "Historical context unavailable."
        if not history:
            return "No previous pattern history found for this threat type."
        highest = max(int(row.get("threat_score") or 0) for row in history)
        return f"{len(history)} historical record(s) for {threat_type}; highest previous score {highest}."

    @staticmethod
    def _blast_radius(affected_clients: list[Any]) -> str:
        count = len([client for client in affected_clients if str(client).strip()])
        if count == 0:
            return "ECOSYSTEM_WIDE"
        if count == 1:
            return "SINGLE_CLIENT"
        return "MULTI_CLIENT"

    @staticmethod
    def _recommended_action(threat_type: str, severity: str) -> str:
        if severity == "CRITICAL" and threat_type == "CREDENTIAL_EXPOSURE":
            return (
                "Force immediate password reset for all affected accounts. Notify security team. "
                "Enable MFA if not active. Owner: SENTINELA. Deadline: 2 hours."
            )
        if severity == "CRITICAL" and threat_type == "ACTIVE_ATTACK_CAMPAIGN":
            return "Activate incident response protocol. Isolate affected systems immediately. Owner: SENTINELA. Deadline: NOW."
        if severity == "CRITICAL" and threat_type == "RANSOMWARE_CAMPAIGN":
            return (
                "Isolate backup systems immediately. Review all privileged access. "
                "Owner: SENTINELA + FORJA. Deadline: NOW."
            )
        if severity == "CRITICAL":
            return (
                "Activate urgent security review. Validate exposure, apply immediate mitigation, "
                "and escalate to SENTINELA. Owner: SENTINELA. Deadline: NOW."
            )
        if severity == "HIGH":
            return (
                "Elevate monitoring on affected assets. Review exposure and apply patches. "
                "Owner: SENTINELA. Deadline: 24 hours."
            )
        if severity == "MEDIUM":
            return "Schedule review and apply available mitigations. Owner: SENTINELA. Deadline: 72 hours."
        return "Log for awareness and trend tracking. No immediate action required. Owner: CEREBRO."

    @staticmethod
    def _forja_specification(threat_type: str, prediction: Any) -> str:
        if threat_type not in FORJA_THREAT_TYPES:
            return ""
        vector = str(getattr(prediction, "predicted_vector", "unknown vector"))
        defense = str(getattr(prediction, "recommended_defense", "prepare defensive capability"))
        return f"Build or update defensive capability for {threat_type}: vector={vector}; defense={defense}."

    @staticmethod
    def _target_client(intel: Any, affected_clients: list[Any]) -> str:
        primary = str(getattr(intel, "primary_client", "") or "").strip()
        if primary and primary != "UNASSIGNED":
            return primary
        if affected_clients:
            return str(affected_clients[0])
        return "ECOSYSTEM"

    @staticmethod
    def _decode_row(row: dict[str, Any]) -> dict[str, Any]:
        decoded = dict(row)
        for key in ("target_assets", "route_to"):
            value = decoded.get(key)
            if isinstance(value, str):
                try:
                    decoded[key] = json.loads(value)
                except json.JSONDecodeError:
                    decoded[key] = value
        decoded["forja_construction_needed"] = bool(decoded.get("forja_construction_needed"))
        decoded["audit_logged"] = bool(decoded.get("audit_logged"))
        return decoded

    @staticmethod
    def _append_alert_log(alert: SombraAlert) -> None:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        with Path(ALERTS_LOG).open("a", encoding="utf-8") as log_file:
            log_file.write(json.dumps(alert.to_dict(), sort_keys=True, default=str) + "\n")
