from functools import lru_cache
import json
from pathlib import Path

from app.schemas.app_registry import EcosystemApp

REGISTRY_PATH = Path(__file__).resolve().parents[1] / "data" / "apps_registry.json"


@lru_cache
def list_registered_apps() -> tuple[EcosystemApp, ...]:
    raw_apps = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    return tuple(EcosystemApp(**item) for item in raw_apps)


def get_registered_app(app_id: str) -> EcosystemApp | None:
    normalized_id = app_id.strip().lower()
    return next(
        (app for app in list_registered_apps() if app.id == normalized_id),
        None,
    )
