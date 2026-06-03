from pydantic import BaseModel, Field


class PermissionRole(BaseModel):
    id: str = Field(min_length=1)
    label: str = Field(min_length=1)
    scope: str = Field(min_length=1)
    permissions: list[str]
    can_touch_external_apps: bool


class PermissionCheck(BaseModel):
    role_id: str
    permission: str
    allowed: bool
    reason: str

