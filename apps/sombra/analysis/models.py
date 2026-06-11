from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import Any


def utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


@dataclass(slots=True, kw_only=True)
class ClassifiedIntel:
    intel_id: str
    timestamp_utc: str
    threat_type: str
    severity: str
    confidence: float
    affected_clients: list[str] = field(default_factory=list)
    legal_risk_flag: bool
    routing: list[str] = field(default_factory=list)
    findings: str
    evidence: str
    time_window: str
    order_origin: str
    source_mission: str
    primary_client: str
    affected_assets: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.confidence = max(0.0, min(1.0, float(self.confidence)))
        self.threat_type = self.threat_type.upper()
        self.severity = self.severity.upper()
        self.affected_clients = _clean_list(self.affected_clients)
        self.routing = _clean_list(self.routing)
        self.affected_assets = _clean_list(self.affected_assets)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True, kw_only=True)
class ThreatScore:
    base: int
    time_multiplier: float
    client_impact: int
    confidence_adjusted: float
    pattern_boost: int
    final: int

    def __post_init__(self) -> None:
        self.base = _clamp_int(self.base)
        self.time_multiplier = max(0.1, float(self.time_multiplier))
        self.client_impact = _clamp_int(self.client_impact)
        self.confidence_adjusted = max(0.0, min(100.0, float(self.confidence_adjusted)))
        self.pattern_boost = _clamp_int(self.pattern_boost)
        self.final = _clamp_int(self.final)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True, kw_only=True)
class ThreatPrediction:
    predicted_vector: str
    time_estimate: str
    high_risk_targets: list[str] = field(default_factory=list)
    recommended_defense: str
    confidence: float
    data_basis: str

    def __post_init__(self) -> None:
        self.confidence = max(0.0, min(1.0, float(self.confidence)))
        self.high_risk_targets = _clean_list(self.high_risk_targets)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True, kw_only=True)
class PoisonAssessment:
    is_poisoned: bool
    confidence: float
    quarantined: bool
    indicators_triggered: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.confidence = max(0.0, min(1.0, float(self.confidence)))
        self.quarantined = bool(self.quarantined or self.is_poisoned)
        self.indicators_triggered = _clean_list(self.indicators_triggered)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True, kw_only=True)
class EnrichedIntel:
    clients: list[str]
    assets: list[str]
    indicators: list[str]
    sectors: list[str]
    time_window: str
    source_mission: str
    primary_client: str
    evidence_summary: str

    def __post_init__(self) -> None:
        self.clients = _clean_list(self.clients)
        self.assets = _clean_list(self.assets)
        self.indicators = _clean_list(self.indicators)
        self.sectors = _clean_list(self.sectors)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True, kw_only=True)
class AnalysisResult:
    classified: ClassifiedIntel
    score: ThreatScore
    prediction: ThreatPrediction
    poison: PoisonAssessment
    enriched: EnrichedIntel
    accepted: bool
    route_locked: bool
    generated_at_utc: str = field(default_factory=utc_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return {
            "accepted": self.accepted,
            "route_locked": self.route_locked,
            "generated_at_utc": self.generated_at_utc,
            "classified": self.classified.to_dict(),
            "score": self.score.to_dict(),
            "prediction": self.prediction.to_dict(),
            "poison": self.poison.to_dict(),
            "enriched": self.enriched.to_dict(),
        }


def _clean_list(values: list[Any]) -> list[str]:
    cleaned: list[str] = []
    for value in values:
        text = str(value).strip()
        if text and text not in cleaned:
            cleaned.append(text)
    return cleaned


def _clamp_int(value: int | float) -> int:
    return max(0, min(100, int(round(float(value)))))
