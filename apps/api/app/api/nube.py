from fastapi import APIRouter, Depends, HTTPException, status

from app.schemas.nube import (
    CloudCostRecord,
    CloudCostRecordCreate,
    CloudDeployment,
    CloudDeploymentCreate,
    CloudHealthCheck,
    CloudHealthCheckCreate,
    CloudProject,
    CloudProjectCreate,
    CloudRisk,
    CloudRiskCreate,
    NubeStatus,
)
from app.services.auth import require_control_center_user
from app.services.nube import (
    NubeValidationError,
    create_cost,
    create_deployment,
    create_health_check,
    create_project,
    create_risk,
    get_nube_status,
    list_costs,
    list_deployments,
    list_health_checks,
    list_projects,
    list_risks,
)

router = APIRouter(
    prefix="/api/v1/nube",
    tags=["nube"],
    dependencies=[Depends(require_control_center_user)],
)


def raise_nube_error(error: NubeValidationError) -> None:
    raise HTTPException(status_code=error.status_code, detail=error.detail) from error


@router.get("/status", response_model=NubeStatus)
def read_nube_status() -> NubeStatus:
    return get_nube_status()


@router.get("/projects", response_model=list[CloudProject])
def read_nube_projects() -> list[CloudProject]:
    return list_projects()


@router.post(
    "/projects",
    response_model=CloudProject,
    status_code=status.HTTP_201_CREATED,
)
def write_nube_project(request: CloudProjectCreate) -> CloudProject:
    try:
        return create_project(request)
    except NubeValidationError as error:
        raise_nube_error(error)


@router.get("/deployments", response_model=list[CloudDeployment])
def read_nube_deployments() -> list[CloudDeployment]:
    return list_deployments()


@router.post(
    "/deployments",
    response_model=CloudDeployment,
    status_code=status.HTTP_201_CREATED,
)
def write_nube_deployment(request: CloudDeploymentCreate) -> CloudDeployment:
    try:
        return create_deployment(request)
    except NubeValidationError as error:
        raise_nube_error(error)


@router.get("/health-checks", response_model=list[CloudHealthCheck])
def read_nube_health_checks() -> list[CloudHealthCheck]:
    return list_health_checks()


@router.post(
    "/health-checks",
    response_model=CloudHealthCheck,
    status_code=status.HTTP_201_CREATED,
)
def write_nube_health_check(request: CloudHealthCheckCreate) -> CloudHealthCheck:
    try:
        return create_health_check(request)
    except NubeValidationError as error:
        raise_nube_error(error)


@router.get("/risks", response_model=list[CloudRisk])
def read_nube_risks() -> list[CloudRisk]:
    return list_risks()


@router.post(
    "/risks",
    response_model=CloudRisk,
    status_code=status.HTTP_201_CREATED,
)
def write_nube_risk(request: CloudRiskCreate) -> CloudRisk:
    try:
        return create_risk(request)
    except NubeValidationError as error:
        raise_nube_error(error)


@router.get("/costs", response_model=list[CloudCostRecord])
def read_nube_costs() -> list[CloudCostRecord]:
    return list_costs()


@router.post(
    "/costs",
    response_model=CloudCostRecord,
    status_code=status.HTTP_201_CREATED,
)
def write_nube_cost(request: CloudCostRecordCreate) -> CloudCostRecord:
    try:
        return create_cost(request)
    except NubeValidationError as error:
        raise_nube_error(error)
