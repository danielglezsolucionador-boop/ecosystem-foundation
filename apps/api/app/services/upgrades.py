from __future__ import annotations

from datetime import UTC, datetime
import json
from uuid import uuid4

from app.core.database import connect, sql_placeholder
from app.core.safe_data import safe_payload
from app.schemas.audit import AuditoriaCriterion, AuditoriaObjectType, AuditoriaReviewCreate
from app.schemas.auth import AuthenticatedUser
from app.schemas.cerebro import CerebroTaskCreate
from app.schemas.upgrades import (
    DepartmentGap,
    ForgeWorkOrder,
    UpgradeAuditStatus,
    UpgradeDecisionRequest,
    UpgradeEvidence,
    UpgradeForgeStatus,
    UpgradeForjaRequest,
    UpgradeImplementedRequest,
    UpgradePackage,
    UpgradePackageCreate,
    UpgradePackageStatus,
    UpgradeReviewLink,
    UpgradeReviewRequest,
    UpgradeStatus,
    UpgradeStatusHistory,
    UpgradeTechnicalStatus,
)
from app.services.audit import create_auditoria_review
from app.services.cerebro import create_cerebro_task
from app.services.departments import (
    DepartmentError,
    get_department,
    get_department_audit,
    list_departments,
    normalize_id,
)

UPGRADE_TABLES = {
    "department_gaps",
    "upgrade_packages",
    "forge_work_orders",
    "upgrade_reviews",
    "upgrade_evidence",
    "upgrade_status_history",
}
SUPPORTED_DEPARTMENTS = {
    "pluma": "PLUMA",
    "lente": "LENTE",
    "marketing": "MARKETING",
    "marca_personal": "MARCA PERSONAL",
    "buscador_de_tendencias": "BUSCADOR",
    "web_factory": "WEB FACTORY",
    "creador_de_apis_y_skills": "CREADOR APIs/SKILLS",
    "ecommerce": "E-COMMERCE",
    "sniff_amazon": "SNIFF AMAZON",
    "dcft": "DCFT",
    "sentinela": "SENTINELA",
    "arsenal": "ARSENAL",
    "forja": "FORJA",
    "hermes": "HERMES",
    "auditoria": "AUDITORÍA",
    "nube": "NUBE",
    "cerebro": "CEREBRO",
}
GOVERNED_DEPARTMENTS = {"dcft", "sentinela", "arsenal"}


class UpgradeError(Exception):
    def __init__(self, status_code: int, detail: dict):
        super().__init__(str(detail))
        self.status_code = status_code
        self.detail = detail


def utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def placeholder() -> str:
    return sql_placeholder()


def ensure_table(table_name: str) -> None:
    if table_name not in UPGRADE_TABLES:
        raise UpgradeError(500, {"error": "invalid_upgrade_table", "table": table_name})


def ensure_upgrade_schema() -> None:
    with connect() as connection:
        for table_name in UPGRADE_TABLES:
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


def upsert_payload(table_name: str, item_id: str, payload: dict) -> None:
    ensure_table(table_name)
    ensure_upgrade_schema()
    ph = placeholder()
    now = utc_now()
    with connect() as connection:
        connection.execute(
            f"""
            INSERT INTO {table_name} (id, payload_json, created_at, updated_at)
            VALUES ({ph}, {ph}, {ph}, {ph})
            ON CONFLICT(id) DO UPDATE SET
                payload_json = excluded.payload_json,
                updated_at = excluded.updated_at
            """,
            (item_id, json.dumps(payload, ensure_ascii=False), now, now),
        )
        connection.commit()


def fetch_payload(table_name: str, item_id: str) -> dict | None:
    ensure_table(table_name)
    ensure_upgrade_schema()
    ph = placeholder()
    with connect() as connection:
        row = connection.execute(
            f"SELECT payload_json FROM {table_name} WHERE id = {ph}",
            (item_id,),
        ).fetchone()
    return safe_payload(row) if row else None


def fetch_payloads(table_name: str) -> list[dict]:
    ensure_table(table_name)
    ensure_upgrade_schema()
    with connect() as connection:
        rows = connection.execute(
            f"""
            SELECT payload_json
            FROM {table_name}
            ORDER BY created_at DESC
            """
        ).fetchall()
    payloads: list[dict] = []
    for row in rows:
        payload = safe_payload(row)
        if payload is not None:
            payloads.append(payload)
    return payloads


def actor_name(actor: AuthenticatedUser) -> str:
    return actor.name or actor.email or actor.role.value


