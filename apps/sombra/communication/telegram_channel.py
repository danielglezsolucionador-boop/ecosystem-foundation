from __future__ import annotations

import logging
import os
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
import json

try:
    import httpx
except ImportError:  # pragma: no cover - fallback keeps alerts usable in lean installs.
    httpx = None  # type: ignore[assignment]


logger = logging.getLogger(__name__)


class TelegramCEOChannel:
    def __init__(self) -> None:
        self.token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = os.getenv("TELEGRAM_CEO_CHAT_ID")
        self.base_url = f"https://api.telegram.org/bot{self.token}" if self.token else ""

    async def send_alert(self, code: str, message: str) -> bool:
        if not await self.is_configured():
            logger.warning("Telegram not configured")
            return False

        emoji_map = {
            "A1-PARA-1": "🔴",
            "A2-PARA-1": "🟠",
            "A3-PARA-1": "🟡",
            "INFO-PARA-1": "🔵",
        }
        emoji = emoji_map.get(str(code), "⚪")
        text = f"""
{emoji} *{code}*
━━━━━━━━━━━━━━━━━━
{message}
━━━━━━━━━━━━━━━━━━
_Centinela Intelligence_
        """.strip()

        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": "Markdown",
        }
        if httpx is not None:
            return await self._send_with_httpx(payload)
        return self._send_with_urllib(payload)

    async def is_configured(self) -> bool:
        return bool(
            self.token
            and self.chat_id
            and str(self.chat_id).strip().lower() not in {"pending", "none", "null", ""}
        )

    async def _send_with_httpx(self, payload: dict[str, Any]) -> bool:
        assert httpx is not None
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                response = await client.post(f"{self.base_url}/sendMessage", json=payload)
            if response.status_code != 200:
                logger.warning("Telegram send failed with status %s", response.status_code)
                return False
            return True
        except Exception as error:
            logger.warning("Telegram send failed: %r", error)
            return False

    def _send_with_urllib(self, payload: dict[str, Any]) -> bool:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        request = Request(
            f"{self.base_url}/sendMessage",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlopen(request, timeout=15) as response:
                return response.status == 200
        except (HTTPError, URLError, TimeoutError) as error:
            logger.warning("Telegram send failed: %r", error)
            return False
