from fastapi import APIRouter, Depends, HTTPException, status

from app.schemas.auth import AuthenticatedUser, ControlCenterRole
from app.schemas.departments import (
    DepartmentAudit,
    DepartmentAuditActionRequest,
    DepartmentAuditCreate,
    DepartmentRecord,
)
from app.services.auth import get_current_user, require_control_center_user
from app.services.departments import (
    DepartmentError,
    create_department_audit,
    get_department,
    get_department_audit,
    latest_department_audit,
    list_department_audits,
    list_departments,
    mark_audit_reviewed,
    send_audit_to_cerebro,
    send_audit_to_forja,
)

router = APIRouter(
    prefix="/api/v1/departments",
    tags=["departments"],
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
REVIEW_ROLES = {
    ControlCenterRole.ceo,
    ControlCenterRole.admin,
    ControlCenterRole.auditor,
}


def require_read(user: AuthenticatedUser) -> None:
    if user.role not in READ_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": "departments_role_not_authorized", "role": user.role.value},
        )


def require_write(user: AuthenticatedUser) -> None:
    if user.role not in WRITE_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": "departments_role_not_authorized", "role": user.role.value},
        )


def require_review(user: AuthenticatedUser) -> None:
    if user.role not in REVIEW_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": "departments_review_role_not_authorized", "role": user.role.value},
        )


def raise_department_error(error: DepartmentError) -> None:
    raise HTTPException(status_code=error.status_code, detail=error.detail) from error


@router.get("", response_model=list[DepartmentRecord])
def read_departments(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> list[DepartmentRecord]:
    require_read(current_user)
    return list_departments()


@router.get("/audits", response_model=list[DepartmentAudit])
def read_department_audits(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> list[DepartmentAudit]:
    require_read(current_user)
    return list_department_audits()


@router.get("/audits/{audit_id}", response_model=DepartmentAudit)
def read_department_audit(
    audit_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> DepartmentAudit:
    require_read(current_user)
    try:
        return get_department_audit(audit_id)
    except DepartmentError as error:
        raise_department_error(error)


@router.post("/audits/{audit_id}/send-to-forja", response_model=DepartmentAudit)
def write_audit_to_forja(
    audit_id: str,
    request: DepartmentAuditActionRequest | None = None,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> DepartmentAudit:
    require_write(current_user)
    try:
        return send_audit_to_forja(audit_id, request or DepartmentAuditActionRequest(), current_user)
    except DepartmentError as error:
        raise_department_error(error)


@router.post("/audits/{audit_id}/send-to-cerebro", response_model=DepartmentAudit)
def write_audit_to_cerebro(
    audit_id: str,
    request: DepartmentAuditActionRequest | None = None,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> DepartmentAudit:
    require_write(current_user)
    try:
        return send_audit_to_cerebro(audit_id, request or DepartmentAuditActionRequest(), current_user)
    except DepartmentError as error:
        raise_department_error(error)


@router.post("/audits/{audit_id}/mark-reviewed", response_model=DepartmentAudit)
def write_audit_reviewed(
    audit_id: str,
    request: DepartmentAuditActionRequest | None = None,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> DepartmentAudit:
    require_review(current_user)
    try:
        return mark_audit_reviewed(audit_id, request or DepartmentAuditActionRequest(), current_user)
    except DepartmentError as error:
        raise_department_error(error)


@router.get("/{department_id}", response_model=DepartmentRecord)
def read_department(
    department_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> DepartmentRecord:
    require_read(current_user)
    try:
        return get_department(department_id)
    except DepartmentError as error:
        raise_department_error(error)


@router.get("/{department_id}/audit", response_model=DepartmentAudit | None)
def read_latest_department_audit(
    department_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> DepartmentAudit | None:
    require_read(current_user)
    try:
        get_department(department_id)
        return latest_department_audit(department_id)
    except DepartmentError as error:
        raise_department_error(error)


@router.post("/{department_id}/audit", response_model=DepartmentAudit, status_code=status.HTTP_201_CREATED)
def write_department_audit(
    department_id: str,
    request: DepartmentAuditCreate | None = None,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> DepartmentAudit:
    require_write(current_user)
    try:
        return create_department_audit(department_id, request or DepartmentAuditCreate(), current_user)
    except DepartmentError as error:
        raise_department_error(error)
