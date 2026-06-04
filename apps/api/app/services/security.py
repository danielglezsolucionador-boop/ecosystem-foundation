from datetime import UTC, datetime
from functools import lru_cache
import json
from pathlib import Path
from uuid import uuid4

from app.core.database import connect, initialize_database, sql_placeholder
from app.schemas.security import (
    AccessValidationRequest,
    AccessValidationResult,
    SecurityApiKeyPlaceholder,
    SecurityAuditEvent,
    SecurityOverview,
    SecurityPermission,
    SecurityPolicy,
    SecurityRole,
    SecurityServiceIdentity,
    SecuritySessionModel,
    SecurityUser,
)

DATA_PATH = Path(__file__).resolve().parents[1] / "data"
ROLES_PATH = DATA_PATH / "permissions_matrix.json"
PERMISSIONS_PATH = DATA_PATH / "security_permissions.json"
POLICIES_PATH = DATA_PATH / "security_policies.json"
USERS_PATH = DATA_PATH / "security_users.json"
SERVICE_IDENTITIES_PATH = DATA_PATH / "security_service_identities.json"
API_KEY_PLACEHOLDERS_PATH = DATA_PATH / "security_api_key_placeholders.json"
SESSION_MODEL_PATH = DATA_PATH / "security_session_model.json"
SECURITY_AUDIT_TABLE = "security_access_audit_events"
EXTERNAL_RESOURCE_PREFIXES = ("forja", "cerebro", "dcft", "external:")


def utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def normalize(value: str) -> str:
    return value.strip().lower()


def read_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


@lru_cache
def list_security_roles() -> tuple[SecurityRole, ...]:
    raw_roles = read_json(ROLES_PATH)
    return tuple(SecurityRole(**item) for item in raw_roles)


def get_security_role(role_id: str) -> SecurityRole | None:
    normalized_role = normalize(role_id)
    return next(
        (role for role in list_security_roles() if role.id == normalized_role),
        None,
    )


@lru_cache
def list_security_permissions() -> tuple[SecurityPermission, ...]:
    raw_permissions = read_json(PERMISSIONS_PATH)
    return tuple(SecurityPermission(**item) for item in raw_permissions)


def get_security_permission(permission_id: str) -> SecurityPermission | None:
    normalized_permission = normalize(permission_id)
    return next(
        (
            permission
            for permission in list_security_permissions()
            if permission.id == normalized_permission
        ),
        None,
    )


@lru_cache
def list_security_policies() -> tuple[SecurityPolicy, ...]:
    raw_policies = read_json(POLICIES_PATH)
    return tuple(SecurityPolicy(**item) for item in raw_policies)


@lru_cache
def list_security_users() -> tuple[SecurityUser, ...]:
    raw_users = read_json(USERS_PATH)
    return tuple(SecurityUser(**item) for item in raw_users)


@lru_cache
def list_service_identities() -> tuple[SecurityServiceIdentity, ...]:
    raw_identities = read_json(SERVICE_IDENTITIES_PATH)
    return tuple(SecurityServiceIdentity(**item) for item in raw_identities)


@lru_cache
def list_api_key_placeholders() -> tuple[SecurityApiKeyPlaceholder, ...]:
    raw_placeholders = read_json(API_KEY_PLACEHOLDERS_PATH)
    return tuple(SecurityApiKeyPlaceholder(**item) for item in raw_placeholders)


@lru_cache
def get_session_model() -> SecuritySessionModel:
    raw_model = read_json(SESSION_MODEL_PATH)
    return SecuritySessionModel(**raw_model)


