from datetime import UTC, datetime
import json
from pathlib import Path
from uuid import uuid4

from app.core.database import connect, initialize_database, sql_placeholder
from app.schemas.audit import AuditCategory, AuditEventCreate, AuditSeverity
from app.schemas.auth import AuthenticatedUser
from app.schemas.cerebro import CerebroMissionCreate, CerebroTaskCreate
from app.schemas.departments import (
    CabinStatus,
    DepartmentAudit,
    DepartmentAuditActionRequest,
    DepartmentAuditCreate,
    DepartmentAuditStatus,
    DepartmentCabinEvidence,
    DepartmentOperationalStatus,
    DepartmentRecord,
)
from app.services.audit import create_audit_event
from app.services.cerebro import create_cerebro_task, create_mission

DEPARTMENT_AUDITS_TABLE = "department_automated_audits"
ROOT_DIR = Path(__file__).resolve().parents[4]
DOCS_DIR = ROOT_DIR / "docs" / "ecosystem" / "execution"


class DepartmentError(Exception):
    def __init__(self, status_code: int, detail: dict[str, object]) -> None:
        self.status_code = status_code
        self.detail = detail
        super().__init__(str(detail))


def utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def normalize_id(value: str) -> str:
    normalized = " ".join(str(value or "").strip().lower().split())
    aliases = {
        "auditoria": "auditoria",
        "auditoría": "auditoria",
        "auditor": "auditoria",
        "marca personal": "marca_personal",
        "buscador de tendencias": "buscador_de_tendencias",
        "web factory": "web_factory",
        "creador de apis/skills": "creador_de_apis_y_skills",
        "creador de apis": "creador_de_apis_y_skills",
        "creador de apis y skills": "creador_de_apis_y_skills",
        "api creator": "creador_de_apis_y_skills",
        "e-commerce": "ecommerce",
        "ecommerce": "ecommerce",
        "comercio autonomo": "ecommerce",
        "comercio autónomo": "ecommerce",
        "sniff amazon": "sniff_amazon",
        "chief amazon": "sniff_amazon",
        "dcft": "dcft",
        "doctor contable financiero tributario": "dcft",
        "sentinela": "sentinela",
        "centinela": "sentinela",
    }
    normalized = aliases.get(normalized, normalized)
    return normalized.replace(" ", "_").replace("-", "_").replace("/", "_")


def cabin(status: CabinStatus, notes: str, sources: list[str] | None = None) -> DepartmentCabinEvidence:
    return DepartmentCabinEvidence(status=status, notes=notes, sources=sources or [])


def department_record(
    *,
    department_id: str,
    name: str,
    purpose: str,
    goals: list[str],
    expected_functions: list[str],
    revenue_relation: str,
    risks: list[str],
    missing_data: list[str],
    operational_status: DepartmentOperationalStatus = DepartmentOperationalStatus.needs_audit,
    commercial_readiness: CabinStatus = CabinStatus.partial,
    technical_readiness: CabinStatus = CabinStatus.partial,
    human_readiness: CabinStatus = CabinStatus.partial,
    aliases: list[str] | None = None,
) -> DepartmentRecord:
    sources = discover_sources(department_id, name)
    has_sources = bool(sources)
    technical_status = CabinStatus.partial if has_sources else CabinStatus.unknown
    human_status = CabinStatus.partial if has_sources else CabinStatus.unknown
    return DepartmentRecord(
        id=department_id,
        name=name,
        aliases=aliases or [],
        purpose=purpose,
        goals=goals,
        expected_functions=expected_functions,
        revenue_relation=revenue_relation,
        cerebro_relation="CEREBRO puede crear mision, priorizar y pedir auditoria sin runtime externo.",
        auditoria_relation="AUDITORIA revisa evidencia, brechas, riesgos y readiness.",
        forja_relation="FORJA solo recibe tarea preparada si hay faltantes implementables.",
        nube_relation="NUBE queda como revision futura de despliegue/costos; no despliega en este bloque.",
        heart_cabin=cabin(
            CabinStatus.missing,
            "No se encontro cabina corazon especifica del departamento en las fuentes locales revisadas.",
            sources=[],
        ),
        technical_cabin=cabin(
            technical_status,
            "Existe evidencia tecnica/documental parcial." if has_sources else "No se encontro evidencia tecnica concreta.",
            sources=sources,
        ),
        human_cabin=cabin(
            human_status,
            "Aparece en cabina/control center o reportes, pero requiere cabina humana dedicada." if has_sources else "Cabina humana dedicada no localizada.",
            sources=sources,
        ),
        operational_status=operational_status,
        risks=risks,
        missing_data=missing_data,
        commercial_readiness=commercial_readiness,
        technical_readiness=technical_status if technical_readiness == CabinStatus.partial else technical_readiness,
        human_readiness=human_status if human_readiness == CabinStatus.partial else human_readiness,
    )


