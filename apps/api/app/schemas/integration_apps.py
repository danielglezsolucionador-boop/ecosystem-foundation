from pydantic import BaseModel, Field


class IntegrationAppProfile(BaseModel):
    app_id: str = Field(min_length=1)
    app_name: str = Field(min_length=1)
    integration_status: str = Field(min_length=1)
    repository_hint: str | None = None
    contract_id: str = Field(min_length=1)
    evidence_files: list[str] = Field(default_factory=list)
    expected_capabilities: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    external_connection_enabled: bool = False
    source: str = Field(min_length=1)


class IntegrationAppDiscovery(BaseModel):
    app_id: str = Field(min_length=1)
    app_name: str = Field(min_length=1)
    integration_status: str = Field(min_length=1)
    contract_id: str = Field(min_length=1)
    repository_detected: bool
    repository_path: str | None = None
    evidence_files_expected: list[str] = Field(default_factory=list)
    evidence_files_found: list[str] = Field(default_factory=list)
    missing_evidence_files: list[str] = Field(default_factory=list)
    expected_capabilities: list[str] = Field(default_factory=list)
    health_status: str = Field(min_length=1)
    blockers: list[str] = Field(default_factory=list)
    external_connection_enabled: bool = False
    discovered_at: str = Field(min_length=1)
