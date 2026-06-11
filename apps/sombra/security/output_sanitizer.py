from __future__ import annotations

import re
from typing import Any


FORBIDDEN_EXTERNAL_PATTERNS = (
    r"sombra",
    r"infiltrat\w*",
    r"covert",
    r"dark[_\s-]*web(?:[_\s-]*identity)?",
    r"operational[_\s-]*identity",
    r"fake[_\s-]*profile",
    r"underground(?:[_\s-]*forum)?",
)


class OutputSanitizer:
    @classmethod
    def sanitize_external(cls, value: Any) -> Any:
        if isinstance(value, dict):
            cleaned: dict[str, Any] = {}
            for key, item in value.items():
                safe_key = cls._sanitize_key(str(key))
                cleaned[safe_key] = cls.sanitize_external(item)
            return cleaned
        if isinstance(value, list):
            return [cls.sanitize_external(item) for item in value]
        if isinstance(value, str):
            return cls._sanitize_text(value)
        return value

    @classmethod
    def contains_forbidden_external_reference(cls, value: Any) -> bool:
        text = str(value)
        if not isinstance(value, str):
            import json

            text = json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)
        return any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in FORBIDDEN_EXTERNAL_PATTERNS)

    @classmethod
    def _sanitize_key(cls, key: str) -> str:
        sanitized = key
        sanitized = re.sub(r"sombra", "engine", sanitized, flags=re.IGNORECASE)
        sanitized = re.sub(r"operational[_\s-]*identity", "classified_profile", sanitized, flags=re.IGNORECASE)
        return sanitized

    @classmethod
    def _sanitize_text(cls, text: str) -> str:
        sanitized = text
        replacements = (
            (r"sombra", "classified engine"),
            (r"infiltrat\w*", "restricted collection"),
            (r"covert", "classified"),
            (r"dark[_\s-]*web(?:[_\s-]*identity)?", "restricted source"),
            (r"operational[_\s-]*identity", "classified profile"),
            (r"fake[_\s-]*profile", "classified profile"),
            (r"underground(?:[_\s-]*forum)?", "restricted source"),
        )
        for pattern, replacement in replacements:
            sanitized = re.sub(pattern, replacement, sanitized, flags=re.IGNORECASE)
        return sanitized
