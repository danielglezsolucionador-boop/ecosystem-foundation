from __future__ import annotations

from abc import ABC, abstractmethod
import asyncio
from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .intel_package import IntelPackage


SOMBRA_ROOT = Path(__file__).resolve().parents[1]
LOG_DIR = SOMBRA_ROOT / "logs"
FAILURE_LOG = LOG_DIR / "collector_failures.log"


class SombraCollectorAgent(ABC):
    def __init__(self, agent_id: str, source_type: str, priority: int) -> None:
        self.agent_id = agent_id
        self.source_type = source_type
        self.priority = priority
        self.user_agent = "SOMBRA-Collector/1.0 defensive-threat-intelligence"

    @abstractmethod
    async def collect(self) -> list[IntelPackage]:
        raise NotImplementedError("collector agents must implement collect")

    async def validate(self, data: object) -> bool:
        if isinstance(data, IntelPackage):
            return data.is_valid()
        if isinstance(data, list):
            return all(isinstance(item, IntelPackage) and item.is_valid() for item in data)
        return False

    async def report_failure(self, error: object) -> None:
        timestamp = datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
        message = f"{timestamp} agent={self.agent_id} source={self.source_type} error={error!r}\n"
        await asyncio.to_thread(self._append_failure_log, message)

    def _append_failure_log(self, message: str) -> None:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        with FAILURE_LOG.open("a", encoding="utf-8") as log_file:
            log_file.write(message)

    async def _fetch_text(
        self,
        url: str,
        *,
        method: str = "GET",
        timeout_seconds: int = 30,
        **kwargs: Any,
    ) -> str:
        headers = {"User-Agent": self.user_agent}
        extra_headers = kwargs.pop("headers", None)
        if extra_headers:
            headers.update(extra_headers)
        try:
            import aiohttp
        except ImportError:
            return await asyncio.to_thread(
                self._fetch_text_with_urllib,
                url,
                method=method,
                timeout_seconds=timeout_seconds,
                headers=headers,
                **kwargs,
            )

        timeout = aiohttp.ClientTimeout(total=timeout_seconds)
        async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
            async with session.request(method, url, **kwargs) as response:
                response.raise_for_status()
                return await response.text()

    def _fetch_text_with_urllib(
        self,
        url: str,
        *,
        method: str,
        timeout_seconds: int,
        headers: dict[str, str],
        **kwargs: Any,
    ) -> str:
        params = kwargs.pop("params", None)
        json_body = kwargs.pop("json", None)
        data = kwargs.pop("data", None)
        if kwargs:
            unsupported = ", ".join(sorted(kwargs))
            raise ValueError(f"urllib fallback does not support request options: {unsupported}")
        if params:
            separator = "&" if "?" in url else "?"
            url = f"{url}{separator}{urlencode(params)}"
        body: bytes | None = None
        if json_body is not None:
            body = json.dumps(json_body).encode("utf-8")
            headers = {**headers, "Content-Type": "application/json"}
        elif data is not None:
            body = data if isinstance(data, bytes) else str(data).encode("utf-8")
        request = Request(url, data=body, headers=headers, method=method.upper())
        try:
            with urlopen(request, timeout=timeout_seconds) as response:
                content_type = response.headers.get_content_charset() or "utf-8"
                return response.read().decode(content_type, errors="replace")
        except HTTPError as error:
            detail = error.read().decode("utf-8", errors="replace")[:500]
            raise RuntimeError(f"HTTP {error.code} from {url}: {detail}") from error
        except URLError as error:
            raise RuntimeError(f"network error from {url}: {error.reason}") from error

    async def _fetch_json(
        self,
        url: str,
        *,
        method: str = "GET",
        timeout_seconds: int = 30,
        **kwargs: Any,
    ) -> dict[str, Any]:
        text = await self._fetch_text(url, method=method, timeout_seconds=timeout_seconds, **kwargs)
        parsed = json.loads(text)
        if not isinstance(parsed, dict):
            raise ValueError(f"expected JSON object from {url}")
        return parsed

    @staticmethod
    def _compact_json(data: object) -> str:
        return json.dumps(data, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
