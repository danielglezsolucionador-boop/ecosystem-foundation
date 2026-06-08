from fastapi import APIRouter, HTTPException, status as http_status

from app.schemas.integration_bus import (
    IntegrationBusAuditEvent,
    IntegrationBusDependency,
    IntegrationBusOverview,
    IntegrationBusPreparedRoute,
    IntegrationBusRoute,
    IntegrationBusRouteCreate,
    IntegrationBusService,
    IntegrationBusStatus,
    IntegrationDispatchRequest,
    IntegrationDispatchResult,
)
from app.services.events import EventValidationError
from app.services.integration_bus import (
    IntegrationBusValidationError,
    create_route,
    dispatch_message,
    get_bus_overview,
    get_bus_status,
    list_bus_audit,
    list_bus_dependencies,
    list_bus_services,
    list_prepared_routes,
    list_routes,
)

router = APIRouter(prefix="/api/v1/integration-bus", tags=["integration-bus"])


@router.get("", response_model=IntegrationBusOverview)
def read_integration_bus() -> IntegrationBusOverview:
    return get_bus_overview()


@router.get("/routes", response_model=list[IntegrationBusRoute])
def read_routes() -> list[IntegrationBusRoute]:
    return list_routes()


@router.get("/prepared-routes", response_model=list[IntegrationBusPreparedRoute])
def read_prepared_routes() -> list[IntegrationBusPreparedRoute]:
    return list(list_prepared_routes())


@router.post(
    "/routes",
    response_model=IntegrationBusRoute,
    status_code=http_status.HTTP_201_CREATED,
)
def register_route(route: IntegrationBusRouteCreate) -> IntegrationBusRoute:
    try:
        return create_route(route)
    except IntegrationBusValidationError as exc:
        raise HTTPException(status_code=400, detail=exc.detail) from exc


@router.get("/services", response_model=list[IntegrationBusService])
def read_services() -> list[IntegrationBusService]:
    return list(list_bus_services())


@router.post("/dispatch", response_model=IntegrationDispatchResult)
def dispatch(request: IntegrationDispatchRequest) -> IntegrationDispatchResult:
    try:
        result = dispatch_message(request)
    except EventValidationError as exc:
        raise HTTPException(status_code=400, detail=exc.detail) from exc

    if result is None:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "route_not_found",
                "route_id": request.route_id,
            },
        )

    return result


@router.get("/dependencies", response_model=list[IntegrationBusDependency])
def read_dependencies() -> list[IntegrationBusDependency]:
    return list_bus_dependencies()


@router.get("/audit", response_model=list[IntegrationBusAuditEvent])
def read_audit() -> list[IntegrationBusAuditEvent]:
    return list_bus_audit()


@router.get("/status", response_model=IntegrationBusStatus)
def read_status() -> IntegrationBusStatus:
    return get_bus_status()