def ensure_security_audit_schema() -> None:
    initialize_database()

    with connect() as connection:
        connection.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {SECURITY_AUDIT_TABLE} (
                id TEXT PRIMARY KEY,
                role_id TEXT NOT NULL,
                permission TEXT NOT NULL,
                resource TEXT NOT NULL,
                allowed INTEGER NOT NULL,
                reason TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        connection.commit()


def write_security_audit_event(
    role_id: str,
    permission: str,
    resource: str,
    allowed: bool,
    reason: str,
) -> SecurityAuditEvent | None:
    try:
        ensure_security_audit_schema()
        event = SecurityAuditEvent(
            id=str(uuid4()),
            role_id=role_id,
            permission=permission,
            resource=resource,
            allowed=allowed,
            reason=reason,
            created_at=utc_now(),
        )
        placeholder = sql_placeholder()

        with connect() as connection:
            connection.execute(
                f"""
                INSERT INTO {SECURITY_AUDIT_TABLE}
                    (id, role_id, permission, resource, allowed, reason, payload_json, created_at)
                VALUES (
                    {placeholder}, {placeholder}, {placeholder}, {placeholder},
                    {placeholder}, {placeholder}, {placeholder}, {placeholder}
                )
                """,
                (
                    event.id,
                    event.role_id,
                    event.permission,
                    event.resource,
                    1 if event.allowed else 0,
                    event.reason,
                    event.model_dump_json(),
                    event.created_at,
                ),
            )
            connection.commit()

        return event
    except Exception:
        return None


def list_security_audit_events() -> list[SecurityAuditEvent]:
    ensure_security_audit_schema()

    with connect() as connection:
        rows = connection.execute(
            f"""
            SELECT payload_json
            FROM {SECURITY_AUDIT_TABLE}
            ORDER BY created_at DESC
            """
        ).fetchall()

    return [SecurityAuditEvent(**json.loads(row["payload_json"])) for row in rows]


def is_external_resource(resource: str) -> bool:
    normalized_resource = normalize(resource)
    return normalized_resource.startswith(EXTERNAL_RESOURCE_PREFIXES)


def validate_access(request: AccessValidationRequest) -> AccessValidationResult:
    role_id = normalize(request.role_id)
    permission_id = normalize(request.permission)
    resource = normalize(request.resource)
    role = get_security_role(role_id)
    permission = get_security_permission(permission_id)

    allowed = False
    reason = "permission_not_granted"
    required_human_approval = False
    can_touch_external_apps = False

    if role is None:
        reason = "role_not_found"
    elif permission is None:
        reason = "permission_unknown"
        can_touch_external_apps = role.can_touch_external_apps
    elif is_external_resource(resource) and not role.can_touch_external_apps:
        reason = "external_app_touch_blocked"
        can_touch_external_apps = role.can_touch_external_apps
    elif permission_id in role.permissions:
        allowed = True
        reason = "permission_granted"
        can_touch_external_apps = role.can_touch_external_apps
        required_human_approval = (
            permission.critical or permission_id in role.requires_human_approval_for
        )
    else:
        reason = "permission_not_in_role"
        can_touch_external_apps = role.can_touch_external_apps

    audit_event = write_security_audit_event(
        role_id=role_id,
        permission=permission_id,
        resource=resource,
        allowed=allowed,
        reason=reason,
    )

    return AccessValidationResult(
        id=str(uuid4()),
        role_id=role_id,
        permission=permission_id,
        resource=resource,
        allowed=allowed,
        reason=reason,
        required_human_approval=required_human_approval,
        can_touch_external_apps=can_touch_external_apps,
        audit_event_id=audit_event.id if audit_event else None,
        evaluated_at=utc_now(),
    )


def get_security_overview() -> SecurityOverview:
    roles = list_security_roles()
    permissions = list_security_permissions()
    policies = list_security_policies()
    users = list_security_users()
    service_identities = list_service_identities()
    api_key_placeholders = list_api_key_placeholders()
    session_model = get_session_model()

    secrets_exposed = any(role.can_view_secrets for role in roles) or any(
        item.secret_material_present
        for item in [*service_identities, *api_key_placeholders, session_model]
    )

    return SecurityOverview(
        status="security_foundation_ready" if not secrets_exposed else "blocked",
        users=list(users),
        roles=list(roles),
        permissions=list(permissions),
        policies=list(policies),
        service_identities=list(service_identities),
        api_key_placeholders=list(api_key_placeholders),
        session_model=session_model,
        external_connections_enabled=False,
        secrets_exposed=secrets_exposed,
    )
