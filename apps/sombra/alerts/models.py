from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
import hashlib
import json
from typing import Any
import uuid


def utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


@dataclass(slots=True, kw_only=True)
class SombraAlert:
    alert_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp_utc: str = field(default_factory=utc_now_iso)
    mission_id: str
    order_origin: str
    severity: str
    threat_score: int
    confidence_level: float
    threat_type: str
    target_client: str
    target_assets: list[str] = field(default_factory=list)
    blast_radius: str
    findings: str
    evidence_summary: str
    time_window: str
    historical_context: str
    recommended_action: str
    route_to: list[str] = field(default_factory=list)
    forja_construction_needed: bool
    forja_specification: str
    source: str = "CLASSIFIED"
    sombra_version: str = "ACTIVE"
    hash_sha256: str = field(init=False)
    audit_logged: bool = True

    def __post_init__(self) -> None:
        self.source = "CLASSIFIED"
        self.sombra_version = "ACTIVE"
        self.audit_logged = True
        self.severity = str(self.severity).upper()
        self.threat_type = str(self.threat_type).upper()
        self.order_origin = str(self.order_origin).upper()
        self.threat_score = max(0, min(100, int(self.threat_score)))
        self.confidence_level = max(0.0, min(1.0, float(self.confidence_level)))
        self.target_assets = [str(asset) for asset in self.target_assets if str(asset).strip()]
        self.route_to = [str(route).upper() for route in self.route_to if str(route).strip()]
        self.hash_sha256 = self._hash_alert()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def _hash_alert(self) -> str:
        payload = {
            "alert_id": self.alert_id,
            "mission_id": self.mission_id,
            "timestamp_utc": self.timestamp_utc,
            "severity": self.severity,
            "threat_score": self.threat_score,
            "threat_type": self.threat_type,
            "target_client": self.target_client,
            "target_assets": self.target_assets,
            "findings": self.findings,
            "recommended_action": self.recommended_action,
        }
        return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()
