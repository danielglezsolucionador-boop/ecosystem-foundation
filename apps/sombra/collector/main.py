from __future__ import annotations

import argparse
import asyncio
from datetime import UTC, datetime
import json
import signal

from .agents import SombraAbuseAgent, SombraCVEAgent, SombraPasteAgent, SombraRSSAgent
from .base_agent import LOG_DIR
from .scheduler import CollectorScheduler


STARTUP_LOG = LOG_DIR / "sombra_collector.log"


def _log_startup(message: str) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    STARTUP_LOG.open("a", encoding="utf-8").write(f"{timestamp} {message}\n")


def build_scheduler() -> CollectorScheduler:
    return CollectorScheduler(
        agents=[
            SombraCVEAgent(),
            SombraRSSAgent(),
            SombraAbuseAgent(),
            SombraPasteAgent(),
        ]
    )


async def run_collector(run_once: bool = False) -> int:
    await asyncio.to_thread(_log_startup, "SOMBRA Collector Engine startup")
    scheduler = build_scheduler()
    if run_once:
        results = await scheduler.run_once()
        summary = {agent_id: len(packages) for agent_id, packages in results.items()}
        print(json.dumps({"status": "complete", "packages": summary}, sort_keys=True))
        return 0

    loop = asyncio.get_running_loop()
    for signame in ("SIGINT", "SIGTERM"):
        sig = getattr(signal, signame, None)
        if sig is None:
            continue
        try:
            loop.add_signal_handler(sig, scheduler.stop)
        except NotImplementedError:
            signal.signal(sig, lambda *_: scheduler.stop())
    await scheduler.start()
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="SOMBRA Collector Engine")
    parser.add_argument("--once", action="store_true", help="run one collection cycle and exit")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    raise SystemExit(asyncio.run(run_collector(run_once=args.once)))


if __name__ == "__main__":
    main()
