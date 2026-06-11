from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import Any
import uuid


def utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


@dataclass(slots=True, kw_only=True)
class OperationalIdentity:
    identity_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    codename: str
    username: str
    creation_date: str = field(default_factory=utc_now_iso)
    status: str = "BUILDING"
    nationality: str
    apparent_skill_level: str
    language_primary: str
    writing_style: dict[str, Any] = field(default_factory=dict)
    timezone_apparent: str
    activity_hours: dict[str, Any] = field(default_factory=dict)
    community: str
    current_phase: str = "PREPARATION"
    reputation_score: float = 0.0
    risk_score: int = 0
    last_active: str = field(default_factory=utc_now_iso)
    requires_ceo_authorization: bool = True
    ceo_authorized: bool = False
    ceo_authorization_date: str = ""
    cooling_period_days: int = 0

    def __post_init__(self) -> None:
        self.identity_id = str(self.identity_id or uuid.uuid4())
        self.codename = str(self.codename).strip()
        self.username = str(self.username).strip()
        self.status = str(self.status).strip().upper()
        self.nationality = str(self.nationality).strip()
        self.apparent_skill_level = str(self.apparent_skill_level).strip()
        self.language_primary = str(self.language_primary).strip()
        self.timezone_apparent = str(self.timezone_apparent).strip()
        self.community = str(self.community).strip()
        self.current_phase = str(self.current_phase).strip().upper()
        self.reputation_score = max(0.0, min(1.0, float(self.reputation_score)))
        self.risk_score = max(0, min(100, int(self.risk_score)))
        self.cooling_period_days = max(0, int(self.cooling_period_days))
        self.writing_style = dict(self.writing_style or {})
        self.activity_hours = dict(self.activity_hours or {})
        if not self.creation_date:
            self.creation_date = utc_now_iso()
        if not self.last_active:
            self.last_active = utc_now_iso()
        if self.ceo_authorized and not self.ceo_authorization_date:
            self.ceo_authorization_date = utc_now_iso()
        if not self.codename or not self.username:
            raise ValueError("codename and username are required")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True, kw_only=True)
class IdentityRiskAssessment:
    identity_id: str
    risk_score: int
    risk_level: str
    indicators: list[str] = field(default_factory=list)
    recommended_action: str
    timestamp: str = field(default_factory=utc_now_iso)

    def __post_init__(self) -> None:
        self.identity_id = str(self.identity_id)
        self.risk_score = max(0, min(100, int(self.risk_score)))
        self.risk_level = str(self.risk_level).upper()
        self.indicators = [str(item).strip() for item in self.indicators if str(item).strip()]
        self.recommended_action = str(self.recommended_action).strip()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
