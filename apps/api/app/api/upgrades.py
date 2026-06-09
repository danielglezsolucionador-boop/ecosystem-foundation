from fastapi import APIRouter, Depends, HTTPException, status

from app.schemas.auth import AuthenticatedUser, ControlCenterRole
from app.schemas.upgrades import (
    UpgradeDecisionRequest,
    UpgradeForjaRequest,
    UpgradeImplementedRequest,
    UpgradePackage,
    UpgradePackageCreate,
    UpgradeReviewRequest,
    UpgradeStatus,
)
from app.services.auth import get_current_user, require_control_center_user
from app.services.upgrades import (
    UpgradeError,
    approve_package,
    create_upgrade_package,
    get_package,
    get_upgrade_status,
    list_packages,
    mark_package_implemented,
    packages_for_department,
    reject_package,
    request_package_review,
    send_package_to_forja,
)

router = APIRouter(
    prefix="/api/v1/upgrades",
    tags=["upgrades"],
    dependencies=[Depends(require_control_center_user)],
)

READ_ROLES = {
    ControlCenterRole.ceo,
    ControlCenterRole.admin,
    ControlCenterRole.operator,
    ControlCenterRole.auditor,
}
WRITE_ROLES = {
    ControlCenterRole.ceo,
    ControlCenterRole.admin,
    ControlCenterRole.operator,
    ControlCenterRole.auditor,
}
DECISION_ROLES = {
    ControlCenterRole.ceo,
    ControlCenterRole.admin,
    ControlCenterRole.auditor,
}


def require_upgrade_read(user: AuthenticatedUser) -> None:
    if user.role not in READ_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": "upgrade_role_not_authorized", "role": user.role.value},
        )


def require_upgrade_write(user: AuthenticatedUser) -> None:
    if user.role not in WRITE_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": "upgrade_write_role_not_authorized", "role": user.role.value},
        )


def require_upgrade_decision(user: AuthenticatedUser) -> None:
    if user.role not in DECISION_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": "upgrade_decision_role_not_authorized", "role": user.role.value},
        )


def raise_upgrade_error(error: UpgradeError) -> None:
    raise HTTPException(status_code=error.status_code, detail=error.detail) from error


@router.get("/status", response_model=UpgradeStatus)
def read_upgrade_status(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> UpgradeStatus:
    require_upgrade_read(current_user)
    return get_upgrade_status()


@router.get("/packages", response_model=list[UpgradePackage])
def read_upgrade_packages(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> list[UpgradePackage]:
    require_upgrade_read(current_user)
    return list_packages()


@router.post("/packages", response_model=UpgradePackage, status_code=status.HTTP_201_CREATED)
def write_upgrade_package(
    request: UpgradePackageCreate,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> UpgradePackage:
    require_upgrade_write(current_user)
    try:
        return create_upgrade_package(request, current_user)
    except UpgradeError as error:
        raise_upgrade_error(error)


@router.get("/packages/{package_id}", response_model=UpgradePackage)
def read_upgrade_package(
    package_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> UpgradePackage:
    require_upgrade_read(current_user)
    try:
        return get_package(package_id)
    except UpgradeError as error:
        raise_upgrade_error(error)


@router.post("/packages/{package_id}/send-to-forja", response_model=UpgradePackage)
def send_upgrade_to_forja(
    package_id: str,
    request: UpgradeForjaRequest | None = None,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> UpgradePackage:
    require_upgrade_write(current_user)
    try:
        return send_package_to_forja(package_id, request or UpgradeForjaRequest(), current_user)
    except UpgradeError as error:
        raise_upgrade_error(error)


@router.post("/packages/{package_id}/mark-implemented", response_model=UpgradePackage)
def mark_upgrade_implemented(
    package_id: str,
    request: UpgradeImplementedRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> UpgradePackage:
    require_upgrade_write(current_user)
    try:
        return mark_package_implemented(package_id, request, current_user)
    except UpgradeError as error:
        raise_upgrade_error(error)


@router.post("/packages/{package_id}/request-review", response_model=UpgradePackage)
def request_upgrade_review(
    package_id: str,
    request: UpgradeReviewRequest | None = None,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> UpgradePackage:
    require_upgrade_write(current_user)
    try:
        return request_package_review(package_id, request or UpgradeReviewRequest(), current_user)
    except UpgradeError as error:
        raise_upgrade_error(error)


@router.post("/packages/{package_id}/approve", response_model=UpgradePackage)
def approve_upgrade_package(
    package_id: str,
    request: UpgradeDecisionRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> UpgradePackage:
    require_upgrade_decision(current_user)
    try:
        return approve_package(package_id, request, current_user)
    except UpgradeError as error:
        raise_upgrade_error(error)


@router.post("/packages/{package_id}/reject", response_model=UpgradePackage)
def reject_upgrade_package(
    package_id: str,
    request: UpgradeDecisionRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> UpgradePackage:
    require_upgrade_decision(current_user)
    try:
        return reject_package(package_id, request, current_user)
    except UpgradeError as error:
        raise_upgrade_error(error)


@router.get("/department/{department_id}", response_model=list[UpgradePackage])
def read_department_upgrades(
    department_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> list[UpgradePackage]:
    require_upgrade_read(current_user)
    return packages_for_department(department_id)
