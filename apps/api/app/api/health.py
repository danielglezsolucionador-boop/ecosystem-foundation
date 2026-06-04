from datetime import UTC, datetime

from fastapi import APIRouter

from app.core.config import get_settings
from app.core.database import initialize_database
from app.core.metadata import APP_COMMIT, APP_ENVIRONMENT, APP_NAME, APP_VERSION

router = APIRouter(tags=["operations"])


def utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def database_dependency_status() -> dict[str, object]:
    try:
        status = initialize_database()
    except Exception as exc:
        return {
            "status": "error",
            "backend": "unknown",
            "configured": False,
            "persistent": False,
            "postgres": False,
            "sqlite": False,
            "schema_version": "unknown",
            "source": "unknown",
            "detail": exc.__class__.__name__,
        }

    settings = get_settings()
    return {
        "status": status.status,
        "backend": status.backend,
        "configured": status.configured,
        "persistent": status.persistent,
        "postgres": status.backend == "postgresql",
        "sqlite": status.backend == "sqlite",
        "schema_version": status.schema_version,
        "source": settings.database_url_source,
    }


@router.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "service": APP_NAME,
        "timestamp": utc_now(),
    }


@router.get("/readiness")
def readiness() -> dict[str, object]:
    database = database_dependency_status()
    return {
        "status": "ready" if database["status"] == "connected" else "degraded",
        "service": APP_NAME,
        "dependencies": {
            "database": database,
            "storage": "database_backed",
            "provider": "not_required",
            "memory": "database_backed",
        },
        "timestamp": utc_now(),
    }


@router.get("/runtime/status")
def runtime_status() -> dict[str, object]:
    database = database_dependency_status()
    return {
        "status": "operational" if database["status"] == "connected" else "degraded",
        "service": APP_NAME,
        "environment": APP_ENVIRONMENT,
        "version": APP_VERSION,
        "commit": APP_COMMIT,
        "database": database,
        "storage": "database_backed",
        "provider": "not_required",
        "memory": "database_backed",
        "updated_at": utc_now(),
    }


@router.get("/version")
def version() -> dict[str, str]:
    return {
        "service": APP_NAME,
        "version": APP_VERSION,
        "commit": APP_COMMIT,
    }
