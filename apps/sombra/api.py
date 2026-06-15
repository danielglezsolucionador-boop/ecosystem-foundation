from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from datetime import UTC, datetime
import json
import os
from pathlib import Path
from typing import Any

from fastapi import Depends, FastAPI, Header, HTTPException, Request

from apps.sombra.core import SombraCore
from apps.sombra.memory.database import LOG_DIR
from apps.sombra.products import DarkWebScanProduct


API_LOG = LOG_DIR / "api.log"
sombra_core = SombraCore()


@asynccontextmanager
async def lifespan(_: FastAPI):
    await sombra_core.start()
    try:
        yield
    finally:
        await sombra_core.shutdown()


app = FastAPI(title="SOMBRA Internal API", version="1.0", lifespan=lifespan)


async def require_sombra_key(x_sombra_key: str | None = Header(default=None, alias="X-Sombra-Key")) -> None:
    expected = os.getenv("SOMBRA_API_KEY")
    if not expected:
        raise HTTPException(status_code=503, detail="SOMBRA_API_KEY is not configured")
    if x_sombra_key != expected:
        await _log_auth_failure("invalid_or_missing_key")
        raise HTTPException(status_code=401, detail="invalid SOMBRA API key")


@app.middleware("http")
async def log_api_call(request: Request, call_next):
    started = datetime.now(UTC)
    response = await call_next(request)
    duration_ms = round((datetime.now(UTC) - started).total_seconds() * 1000, 2)
    await asyncio.to_thread(
        _append_api_log,
        {
            "timestamp_utc": _now(),
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": duration_ms,
        },
    )
    return response


@app.post("/order", dependencies=[Depends(require_sombra_key)])
async def receive_order(raw_order: dict[str, Any]) -> dict[str, Any]:
    return await sombra_core.receive_order(raw_order)


@app.get("/status", dependencies=[Depends(require_sombra_key)])
async def get_status() -> dict[str, Any]:
    return await sombra_core.get_status()


@app.get("/alerts/recent", dependencies=[Depends(require_sombra_key)])
async def get_recent_alerts() -> list[dict[str, Any]]:
    return await sombra_core.alert_generator.get_recent_alerts(hours=24)


@app.get("/health", dependencies=[Depends(require_sombra_key)])
async def get_health() -> dict[str, dict[str, Any]]:
    return await sombra_core.health_monitor.check_all_modules()


@app.get("/briefing/daily", dependencies=[Depends(require_sombra_key)])
async def get_daily_briefing() -> dict[str, Any]:
    return await sombra_core.briefing_engine.generate()


@app.post("/client", dependencies=[Depends(require_sombra_key)])
async def create_client(client_data: dict[str, Any]) -> dict[str, str]:
    client_id = await sombra_core.client_memory.create_client(client_data)
    await sombra_core.blackbox.log(
        "API_CLIENT_CREATED",
        client_id,
        {"client_name": client_data.get("client_name"), "industry_sector": client_data.get("industry_sector")},
        order_origin="SOMBRA_API",
    )
    return {"client_id": client_id}


@app.post("/scan")
async def generate_dark_web_scan(
    scan_request: dict[str, Any],
    x_sombra_key: str | None = Header(default=None, alias="X-Sombra-Key"),
) -> dict[str, Any]:
    expected = os.getenv("SOMBRA_API_KEY")
    if not expected:
        raise HTTPException(status_code=503, detail="SOMBRA_API_KEY is not configured")
    supplied_key = x_sombra_key or scan_request.get("api_key")
    if supplied_key != expected:
        await _log_auth_failure("invalid_scan_api_key")
        raise HTTPException(status_code=401, detail="invalid SOMBRA API key")
    try:
        company_name = str(scan_request["company_name"])
        domain = str(scan_request["domain"])
        email_patterns = scan_request["email_patterns"]
    except KeyError as error:
        raise HTTPException(status_code=422, detail=f"missing required field: {error.args[0]}") from error
    product = DarkWebScanProduct(sombra_core.database, sombra_core.blackbox)
    try:
        return await product.generate_scan(company_name, domain, email_patterns)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


def _append_api_log(row: dict[str, Any]) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    with Path(API_LOG).open("a", encoding="utf-8") as log_file:
        log_file.write(json.dumps(row, sort_keys=True, default=str) + "\n")


def _now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


async def _log_auth_failure(reason: str) -> None:
    try:
        await sombra_core._ensure_database()
        await sombra_core.blackbox.log(
            "UNAUTHORIZED_ORDER_ATTEMPT",
            "API_AUTH",
            {"reason": reason},
            order_origin="SECURITY",
        )
        await sombra_core.intrusion_detector.record_failed_auth("api")
    except Exception:
        return
