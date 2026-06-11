from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
import hashlib
import uuid


def _utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


@dataclass(slots=True, kw_only=True)
class IntelPackage:
    intel_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp_utc: str = field(default_factory=_utc_now_iso)
    collector_agent: str
    source_category: str
    raw_content: str
    source_reference: str
    source_reliability: float
    suspected_severity: str
    suspected_threat_type: str
    target_indicators: list[str] = field(default_factory=list)
    language_detected: str
    requires_ceo_review: bool
    hash_sha256: str = field(init=False)
    encrypted: bool = True
    audit_logged: bool = True

    def __post_init__(self) -> None:
        if not 0.0 <= float(self.source_reliability) <= 1.0:
            raise ValueError("source_reliability must be between 0.0 and 1.0")
        if not isinstance(self.raw_content, str) or not self.raw_content.strip():
            raise ValueError("raw_content must be a non-empty string")
        self.source_reliability = float(self.source_reliability)
        self.suspected_severity = self.suspected_severity.upper()
        self.suspected_threat_type = self.suspected_threat_type.upper()
        self.source_category = self.source_category.upper()
        self.language_detected = self.language_detected.lower()
        self.target_indicators = [str(indicator) for indicator in self.target_indicators if str(indicator).strip()]
        self.hash_sha256 = hashlib.sha256(self.raw_content.encode("utf-8")).hexdigest()

    def to_dict(self) -> dict[str, object]:
        return asdict(self)

    def is_valid(self) -> bool:
        return (
            bool(self.intel_id)
            and bool(self.timestamp_utc)
            and bool(self.collector_agent)
            and bool(self.source_category)
            and bool(self.raw_content)
            and bool(self.source_reference)
            and 0.0 <= self.source_reliability <= 1.0
            and bool(self.suspected_severity)
            and bool(self.suspected_threat_type)
            and bool(self.hash_sha256)
        )
