from datetime import UTC, datetime
import json
import re
from typing import Any, TypeVar
from uuid import uuid4

from app.core.database import connect, initialize_database, sql_placeholder
from app.schemas.audit import AuditCategory, AuditEvent, AuditEventCreate, AuditSeverity
from app.schemas.nube import (
    MASKED_VALUE,
    CloudBackup,
    CloudCostRecord,
    CloudCostRecordCreate,
    CloudDatabase,
    CloudDeployment,
    CloudDeploymentCreate,
    CloudDomain,
    CloudHealthCheck,
    CloudHealthCheckCreate,
    CloudProject,
    CloudProjectCreate,
    CloudProvider,
    CloudRisk,
    CloudRiskCreate,
    CloudVariable,
    CloudVariableCreate,
    NubeEvidence,
    NubeStatus,
)

NUBE_PROJECTS_TABLE = "nube_cloud_projects"
NUBE_DEPLOYMENTS_TABLE = "nube_cloud_deployments"
NUBE_HEALTH_CHECKS_TABLE = "nube_cloud_health_checks"
NUBE_RISKS_TABLE = "nube_cloud_risks"
NUBE_COSTS_TABLE = "nube_cloud_costs"

PROJECT_ID = "ecosystem-foundation"
PRODUCTION_URL = "https://ecosystem-foundation.vercel.app"
CONTROL_CENTER_URL = "https://ecosystem-foundation.vercel.app/control-center"
KNOWN_TAGS = ["v1-ecosystem-company-cabin", "v1-cerebro-internal-bus"]
CURRENT_RECORDED_COMMIT = "d51963a"
SECRET_VALUE_PATTERNS = [
    re.compile(r"sk_(live|test)_[A-Za-z0-9]{16,}"),
    re.compile(r"whsec_[A-Za-z0-9]{16,}"),
    re.compile(r"gh[pousr]_[A-Za-z0-9_]{30,}"),
    re.compile(r"AIza[0-9A-Za-z\-_]{35}"),
    re.compile(r"sk-or-v1-[A-Za-z0-9]{20,}"),
    re.compile(r"sk-proj-[A-Za-z0-9_-]{20,}"),
    re.compile(r"-----BEGIN (RSA |EC |OPENSSH |)PRIVATE KEY-----"),
    re.compile(r"(?i)\b(secret|password|token|api[_-]?key)\b\s*[:=]\s*[^\s]{8,}"),
]

ModelT = TypeVar(
    "ModelT",
    CloudProject,
    CloudDeployment,
    CloudHealthCheck,
    CloudRisk,
    CloudCostRecord,
)


class NubeValidationError(RuntimeError):
    def __init__(self, detail: dict[str, object], status_code: int = 400) -> None:
        self.detail = detail
        self.status_code = status_code
        super().__init__(str(detail))


def utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def ensure_nube_schema() -> None:
    initialize_database()
    with connect() as connection:
        for table_name in [
            NUBE_PROJECTS_TABLE,
            NUBE_DEPLOYMENTS_TABLE,
            NUBE_HEALTH_CHECKS_TABLE,
            NUBE_RISKS_TABLE,
            NUBE_COSTS_TABLE,
        ]:
            connection.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {table_name} (
                    id TEXT PRIMARY KEY,
                    payload_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
        connection.commit()


def check_no_secret_values(payload: Any) -> None:
    if isinstance(payload, dict):
        for value in payload.values():
            check_no_secret_values(value)
        return
    if isinstance(payload, list):
        for value in payload:
            check_no_secret_values(value)
        return
    if isinstance(payload, str):
        for pattern in SECRET_VALUE_PATTERNS:
            if pattern.search(payload):
                raise NubeValidationError(
                    {
                        "error": "nube_secret_value_rejected",
                        "detail": "NUBE internal registry does not accept secret values.",
                    }
                )


def normalize_id(value: str) -> str:
    normalized = str(value or "").strip().lower().replace(" ", "-").replace("_", "-")
    normalized = re.sub(r"[^a-z0-9.-]+", "-", normalized).strip("-")
    return normalized or str(uuid4())


def clean_list(values: list[str]) -> list[str]:
    return [item.strip() for item in values if item and item.strip()]


def mask_variable(variable: CloudVariableCreate) -> CloudVariable:
    return CloudVariable(
        name=variable.name.strip(),
        status=variable.status.strip().lower(),
        required=variable.required,
        sensitive=variable.sensitive,
        notes=variable.notes,
        value=MASKED_VALUE,
    )


def save_payload(table_name: str, item: ModelT) -> ModelT:
    ensure_nube_schema()
    placeholder = sql_placeholder()
    updated_at = utc_now()
    if hasattr(item, "updated_at"):
        item.updated_at = updated_at
    payload_json = item.model_dump_json()
    with connect() as connection:
        connection.execute(
            f"""
            INSERT INTO {table_name} (id, payload_json, created_at, updated_at)
            VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder})
            ON CONFLICT(id) DO UPDATE SET
                payload_json = excluded.payload_json,
                updated_at = excluded.updated_at
            """,
            (item.id, payload_json, item.created_at, updated_at),
        )
        connection.commit()
    return item


def list_payloads(table_name: str, model: type[ModelT]) -> list[ModelT]:
    ensure_nube_schema()
    with connect() as connection:
        rows = connection.execute(
            f"""
            SELECT payload_json
            FROM {table_name}
            ORDER BY updated_at DESC
            """
        ).fetchall()
    return [model(**json.loads(row["payload_json"])) for row in rows]


def get_payload(table_name: str, item_id: str, model: type[ModelT]) -> ModelT | None:
    ensure_nube_schema()
    placeholder = sql_placeholder()
    with connect() as connection:
        row = connection.execute(
            f"""
            SELECT payload_json
            FROM {table_name}
            WHERE id = {placeholder}
            """,
            (item_id,),
        ).fetchone()
    return model(**json.loads(row["payload_json"])) if row else None


def record_nube_audit_event(
    *,
    action: str,
    status: str,
    detail: str,
    severity: AuditSeverity = AuditSeverity.info,
    metadata: dict[str, object] | None = None,
) -> AuditEvent:
    from app.services.audit import create_audit_event

    return create_audit_event(
        AuditEventCreate(
            category=AuditCategory.runtime,
            severity=severity,
            source="nube.internal_control_tower",
            action=action,
            status=status,
            detail=detail,
            metadata={
                "external_connection_enabled": False,
                "deploy_automation_enabled": False,
                "vercel_api_connected": False,
                "local_nube_touched": False,
                **(metadata or {}),
            },
        )
    )


def initial_variables() -> list[CloudVariable]:
    return [
        mask_variable(CloudVariableCreate(name="DATABASE_URL", status="configured", required=True)),
        mask_variable(CloudVariableCreate(name="CONTROL_CENTER_ADMIN_EMAIL", status="configured", required=True)),
        mask_variable(CloudVariableCreate(name="CONTROL_CENTER_ADMIN_PASSWORD", status="configured", required=True)),
        mask_variable(CloudVariableCreate(name="CONTROL_CENTER_SESSION_SECRET", status="unknown", required=True)),
        mask_variable(CloudVariableCreate(name="APP_ENVIRONMENT", status="configured", required=False, sensitive=False)),
    ]


def initial_project() -> CloudProject:
    now = utc_now()
    return CloudProject(
        id=PROJECT_ID,
        name="ecosystem-foundation",
        production_url=PRODUCTION_URL,
        control_center_url=CONTROL_CENTER_URL,
        provider="Vercel",
        status="production_registry_internal",
        last_commit=CURRENT_RECORDED_COMMIT,
        tags=KNOWN_TAGS,
        providers=[
            CloudProvider(
                id="vercel",
                name="Vercel",
                provider_type="hosting",
                status="registered",
                external_api_connected=False,
            )
        ],
        databases=[
            CloudDatabase(
                id="postgresql-production",
                name="PostgreSQL production",
                engine="PostgreSQL",
                status="persistent_true",
                persistent=True,
                temporal=False,
            )
        ],
        variables=initial_variables(),
        backups=[
            CloudBackup(
                id="backup-registry-local",
                label="Backups locales documentados por bloque",
                status="registered_internal",
            )
        ],
        domains=[
            CloudDomain(
                id="ecosystem-foundation-vercel",
                domain="ecosystem-foundation.vercel.app",
                status="registered",
                provider="Vercel",
            )
        ],
        production_public_status="production_public_pass",
        production_auth_status="production_auth_pass_previous_closures",
        persistent_session_status="pending_productive_closure",
        cost_status="unknown",
        requires_manual_review=True,
        notes="NUBE interna registra estado cloud; no despliega, no edita variables y no llama APIs externas.",
        created_at=now,
        updated_at=now,
    )


def initial_deployment() -> CloudDeployment:
    now = utc_now()
    return CloudDeployment(
        id="deployment-ecosystem-foundation-production-known",
        project_id=PROJECT_ID,
        environment="production",
        url=PRODUCTION_URL,
        provider="Vercel",
        commit=CURRENT_RECORDED_COMMIT,
        status="production_public_pass",
        tags=KNOWN_TAGS,
        evidence="Registro interno de cierres productivos previos; sin llamada a Vercel API.",
        created_at=now,
        updated_at=now,
    )


def initial_health_checks() -> list[CloudHealthCheck]:
    now = utc_now()
    return [
        CloudHealthCheck(
            id="health-production-root",
            project_id=PROJECT_ID,
            url=PRODUCTION_URL,
            status="production_public_pass",
            status_code=200,
            source="previous_closure_report",
            evidence="Producción pública PASS en cierres previos.",
            created_at=now,
            updated_at=now,
        ),
        CloudHealthCheck(
            id="health-control-center-auth",
            project_id=PROJECT_ID,
            url=CONTROL_CENTER_URL,
            status="production_auth_pass_previous_closures",
            status_code=200,
            source="previous_closure_report",
            evidence="Control Center autenticado PASS en cierres previos.",
            created_at=now,
            updated_at=now,
        ),
    ]


def initial_cost() -> CloudCostRecord:
    now = utc_now()
    return CloudCostRecord(
        id="cost-ecosystem-foundation-vercel-unknown",
        project_id=PROJECT_ID,
        provider="Vercel",
        cost_status="unknown",
        estimated_monthly=None,
        currency="USD",
        requires_manual_review=True,
        notes="No hay costos reales registrados; requiere revisión manual.",
        created_at=now,
        updated_at=now,
    )


def seed_initial_records() -> None:
    ensure_nube_schema()
    if get_payload(NUBE_PROJECTS_TABLE, PROJECT_ID, CloudProject) is None:
        save_payload(NUBE_PROJECTS_TABLE, initial_project())
    if get_payload(NUBE_DEPLOYMENTS_TABLE, "deployment-ecosystem-foundation-production-known", CloudDeployment) is None:
        save_payload(NUBE_DEPLOYMENTS_TABLE, initial_deployment())
    for health_check in initial_health_checks():
        if get_payload(NUBE_HEALTH_CHECKS_TABLE, health_check.id, CloudHealthCheck) is None:
            save_payload(NUBE_HEALTH_CHECKS_TABLE, health_check)
    if get_payload(NUBE_COSTS_TABLE, "cost-ecosystem-foundation-vercel-unknown", CloudCostRecord) is None:
        save_payload(NUBE_COSTS_TABLE, initial_cost())


def list_projects() -> list[CloudProject]:
    seed_initial_records()
    return list_payloads(NUBE_PROJECTS_TABLE, CloudProject)


def create_project(request: CloudProjectCreate) -> CloudProject:
    check_no_secret_values(request.model_dump())
    now = utc_now()
    project = CloudProject(
        id=normalize_id(request.id or request.name),
        name=request.name.strip(),
        production_url=request.production_url,
        control_center_url=request.control_center_url,
        provider=request.provider.strip(),
        status=request.status.strip().lower(),
        last_commit=request.last_commit,
        tags=clean_list(request.tags),
        providers=request.providers,
        databases=request.databases,
        variables=[mask_variable(item) for item in request.variables],
        backups=request.backups,
        domains=request.domains,
        production_public_status=request.production_public_status.strip().lower(),
        production_auth_status=request.production_auth_status.strip().lower(),
        persistent_session_status=request.persistent_session_status.strip().lower(),
        cost_status=request.cost_status.strip().lower(),
        requires_manual_review=request.requires_manual_review,
        notes=request.notes,
        created_at=now,
        updated_at=now,
    )
    saved = save_payload(NUBE_PROJECTS_TABLE, project)
    record_nube_audit_event(
        action="cloud_project_registered",
        status=saved.status,
        detail=f"NUBE registered cloud project {saved.id} without external provider calls.",
        metadata={"project_id": saved.id},
    )
    return saved


def list_deployments() -> list[CloudDeployment]:
    seed_initial_records()
    return list_payloads(NUBE_DEPLOYMENTS_TABLE, CloudDeployment)


def create_deployment(request: CloudDeploymentCreate) -> CloudDeployment:
    check_no_secret_values(request.model_dump())
    now = utc_now()
    deployment = CloudDeployment(
        id=f"deployment-{normalize_id(request.project_id)}-{uuid4()}",
        project_id=normalize_id(request.project_id),
        environment=request.environment.strip().lower(),
        url=request.url,
        provider=request.provider.strip(),
        commit=request.commit,
        status=request.status.strip().lower(),
        tags=clean_list(request.tags),
        evidence=request.evidence,
        external_connection_enabled=False,
        deploy_executed_by_nube=False,
        created_at=now,
        updated_at=now,
    )
    saved = save_payload(NUBE_DEPLOYMENTS_TABLE, deployment)
    record_nube_audit_event(
        action="cloud_deployment_registered",
        status=saved.status,
        detail=f"NUBE registered deployment evidence for {saved.project_id}; no deploy was executed.",
        metadata={"deployment_id": saved.id, "project_id": saved.project_id},
    )
    return saved


def list_health_checks() -> list[CloudHealthCheck]:
    seed_initial_records()
    return list_payloads(NUBE_HEALTH_CHECKS_TABLE, CloudHealthCheck)


def create_health_check(request: CloudHealthCheckCreate) -> CloudHealthCheck:
    check_no_secret_values(request.model_dump())
    now = utc_now()
    health_check = CloudHealthCheck(
        id=f"health-{normalize_id(request.project_id)}-{uuid4()}",
        project_id=normalize_id(request.project_id),
        url=request.url,
        status=request.status.strip().lower(),
        status_code=request.status_code,
        source=request.source.strip(),
        evidence=request.evidence,
        external_monitor_connected=False,
        created_at=now,
        updated_at=now,
    )
    saved = save_payload(NUBE_HEALTH_CHECKS_TABLE, health_check)
    record_nube_audit_event(
        action="cloud_health_check_registered",
        status=saved.status,
        detail=f"NUBE registered health evidence for {saved.url}; no external monitor was connected.",
        metadata={"health_check_id": saved.id, "project_id": saved.project_id},
    )
    return saved


def list_risks() -> list[CloudRisk]:
    seed_initial_records()
    return list_payloads(NUBE_RISKS_TABLE, CloudRisk)


def create_risk(request: CloudRiskCreate) -> CloudRisk:
    check_no_secret_values(request.model_dump())
    now = utc_now()
    risk = CloudRisk(
        id=f"risk-{normalize_id(request.project_id)}-{uuid4()}",
        project_id=normalize_id(request.project_id),
        title=request.title.strip(),
        severity=request.severity.strip().lower(),
        status=request.status.strip().lower(),
        description=request.description.strip(),
        requires_manual_review=request.requires_manual_review,
        created_at=now,
        updated_at=now,
    )
    saved = save_payload(NUBE_RISKS_TABLE, risk)
    record_nube_audit_event(
        action="cloud_risk_registered",
        status=saved.status,
        detail=f"NUBE registered cloud risk {saved.id}.",
        severity=AuditSeverity.medium if saved.severity in {"high", "critical"} else AuditSeverity.info,
        metadata={"risk_id": saved.id, "project_id": saved.project_id},
    )
    return saved


def list_costs() -> list[CloudCostRecord]:
    seed_initial_records()
    return list_payloads(NUBE_COSTS_TABLE, CloudCostRecord)


def create_cost(request: CloudCostRecordCreate) -> CloudCostRecord:
    check_no_secret_values(request.model_dump())
    now = utc_now()
    cost = CloudCostRecord(
        id=f"cost-{normalize_id(request.project_id)}-{uuid4()}",
        project_id=normalize_id(request.project_id),
        provider=request.provider.strip(),
        cost_status=request.cost_status.strip().lower(),
        estimated_monthly=request.estimated_monthly,
        currency=request.currency.strip().upper(),
        requires_manual_review=request.requires_manual_review,
        notes=request.notes,
        created_at=now,
        updated_at=now,
    )
    saved = save_payload(NUBE_COSTS_TABLE, cost)
    record_nube_audit_event(
        action="cloud_cost_record_registered",
        status=saved.cost_status,
        detail=f"NUBE registered cost record for {saved.project_id}; values remain manual evidence only.",
        metadata={"cost_record_id": saved.id, "project_id": saved.project_id},
    )
    return saved


def primary_project() -> CloudProject:
    projects = list_projects()
    return next((project for project in projects if project.id == PROJECT_ID), projects[0])


def get_nube_status() -> NubeStatus:
    project = primary_project()
    deployments = list_deployments()
    health_checks = list_health_checks()
    risks = list_risks()
    costs = list_costs()
    database = next((item for item in project.databases if item.persistent), project.databases[0])
    return NubeStatus(
        status="nube_internal_control_tower",
        role="Torre de control cloud interna: registra, visualiza y audita; no despliega.",
        project_id=project.id,
        production_url=project.production_url,
        control_center_url=project.control_center_url,
        provider=project.provider,
        database=database.engine,
        persistent=database.persistent,
        temporal=database.temporal,
        last_commit=project.last_commit,
        tags=project.tags,
        backups=len(project.backups),
        variables=project.variables,
        risks=len(risks),
        cost_status=project.cost_status,
        projects=len(list_projects()),
        deployments=len(deployments),
        health_checks=len(health_checks),
        production_public_status=project.production_public_status,
        production_auth_status=project.production_auth_status,
        persistent_session_status=project.persistent_session_status,
        requires_manual_review=project.requires_manual_review or any(cost.requires_manual_review for cost in costs),
        external_connection_enabled=False,
        deploy_automation_enabled=False,
        vercel_api_connected=False,
        local_nube_touched=False,
        local_nube_path="not_touched",
        generated_at=utc_now(),
    )


def get_nube_evidence_for_auditoria(
    purpose: str = "cloud_evidence_review",
) -> NubeEvidence:
    evidence = NubeEvidence(
        requested_by="AUDITORIA",
        purpose=purpose,
        status=get_nube_status(),
        latest_deployments=list_deployments()[:5],
        latest_health_checks=list_health_checks()[:5],
        risks=list_risks()[:8],
        costs=list_costs()[:5],
        variables_masked=True,
        secrets_exposed=False,
        external_connection_enabled=False,
        metadata={
            "no_vercel_api": True,
            "no_deploy_executed": True,
            "no_local_nube_touch": True,
        },
    )
    record_nube_audit_event(
        action="auditoria_requested_cloud_evidence",
        status="evidence_prepared",
        detail="NUBE prepared internal cloud evidence for AUDITORIA without external provider access.",
        metadata={"purpose": purpose},
    )
    return evidence


def get_nube_brief_for_cerebro() -> dict[str, object]:
    status = get_nube_status()
    record_nube_audit_event(
        action="cerebro_requested_cloud_status",
        status=status.status,
        detail="NUBE prepared an internal cloud status brief for CEREBRO.",
        metadata={"project_id": status.project_id},
    )
    return {
        "status": status.status,
        "project_id": status.project_id,
        "production_url": status.production_url,
        "control_center_url": status.control_center_url,
        "provider": status.provider,
        "database": status.database,
        "persistent": status.persistent,
        "last_commit": status.last_commit,
        "tags": status.tags,
        "cost_status": status.cost_status,
        "risks": status.risks,
        "variables_masked": True,
        "external_connection_enabled": False,
        "deploy_automation_enabled": False,
        "vercel_api_connected": False,
        "local_nube_touched": False,
    }
