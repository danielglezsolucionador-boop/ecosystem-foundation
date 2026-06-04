from fastapi import FastAPI

from app.api.audit import router as audit_router
from app.api.apps import router as apps_router
from app.api.control_center import router as control_center_router
from app.api.health import router as health_router
from app.api.integrations import router as integrations_router
from app.api.memory import router as memory_router
from app.api.observability import router as observability_router
from app.api.permissions import router as permissions_router
from app.api.platform import router as platform_router
from app.api.security import router as security_router
from app.api.storage import router as storage_router
from app.core.metadata import APP_NAME, APP_VERSION

app = FastAPI(
    title="Ecosystem Foundation API",
    version=APP_VERSION,
    description="Local executable foundation for the ecosystem platform.",
)

app.include_router(apps_router)
app.include_router(audit_router)
app.include_router(control_center_router)
app.include_router(health_router)
app.include_router(integrations_router)
app.include_router(memory_router)
app.include_router(observability_router)
app.include_router(permissions_router)
app.include_router(platform_router)
app.include_router(security_router)
app.include_router(storage_router)


@app.get("/")
def read_root() -> dict[str, str]:
    return {
        "service": APP_NAME,
        "status": "ok",
        "version": APP_VERSION,
    }