def supported_department_ids() -> list[str]:
    known = {department.id for department in list_departments()}
    ids = list(SUPPORTED_DEPARTMENTS)
    for department_id in known:
        if department_id not in ids:
            ids.append(department_id)
    return ids


def department_metadata(raw_department_id: str) -> tuple[str, str, str, bool]:
    department_id = normalize_id(raw_department_id)
    try:
        department = get_department(department_id)
        return department.id, department.name, department.operational_status.value, department.id in GOVERNED_DEPARTMENTS
    except DepartmentError:
        name = SUPPORTED_DEPARTMENTS.get(department_id, raw_department_id.strip() or "UNKNOWN")
        return department_id, name, "missing/unknown", department_id in GOVERNED_DEPARTMENTS


def priority_from_data(
    *,
    requested_priority: str | None,
    source_priority: str | None,
    gaps: list[str],
    business_impact: str,
    risk: str,
    governed: bool,
) -> str:
    if requested_priority:
        return requested_priority
    if source_priority:
        return source_priority
    text = " ".join([*gaps, business_impact, risk]).lower()
    if any(word in text for word in ("bloqueo", "critical", "crítico", "seguridad", "legal", "tributario")):
        return "p0"
    if any(word in text for word in ("ingreso", "revenue", "venta", "e-commerce", "comercial", "usd")):
        return "p1"
    return "p2" if governed else "p1"


def status_history(
    package_id: str,
    *,
    status: str,
    message: str,
    actor: str,
) -> UpgradeStatusHistory:
    return UpgradeStatusHistory(
        id=f"upgrade_history_{uuid4()}",
        package_id=package_id,
        status=status,
        message=message,
        actor=actor,
        created_at=utc_now(),
    )


def save_history(entry: UpgradeStatusHistory) -> None:
    upsert_payload("upgrade_status_history", entry.id, entry.model_dump(mode="json"))


def save_package(package: UpgradePackage) -> UpgradePackage:
    package.updated_at = utc_now()
    upsert_payload("upgrade_packages", package.id, package.model_dump(mode="json"))
    return package


def get_package(package_id: str) -> UpgradePackage:
    payload = fetch_payload("upgrade_packages", package_id)
    if payload is None:
        raise UpgradeError(404, {"error": "upgrade_package_not_found", "package_id": package_id})
    return UpgradePackage(**payload)


def list_packages() -> list[UpgradePackage]:
    packages: list[UpgradePackage] = []
    for payload in fetch_payloads("upgrade_packages"):
        try:
            packages.append(UpgradePackage(**payload))
        except Exception:
            continue
    return packages


def source_audit_payload(source_audit_id: str | None):
    if not source_audit_id:
        return None
    try:
        return get_department_audit(source_audit_id)
    except DepartmentError as error:
        raise UpgradeError(error.status_code, error.detail) from error


def create_upgrade_package(
    request: UpgradePackageCreate,
    actor: AuthenticatedUser,
) -> UpgradePackage:
    audit = source_audit_payload(request.source_audit_id)
    raw_department_id = audit.department_id if audit is not None else request.department_id
    department_id, department_name, department_status, governed = department_metadata(raw_department_id)
    gaps = request.gaps or (audit.gaps if audit is not None else [])
    required_changes = request.required_changes or (audit.suggested_tasks if audit is not None else [])
    if not gaps:
        gaps = ["Brecha no especificada; requiere auditoría para completar evidencia."]
    if not required_changes:
        required_changes = ["Preparar paquete de mejora sin declarar implementación."]
    business_impact = request.business_impact or (
        audit.economic_impact if audit is not None else "Impacto económico pendiente de estimar."
    )
    priority = priority_from_data(
        requested_priority=request.priority,
        source_priority=audit.priority if audit is not None else None,
        gaps=gaps,
        business_impact=business_impact,
        risk=request.risk,
        governed=governed,
    )
    package_id = f"upgrade_package_{uuid4()}"
    now = utc_now()
    package = UpgradePackage(
        id=package_id,
        department=department_name,
        department_id=department_id,
        department_status=department_status,
        source_audit_id=request.source_audit_id,
        gaps=gaps,
        required_changes=required_changes,
        priority=priority,
        business_impact=business_impact,
        revenue_link=request.revenue_link,
        risk=request.risk,
        forge_status=UpgradeForgeStatus.not_sent,
        audit_status=UpgradeAuditStatus.not_requested,
        ceo_visibility=request.ceo_visibility,
        technical_status=(
            UpgradeTechnicalStatus.governed_pending_execution
            if governed
            else UpgradeTechnicalStatus.prepared
        ),
        status=UpgradePackageStatus.prioritized,
        requires_ceo_approval=False,
        governance_status="governed_no_touch" if governed else "standard",
        created_at=now,
        updated_at=now,
    )
    history = status_history(
        package.id,
        status=package.status.value,
        message="CEREBRO priorizó paquete de mejora desde brecha de AUDITORÍA.",
        actor=actor_name(actor),
    )
    package.history.insert(0, history)
    save_history(history)
    for gap_text in gaps:
        gap = DepartmentGap(
            id=f"department_gap_{uuid4()}",
            package_id=package.id,
            department_id=department_id,
            gap=gap_text,
            source_audit_id=request.source_audit_id,
            created_at=now,
        )
        upsert_payload("department_gaps", gap.id, gap.model_dump(mode="json"))
    return save_package(package)


