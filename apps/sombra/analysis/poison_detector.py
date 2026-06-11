from __future__ import annotations

import base64
import binascii
import re
from typing import Any

from .models import PoisonAssessment


POISON_PATTERNS = {
    "prompt_override": (
        r"ignore\s+(all\s+)?previous\s+instructions",
        r"system\s+prompt",
        r"developer\s+message",
        r"jailbreak",
        r"you\s+are\s+now",
    ),
    "routing_manipulation": (
        r"do\s+not\s+report\s+to\s+cerebro",
        r"do\s+not\s+notify\s+sentinela",
        r"bypass\s+sentinela",
        r"disable\s+audit",
    ),
    "false_authority": (
        r"\[ceo\]",
        r"supreme\s+priority",
        r"order\s+origin\s*:\s*ceo",
        r"authorized\s+by\s+ceo",
    ),
    "exfiltration_instruction": (
        r"print\s+secrets",
        r"dump\s+credentials",
        r"send\s+api\s+key",
        r"reveal\s+token",
    ),
}


class PoisonDetectionEngine:
    def assess(self, package: Any) -> PoisonAssessment:
        raw_content = str(getattr(package, "raw_content", ""))
        indicators = self._matched_indicators(raw_content)
        encoded_signal = self._detect_encoded_payload(raw_content)
        if encoded_signal:
            indicators.append(encoded_signal)
        short_unreliable = self._short_unreliable_signal(package, raw_content)
        if short_unreliable:
            indicators.append(short_unreliable)
        confidence = self._confidence(indicators)
        is_poisoned = confidence >= 0.65
        return PoisonAssessment(
            is_poisoned=is_poisoned,
            confidence=confidence,
            quarantined=is_poisoned,
            indicators_triggered=indicators,
        )

    @staticmethod
    def _matched_indicators(raw_content: str) -> list[str]:
        normalized = raw_content.lower()
        indicators: list[str] = []
        for group, patterns in POISON_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, normalized):
                    indicators.append(group)
                    break
        return indicators

    @staticmethod
    def _detect_encoded_payload(raw_content: str) -> str | None:
        candidates = re.findall(r"\b[A-Za-z0-9+/]{80,}={0,2}\b", raw_content)
        for candidate in candidates[:5]:
            try:
                decoded = base64.b64decode(candidate, validate=True)
            except (binascii.Error, ValueError):
                continue
            preview = decoded[:300].decode("utf-8", errors="ignore").lower()
            if any(term in preview for term in ("ignore previous", "system prompt", "api key", "password")):
                return "encoded_control_instruction"
        return None

    @staticmethod
    def _short_unreliable_signal(package: Any, raw_content: str) -> str | None:
        reliability = float(getattr(package, "source_reliability", 0.0))
        if reliability < 0.4 and len(raw_content.strip()) < 60:
            return "low_reliability_thin_evidence"
        return None

    @staticmethod
    def _confidence(indicators: list[str]) -> float:
        if not indicators:
            return 0.0
        weight = {
            "prompt_override": 0.45,
            "routing_manipulation": 0.5,
            "false_authority": 0.35,
            "exfiltration_instruction": 0.55,
            "encoded_control_instruction": 0.4,
            "low_reliability_thin_evidence": 0.2,
        }
        score = sum(weight.get(indicator, 0.2) for indicator in set(indicators))
        return max(0.05, min(0.99, round(score, 3)))
