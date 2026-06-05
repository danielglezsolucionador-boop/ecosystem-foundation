from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class ControlCenterRole(StrEnum):
    ceo = "CEO"
    admin = "ADMIN"
    operator = "OPERATOR"
    auditor = "AUDITOR"
    service = "SERVICE"


class UserStatus(StrEnum):
    active = "active"
    disabled = "disabled"


class SessionStatus(StrEnum):
    active = "active"
    revoked = "revoked"
    expired = "expired"


class LoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=1, max_length=512)


class LogoutRequest(BaseModel):
    session_id: str | None = None


class SessionRevokeRequest(BaseModel):
    session_id: str = Field(min_length=1)
    reason: str = Field(default="manual_revoke", min_length=1, max_length=240)


class UserPublic(BaseModel):
    id: str = Field(min_length=1)
    email: str = Field(min_length=3, max_length=320)
    name: str = Field(min_length=1)
    role: ControlCenterRole
    status: UserStatus
    created_at: str = Field(min_length=1)
    updated_at: str = Field(min_length=1)
    last_login_at: str | None = None


class AuthSessionPublic(BaseModel):
    id: str = Field(min_length=1)
    user_id: str = Field(min_length=1)
    status: SessionStatus
    created_at: str = Field(min_length=1)
    expires_at: str = Field(min_length=1)
    revoked_at: str | None = None
    last_seen_at: str | None = None
    ip_address: str | None = None
    user_agent: str | None = None


class LoginResponse(BaseModel):
    token: str = Field(min_length=1)
    token_type: str = "bearer"
    expires_at: str = Field(min_length=1)
    user: UserPublic
    session: AuthSessionPublic


class AuthenticatedUser(UserPublic):
    session_id: str = Field(min_length=1)


class AuthAuditEvent(BaseModel):
    id: str = Field(min_length=1)
    user_id: str | None = None
    email: str | None = None
    role: str | None = None
    session_id: str | None = None
    action: str = Field(min_length=1)
    resource: str = Field(min_length=1)
    result: str = Field(min_length=1)
    ip_address: str | None = None
    user_agent: str | None = None
    timestamp: str = Field(min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)