def send_package_to_forja(
    package_id: str,
    request: UpgradeForjaRequest,
    actor: AuthenticatedUser,
) -> UpgradePackage:
    package = get_package(package_id)
    instruction = request.instruction or (
        f"Preparar mejora para {package.department}: "
        + "; ".join(package.required_changes[:4])
        + ". Sin ejecución externa ni producto protegido real."
    )
    task = create_cerebro_task(
        CerebroTaskCreate(
            title=f"Upgrade package {package.department}",
            description=instruction,
            destination="FORJA",
            priority=package.priority,
            requires_ceo_approval=False,
            reason="Department Upgrade Pipeline prepara tarea interna; no toca FORJA externa.",
        ),
        actor,
    )
    order = ForgeWorkOrder(
        id=f"forge_work_order_{uuid4()}",
        package_id=package.id,
        task_id=task.id,
        status=UpgradeForgeStatus.prepared,
        instruction=instruction,
        created_at=utc_now(),
    )
    package.work_orders.insert(0, order)
    package.forge_task_id = task.id
    package.forge_status = UpgradeForgeStatus.prepared
    package.technical_status = (
        UpgradeTechnicalStatus.governed_pending_execution
        if package.department_id in GOVERNED_DEPARTMENTS
        else UpgradeTechnicalStatus.pending_execution
    )
    package.status = UpgradePackageStatus.sent_to_forja
    history = status_history(
        package.id,
        status=package.status.value,
        message="FORJA recibió tarea preparada; implementación real no declarada.",
        actor=actor_name(actor),
    )
    package.history.insert(0, history)
    upsert_payload("forge_work_orders", order.id, order.model_dump(mode="json"))
    save_history(history)
    return save_package(package)


def mark_package_implemented(
    package_id: str,
    request: UpgradeImplementedRequest,
    actor: AuthenticatedUser,
) -> UpgradePackage:
    if not request.evidence or not request.evidence.strip():
        raise UpgradeError(
            400,
            {
                "error": "upgrade_evidence_required",
                "reason": "No se puede marcar implementación sin evidencia.",
            },
        )
    package = get_package(package_id)
    evidence = UpgradeEvidence(
        id=f"upgrade_evidence_{uuid4()}",
        package_id=package.id,
        evidence=request.evidence.strip(),
        implemented_by=request.implemented_by,
        created_at=utc_now(),
    )
    package.evidence.insert(0, evidence)
    package.forge_status = UpgradeForgeStatus.implemented_with_evidence
    package.technical_status = UpgradeTechnicalStatus.evidence_recorded_pending_audit
    package.status = UpgradePackageStatus.implemented_pending_audit
    package.audit_status = (
        UpgradeAuditStatus.pending_review
        if package.audit_review_id
        else UpgradeAuditStatus.not_requested
    )
    history = status_history(
        package.id,
        status=package.status.value,
        message="Implementación registrada con evidencia; falta revisión AUDITORÍA.",
        actor=actor_name(actor),
    )
    package.history.insert(0, history)
    upsert_payload("upgrade_evidence", evidence.id, evidence.model_dump(mode="json"))
    save_history(history)
    return save_package(package)


