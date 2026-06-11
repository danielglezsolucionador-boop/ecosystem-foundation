from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from pathlib import Path

from .agents import SombraAbuseAgent, SombraCVEAgent, SombraPasteAgent, SombraRSSAgent
from .base_agent import LOG_DIR, SombraCollectorAgent
from .intel_package import IntelPackage


SCHEDULER_LOG = LOG_DIR / "scheduler.log"


class CollectorScheduler:
    DEFAULT_INTERVALS = {
        "sombra-cve-agent": 60 * 60,
        "sombra-rss-agent": 30 * 60,
        "sombra-abuse-agent": 15 * 60,
        "sombra-paste-agent": 30 * 60,
    }

    def __init__(
        self,
        agents: list[SombraCollectorAgent] | None = None,
        intervals: dict[str, int] | None = None,
    ) -> None:
        self.agents = agents if agents is not None else [
            SombraCVEAgent(),
            SombraRSSAgent(),
            SombraAbuseAgent(),
            SombraPasteAgent(),
        ]
        self.intervals = {**self.DEFAULT_INTERVALS, **(intervals or {})}
        self._stop_event = asyncio.Event()

    async def start(self) -> None:
        await self._log_cycle("scheduler_start", "Collector scheduler started")
        tasks = [asyncio.create_task(self._run_agent_forever(agent)) for agent in self.agents]
        try:
            await self._stop_event.wait()
        finally:
            for task in tasks:
                task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
            await self._log_cycle("scheduler_stop", "Collector scheduler stopped")

    def stop(self) -> None:
        self._stop_event.set()

    async def run_once(self) -> dict[str, list[IntelPackage]]:
        results: dict[str, list[IntelPackage]] = {}
        for agent in sorted(self.agents, key=lambda item: item.priority):
            results[agent.agent_id] = await self._run_agent_cycle(agent)
        return results

    async def _run_agent_forever(self, agent: SombraCollectorAgent) -> None:
        interval = self.intervals.get(agent.agent_id, 30 * 60)
        while not self._stop_event.is_set():
            await self._run_agent_cycle(agent)
            try:
                await asyncio.wait_for(self._stop_event.wait(), timeout=interval)
            except TimeoutError:
                continue

    async def _run_agent_cycle(self, agent: SombraCollectorAgent) -> list[IntelPackage]:
        await self._log_cycle(agent.agent_id, "cycle_start")
        try:
            packages = await agent.collect()
            await self._log_cycle(agent.agent_id, f"cycle_complete packages={len(packages)}")
            return packages
        except Exception as error:
            await agent.report_failure(error)
            await self._log_cycle(agent.agent_id, f"cycle_failed error={error!r}")
            return []

    async def _log_cycle(self, source: str, message: str) -> None:
        await asyncio.to_thread(self._append_scheduler_log, source, message)

    def _append_scheduler_log(self, source: str, message: str) -> None:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
        Path(SCHEDULER_LOG).open("a", encoding="utf-8").write(f"{timestamp} {source} {message}\n")
