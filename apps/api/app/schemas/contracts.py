from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ContractCreate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    app_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    version: str = Field(default="v1", min_length=1)
    contract_schema: dict[str, Any] = Field(alias="schema")
    status: str = Field(default="draft", min_length=1)
    description: str = Field(min_length=1)


class ContractUpdate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: str | None = Field(default=None, min_length=1)
    version: str | None = Field(default=None, min_length=1)
    contract_schema: dict[str, Any] | None = Field(default=None, alias="schema")
    status: str | None = Field(default=None, min_length=1)
    description: str | None = Field(default=None, min_length=1)
    change_reason: str = Field(default="contract_update", min_length=1)


class ContractRecord(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    app_id: str
    name: str
    version: str
    status: str
    contract_schema: dict[str, Any] = Field(alias="schema")
    description: str
    breaking_change_detected: bool
    external_connection_enabled: bool
    created_at: str
    updated_at: str


class ContractVersion(BaseModel):
    id: str
    contract_id: str
    sequence: int
    action: str
    payload: ContractRecord
    created_at: str


class ContractPayloadValidationRequest(BaseModel):
    payload: dict[str, Any]


class ContractPayloadValidationResult(BaseModel):
    contract_id: str
    valid: bool
    errors: list[str]


class ContractCompatibilityRequest(BaseModel):
    proposed_schema: dict[str, Any]


class ContractCompatibilityResult(BaseModel):
    contract_id: str
    compatible: bool
    breaking_changes: list[str]
    checked_at: str


class ContractAuditEvent(BaseModel):
    id: str
    contract_id: str
    action: str
    status: str
    detail: str
    created_at: str


class ContractStatus(BaseModel):
    status: str
    contracts: int
    versions: int
    audit_events: int
    external_connections_enabled: bool
