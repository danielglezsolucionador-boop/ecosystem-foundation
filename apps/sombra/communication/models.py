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
class OutboundMessage:
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp_utc: str = field(default_factory=utc_now_iso)
    sender: str = "SOMBRA"
    recipient: str
    priority: str
    classification: str
    payload: dict[str, Any]
    hash_sha256: str = field(init=False)
    delivered: bool = False
    delivery_attempts: int = 0
    last_attempt: str = ""

    def __post_init__(self) -> None:
        self.sender = "SOMBRA"
        self.recipient = str(self.recipient).upper()
        self.priority = str(self.priority).upper()
        self.classification = str(self.classification).upper()
        self.payload = dict(self.payload or {})
        self.delivery_attempts = max(0, int(self.delivery_attempts))
        self.hash_sha256 = self._hash_payload()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def _hash_payload(self) -> str:
        content = {
            "message_id": self.message_id,
            "timestamp_utc": self.timestamp_utc,
            "sender": self.sender,
            "recipient": self.recipient,
            "priority": self.priority,
            "classification": self.classification,
            "payload": self.payload,
        }
        return hashlib.sha256(json.dumps(content, sort_keys=True).encode("utf-8")).hexdigest()


@dataclass(slots=True, kw_only=True)
class InboundOrder:
    order_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp_utc: str = field(default_factory=utc_now_iso)
    sender: str
    order_type: str
    target: str
    priority: str
    is_ceo_order: bool
    raw: dict[str, Any]

    def __post_init__(self) -> None:
        self.sender = str(self.sender or "UNKNOWN").upper()
        self.order_type = str(self.order_type).upper()
        self.target = str(self.target)
        self.priority = str(self.priority).upper()
        self.raw = dict(self.raw or {})

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
