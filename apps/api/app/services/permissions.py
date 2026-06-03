from functools import lru_cache
import json
from pathlib import Path

from app.schemas.permissions import PermissionCheck, PermissionRole

PERMISSIONS_PATH = Path(__file__).resolve().parents[1] / "data" / "permissions_matrix.json"


@lru_cache
def list_permission_roles() -> tuple[PermissionRole, ...]:
    raw_roles = json.loads(PERMISSIONS_PATH.read_text(encoding="utf-8"))
    return tuple(PermissionRole(**item) for item in raw_roles)


def get_permission_role(role_id: str) -> PermissionRole | None:
    normalized_id = role_id.strip().lower()
    return next(
        (role for role in list_permission_roles() if role.id == normalized_id),
        None,
    )


def check_permission(role_id: str, permission: str) -> PermissionCheck | None:
    role = get_permission_role(role_id)

    if role is None:
        return None

    normalized_permission = permission.strip().lower()
    allowed = normalized_permission in role.permissions

    return PermissionCheck(
        role_id=role.id,
        permission=normalized_permission,
        allowed=allowed,
        reason="permission_granted" if allowed else "permission_not_in_role",
    )

