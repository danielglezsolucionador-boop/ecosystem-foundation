from __future__ import annotations

import asyncio
from datetime import UTC, datetime
import json
import os
from pathlib import Path
import shutil
from typing import Any
import uuid
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from apps.sombra.memory.database import LOG_DIR


REPO_ROOT = Path(__file__).resolve().parents[3]
OUTBOX_DIRS = {
    "cerebro": "apps/sombra/outbox/cerebro/",
    "sentinela": "apps/sombra/outbox/sentinela/",
    "forja": "apps/sombra/outbox/forja/",
}
WEBHOOK_ENV = {
    "cerebro": "CEREBRO_WEBHOOK_URL",
    "sentinela": "SENTINELA_WEBHOOK_URL",
    "forja": "FORJA_WEBHOOK_URL",
}
OUTBOX_MONITOR_LOG = LOG_DIR / "outbox_monitor.log"


class OutboxMonitor:
    async def scan_outboxes(self) -> dict[str, Any]:
        return await asyncio.to_thread(self._scan_outboxes_sync)

    async def attempt_delivery(self, destination: str, webhook_url: str | None) -> dict[str, Any]:
        normalized = destination.lower()
        if normalized not in OUTBOX_DIRS:
            raise ValueError(f"unknown outbox destination: {destination}")
        if not webhook_url:
            result = {
                "destination": normalized,
                "webhook_configured": False,
                "attempted": 0,
                "delivered": 0,
                "failed": 0,
                "skipped": True,
                "errors": [],
            }
            await asyncio.to_thread(self._append_monitor_log, result)
            return result
        if not self._safe_transport(webhook_url):
            result = {
                "destination": normalized,
                "webhook_configured": True,
                "attempted": 0,
                "delivered": 0,
                "failed": 0,
                "skipped": True,
                "errors": [{"error": "unsafe_transport_blocked", "url_host": urlparse(webhook_url).netloc}],
            }
            await asyncio.to_thread(self._append_monitor_log, result)
            return result

        outbox_path = self._destination_path(normalized)
        outbox_path.mkdir(parents=True, exist_ok=True)
        files = sorted(path for path in outbox_path.glob("*.json") if path.is_file())
        result = {
            "destination": normalized,
            "webhook_configured": True,
            "attempted": 0,
            "delivered": 0,
            "failed": 0,
            "skipped": False,
            "errors": [],
        }
        for path in files:
            result["attempted"] += 1
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
                await asyncio.to_thread(self._post_payload, normalized, webhook_url, payload)
                await asyncio.to_thread(self._move_to_delivered, path)
                result["delivered"] += 1
            except Exception as error:
                result["failed"] += 1
                result["errors"].append({"file": path.name, "error": repr(error)})
        await asyncio.to_thread(self._append_monitor_log, result)
        return result

    async def retry_all_pending(self) -> dict[str, Any]:
        results: dict[str, Any] = {"timestamp_utc": self._now(), "destinations": {}}
        for destination, env_name in WEBHOOK_ENV.items():
            results["destinations"][destination] = await self.attempt_delivery(destination, os.getenv(env_name))
        await asyncio.to_thread(self._append_monitor_log, results)
        return results

    @classmethod
    def _scan_outboxes_sync(cls) -> dict[str, Any]:
        summary: dict[str, Any] = {"timestamp_utc": cls._now(), "outboxes": {}}
        for destination in OUTBOX_DIRS:
            outbox_path = cls._destination_path(destination)
            outbox_path.mkdir(parents=True, exist_ok=True)
            files = sorted(path for path in outbox_path.glob("*.json") if path.is_file())
            sizes = [path.stat().st_size for path in files]
            mtimes = [path.stat().st_mtime for path in files]
            summary["outboxes"][destination] = {
                "path": str(outbox_path),
                "file_count": len(files),
                "oldest_file_timestamp": cls._timestamp_from_mtime(min(mtimes)) if mtimes else None,
                "newest_file_timestamp": cls._timestamp_from_mtime(max(mtimes)) if mtimes else None,
                "total_size_kb": round(sum(sizes) / 1024, 2),
            }
        return summary

    @classmethod
    def _destination_path(cls, destination: str) -> Path:
        return REPO_ROOT / OUTBOX_DIRS[destination]

    @staticmethod
    def _post_payload(destination: str, webhook_url: str, payload: dict[str, Any]) -> None:
        body = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        headers = OutboxMonitor._headers_for_destination(destination)
        request = Request(webhook_url, data=body, headers=headers, method="POST")
        try:
            with urlopen(request, timeout=10) as response:
                if response.status >= 400:
                    raise RuntimeError(f"HTTP {response.status}")
        except HTTPError as error:
            detail = error.read().decode("utf-8", errors="replace")[:300]
            raise RuntimeError(f"HTTP {error.code}: {detail}") from error
        except URLError as error:
            raise RuntimeError(f"network error: {error.reason}") from error

    @staticmethod
    def _headers_for_destination(destination: str) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if destination == "cerebro":
            key = os.getenv("SOMBRA_API_KEY", "")
            if key:
                headers["X-Sombra-Key"] = key
        elif destination == "sentinela":
            headers["X-Intel-Source"] = "CLASSIFIED"
            key = os.getenv("SENTINELA_API_KEY", "")
            if key:
                headers["X-Sentinela-Key"] = key
        elif destination == "forja":
            headers["X-Signal-Source"] = "INTEL_ENGINE"
            key = os.getenv("FORJA_API_KEY", "")
            if key:
                headers["X-Forja-Key"] = key
        return headers

    @staticmethod
    def _move_to_delivered(path: Path) -> None:
        delivered_dir = path.parent / "delivered"
        delivered_dir.mkdir(parents=True, exist_ok=True)
        target = delivered_dir / path.name
        if target.exists():
            target = delivered_dir / f"{path.stem}_{uuid.uuid4().hex}{path.suffix}"
        shutil.move(str(path), str(target))

    @staticmethod
    def _safe_transport(url: str) -> bool:
        parsed = urlparse(url)
        if parsed.scheme == "https":
            return True
        if parsed.scheme == "http" and parsed.hostname in {"127.0.0.1", "localhost"}:
            return True
        return False

    @staticmethod
    def _append_monitor_log(row: dict[str, Any]) -> None:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        enriched = {"timestamp_utc": OutboxMonitor._now(), **row}
        with Path(OUTBOX_MONITOR_LOG).open("a", encoding="utf-8") as log_file:
            log_file.write(json.dumps(enriched, sort_keys=True, default=str) + "\n")

    @staticmethod
    def _timestamp_from_mtime(mtime: float) -> str:
        return datetime.fromtimestamp(mtime, UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    @staticmethod
    def _now() -> str:
        return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
