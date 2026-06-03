from fastapi import FastAPI

from app.api.apps import router as apps_router
from app.api.health import router as health_router
from app.core.metadata import APP_NAME, APP_VERSION

app = FastAPI(
    title="Ecosystem Foundation API",
    version=APP_VERSION,
    description="Local executable foundation for the ecosystem platform.",
)

app.include_router(apps_router)
app.include_router(health_router)


@app.get("/")
def read_root() -> dict[str, str]:
    return {
        "service": APP_NAME,
        "status": "ok",
        "version": APP_VERSION,
    }
