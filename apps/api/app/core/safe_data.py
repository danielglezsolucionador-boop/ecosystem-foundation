from __future__ import annotations

from datetime import UTC, datetime
import json
from typing import Any

from app.core.database import get_row_value


SAFE_FALLBACK_MESSAGE = "Safe fallback because source data is missing or incomplete."


def safe_dict(value: Any) -> dict:
    return value if isinstance(value, dict) else {}


def safe_list(value: Any) -> list:
    return value if isinstance(value, list) else []


def safe_count(value: Any) -> int:
    if isinstance(value, int):
        return max(value, 0)
    if isinstance(value, (list, tuple, set, dict)):
        return len(value)
    try:
        return max(int(value), 0)
    except (TypeError, ValueError):
        return 0


def safe_iso_datetime(value: Any = None) -> str:
    if isinstance(value, datetime):
        return value.astimezone(UTC).isoformat().replace("+00:00", "Z")
    text = str(value or "").strip()
    if text:
        return text
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def safe_payload_json(raw_payload: Any) -> dict | None:
    if raw_payload is None or raw_payload == "":
        return None
    if isinstance(raw_payload, dict):
        return raw_payload
    if isinstance(raw_payload, bytes):
        raw_payload = raw_payload.decode("utf-8", errors="ignore")
    try:
        payload = json.loads(str(raw_payload))
    except (TypeError, ValueError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def safe_json_value(raw_payload: Any, default: Any = None) -> Any:
    if raw_payload is None or raw_payload == "":
        return default
    if isinstance(raw_payload, (dict, list, int, float, bool)):
        return raw_payload
    if isinstance(raw_payload, bytes):
        raw_payload = raw_payload.decode("utf-8", errors="ignore")
    try:
        return json.loads(str(raw_payload))
    except (TypeError, ValueError, json.JSONDecodeError):
        return default


def safe_payload(row: Any, key: str = "payload_json", index: int | None = 0) -> dict | None:
    return safe_payload_json(get_row_value(row, key, index=index))


def safe_endpoint_response(
    default_payload: dict | None = None,
    *,
    mode: str = "degraded",
    fallback: bool = True,
    message: str = SAFE_FALLBACK_MESSAGE,
    error_context: str | None = None,
) -> dict:
    payload = {
        "status": "ok",
        "mode": mode,
        "fallback": fallback,
        "items": [],
        "count": 0,
        "requires_ceo_action": False,
        "message": message,
        "external_connection_enabled": False,
        "runtime_connected": False,
        "payment_connected": False,
        "sunat_enabled": False,
        "local_agent_enabled": False,
    }
    payload.update(default_payload or {})
    if error_context:
        payload["error_context"] = error_context
    return payload
