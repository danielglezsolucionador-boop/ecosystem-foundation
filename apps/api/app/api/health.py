from datetime import UTC, datetime

from fastapi import APIRouter

from app.core.metadata import APP_COMMIT, APP_ENVIRONMENT, APP_NAME, APP_VERSION

router = APIRouter(tags=["operations"])


def utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


@router.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "service": APP_NAME,
        "timestamp": utc_now(),
    }


@router.get("/readiness")
def readiness() -> dict[str, object]:
    return {
        "status": "ready",
        "service": APP_NAME,
        "dependencies": {
            "database": "not_required",
            "storage": "not_required",
            "provider": "not_required",
            "memory": "not_required",
        },
        "timestamp": utc_now(),
    }


@router.get("/runtime/status")
def runtime_status() -> dict[str, str]:
    return {
        "status": "operational",
        "service": APP_NAME,
        "environment": APP_ENVIRONMENT,
        "version": APP_VERSION,
        "commit": APP_COMMIT,
        "database": "not_required",
        "storage": "not_required",
        "provider": "not_required",
        "memory": "not_required",
        "updated_at": utc_now(),
    }


@router.get("/version")
def version() -> dict[str, str]:
    return {
        "service": APP_NAME,
        "version": APP_VERSION,
        "commit": APP_COMMIT,
    }

