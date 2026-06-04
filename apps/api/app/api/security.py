from fastapi import APIRouter, HTTPException, status

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
from app.services.security import (
    get_security_overview,
    get_security_role,
    get_session_model,
    list_api_key_placeholders,
    list_security_audit_events,
    list_security_permissions,
    list_security_policies,
    list_security_roles,
    list_security_users,
    list_service_identities,
    validate_access,
)

router = APIRouter(prefix="/api/v1/security", tags=["security"])


@router.get("", response_model=SecurityOverview)
def read_security_overview() -> SecurityOverview:
    return get_security_overview()


@router.get("/users", response_model=list[SecurityUser])
def read_security_users() -> list[SecurityUser]:
    return list(list_security_users())


@router.get("/roles", response_model=list[SecurityRole])
def read_security_roles() -> list[SecurityRole]:
    return list(list_security_roles())


@router.get("/roles/{role_id}", response_model=SecurityRole)
def read_security_role(role_id: str) -> SecurityRole:
    role = get_security_role(role_id)

    if role is None:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "role_not_found",
                "role_id": role_id,
            },
        )

    return role


@router.get("/permissions", response_model=list[SecurityPermission])
def read_security_permissions() -> list[SecurityPermission]:
    return list(list_security_permissions())


@router.get("/policies", response_model=list[SecurityPolicy])
def read_security_policies() -> list[SecurityPolicy]:
    return list(list_security_policies())


@router.get("/service-identities", response_model=list[SecurityServiceIdentity])
def read_service_identities() -> list[SecurityServiceIdentity]:
    return list(list_service_identities())


@router.get("/api-key-placeholders", response_model=list[SecurityApiKeyPlaceholder])
def read_api_key_placeholders() -> list[SecurityApiKeyPlaceholder]:
    return list(list_api_key_placeholders())


@router.get("/session-model", response_model=SecuritySessionModel)
def read_session_model() -> SecuritySessionModel:
    return get_session_model()


@router.post(
    "/validate-access",
    response_model=AccessValidationResult,
    status_code=status.HTTP_201_CREATED,
)
def create_access_validation(
    request: AccessValidationRequest,
) -> AccessValidationResult:
    return validate_access(request)


@router.get("/audit", response_model=list[SecurityAuditEvent])
def read_security_audit() -> list[SecurityAuditEvent]:
    return list_security_audit_events()