def supported_departments() -> dict[str, DepartmentRecord]:
    rows = [
        department_record(
            department_id="cerebro",
            name="CEREBRO",
            aliases=["Chief of Staff OS"],
            purpose="Coordinar prioridades, misiones, decisiones, riesgos y oportunidades.",
            goals=["Mover la empresa sin pedir permiso para todo.", "Escalar al CEO solo lo sensible."],
            expected_functions=["misiones", "alertas", "checkpoints", "matriz economica"],
            revenue_relation="Acelera decisiones y prioriza acciones que aportan a USD 6,000/mes.",
            risks=["Alucinar ejecuciones reales si no mantiene flags prepared/no_runtime."],
            missing_data=["Cabina corazon exacta especifica."],
            operational_status=DepartmentOperationalStatus.ready,
            commercial_readiness=CabinStatus.partial,
            technical_readiness=CabinStatus.complete,
            human_readiness=CabinStatus.partial,
        ),
        department_record(
            department_id="auditoria",
            name="AUDITORIA",
            aliases=["AUDITORÍA"],
            purpose="Revisar evidencia, brechas, riesgos, permisos y calidad.",
            goals=["Evitar claims falsos.", "Detectar faltantes por departamento."],
            expected_functions=["reviews", "queue", "gates", "audit trail"],
            revenue_relation="Reduce perdida por errores y acelera readiness comercial.",
            risks=["Bloquear de mas si falta evidencia estructurada."],
            missing_data=["Cabina corazon exacta dedicada."],
            operational_status=DepartmentOperationalStatus.ready,
            technical_readiness=CabinStatus.complete,
        ),
        department_record(
            department_id="nube",
            name="NUBE",
            purpose="Controlar URLs, costos, deploys preparados y salud cloud.",
            goals=["Reportar estado y riesgos cloud.", "No tocar NUBE local externa."],
            expected_functions=["status", "projects", "deployments", "health checks", "costs"],
            revenue_relation="Evita caidas, costos ocultos y friccion de despliegue.",
            risks=["Confundir torre documental con deploy real."],
            missing_data=["Cabina corazon exacta dedicada."],
            operational_status=DepartmentOperationalStatus.ready,
            technical_readiness=CabinStatus.complete,
        ),
        department_record(
            department_id="forja",
            name="FORJA",
            purpose="Recibir paquetes preparados para construccion controlada.",
            goals=["Convertir brechas auditadas en entregables."],
            expected_functions=["tareas preparadas", "paquetes de implementacion", "evidencia"],
            revenue_relation="Construye activos que pueden generar ingresos despues de auditoria.",
            risks=["Tocar FORJA externa real desde ecosistema."],
            missing_data=["No se toca FORJA productiva; falta cabina de ejecucion local especifica."],
            operational_status=DepartmentOperationalStatus.governed,
        ),
        department_record(
            department_id="hermes",
            name="HERMES",
            purpose="Apoyo de automatizacion ligera.",
            goals=["Acelerar tareas repetibles sin runtime externo."],
            expected_functions=["automatizacion ligera", "soporte a FORJA", "notificaciones preparadas"],
            revenue_relation="Reduce tiempo operativo.",
            risks=["Activar automatizacion real sin aprobacion tecnica."],
            missing_data=["Cabina humana/corazon dedicada."],
        ),
        department_record(
            department_id="pluma",
            name="PLUMA",
            purpose="Contenido, escritura y piezas comerciales.",
            goals=["Libros y bestseller como meta larga.", "Contenido bilingue para crecimiento."],
            expected_functions=[
                "libros",
                "articulos",
                "posts",
                "newsletters",
                "guiones",
                "contenido comercial",
                "espanol e ingles",
                "apoyo a marca personal y marketing",
            ],
            revenue_relation="Puede alimentar marca, leads y conversion organica.",
            risks=["Publicar o prometer bestseller sin evidencia."],
            missing_data=["Plan bestseller", "flujo bilingue validado", "cabina corazon dedicada."],
        ),
        department_record(
            department_id="lente",
            name="LENTE",
            purpose="Visual, video, avatares y criterio audiovisual.",
            goals=["5 canales con 100K+ suscriptores como meta larga."],
            expected_functions=[
                "YouTube",
                "TikTok",
                "avatares",
                "animacion",
                "podcasts con avatares",
                "canales por nicho",
            ],
            revenue_relation="Puede convertir video y visuales en audiencia y ventas.",
            risks=["Prometer canales o assets reales sin produccion validada."],
            missing_data=["Plan de canales", "pipeline de avatares", "cabina corazon dedicada."],
        ),
        department_record(
            department_id="marketing",
            name="MARKETING",
            purpose="Crecimiento, embudos, leads y campanas.",
            goals=["Vender ofertas del ecosistema sin gasto por defecto."],
            expected_functions=["organico", "embudos", "leads", "ROI de campanas pagadas", "venta de DCFT/SENTINELA si CEO lo decide"],
            revenue_relation="Canal directo para ingresos; pagos reales requieren CEO.",
            risks=["Campanas pagadas sin ROI o sin aprobacion CEO."],
            missing_data=["Funnel documentado", "modelo de lead scoring", "ROI validado."],
        ),
        department_record(
            department_id="marca_personal",
            name="MARCA PERSONAL",
            purpose="Convertir autoridad del CEO en audiencia y oportunidades.",
            goals=["Metas de seguidores en TikTok, Instagram, LinkedIn, X y YouTube."],
            expected_functions=["calendario CEO", "posts", "video corto", "autoridad", "leads organicos"],
            revenue_relation="Atrae demanda y alianzas.",
            risks=["Inflar seguidores sin estrategia medible."],
            missing_data=["Metas numericas por red", "baseline actual."],
        ),
        department_record(
            department_id="buscador_de_tendencias",
            name="BUSCADOR DE TENDENCIAS",
            purpose="Detectar senales utiles de mercado.",
            goals=["Encontrar oportunidades antes que el mercado."],
            expected_functions=["radar", "senales", "priorizacion", "alertas a CEREBRO"],
            revenue_relation="Origina ideas de ingreso sin ejecutar compras.",
            risks=["Confundir radar documental con investigacion externa real."],
            missing_data=["Fuente de senales configurada", "criterio de scoring."],
        ),
        department_record(
            department_id="web_factory",
            name="WEB FACTORY",
            purpose="Preparar landings y experiencias web.",
            goals=["Convertir ofertas en paginas listas para revision."],
            expected_functions=["landing", "sitios", "formularios", "conversion"],
            revenue_relation="Convierte trafico en leads.",
            risks=["Publicar sitios sin auditoria o deploy seguro."],
            missing_data=["Plantillas aprobadas", "metricas de conversion."],
        ),
        department_record(
            department_id="creador_de_apis_y_skills",
            name="CREADOR DE APIS Y SKILLS",
            aliases=["Creador de APIs/Skills"],
            purpose="Preparar APIs, skills y capacidades vendibles.",
            goals=["Convertir capacidades en productos internos o comerciales."],
            expected_functions=["API ideas", "skills", "contratos", "capacidades para ARSENAL"],
            revenue_relation="Puede generar productos vendibles tras auditoria.",
            risks=["Conectar APIs externas con costo sin CEO."],
            missing_data=["Catalogo de skills priorizado", "pricing validado."],
        ),
        department_record(
            department_id="ecommerce",
            name="E-COMMERCE",
            aliases=["Comercio Autonomo"],
            purpose="Linea comercial separada de comercio.",
            goals=["USD 10,000 mensuales separados de la meta global."],
            expected_functions=["productos", "margen", "operacion", "riesgo", "ventas"],
            revenue_relation="Meta propia USD 10,000/mes, separada del ecosistema global.",
            risks=["Mezclar meta e-commerce con meta global."],
            missing_data=["Productos priorizados", "margen real", "proveedores."],
        ),
        department_record(
            department_id="sniff_amazon",
            name="SNIFF AMAZON / CHIEF AMAZON",
            aliases=["SNIFF AMAZON", "CHIEF AMAZON"],
            purpose="Radar de oportunidades Amazon/marketplace.",
            goals=["Detectar oportunidades sin contactar Amazon ni proveedores reales."],
            expected_functions=["marketplace radar", "producto", "margen estimado", "senales"],
            revenue_relation="Alimenta oportunidades de e-commerce.",
            risks=["Confundir radar con compra o venta real."],
            missing_data=["Fuente de datos validada", "criterio de margen."],
        ),
        department_record(
            department_id="dcft",
            name="DCFT",
            aliases=["Doctor Contable Financiero Tributario"],
            purpose="Producto contable financiero tributario protegido.",
            goals=["Actualizar readiness y gaps sin SUNAT real.", "No asignar meta de venta propia en esta auditoria."],
            expected_functions=["contabilidad", "finanzas", "tributacion", "auditoria contable", "auditoria financiera"],
            revenue_relation="Puede ser producto prioritario del ecosistema, pero esta auditoria no le asigna venta propia.",
            risks=["Tocar SUNAT real o declarar integracion productiva."],
            missing_data=["Cabinas originales completas", "readiness productivo autorizado."],
            operational_status=DepartmentOperationalStatus.governed,
            commercial_readiness=CabinStatus.unknown,
        ),
        department_record(
            department_id="sentinela",
            name="SENTINELA",
            aliases=["CENTINELA"],
            purpose="Seguridad y proteccion del ecosistema.",
            goals=["Actualizar readiness de seguridad sin runtime productivo.", "No asignar meta de venta propia en esta auditoria."],
            expected_functions=["permisos", "datos", "prompts", "incidentes", "riesgos"],
            revenue_relation="Queda como proteccion defensiva del ecosistema, sin etiqueta comercial propia en Bloque I.",
            risks=["Declarar producto o runtime real sin evidencia."],
            missing_data=["Cabina defensiva completa", "criterios de activacion."],
            operational_status=DepartmentOperationalStatus.governed,
            commercial_readiness=CabinStatus.unknown,
        ),
        department_record(
            department_id="arsenal",
            name="ARSENAL",
            purpose="Almacen estrategico de APIs, skills, modelos, conectores y capacidades.",
            goals=["Registrar capacidades futuras sin secretos ni runtime."],
            expected_functions=["catalogo de capacidades", "conectores", "modelos", "skills"],
            revenue_relation="Repositorio de capacidades futuras; sin venta directa en este bloque.",
            risks=["Guardar secretos o conectar APIs reales."],
            missing_data=["Cabina humana completa", "catalogo priorizado."],
            operational_status=DepartmentOperationalStatus.unknown,
            commercial_readiness=CabinStatus.unknown,
        ),
    ]
    return {row.id: row for row in rows}


