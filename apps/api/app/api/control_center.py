from fastapi import APIRouter

from app.schemas.control_center import (
    AlertSummary,
    ControlCenterApplicationStatus,
    ControlCenterDependencyStatus,
    ControlCenterMetric,
    ControlCenterOverview,
    ControlCenterResponse,
    ControlCenterServiceStatus,
    ControlCenterStatus,
    ReadinessSummary,
)
from app.services.control_center import (
    get_control_center,
    get_control_center_overview,
    get_control_center_readiness,
    get_control_center_status,
    list_control_center_alerts,
    list_control_center_apps,
    list_control_center_dependencies,
    list_control_center_metrics,
    list_control_center_services,
)

router = APIRouter(prefix="/api/v1/control-center", tags=["control-center"])


@router.get("", response_model=ControlCenterResponse)
def get_control_center_root() -> ControlCenterResponse:
    return get_control_center()


@router.get("/overview", response_model=ControlCenterOverview)
def get_overview() -> ControlCenterOverview:
    return get_control_center_overview()


@router.get("/status", response_model=ControlCenterStatus)
def get_status() -> ControlCenterStatus:
    return get_control_center_status()


@router.get("/apps", response_model=list[ControlCenterApplicationStatus])
def get_apps() -> list[ControlCenterApplicationStatus]:
    return list_control_center_apps()


@router.get("/services", response_model=list[ControlCenterServiceStatus])
def get_services() -> list[ControlCenterServiceStatus]:
    return list_control_center_services()


@router.get("/dependencies", response_model=list[ControlCenterDependencyStatus])
def get_dependencies() -> list[ControlCenterDependencyStatus]:
    return list_control_center_dependencies()


@router.get("/metrics", response_model=list[ControlCenterMetric])
def get_metrics() -> list[ControlCenterMetric]:
    return list_control_center_metrics()


@router.get("/alerts", response_model=list[AlertSummary])
def get_alerts() -> list[AlertSummary]:
    return list_control_center_alerts()


@router.get("/readiness", response_model=ReadinessSummary)
def get_readiness() -> ReadinessSummary:
    return get_control_center_readiness()
