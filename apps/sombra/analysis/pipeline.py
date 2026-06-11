from __future__ import annotations

from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Any

from apps.sombra.memory.database import LOG_DIR

from .classifier import ThreatClassificationEngine
from .enricher import ThreatEnrichmentEngine
from .models import AnalysisResult
from .poison_detector import PoisonDetectionEngine
from .predictor import ThreatPredictionEngine
from .scorer import ThreatScoringEngine


ANALYSIS_PIPELINE_LOG = LOG_DIR / "analysis_pipeline.log"


class SombraAnalysisPipeline:
    def __init__(
        self,
        classifier: ThreatClassificationEngine | None = None,
        scorer: ThreatScoringEngine | None = None,
        predictor: ThreatPredictionEngine | None = None,
        poison_detector: PoisonDetectionEngine | None = None,
        enricher: ThreatEnrichmentEngine | None = None,
    ) -> None:
        self.classifier = classifier if classifier is not None else ThreatClassificationEngine()
        self.scorer = scorer if scorer is not None else ThreatScoringEngine()
        self.predictor = predictor if predictor is not None else ThreatPredictionEngine()
        self.poison_detector = poison_detector if poison_detector is not None else PoisonDetectionEngine()
        self.enricher = enricher if enricher is not None else ThreatEnrichmentEngine()

    def analyze(self, package: Any) -> AnalysisResult:
        self._stage_1_validate_package(package)
        poison = self._stage_2_detect_poison(package)
        enriched = self._stage_3_enrich(package)
        classified = self._stage_4_classify(package)
        self._apply_enrichment(classified, enriched)
        score = self._stage_5_score(classified)
        prediction = self._stage_6_predict(classified, score)
        accepted, route_locked = self._stage_7_route_control(classified, poison)
        result = AnalysisResult(
            classified=classified,
            score=score,
            prediction=prediction,
            poison=poison,
            enriched=enriched,
            accepted=accepted,
            route_locked=route_locked,
        )
        self._append_analysis_log(package, result)
        return result

    def analyze_many(self, packages: list[Any]) -> list[AnalysisResult]:
        results: list[AnalysisResult] = []
        for package in packages:
            results.append(self.analyze(package))
        return results

    @staticmethod
    def _stage_1_validate_package(package: Any) -> None:
        required_fields = (
            "intel_id",
            "timestamp_utc",
            "collector_agent",
            "source_category",
            "raw_content",
            "source_reference",
            "source_reliability",
            "suspected_severity",
            "suspected_threat_type",
            "target_indicators",
            "language_detected",
            "requires_ceo_review",
            "hash_sha256",
        )
        missing = [field for field in required_fields if not hasattr(package, field)]
        if missing:
            raise ValueError(f"analysis rejected invalid IntelPackage: missing {', '.join(missing)}")
        if hasattr(package, "is_valid") and not package.is_valid():
            raise ValueError("analysis rejected invalid IntelPackage: is_valid returned false")

    def _stage_2_detect_poison(self, package: Any):
        return self.poison_detector.assess(package)

    def _stage_3_enrich(self, package: Any):
        return self.enricher.enrich(package)

    def _stage_4_classify(self, package: Any):
        return self.classifier.classify(package)

    def _stage_5_score(self, classified):
        return self.scorer.calculate_score(classified)

    def _stage_6_predict(self, classified, score):
        return self.predictor.predict(classified, score)

    @staticmethod
    def _stage_7_route_control(classified, poison):
        if poison.quarantined:
            classified.routing = ["CEREBRO"]
            classified.legal_risk_flag = True
            classified.findings = f"{classified.findings} Evidence quarantined by poison detector."
            return False, True
        return True, False

    @staticmethod
    def _apply_enrichment(classified, enriched) -> None:
        classified.affected_clients = enriched.clients
        classified.affected_assets = enriched.assets or classified.affected_assets
        classified.primary_client = enriched.primary_client
        classified.source_mission = enriched.source_mission
        if enriched.time_window != "monitor":
            classified.time_window = enriched.time_window
        if enriched.evidence_summary:
            classified.evidence = f"{classified.evidence}; enriched={enriched.evidence_summary}"

    @staticmethod
    def _append_analysis_log(package: Any, result: AnalysisResult) -> None:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        row = {
            "timestamp_utc": datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
            "intel_id": str(getattr(package, "intel_id", "")),
            "collector_agent": str(getattr(package, "collector_agent", "")),
            "threat_type": result.classified.threat_type,
            "severity": result.classified.severity,
            "score": result.score.final,
            "accepted": result.accepted,
            "route_locked": result.route_locked,
            "routing": result.classified.routing,
        }
        with Path(ANALYSIS_PIPELINE_LOG).open("a", encoding="utf-8") as log_file:
            log_file.write(json.dumps(row, sort_keys=True, default=str) + "\n")
