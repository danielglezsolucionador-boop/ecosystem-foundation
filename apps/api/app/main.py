from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.audit import router as audit_router
from app.api.auditoria import router as auditoria_router
from app.api.auth import router as auth_router
from app.api.apps import router as apps_router
from app.api.arsenal import router as arsenal_router
from app.api.cerebro import router as cerebro_router
from app.api.ceo import router as ceo_router
from app.api.control_center import router as control_center_router
from app.api.contracts import router as contracts_router
from app.api.departments import router as departments_router
from app.api.events import router as events_router
from app.api.governance import router as governance_router
from app.api.health import router as health_router
from app.api.integration_bus import router as integration_bus_router
from app.api.integrations import router as integrations_router
from app.api.memory import router as memory_router
from app.api.missions import router as missions_router
from app.api.nube import router as nube_router
from app.api.observability import router as observability_router
from app.api.permissions import router as permissions_router
from app.api.platform import router as platform_router
from app.api.product_readiness import router as product_readiness_router
from app.api.publishing import router as publishing_router
from app.api.revenue import router as revenue_router
from app.api.security import router as security_router
from app.api.storage import router as storage_router
from app.api.upgrades import router as upgrades_router
from app.api.workday import router as workday_router
from app.core.metadata import APP_NAME, APP_VERSION

ROOT_DIR = Path(__file__).resolve().parents[3]
CONTROL_CENTER_DIR = ROOT_DIR / "apps" / "web" / "control-center"

app = FastAPI(
    title="Ecosystem Foundation API",
    version=APP_VERSION,
    description="Local executable foundation for the ecosystem platform.",
)

app.include_router(apps_router)
app.include_router(arsenal_router)
app.include_router(audit_router)
app.include_router(auditoria_router)
app.include_router(auth_router)
app.include_router(cerebro_router)
app.include_router(ceo_router)
app.include_router(control_center_router)
app.include_router(contracts_router)
app.include_router(departments_router)
app.include_router(events_router)
app.include_router(governance_router)
app.include_router(health_router)
app.include_router(integration_bus_router)
app.include_router(integrations_router)
app.include_router(memory_router)
app.include_router(missions_router)
app.include_router(nube_router)
app.include_router(observability_router)
app.include_router(permissions_router)
app.include_router(platform_router)
app.include_router(product_readiness_router)
app.include_router(publishing_router)
app.include_router(revenue_router)
app.include_router(security_router)
app.include_router(storage_router)
app.include_router(upgrades_router)
app.include_router(workday_router)

app.mount(
    "/control-center/assets",
    StaticFiles(directory=CONTROL_CENTER_DIR / "assets"),
    name="control-center-assets",
)


@app.get("/control-center", include_in_schema=False)
def read_control_center_experience() -> FileResponse:
    return FileResponse(CONTROL_CENTER_DIR / "index.html")


@app.get("/favicon.ico", include_in_schema=False)
def read_favicon() -> FileResponse:
    return FileResponse(CONTROL_CENTER_DIR / "assets" / "favicon.svg", media_type="image/svg+xml")


@app.get("/")
def read_root() -> dict[str, str]:
    return {
        "service": APP_NAME,
        "status": "ok",
        "version": APP_VERSION,
    }
