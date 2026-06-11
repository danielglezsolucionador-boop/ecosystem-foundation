from __future__ import annotations

import asyncio
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from apps.sombra.api import app  # noqa: E402,F401
from apps.sombra.core import SombraCore  # noqa: E402


UVICORN_STARTUP_COMMAND = "uvicorn apps.sombra.api:app --host 0.0.0.0 --port 8000 --reload"


async def main() -> None:
    sombra = SombraCore()
    try:
        await sombra.start(background_services=False)
        await sombra.process_intel_cycle()
    finally:
        await sombra.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
