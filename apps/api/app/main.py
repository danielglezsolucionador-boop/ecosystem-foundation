from fastapi import FastAPI

APP_NAME = "ecosystem-foundation-api"
APP_VERSION = "0.1.0"

app = FastAPI(
    title="Ecosystem Foundation API",
    version=APP_VERSION,
    description="Local executable foundation for the ecosystem platform.",
)


@app.get("/")
def read_root() -> dict[str, str]:
    return {
        "service": APP_NAME,
        "status": "ok",
        "version": APP_VERSION,
    }

