from pydantic import BaseModel, Field


class SecurityUser(BaseModel):
    id: str = Field(min_length=1)
    display_name: str = Field(min_length=1)
    role_id: str = Field(min_length=1)
    status: str = Field(min_length=1)
    authentication_mode: str = Field(min_length=1)
    notes: str = Field(min_length=1)


class SecurityRole(BaseModel):
    id: str = Field(min_length=1)
    label: str = Field(min_length=1)
    scope: str = Field(min_length=1)
    description: str = Field(min_length=1)
    permissions: list[str]
    can_touch_external_apps: bool
    can_view_secrets: bool
    requires_human_approval_for: list[str] = Field(default_factory=list)


class SecurityPermission(BaseModel):
    id: str = Field(min_length=1)
    label: str = Field(min_length=1)
    category: str = Field(min_length=1)
    critical: bool
    description: str = Field(min_length=1)


class SecurityPolicy(BaseModel):
    id: str = Field(min_length=1)
    label: str = Field(min_length=1)
    status: str = Field(min_length=1)
    enforced: bool
    rules: list[str]


class SecurityServiceIdentity(BaseModel):
    id: str = Field(min_length=1)
    service: str = Field(min_length=1)
    role_id: str = Field(min_length=1)
    status: str = Field(min_length=1)
    allowed_permissions: list[str]
    api_key_placeholder_id: str = Field(min_length=1)
    secret_material_present: bool


class SecurityApiKeyPlaceholder(BaseModel):
    id: str = Field(min_length=1)
    service_identity_id: str = Field(min_length=1)
    status: str = Field(min_length=1)
    storage_policy: str = Field(min_length=1)
    secret_material_present: bool


class SecuritySessionModel(BaseModel):
    id: str = Field(min_length=1)
    status: str = Field(min_length=1)
    issuing_strategy: str = Field(min_length=1)
    expiration_policy: str = Field(min_length=1)
    secret_material_present: bool


class AccessValidationRequest(BaseModel):
    role_id: str = Field(min_length=1)
    permission: str = Field(min_length=1)
    resource: str = Field(default="platform", min_length=1)
    context: str = Field(default="local_backbone", min_length=1)


class AccessValidationResult(BaseModel):
    id: str = Field(min_length=1)
    role_id: str = Field(min_length=1)
    permission: str = Field(min_length=1)
    resource: str = Field(min_length=1)
    allowed: bool
    reason: str = Field(min_length=1)
    required_human_approval: bool
    can_touch_external_apps: bool
    audit_event_id: str | None
    evaluated_at: str = Field(min_length=1)


class SecurityAuditEvent(BaseModel):
    id: str = Field(min_length=1)
    role_id: str = Field(min_length=1)
    permission: str = Field(min_length=1)
    resource: str = Field(min_length=1)
    allowed: bool
    reason: str = Field(min_length=1)
    created_at: str = Field(min_length=1)


class SecurityOverview(BaseModel):
    status: str = Field(min_length=1)
    users: list[SecurityUser]
    roles: list[SecurityRole]
    permissions: list[SecurityPermission]
    policies: list[SecurityPolicy]
    service_identities: list[SecurityServiceIdentity]
    api_key_placeholders: list[SecurityApiKeyPlaceholder]
    session_model: SecuritySessionModel
    external_connections_enabled: bool
    secrets_exposed: bool
