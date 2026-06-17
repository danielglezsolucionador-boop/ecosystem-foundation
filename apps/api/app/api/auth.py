from fastapi import APIRouter, Depends, Request, status

from app.schemas.auth import (
    AuthAuditEvent,
    AuthSessionPublic,
    AuthenticatedUser,
    LoginRequest,
    LoginResponse,
    LogoutRequest,
    SessionRevokeRequest,
)
from app.services.auth import (
    control_center_auth_enabled,
    get_current_user,
    list_auth_audit_events,
    list_sessions,
    login,
    logout_user,
    revoke_session,
)

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.get("/config")
def read_auth_config() -> dict[str, bool]:
    return {"control_center_auth_enabled": control_center_auth_enabled()}


@router.post("/login", response_model=LoginResponse, status_code=status.HTTP_200_OK)
def login_control_center(request_data: LoginRequest, request: Request) -> LoginResponse:
    return login(request_data, request)


@router.post("/logout")
def logout_control_center(
    request: Request,
    request_data: LogoutRequest | None = None,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> dict[str, str]:
    return logout_user(current_user, request_data, request)


@router.get("/me", response_model=AuthenticatedUser)
def read_current_user(current_user: AuthenticatedUser = Depends(get_current_user)) -> AuthenticatedUser:
    return current_user


@router.get("/sessions", response_model=list[AuthSessionPublic])
def read_sessions(current_user: AuthenticatedUser = Depends(get_current_user)) -> list[AuthSessionPublic]:
    return list_sessions(current_user)


@router.post("/sessions/revoke")
def revoke_auth_session(
    request_data: SessionRevokeRequest,
    request: Request,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> dict[str, str]:
    return revoke_session(request_data, current_user, request)


@router.get("/audit", response_model=list[AuthAuditEvent])
def read_auth_audit(current_user: AuthenticatedUser = Depends(get_current_user)) -> list[AuthAuditEvent]:
    return list_auth_audit_events()
