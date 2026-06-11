from __future__ import annotations

from datetime import UTC, datetime

from .manager import IdentityManager
from .models import IdentityRiskAssessment, OperationalIdentity


class IdentityLifecycleManager:
    def __init__(self, manager: IdentityManager) -> None:
        self.manager = manager

    async def assess_all_identities(self) -> list[IdentityRiskAssessment]:
        identities = await self.manager.get_all_active()
        assessments: list[IdentityRiskAssessment] = []
        for identity in identities:
            indicators: list[str] = []
            risk_score = identity.risk_score
            days_since_last_active = self._days_since(identity.last_active)
            days_since_creation = self._days_since(identity.creation_date)
            if days_since_last_active > 30:
                risk_score += 20
                indicators.append("inactive_over_30_days")
            if identity.reputation_score < 0.3:
                risk_score += 15
                indicators.append("low_reputation_score")
            if identity.status == "BUILDING" and days_since_creation > 60:
                risk_score += 10
                indicators.append("building_phase_over_60_days")
            risk_score = max(0, min(100, risk_score))
            await self.manager.update_risk_score(identity.identity_id, risk_score)
            assessments.append(
                IdentityRiskAssessment(
                    identity_id=identity.identity_id,
                    risk_score=risk_score,
                    risk_level=self._risk_level(risk_score),
                    indicators=indicators,
                    recommended_action=self._recommended_action(risk_score, indicators),
                )
            )
        return assessments

    async def get_identities_needing_action(self) -> list[OperationalIdentity]:
        await self.manager._ensure_ready()
        rows = await self.manager.database.fetch(
            """
            SELECT * FROM sombra_identities
            WHERE risk_score >= 60
            ORDER BY risk_score DESC
            """
        )
        return [self.manager._row_to_identity(row) for row in rows]

    async def calculate_cooling_period(self, identity: OperationalIdentity) -> int:
        if identity.risk_score >= 80:
            return 90
        if identity.risk_score >= 60:
            return 45
        return 30

    async def get_status_summary(self) -> dict[str, object]:
        await self.manager._ensure_ready()
        rows = await self.manager.database.fetch(
            """
            SELECT status, COUNT(*) AS count
            FROM sombra_identities
            GROUP BY status
            ORDER BY count DESC
            """
        )
        aggregate = await self.manager.database.fetchrow(
            """
            SELECT AVG(risk_score) AS average_risk_score,
                   SUM(CASE WHEN risk_score >= 60 THEN 1 ELSE 0 END) AS identities_at_risk_count,
                   COUNT(*) AS total_identities
            FROM sombra_identities
            """
        )
        return {
            "counts_by_status": {row["status"]: int(row["count"]) for row in rows},
            "average_risk_score": round(float((aggregate or {}).get("average_risk_score") or 0.0), 2),
            "identities_at_risk_count": int((aggregate or {}).get("identities_at_risk_count") or 0),
            "total_identities": int((aggregate or {}).get("total_identities") or 0),
        }

    @staticmethod
    def _days_since(value: str) -> int:
        parsed = IdentityLifecycleManager._parse_datetime(value)
        now = datetime.now(UTC)
        return max(0, (now - parsed).days)

    @staticmethod
    def _parse_datetime(value: str) -> datetime:
        try:
            parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        except ValueError:
            return datetime.now(UTC)
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=UTC)
        return parsed.astimezone(UTC)

    @staticmethod
    def _risk_level(score: int) -> str:
        if score >= 80:
            return "CRITICAL"
        if score >= 60:
            return "HIGH"
        if score >= 35:
            return "MEDIUM"
        return "LOW"

    @staticmethod
    def _recommended_action(score: int, indicators: list[str]) -> str:
        if score >= 80:
            return "retire identity and enter cooling period"
        if score >= 60:
            return "restrict activity and review compartment"
        if indicators:
            return "monitor and improve profile quality"
        return "continue lifecycle monitoring"