def ensure_department_schema() -> None:
    initialize_database()
    placeholder = sql_placeholder()
    with connect() as connection:
        connection.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {DEPARTMENT_AUDITS_TABLE} (
                id TEXT PRIMARY KEY,
                department_id TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        connection.execute(
            f"""
            CREATE INDEX IF NOT EXISTS idx_department_audits_department
            ON {DEPARTMENT_AUDITS_TABLE} (department_id)
            """
        )
        connection.commit()
        # Keep placeholder referenced for Postgres compatibility lint/readability.
        _ = placeholder


def discover_sources(department_id: str, name: str) -> list[str]:
    if not DOCS_DIR.exists():
        return []
    terms = {department_id.replace("_", " "), name.lower(), department_id.lower()}
    if department_id == "sentinela":
        terms.add("centinela")
    if department_id == "dcft":
        terms.add("doctor contable")
    matches: list[str] = []
    for path in DOCS_DIR.rglob("*.md"):
        try:
            text = path.read_text(encoding="utf-8", errors="ignore").lower()
        except OSError:
            continue
        if any(term and term in text for term in terms):
            matches.append(str(path.relative_to(ROOT_DIR)).replace("\\", "/"))
    return sorted(matches)[:8]


def audit_event(
    *,
    actor: AuthenticatedUser,
    action: str,
    status: str,
    detail: str,
    department_id: str,
    severity: AuditSeverity = AuditSeverity.info,
    metadata: dict[str, object] | None = None,
) -> str:
    event = create_audit_event(
        AuditEventCreate(
            category=AuditCategory.runtime,
            severity=severity,
            source="departments.automated_audit",
            action=action,
            status=status,
            detail=detail,
            metadata={
                "department_id": department_id,
                "external_connection_enabled": False,
                "runtime_connected": False,
                "sunat_enabled": False,
                **(metadata or {}),
            },
        )
    )
    return event.id


def insert_audit(audit: DepartmentAudit) -> None:
    ensure_department_schema()
    placeholder = sql_placeholder()
    with connect() as connection:
        connection.execute(
            f"""
            INSERT INTO {DEPARTMENT_AUDITS_TABLE} (id, department_id, payload_json, created_at, updated_at)
            VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder})
            """,
            (audit.id, audit.department_id, audit.model_dump_json(), audit.created_at, audit.updated_at),
        )
        connection.commit()


def update_audit(audit: DepartmentAudit) -> None:
    ensure_department_schema()
    placeholder = sql_placeholder()
    now = utc_now()
    audit.updated_at = now
    with connect() as connection:
        connection.execute(
            f"""
            UPDATE {DEPARTMENT_AUDITS_TABLE}
            SET payload_json = {placeholder}, updated_at = {placeholder}
            WHERE id = {placeholder}
            """,
            (audit.model_dump_json(), now, audit.id),
        )
        connection.commit()


def fetch_audit_payload(audit_id: str) -> dict | None:
    ensure_department_schema()
    placeholder = sql_placeholder()
    with connect() as connection:
        row = connection.execute(
            f"SELECT payload_json FROM {DEPARTMENT_AUDITS_TABLE} WHERE id = {placeholder}",
            (audit_id,),
        ).fetchone()
    return json.loads(row["payload_json"]) if row else None


def list_departments() -> list[DepartmentRecord]:
    return list(supported_departments().values())


def get_department(department_id: str) -> DepartmentRecord:
    normalized = normalize_id(department_id)
    department = supported_departments().get(normalized)
    if department is None:
        raise DepartmentError(404, {"error": "department_not_found", "department_id": department_id})
    return department


def list_department_audits() -> list[DepartmentAudit]:
    ensure_department_schema()
    with connect() as connection:
        rows = connection.execute(
            f"""
            SELECT payload_json
            FROM {DEPARTMENT_AUDITS_TABLE}
            ORDER BY created_at DESC
            """
        ).fetchall()
    return [DepartmentAudit(**json.loads(row["payload_json"])) for row in rows]


def get_department_audit(audit_id: str) -> DepartmentAudit:
    payload = fetch_audit_payload(audit_id)
    if payload is None:
        raise DepartmentError(404, {"error": "department_audit_not_found", "audit_id": audit_id})
    return DepartmentAudit(**payload)


def latest_department_audit(department_id: str) -> DepartmentAudit | None:
    normalized = normalize_id(department_id)
    for audit in list_department_audits():
        if audit.department_id == normalized:
            return audit
    return None


def audit_gaps(department: DepartmentRecord) -> tuple[list[str], list[str]]:
    gaps = list(department.missing_data)
    tasks: list[str] = []
    for expected in department.expected_functions:
        expected_lower = expected.lower()
        if department.id in {"pluma", "lente", "marketing", "marca_personal", "ecommerce", "sniff_amazon"}:
            if expected_lower in {"libros", "youtube", "organico", "productos", "marketplace radar"}:
                continue
            gaps.append(f"Validar capacidad: {expected}.")
            tasks.append(f"Preparar evidencia y flujo para {department.name}: {expected}.")
    if department.heart_cabin.status != CabinStatus.complete:
        tasks.append(f"Crear o completar cabina corazon de {department.name}.")
    if department.technical_cabin.status in {CabinStatus.missing, CabinStatus.unknown, CabinStatus.partial}:
        tasks.append(f"Completar cabina tecnica/readiness de {department.name}.")
    return gaps[:12], tasks[:12]


def audit_priority(department: DepartmentRecord, gaps: list[str]) -> str:
    if department.id in {"dcft", "sentinela"}:
        return "p1"
    if len(gaps) >= 6:
        return "p1"
    if department.operational_status == DepartmentOperationalStatus.ready:
        return "p2"
    return "p1"


def audit_recommendation(department: DepartmentRecord, gaps: list[str], requires_forja: bool) -> str:
    if department.id == "dcft":
        return "Revisar readiness y actualizacion sin SUNAT real; no asignar meta de venta propia."
    if department.id == "sentinela":
        return "Revisar actualizacion defensiva sin runtime productivo; sin etiqueta comercial propia ni meta de venta propia."
    if requires_forja:
        return "AUDITORIA recomienda paquete preparado para FORJA y nueva revision posterior."
    if gaps:
        return "AUDITORIA recomienda completar evidencia antes de declarar readiness."
    return "AUDITORIA no detecta brecha critica nueva; mantener seguimiento."


def create_department_audit(
    department_id: str,
    request: DepartmentAuditCreate,
    actor: AuthenticatedUser,
) -> DepartmentAudit:
    department = get_department(department_id)
    now = utc_now()
    gaps, tasks = audit_gaps(department)
    requires_forja = bool(tasks) and department.id not in {"dcft", "sentinela", "arsenal"}
    requires_ceo = department.id in {"dcft", "sentinela", "arsenal"} or any(
        "campana pagada" in gap.lower() or "pago" in gap.lower() for gap in gaps
    )
    priority = audit_priority(department, gaps)
    operational = (
        DepartmentOperationalStatus.needs_forge
        if requires_forja
        else department.operational_status
    )
    audit_id = f"department_audit_{uuid4()}"
    trail_id = audit_event(
        actor=actor,
        action="create_department_audit",
        status="generated",
        detail=f"AUDITORIA generated automated audit for {department.name}.",
        department_id=department.id,
        metadata={"requested_by": request.requested_by, "priority": priority},
    )
    mission_id = None
    if request.create_cerebro_mission:
        mission = create_mission(
            CerebroMissionCreate(
                title=f"Auditar {department.name}",
                objective=request.instruction or f"Revisar brechas de {department.name} y reportar al CEO.",
                origin="department_automated_audit",
                leader_department="AUDITORIA",
                involved_departments=["CEREBRO", "AUDITORIA", department.name],
                priority=priority,
                action_type="request_audit_report",
                requires_money=False,
                expected_report=f"Reporte de auditoria automatica para {department.name}.",
            ),
            actor,
        )
        mission_id = mission.id
    audit = DepartmentAudit(
        id=audit_id,
        department_id=department.id,
        department_name=department.name,
        requested_by=request.requested_by,
        instruction=request.instruction,
        sources_reviewed=department.technical_cabin.sources or department.human_cabin.sources,
        heart_cabin=department.heart_cabin,
        technical_cabin=department.technical_cabin,
        human_cabin=department.human_cabin,
        gaps=gaps,
        suggested_tasks=tasks,
        priority=priority,
        economic_impact=department.revenue_relation,
        risk="; ".join(department.risks) or "unknown",
        status=DepartmentAuditStatus.generated,
        operational_status=operational,
        recommendation=audit_recommendation(department, gaps, requires_forja),
        requires_forja=requires_forja,
        requires_ceo=requires_ceo,
        cerebro_mission_id=mission_id,
        audit_trail=[trail_id],
        created_at=now,
        updated_at=now,
    )
    insert_audit(audit)
    return audit


def send_audit_to_forja(
    audit_id: str,
    request: DepartmentAuditActionRequest,
    actor: AuthenticatedUser,
) -> DepartmentAudit:
    audit = get_department_audit(audit_id)
    if audit.department_id in {"dcft", "sentinela", "arsenal"}:
        raise DepartmentError(
            400,
            {
                "error": "protected_department_forja_blocked",
                "department_id": audit.department_id,
                "reason": "protected_or_governed_department",
            },
        )
    task = create_cerebro_task(
        CerebroTaskCreate(
            title=f"FORJA package for {audit.department_name}",
            description=(
                request.reason
                or f"Preparar paquete implementable desde auditoria {audit.id}: "
                + "; ".join(audit.suggested_tasks[:4])
            ),
            destination="FORJA",
            priority=audit.priority,
            reason="Tarea preparada por auditoria automatica; sin FORJA externa real.",
        ),
        actor,
    )
    trail_id = audit_event(
        actor=actor,
        action="send_department_audit_to_forja",
        status="sent_to_forja",
        detail=f"AUDITORIA prepared FORJA task for {audit.department_name}.",
        department_id=audit.department_id,
        metadata={"audit_id": audit.id, "forja_task_id": task.id},
    )
    audit.status = DepartmentAuditStatus.sent_to_forja
    audit.forja_task_id = task.id
    audit.audit_trail.insert(0, trail_id)
    audit.requires_forja = True
    update_audit(audit)
    return audit


def send_audit_to_cerebro(
    audit_id: str,
    request: DepartmentAuditActionRequest,
    actor: AuthenticatedUser,
) -> DepartmentAudit:
    audit = get_department_audit(audit_id)
    mission = create_mission(
        CerebroMissionCreate(
            title=f"Seguimiento auditoria {audit.department_name}",
            objective=request.reason or audit.recommendation,
            origin="department_audit_report",
            leader_department="CEREBRO",
            involved_departments=["CEREBRO", "AUDITORIA", audit.department_name],
            priority=audit.priority,
            action_type="request_audit_report",
            expected_report=f"CEREBRO reporta al CEO auditoria {audit.id}.",
        ),
        actor,
    )
    trail_id = audit_event(
        actor=actor,
        action="send_department_audit_to_cerebro",
        status="sent_to_cerebro",
        detail=f"AUDITORIA sent department audit report to CEREBRO for {audit.department_name}.",
        department_id=audit.department_id,
        metadata={"audit_id": audit.id, "cerebro_mission_id": mission.id},
    )
    audit.status = DepartmentAuditStatus.sent_to_cerebro
    audit.cerebro_mission_id = mission.id
    audit.audit_trail.insert(0, trail_id)
    update_audit(audit)
    return audit


def mark_audit_reviewed(
    audit_id: str,
    request: DepartmentAuditActionRequest,
    actor: AuthenticatedUser,
) -> DepartmentAudit:
    audit = get_department_audit(audit_id)
    trail_id = audit_event(
        actor=actor,
        action="mark_department_audit_reviewed",
        status="reviewed",
        detail=f"Department audit marked reviewed for {audit.department_name}.",
        department_id=audit.department_id,
        metadata={"audit_id": audit.id, "evidence": request.evidence or "not_provided"},
    )
    audit.status = DepartmentAuditStatus.reviewed
    audit.audit_trail.insert(0, trail_id)
    update_audit(audit)
    return audit
