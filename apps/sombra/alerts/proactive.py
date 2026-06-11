from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

from apps.sombra.memory.database import LOG_DIR


PROACTIVE_LOG = LOG_DIR / "proactive.log"


class ProactiveAlertProtocol:
    async def evaluate(self, intel: Any, score: Any) -> bool:
        trigger = self._trigger_name(intel, score)
        if trigger is None:
            return False
        try:
            setattr(intel, "order_origin", "PROACTIVE")
        except Exception:
            await asyncio.to_thread(self._append_proactive_log, "ORDER_ORIGIN_UPDATE_FAILED", intel, score)
        await asyncio.to_thread(self._append_proactive_log, trigger, intel, score)
        return True

    @staticmethod
    def _trigger_name(intel: Any, score: Any) -> str | None:
        final_score = int(getattr(score, "final", 0))
        threat_type = str(getattr(intel, "threat_type", "")).upper()
        if final_score >= 75:
            return "SCORE_FINAL_75_PLUS"
        if threat_type == "CREDENTIAL_EXPOSURE" and final_score >= 50:
            return "CREDENTIAL_EXPOSURE_50_PLUS"
        if threat_type == "ACTIVE_ATTACK_CAMPAIGN":
            return "ACTIVE_ATTACK_CAMPAIGN"
        if threat_type == "RANSOMWARE_CAMPAIGN":
            return "RANSOMWARE_CAMPAIGN"
        return None

    @staticmethod
    def _append_proactive_log(trigger: str, intel: Any, score: Any) -> None:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        payload = {
            "trigger": trigger,
            "intel_id": str(getattr(intel, "intel_id", "")),
            "threat_type": str(getattr(intel, "threat_type", "")),
            "severity": str(getattr(intel, "severity", "")),
            "score_final": int(getattr(score, "final", 0)),
            "order_origin": str(getattr(intel, "order_origin", "")),
        }
        with Path(PROACTIVE_LOG).open("a", encoding="utf-8") as log_file:
            log_file.write(json.dumps(payload, sort_keys=True) + "\n")
