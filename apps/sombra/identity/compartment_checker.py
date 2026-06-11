from __future__ import annotations

import re

from .manager import IdentityManager


class CompartmentChecker:
    def __init__(self, manager: IdentityManager) -> None:
        self.manager = manager

    async def check_community_conflict(self, community: str, exclude_identity_id: str) -> bool:
        await self.manager._ensure_ready()
        row = await self.manager.database.fetchrow(
            """
            SELECT identity_id FROM sombra_identities
            WHERE LOWER(community) = LOWER($1)
              AND identity_id != $2
              AND status = 'ACTIVE'
            LIMIT 1
            """,
            community,
            exclude_identity_id,
        )
        return row is not None

    async def check_content_similarity(self, content_a: str, content_b: str) -> float:
        words_a = self._words(content_a)
        words_b = self._words(content_b)
        if not words_a or not words_b:
            return 0.0
        overlap = words_a.intersection(words_b)
        union = words_a.union(words_b)
        return round(len(overlap) / len(union), 4)

    async def validate_before_action(self, identity_id: str, community: str, content: str) -> dict[str, object]:
        await self.manager._ensure_ready()
        conflicts: list[str] = []
        warnings: list[str] = []
        try:
            identity = await self.manager.get_identity(identity_id)
        except ValueError:
            return {
                "can_proceed": False,
                "conflicts": ["identity_not_found"],
                "warnings": [],
            }
        if identity.status not in {"ACTIVE", "BUILDING"}:
            conflicts.append(f"identity_status_{identity.status.lower()}")
        community_conflict = await self.check_community_conflict(community, identity_id)
        if community_conflict:
            conflicts.append("active_identity_already_in_community")
        similarity = await self.check_content_similarity(content, f"{identity.codename} {identity.username} {community}")
        if similarity >= 0.45:
            warnings.append("content_too_similar_to_identity_metadata")
        if len(content.strip()) < 20:
            warnings.append("content_too_short_for_safe_compartment_validation")
        result = {
            "can_proceed": not conflicts,
            "conflicts": conflicts,
            "warnings": warnings,
            "similarity_score": similarity,
            "identity_status": identity.status,
        }
        await self.manager.blackbox.log(
            "IDENTITY_COMPARTMENT_VALIDATION",
            identity_id,
            {
                "community": community,
                "can_proceed": result["can_proceed"],
                "conflicts": conflicts,
                "warnings": warnings,
                "similarity_score": similarity,
            },
            order_origin="COMPARTMENT_CHECKER",
        )
        return result

    @staticmethod
    def _words(content: str) -> set[str]:
        return {
            word
            for word in re.findall(r"[a-zA-Z0-9_]{3,}", content.lower())
            if word not in {"the", "and", "for", "with", "this", "that"}
        }
