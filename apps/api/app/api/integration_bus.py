from fastapi import APIRouter, Depends, HTTPException, status as http_status

from app.schemas.auth import AuthenticatedUser, ControlCenterRole
from app.schemas.integration_bus import (
    IntegrationBusAuditEvent,
    IntegrationBusDependency,
    IntegrationBusOverview,
    IntegrationBusPreparedRoute,
    IntegrationBusRoute,
    IntegrationBusRouteCreate,
    IntegrationBusRouteStateUpdate,
    IntegrationBusService,
    IntegrationBusStatus,
    IntegrationDispatchRequest,
    IntegrationDispatchResult,
)
from app.services.auth import get_current_user
from app.services.events import EventValidationError
from app.services.integration_bus import (
    IntegrationBusValidationError,
    create_route,
    dispatch_message,
    get_bus_overview,
    get_bus_status,
    get_route,
    list_bus_audit,
    list_bus_dependencies,
    list_bus_services,
    list_prepared_routes,
    list_routes,
    update_route_state,
)

router = APIRouter(prefix="/api/v1/integration-bus", tags=["integration-bus"])
BUS_READ_ROLES = {
    ControlCenterRole.ceo,
    ControlCenterRole.admin,
    ControlCenterRole.operator,
    ControlCenterRole.auditor,
}
BUS_WRITE_ROLES = {
    ControlCenterRole.ceo,
    ControlCenterRole.admin,
    ControlCenterRole.operator,
}


def ensure_bus_role(user: AuthenticatedUser, allowed_roles: set[ControlCenterRole]) -> None:
    if user.role not in allowed_roles:
        raise HTTPException(
            status_code=403,
            detail={
                "error": "integration_bus_role_not_authorized",
                "role": user.role.value,
            },
        )


@router.get("", response_model=IntegrationBusOverview)
def read_integration_bus() -> IntegrationBusOverview:
    return get_bus_overview()


@router.get("/routes", response_model=list[IntegrationBusRoute])
def read_routes(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> list[IntegrationBusRoute]:
    ensure_bus_role(current_user, BUS_READ_ROLES)
    return list_routes()


@router.get("/prepared-routes", response_model=list[IntegrationBusPreparedRoute])
def read_prepared_routes() -> list[IntegrationBusPreparedRoute]:
    return list(list_prepared_routes())


@router.post(
    "/routes",
    response_model=IntegrationBusRoute,
    status_code=http_status.HTTP_201_CREATED,
)
def register_route(
    route: IntegrationBusRouteCreate,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> IntegrationBusRoute:
    ensure_bus_role(current_user, BUS_WRITE_ROLES)
    # Kept for the existing generic internal event route registry.
    try:
        return create_route(route)
    except IntegrationBusValidationError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc


@router.get("/routes/{route_id}", response_model=IntegrationBusRoute)
def read_route(
    route_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> IntegrationBusRoute:
    ensure_bus_role(current_user, BUS_READ_ROLES)
    route = get_route(route_id)
    if route is None:
        raise HTTPException(
            status_code=404,
            detail={"error": "route_not_found", "route_id": route_id},
        )
    return route


@router.post("/routes/{route_id}/state", response_model=IntegrationBusRoute)
def update_route(
    route_id: str,
    request: IntegrationBusRouteStateUpdate,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> IntegrationBusRoute:
    ensure_bus_role(current_user, BUS_WRITE_ROLES)
    try:
        route = update_route_state(route_id, request)
    except IntegrationBusValidationError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc

    if route is None:
        raise HTTPException(
            status_code=404,
            detail={"error": "route_not_found", "route_id": route_id},
        )
    return route


@router.get("/services", response_model=list[IntegrationBusService])
def read_services() -> list[IntegrationBusService]:
    return list(list_bus_services())


@router.post("/dispatch", response_model=IntegrationDispatchResult)
def dispatch(
    request: IntegrationDispatchRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> IntegrationDispatchResult:
    ensure_bus_role(current_user, BUS_WRITE_ROLES)
    try:
        result = dispatch_message(request)
    except EventValidationError as exc:
        raise HTTPException(status_code=400, detail=exc.detail) from exc
    except IntegrationBusValidationError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc

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