def request_package_review(
    package_id: str,
    request: UpgradeReviewRequest,
    actor: AuthenticatedUser,
) -> UpgradePackage:
    package = get_package(package_id)
    review = create_auditoria_review(
        AuditoriaReviewCreate(
            object_type=AuditoriaObjectType.department,
            reference=package.id,
            source="department_upgrade_pipeline",
            priority=package.priority,
            criteria=[
                AuditoriaCriterion.functional_quality,
                AuditoriaCriterion.security,
                AuditoriaCriterion.ceo_standard,
                AuditoriaCriterion.operational_risk,
                AuditoriaCriterion.commercial_risk,
            ],
            observations=[
                request.reason,
                "Revisión posterior de paquete; sin ejecución externa, sin pagos y sin SUNAT real.",
            ],
            metadata={
                "package_id": package.id,
                "department_id": package.department_id,
                "source_audit_id": package.source_audit_id,
                "external_connection_enabled": False,
                "runtime_connected": False,
            },
        )
    )
    link = UpgradeReviewLink(
        id=f"upgrade_review_{uuid4()}",
        package_id=package.id,
        review_id=review.id,
        status=UpgradeAuditStatus.pending_review,
        created_at=utc_now(),
    )
    package.audit_review_id = review.id
    package.audit_status = UpgradeAuditStatus.pending_review
    package.status = UpgradePackageStatus.waiting_audit
    package.review_links.insert(0, link)
    history = status_history(
        package.id,
        status=package.status.value,
        message="AUDITORÍA recibió revisión posterior del paquete.",
        actor=actor_name(actor),
    )
    package.history.insert(0, history)
    upsert_payload("upgrade_reviews", link.id, link.model_dump(mode="json"))
    save_history(history)
    return save_package(package)


def approve_package(
    package_id: str,
    request: UpgradeDecisionRequest,
    actor: AuthenticatedUser,
) -> UpgradePackage:
    package = get_package(package_id)
    review_id = request.auditoria_review_id or package.audit_review_id
    if not review_id:
        raise UpgradeError(
            400,
            {
                "error": "auditoria_review_required",
                "reason": "No se puede aprobar sin revisión AUDITORÍA.",
            },
        )
    package.audit_review_id = review_id
    package.audit_status = UpgradeAuditStatus.approved
    package.status = UpgradePackageStatus.approved
    package.technical_status = UpgradeTechnicalStatus.audit_approved
    history = status_history(
        package.id,
        status=package.status.value,
        message=f"AUDITORÍA aprobó el paquete: {request.reason}",
        actor=actor_name(actor),
    )
    package.history.insert(0, history)
    save_history(history)
    return save_package(package)


def reject_package(
    package_id: str,
    request: UpgradeDecisionRequest,
    actor: AuthenticatedUser,
) -> UpgradePackage:
    package = get_package(package_id)
    package.audit_status = UpgradeAuditStatus.rejected
    package.status = UpgradePackageStatus.rejected
    package.technical_status = UpgradeTechnicalStatus.audit_rejected
    package.risk = f"{package.risk}; rejected: {request.reason}"
    history = status_history(
        package.id,
        status=package.status.value,
        message=f"AUDITORÍA rechazó/observó el paquete: {request.reason}",
        actor=actor_name(actor),
    )
    package.history.insert(0, history)
    save_history(history)
    return save_package(package)


def packages_for_department(department_id: str) -> list[UpgradePackage]:
    normalized = normalize_id(department_id)
    return [package for package in list_packages() if package.department_id == normalized]


def get_upgrade_status() -> UpgradeStatus:
    packages = list_packages()
    waiting_forge = [
        package
        for package in packages
        if package.forge_status in {UpgradeForgeStatus.not_sent, UpgradeForgeStatus.prepared}
        and package.status not in {UpgradePackageStatus.approved, UpgradePackageStatus.rejected}
    ]
    waiting_audit = [
        package
        for package in packages
        if package.status in {UpgradePackageStatus.waiting_audit, UpgradePackageStatus.implemented_pending_audit}
    ]
    approved = [package for package in packages if package.status == UpgradePackageStatus.approved]
    rejected = [package for package in packages if package.status == UpgradePackageStatus.rejected]
    governed = [package for package in packages if package.governance_status.startswith("governed")]
    return UpgradeStatus(
        status="department_upgrade_pipeline_prepared_internal",
        packages=len(packages),
        open_gaps=sum(len(package.gaps) for package in packages if package.status != UpgradePackageStatus.approved),
        waiting_forge=len(waiting_forge),
        waiting_audit=len(waiting_audit),
        approved=len(approved),
        rejected=len(rejected),
        governed_packages=len(governed),
        supported_departments=supported_department_ids(),
        top_packages=packages[:6],
        external_connection_enabled=False,
        runtime_connected=False,
        payment_connected=False,
        sunat_enabled=False,
        generated_at=utc_now(),
    )
