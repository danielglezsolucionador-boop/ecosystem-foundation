from fastapi import APIRouter, HTTPException

from app.schemas.permissions import PermissionCheck, PermissionRole
from app.services.permissions import (
    check_permission,
    get_permission_role,
    list_permission_roles,
)

router = APIRouter(prefix="/api/v1/permissions", tags=["permissions"])


@router.get("/roles", response_model=list[PermissionRole])
def get_roles() -> list[PermissionRole]:
    return list(list_permission_roles())


@router.get("/roles/{role_id}", response_model=PermissionRole)
def get_role(role_id: str) -> PermissionRole:
    role = get_permission_role(role_id)

    if role is None:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "role_not_found",
                "role_id": role_id,
            },
        )

    return role


@router.get("/check", response_model=PermissionCheck)
def get_permission_check(role_id: str, permission: str) -> PermissionCheck:
    result = check_permission(role_id, permission)

    if result is None:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "role_not_found",
                "role_id": role_id,
            },
        )

    return result

