from datetime import UTC, datetime
import json
from uuid import uuid4

from app.core.database import connect, initialize_database, sql_placeholder
from app.schemas.audit import AuditCategory, AuditEventCreate, AuditSeverity
from app.schemas.auth import AuthenticatedUser
from app.schemas.cerebro import CerebroApprovalRequestCreate
from app.schemas.revenue import (
    RevenueApprovalRequest,
    RevenueDailyReport,
    RevenueDepartmentContribution,
    RevenueEconomicMatrix,
    RevenueGoal,
    RevenueGoalCreate,
    RevenueOpportunity,
    RevenueOpportunityCreate,
    RevenueOpportunityEvaluateRequest,
    RevenueOpportunityStatus,
    RevenueSprintDaily,
    RevenueSprintEvidenceStatus,
    RevenueSprintMission,
    RevenueSprintMissionCreate,
    RevenueSprintReport,
    RevenueSprintReportCreate,
    RevenueSprintRoute,
    RevenueSprintRouteCreate,
    RevenueSprintRouteStatus,
    RevenueSprintStatus,
    RevenueSprintStatusValue,
    RevenueStatus,
)
from app.services.audit import create_audit_event
from app.services.cerebro import create_approval_request

REVENUE_GOALS_TABLE = "revenue_os_goals"
REVENUE_OPPORTUNITIES_TABLE = "revenue_os_opportunities"
REVENUE_APPROVAL_REQUESTS_TABLE = "revenue_os_approval_requests"
REVENUE_SPRINT_STATE_TABLE = "revenue_sprint_state"
REVENUE_SPRINT_ROUTES_TABLE = "revenue_sprint_routes"
REVENUE_SPRINT_MISSIONS_TABLE = "revenue_sprint_missions"
REVENUE_SPRINT_REPORTS_TABLE = "revenue_sprint_reports"

GLOBAL_MONTHLY_GOAL_USD = 6000.0
ECOMMERCE_MONTHLY_GOAL_USD = 10000.0

MONEY_ACTIONS = {
    "real_money_payment",
    "paid_campaign",
    "paid_api",
    "api_with_cost",
    "tool_with_cost",
    "inventory_purchase",
    "contract_service",
    "hiring",
    "external_account_with_cost",
    "paid_ads",
    "paid_tool",
}

NO_APPROVAL_ACTIONS = {
    "organic",
    "organic_post",
    "organic_validation",
    "analysis",
    "internal_mission",
    "local_agent",
    "local_agent_activation",
    "send_task_to_forja",
    "controlled_deploy",
    "controlled_production_deploy",
    "organic_post_configured_account",
    "content_preparation",
    "landing_preparation",
    "demand_validation",
}

DEPARTMENT_REVENUE_ROLES = [
    (
        "pluma",
        "PLUMA",
        "Autoridad, libros, contenido comercial y trafico organico.",
        "direct",
        "global",
    ),
    (
        "lente",
        "LENTE",
        "Canales, videos, assets y monetizacion audiovisual preparada.",
        "direct",
        "global",
    ),
    (
        "marketing",
        "MARKETING",
        "Leads, demanda, ventas y embudos; vende DCFT y SENTINELA cuando esten listos.",
        "direct",
        "global",
    ),
    (
        "marca_personal",
        "MARCA PERSONAL",
        "Autoridad, audiencia, alianzas y confianza del CEO.",
        "direct",
        "global",
    ),
    (
        "buscador_de_tendencias",
        "BUSCADOR DE TENDENCIAS",
        "Detecta oportunidades monetizables antes de construir.",
        "direct",
        "global",
    ),
    (
        "creador_de_apis_y_skills",
        "CREADOR APIs/SKILLS",
        "Productos tecnicos vendibles, APIs, skills y automatizaciones.",
        "direct",
        "global",
    ),
    (
        "web_factory",
        "WEB FACTORY",
        "Landings y paginas para vender ofertas preparadas.",
        "direct",
        "global",
    ),
    (
        "ecommerce",
        "E-COMMERCE",
        "Meta propia USD 10,000 mensual, separada de la meta global.",
        "direct",
        "ecommerce",
    ),
    (
        "sniff_amazon",
        "SNIFF AMAZON",
        "Oportunidades Amazon y marketplace para e-commerce.",
        "direct",
        "ecommerce",
    ),
    (
        "dcft",
        "DCFT",
        "Producto protegido: Marketing lo vendera cuando este actualizado; sin SUNAT real.",
        "prepared_product",
        "global",
    ),
    (
        "sentinela",
        "SENTINELA",
        "Producto protegido: Marketing lo vendera cuando este actualizado; sin runtime real.",
        "prepared_product",
        "global",
    ),
    (
        "auditoria",
        "AUDITORIA",
        "Control de calidad, evidencia, riesgo comercial y no inventar ingresos.",
        "indirect",
        "indirect",
    ),
    (
        "nube",
        "NUBE",
        "Control operativo, URLs, costos y despliegues preparados.",
        "indirect",
        "indirect",
    ),
    (
        "hermes",
        "HERMES",
        "Automatizacion ligera y soporte interno sin cuentas externas nuevas.",
        "indirect",
        "indirect",
    ),
    (
        "forja",
        "FORJA",
        "Ejecucion preparada de entregables internos cuando la politica lo permite.",
        "indirect",
        "indirect",
    ),
]


class RevenueError(Exception):
    def __init__(self, status_code: int, detail: dict[str, object]) -> None:
        self.status_code = status_code
        self.detail = detail
        super().__init__(str(detail))


def utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def normalize(value: object) -> str:
    return str(value or "").strip().lower().replace(" ", "_").replace("-", "_")


def actor_name(user: AuthenticatedUser) -> str:
    return user.email or user.name or user.id


def safe_id(value: str, fallback: str) -> str:
    normalized = "".join(char if char.isalnum() else "_" for char in normalize(value))
    normalized = "_".join(part for part in normalized.split("_") if part)
    return normalized or fallback


def ensure_revenue_schema() -> None:
    initialize_database()
    with connect() as connection:
        for table_name in [
            REVENUE_GOALS_TABLE,
            REVENUE_OPPORTUNITIES_TABLE,
            REVENUE_APPROVAL_REQUESTS_TABLE,
            REVENUE_SPRINT_STATE_TABLE,
            REVENUE_SPRINT_ROUTES_TABLE,
            REVENUE_SPRINT_MISSIONS_TABLE,
            REVENUE_SPRINT_REPORTS_TABLE,
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


def insert_payload(table_name: str, item_id: str, payload: str) -> None:
    placeholder = sql_placeholder()
    now = utc_now()
    with connect() as connection:
        connection.execute(
            f"""
            INSERT INTO {table_name} (id, payload_json, created_at, updated_at)
            VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder})
            """,
            (item_id, payload, now, now),
        )
        connection.commit()


def update_payload(table_name: str, item_id: str, payload: str) -> None:
    placeholder = sql_placeholder()
    now = utc_now()
    with connect() as connection:
        connection.execute(
            f"""
            UPDATE {table_name}
            SET payload_json = {placeholder}, updated_at = {placeholder}
            WHERE id = {placeholder}
            """,
            (payload, now, item_id),
        )
        connection.commit()


def fetch_payloads(table_name: str) -> list[dict]:
    ensure_revenue_schema()
    with connect() as connection:
        rows = connection.execute(
            f"""
            SELECT payload_json
            FROM {table_name}
            ORDER BY created_at DESC
            """
        ).fetchall()
    return [json.loads(row["payload_json"]) for row in rows]


def fetch_payload(table_name: str, item_id: str) -> dict | None:
    ensure_revenue_schema()
    placeholder = sql_placeholder()
    with connect() as connection:
        row = connection.execute(
            f"SELECT payload_json FROM {table_name} WHERE id = {placeholder}",
            (item_id,),
        ).fetchone()
    return json.loads(row["payload_json"]) if row else None


def upsert_payload(table_name: str, item_id: str, payload: str) -> None:
    existing = fetch_payload(table_name, item_id)
    if existing is None:
        insert_payload(table_name, item_id, payload)
    else:
        update_payload(table_name, item_id, payload)


def audit_revenue_action(
    *,
    actor: AuthenticatedUser | None,
    action: str,
    status: str,
    detail: str,
    severity: AuditSeverity = AuditSeverity.info,
    metadata: dict[str, object] | None = None,
) -> str:
    event = create_audit_event(
        AuditEventCreate(
            category=AuditCategory.data_change,
            severity=severity,
            source="revenue.os",
            action=action,
            status=status,
            detail=detail,
            metadata={
                "actor": actor_name(actor) if actor else "system",
                "external_connection_enabled": False,
                "runtime_connected": False,
                "payment_connected": False,
                "sunat_enabled": False,
                "real_revenue_confirmed": False,
                **(metadata or {}),
            },
        )
    )
    return event.id


def default_goals() -> list[RevenueGoal]:
    now = utc_now()
    return [
        RevenueGoal(
            id="global_6000_usd",
            name="Meta global Ecosistema IA",
            monthly_target_usd=GLOBAL_MONTHLY_GOAL_USD,
            scope="global",
            separated_from_global=False,
            created_at=now,
            updated_at=now,
        ),
        RevenueGoal(
            id="ecommerce_10000_usd",
            name="Meta E-COMMERCE separada",
            monthly_target_usd=ECOMMERCE_MONTHLY_GOAL_USD,
            scope="ecommerce",
            separated_from_global=True,
            created_at=now,
            updated_at=now,
        ),
    ]


def seed_revenue_defaults() -> None:
    ensure_revenue_schema()
    existing = fetch_payloads(REVENUE_GOALS_TABLE)
    if existing:
        return
    for goal in default_goals():
        insert_payload(REVENUE_GOALS_TABLE, goal.id, goal.model_dump_json())


def money_requires_approval(action_type: str, investment_usd: float | None) -> bool:
    action = normalize(action_type)
    if investment_usd is not None and investment_usd > 0:
        return True
    if action in MONEY_ACTIONS:
        return True
    if action in NO_APPROVAL_ACTIONS:
        return False
    return False


def matrix_has_required_data(
    *,
    investment_usd: float | None,
    expected_revenue_usd: float | None,
    probability_percent: float | None,
    requires_ceo_approval: bool,
) -> bool:
    if expected_revenue_usd is None:
        return False
    if requires_ceo_approval and investment_usd is None:
        return False
    if probability_percent is None:
        return False
    return True


def build_economic_matrix(
    *,
    investment_usd: float | None,
    expected_revenue_usd: float | None,
    expected_net_profit_usd: float | None,
    probability_percent: float | None,
    risk: str,
    payback_time: str,
    ecommerce_separate: bool,
    action_type: str,
    recommendation: str | None = None,
) -> RevenueEconomicMatrix:
    requires_ceo = money_requires_approval(action_type, investment_usd)
    complete = matrix_has_required_data(
        investment_usd=investment_usd,
        expected_revenue_usd=expected_revenue_usd,
        probability_percent=probability_percent,
        requires_ceo_approval=requires_ceo,
    )
    if not complete:
        return RevenueEconomicMatrix(
            investment_usd=investment_usd,
            expected_revenue_usd=expected_revenue_usd,
            expected_net_profit_usd=expected_net_profit_usd,
            probability_percent=probability_percent,
            payback_time=payback_time,
            risk=risk,
            status="needs_more_data",
            recommendation=recommendation or "Pedir datos antes de decidir; no inventar ROI.",
        )

    investment = float(investment_usd or 0)
    expected = float(expected_revenue_usd or 0)
    net_profit = (
        float(expected_net_profit_usd)
        if expected_net_profit_usd is not None
        else expected - investment
    )
    probability = float(probability_percent or 0)
    weighted_expected = expected * (probability / 100)
    roi_percent = ((net_profit / investment) * 100) if investment > 0 else None
    global_contribution = None if ecommerce_separate else (net_profit / GLOBAL_MONTHLY_GOAL_USD) * 100
    ecommerce_contribution = (net_profit / ECOMMERCE_MONTHLY_GOAL_USD) * 100 if ecommerce_separate else None
    if recommendation:
        final_recommendation = recommendation
    elif requires_ceo:
        final_recommendation = "CEO, revisar matriz economica antes de aprobar dinero real."
    else:
        final_recommendation = "Preparar oportunidad organica sin gasto real."

    return RevenueEconomicMatrix(
        investment_usd=round(investment, 2),
        expected_revenue_usd=round(expected, 2),
        expected_net_profit_usd=round(net_profit, 2),
        probability_percent=round(probability, 2),
        weighted_expected_revenue_usd=round(weighted_expected, 2),
        roi_percent=round(roi_percent, 2) if roi_percent is not None else None,
        payback_time=payback_time,
        risk=risk,
        monthly_goal_contribution_percent=round(global_contribution, 2)
        if global_contribution is not None
        else None,
        ecommerce_goal_contribution_percent=round(ecommerce_contribution, 2)
        if ecommerce_contribution is not None
        else None,
        status="calculated",
        recommendation=final_recommendation,
    )


def status_for_opportunity(
    *,
    matrix: RevenueEconomicMatrix,
    requires_ceo_approval: bool,
    requested_status: RevenueOpportunityStatus | None = None,
) -> RevenueOpportunityStatus:
    if requested_status is not None:
        return requested_status
    if matrix.status == "needs_more_data":
        return RevenueOpportunityStatus.needs_more_data
    if requires_ceo_approval:
        return RevenueOpportunityStatus.waiting_ceo_approval
    return RevenueOpportunityStatus.prepared


def list_goals() -> list[RevenueGoal]:
    seed_revenue_defaults()
    return [RevenueGoal(**payload) for payload in fetch_payloads(REVENUE_GOALS_TABLE)]


def create_goal(request: RevenueGoalCreate, actor: AuthenticatedUser) -> RevenueGoal:
    seed_revenue_defaults()
    now = utc_now()
    goal_id = request.id or f"revenue_goal_{safe_id(request.name, str(uuid4()))}"
    existing = fetch_payload(REVENUE_GOALS_TABLE, goal_id)
    goal = RevenueGoal(
        id=goal_id,
        name=request.name,
        monthly_target_usd=request.monthly_target_usd,
        scope=request.scope,
        separated_from_global=request.separated_from_global or request.scope == "ecommerce",
        status=request.status,
        created_at=existing.get("created_at", now) if existing else now,
        updated_at=now,
    )
    upsert_payload(REVENUE_GOALS_TABLE, goal.id, goal.model_dump_json())
    audit_revenue_action(
        actor=actor,
        action="upsert_revenue_goal",
        status=goal.status,
        detail="Revenue OS updated a monthly goal.",
        metadata={"goal_id": goal.id, "scope": goal.scope},
    )
    return goal


def get_global_goal() -> RevenueGoal:
    goals = list_goals()
    return next(goal for goal in goals if goal.scope == "global")


def get_ecommerce_goal() -> RevenueGoal:
    goals = list_goals()
    return next(goal for goal in goals if goal.scope == "ecommerce")


def list_opportunities() -> list[RevenueOpportunity]:
    seed_revenue_defaults()
    return [
        RevenueOpportunity(**payload)
        for payload in fetch_payloads(REVENUE_OPPORTUNITIES_TABLE)
    ]


def get_opportunity(opportunity_id: str) -> RevenueOpportunity:
    payload = fetch_payload(REVENUE_OPPORTUNITIES_TABLE, opportunity_id)
    if payload is None:
        raise RevenueError(404, {"error": "revenue_opportunity_not_found", "opportunity_id": opportunity_id})
    return RevenueOpportunity(**payload)


def create_opportunity(
    request: RevenueOpportunityCreate,
    actor: AuthenticatedUser,
) -> RevenueOpportunity:
    seed_revenue_defaults()
    now = utc_now()
    matrix = build_economic_matrix(
        investment_usd=request.investment_usd,
        expected_revenue_usd=request.expected_revenue_usd,
        expected_net_profit_usd=request.expected_net_profit_usd,
        probability_percent=request.probability_percent,
        risk=request.risk,
        payback_time=request.payback_time,
        ecommerce_separate=request.ecommerce_separate,
        action_type=request.action_type,
        recommendation=request.recommendation,
    )
    requires_ceo = money_requires_approval(request.action_type, request.investment_usd)
    opportunity = RevenueOpportunity(
        id=f"revenue_opportunity_{uuid4()}",
        title=request.title,
        origin=request.origin,
        department=request.department,
        related_product=request.related_product,
        action_type=request.action_type,
        investment_usd=request.investment_usd,
        expected_revenue_usd=request.expected_revenue_usd,
        expected_net_profit_usd=request.expected_net_profit_usd,
        probability_percent=request.probability_percent,
        risk=request.risk,
        payback_time=request.payback_time,
        ecommerce_separate=request.ecommerce_separate,
        contributes_to_global_goal=not request.ecommerce_separate,
        contributes_to_ecommerce_goal=request.ecommerce_separate,
        requires_ceo_approval=requires_ceo,
        status=status_for_opportunity(
            matrix=matrix,
            requires_ceo_approval=requires_ceo,
            requested_status=request.status,
        ),
        economic_matrix=matrix,
        created_by=actor_name(actor),
        created_at=now,
        updated_at=now,
    )
    insert_payload(REVENUE_OPPORTUNITIES_TABLE, opportunity.id, opportunity.model_dump_json())
    audit_revenue_action(
        actor=actor,
        action="create_revenue_opportunity",
        status=opportunity.status.value,
        detail="Revenue OS registered an internal opportunity without real payment execution.",
        metadata={
            "opportunity_id": opportunity.id,
            "department": opportunity.department,
            "requires_ceo_approval": opportunity.requires_ceo_approval,
            "matrix_status": opportunity.economic_matrix.status,
        },
    )
    return opportunity


def evaluate_opportunity(
    opportunity_id: str,
    request: RevenueOpportunityEvaluateRequest,
    actor: AuthenticatedUser,
) -> RevenueOpportunity:
    opportunity = get_opportunity(opportunity_id)
    investment = request.investment_usd if request.investment_usd is not None else opportunity.investment_usd
    expected_revenue = (
        request.expected_revenue_usd
        if request.expected_revenue_usd is not None
        else opportunity.expected_revenue_usd
    )
    expected_net = (
        request.expected_net_profit_usd
        if request.expected_net_profit_usd is not None
        else opportunity.expected_net_profit_usd
    )
    probability = (
        request.probability_percent
        if request.probability_percent is not None
        else opportunity.probability_percent
    )
    risk = request.risk or opportunity.risk
    payback_time = request.payback_time or opportunity.payback_time
    matrix = build_economic_matrix(
        investment_usd=investment,
        expected_revenue_usd=expected_revenue,
        expected_net_profit_usd=expected_net,
        probability_percent=probability,
        risk=risk,
        payback_time=payback_time,
        ecommerce_separate=opportunity.ecommerce_separate,
        action_type=opportunity.action_type,
        recommendation=request.recommendation,
    )
    requires_ceo = money_requires_approval(opportunity.action_type, investment)
    opportunity.investment_usd = investment
    opportunity.expected_revenue_usd = expected_revenue
    opportunity.expected_net_profit_usd = expected_net
    opportunity.probability_percent = probability
    opportunity.risk = risk
    opportunity.payback_time = payback_time
    opportunity.requires_ceo_approval = requires_ceo
    opportunity.economic_matrix = matrix
    opportunity.status = status_for_opportunity(
        matrix=matrix,
        requires_ceo_approval=requires_ceo,
        requested_status=None,
    )
    if opportunity.status == RevenueOpportunityStatus.prepared:
        opportunity.status = RevenueOpportunityStatus.evaluated
    opportunity.updated_at = utc_now()
    update_payload(REVENUE_OPPORTUNITIES_TABLE, opportunity.id, opportunity.model_dump_json())
    audit_revenue_action(
        actor=actor,
        action="evaluate_revenue_opportunity",
        status=opportunity.status.value,
        detail="Revenue OS evaluated an opportunity economic matrix.",
        metadata={"opportunity_id": opportunity.id, "matrix_status": matrix.status},
    )
    return opportunity


def list_approval_requests() -> list[RevenueApprovalRequest]:
    seed_revenue_defaults()
    return [
        RevenueApprovalRequest(**payload)
        for payload in fetch_payloads(REVENUE_APPROVAL_REQUESTS_TABLE)
    ]


def request_approval_for_opportunity(
    opportunity_id: str,
    actor: AuthenticatedUser,
) -> RevenueApprovalRequest:
    opportunity = get_opportunity(opportunity_id)
    if not opportunity.requires_ceo_approval:
        raise RevenueError(
            400,
            {
                "error": "approval_not_required",
                "opportunity_id": opportunity.id,
                "action_type": opportunity.action_type,
            },
        )
    if opportunity.economic_matrix.status == "needs_more_data":
        raise RevenueError(
            400,
            {
                "error": "economic_matrix_needs_more_data",
                "opportunity_id": opportunity.id,
                "required_fields": [
                    "investment_usd",
                    "expected_revenue_usd",
                    "probability_percent",
                    "payback_time",
                    "risk",
                    "recommendation",
                ],
            },
        )

    existing = [
        approval
        for approval in list_approval_requests()
        if approval.opportunity_id == opportunity.id and approval.status == "pending_ceo"
    ]
    if existing:
        return existing[0]

    matrix = opportunity.economic_matrix
    cerebro_approval = create_approval_request(
        CerebroApprovalRequestCreate(
            title=opportunity.title,
            description=(
                "Revenue OS pide aprobacion CEO para dinero real o accion de costo. "
                f"Oportunidad: {opportunity.title}."
            ),
            action_type=opportunity.action_type,
            requested_by_department=opportunity.department,
            investment_required=matrix.investment_usd or 0,
            expected_revenue=matrix.expected_revenue_usd or 0,
            currency=matrix.currency,
            return_time=matrix.payback_time,
            risk=matrix.risk,
            recommendation=matrix.recommendation,
            ecommerce_separate=opportunity.ecommerce_separate,
        ),
        actor,
    )
    now = utc_now()
    approval = RevenueApprovalRequest(
        id=f"revenue_approval_{uuid4()}",
        opportunity_id=opportunity.id,
        title=opportunity.title,
        department=opportunity.department,
        action_type=opportunity.action_type,
        economic_matrix=matrix,
        recommendation=matrix.recommendation,
        cerebro_approval_request_id=cerebro_approval.id,
        created_at=now,
        updated_at=now,
    )
    insert_payload(REVENUE_APPROVAL_REQUESTS_TABLE, approval.id, approval.model_dump_json())
    opportunity.status = RevenueOpportunityStatus.approval_requested
    opportunity.approval_request_id = approval.id
    opportunity.cerebro_approval_request_id = cerebro_approval.id
    opportunity.updated_at = now
    update_payload(REVENUE_OPPORTUNITIES_TABLE, opportunity.id, opportunity.model_dump_json())
    audit_revenue_action(
        actor=actor,
        action="request_revenue_approval",
        status="pending_ceo",
        detail="Revenue OS requested CEO approval through CEREBRO.",
        severity=AuditSeverity.medium,
        metadata={
            "opportunity_id": opportunity.id,
            "approval_request_id": approval.id,
            "cerebro_approval_request_id": cerebro_approval.id,
        },
    )
    return approval


def _estimated_pipeline(opportunities: list[RevenueOpportunity], *, ecommerce: bool) -> float:
    total = 0.0
    for opportunity in opportunities:
        if opportunity.ecommerce_separate is not ecommerce:
            continue
        matrix = opportunity.economic_matrix
        if matrix.status == "needs_more_data":
            continue
        total += max(float(matrix.expected_net_profit_usd or 0), 0)
    return round(total, 2)


def _progress(pipeline: float, goal: float) -> float:
    return round((pipeline / goal) * 100, 2) if goal else 0


def get_revenue_status() -> RevenueStatus:
    seed_revenue_defaults()
    opportunities = list_opportunities()
    approvals = list_approval_requests()
    global_pipeline = _estimated_pipeline(opportunities, ecommerce=False)
    ecommerce_pipeline = _estimated_pipeline(opportunities, ecommerce=True)
    global_goal = get_global_goal()
    ecommerce_goal = get_ecommerce_goal()
    global_goal.estimated_pipeline_usd = global_pipeline
    ecommerce_goal.estimated_pipeline_usd = ecommerce_pipeline
    top = sorted(
        [
            opportunity
            for opportunity in opportunities
            if opportunity.economic_matrix.status != "needs_more_data"
        ],
        key=lambda item: float(item.economic_matrix.expected_net_profit_usd or 0),
        reverse=True,
    )[:6]
    return RevenueStatus(
        status="revenue_os_prepared_internal",
        mode="no_real_payments_no_external_accounts",
        global_goal=global_goal,
        ecommerce_goal=ecommerce_goal,
        actual_revenue_usd=0,
        actual_revenue_status="no_real_revenue_reported",
        estimated_global_pipeline_usd=global_pipeline,
        estimated_ecommerce_pipeline_usd=ecommerce_pipeline,
        global_progress_percent=_progress(global_pipeline, GLOBAL_MONTHLY_GOAL_USD),
        ecommerce_progress_percent=_progress(ecommerce_pipeline, ECOMMERCE_MONTHLY_GOAL_USD),
        opportunities=len(opportunities),
        opportunities_needing_data=len(
            [
                opportunity
                for opportunity in opportunities
                if opportunity.economic_matrix.status == "needs_more_data"
            ]
        ),
        approval_requests=len(approvals),
        top_opportunities=top,
        generated_at=utc_now(),
    )


def get_department_contribution() -> list[RevenueDepartmentContribution]:
    opportunities = list_opportunities()
    approvals = list_approval_requests()
    rows: list[RevenueDepartmentContribution] = []
    for department_id, name, role, contribution_type, target_scope in DEPARTMENT_REVENUE_ROLES:
        aliases = {department_id, normalize(name), normalize(name.replace("/", "_"))}
        related = [
            opportunity
            for opportunity in opportunities
            if normalize(opportunity.department) in aliases
            or normalize(opportunity.related_product) == department_id
        ]
        pipeline = round(
            sum(
                max(float(opportunity.economic_matrix.expected_net_profit_usd or 0), 0)
                for opportunity in related
                if opportunity.economic_matrix.status != "needs_more_data"
            ),
            2,
        )
        approval_count = len(
            [
                approval
                for approval in approvals
                if normalize(approval.department) in aliases
            ]
        )
        rows.append(
            RevenueDepartmentContribution(
                department_id=department_id,
                department_name=name,
                revenue_role=role,
                contribution_type=contribution_type,
                target_scope=target_scope,
                estimated_pipeline_usd=pipeline,
                opportunities=len(related),
                approval_requests=approval_count,
            )
        )
    return rows


def sprint_plan_30_days() -> list[dict]:
    return [
        {
            "week": 1,
            "title": "Auditoria y preparacion",
            "focus": "Validar rutas, evidencia faltante, riesgos y oferta sin vender.",
            "output": "Lista priorizada de rutas y misiones internas.",
        },
        {
            "week": 2,
            "title": "Contenido y validacion organica",
            "focus": "Marketing, PLUMA y LENTE prueban demanda organica sin gasto real.",
            "output": "Senales cualitativas y piezas listas para revision.",
        },
        {
            "week": 3,
            "title": "Embudos, landings y ofertas",
            "focus": "Web Factory prepara landings y ofertas sin checkout ni cobro real.",
            "output": "Flujos de conversion preparados y auditables.",
        },
        {
            "week": 4,
            "title": "Conversion preparada y propuesta de inversion",
            "focus": "Solo si hay senal, CEREBRO prepara solicitud con ROI para CEO.",
            "output": "Decision CEO: mantener organico, invertir o bloquear.",
        },
    ]


def initial_sprint_route_requests() -> list[RevenueSprintRouteCreate]:
    return [
        RevenueSprintRouteCreate(
            name="DCFT vendido por Marketing",
            owner="MARKETING",
            hypothesis="Marketing puede validar demanda de DCFT como primer producto comercial protegido.",
            next_actions=["Definir oferta no productiva.", "Preparar copy organico.", "Pedir evidencia a AUDITORIA."],
            evidence_missing=["pricing final", "estado producto", "validacion CEO", "SUNAT real apagado"],
            risk="DCFT protected_no_touch; no vender como activo real sin cierre CEO.",
            priority="p1",
        ),
        RevenueSprintRouteCreate(
            name="SENTINELA vendido por Marketing",
            owner="MARKETING",
            hypothesis="SENTINELA puede explorarse como futuro B2B de seguridad sin runtime real.",
            next_actions=["Definir ICP B2B.", "Preparar una pagina de valor.", "Auditar claims de seguridad."],
            evidence_missing=["producto B2B cerrado", "runtime real", "pruebas de seguridad"],
            risk="SENTINELA protected/pending_review; no activar ni prometer defensa real.",
            priority="p2",
        ),
        RevenueSprintRouteCreate(
            name="APIs/Skills vendibles",
            owner="CREADOR APIs/SKILLS",
            hypothesis="Capacidades internas pueden convertirse en productos tecnicos vendibles.",
            next_actions=["Listar skills vendibles.", "Priorizar por dolor comercial.", "Pedir landing a WEB FACTORY."],
            evidence_missing=["demanda validada", "precio", "evidencia tecnica"],
            priority="p1",
        ),
        RevenueSprintRouteCreate(
            name="Web Factory / landings",
            owner="WEB FACTORY",
            hypothesis="Landings rapidas pueden convertir ofertas preparadas si hay demanda organica.",
            next_actions=["Preparar plantilla.", "Mapear oferta.", "Conectar solo formularios internos preparados."],
            evidence_missing=["oferta prioritaria", "copy validado", "canal organico"],
            priority="p1",
        ),
        RevenueSprintRouteCreate(
            name="Marca Personal",
            owner="MARCA PERSONAL",
            hypothesis="Autoridad del CEO puede abrir leads, alianzas y demanda organica.",
            next_actions=["Definir narrativa.", "Plan de 10 piezas.", "Medir senales organicas."],
            evidence_missing=["baseline redes", "calendario validado"],
            priority="p1",
        ),
        RevenueSprintRouteCreate(
            name="PLUMA / libros / contenido / autoridad",
            owner="PLUMA",
            hypothesis="Contenido y libros pueden construir autoridad y alimentar ventas organicas.",
            next_actions=["Crear briefing editorial.", "Elegir tema de mayor ROI.", "Revisar con AUDITORIA."],
            evidence_missing=["tema validado", "buyer persona", "prueba organica"],
            priority="p2",
        ),
        RevenueSprintRouteCreate(
            name="LENTE / canales / video / assets",
            owner="LENTE",
            hypothesis="Video y assets pueden aumentar confianza y conversion sin gasto pagado.",
            next_actions=["Diseñar assets basicos.", "Preparar 3 guiones.", "Medir respuesta organica."],
            evidence_missing=["canal activo", "formato validado", "metricas"],
            priority="p2",
        ),
        RevenueSprintRouteCreate(
            name="E-COMMERCE separado",
            owner="E-COMMERCE",
            hypothesis="E-commerce persigue USD 10,000 mensuales separado de la meta global.",
            next_actions=["Separar tablero.", "Validar producto sin compra real.", "Pedir matriz a Revenue OS."],
            evidence_missing=["producto", "margen", "proveedor", "operacion"],
            ecommerce_separate=True,
            priority="p1",
            risk="Meta separada; no comprar inventario ni cobrar.",
        ),
        RevenueSprintRouteCreate(
            name="SNIFF AMAZON",
            owner="SNIFF AMAZON",
            hypothesis="SNIFF AMAZON puede detectar oportunidades para e-commerce sin ejecutar compras.",
            next_actions=["Definir criterio de oportunidad.", "Preparar scoring.", "Escalar a CEREBRO."],
            evidence_missing=["fuentes", "margen", "validacion producto"],
            ecommerce_separate=True,
            priority="p2",
        ),
        RevenueSprintRouteCreate(
            name="Productos digitales derivados de tendencias",
            owner="BUSCADOR DE TENDENCIAS",
            hypothesis="Tendencias pueden convertirse en productos digitales si se valida demanda.",
            next_actions=["Detectar tendencia.", "Crear brief de producto.", "Pedir contenido y landing preparados."],
            evidence_missing=["senal real", "comprador", "precio", "canal"],
            priority="p1",
        ),
    ]


def sprint_route_id(name: str) -> str:
    return f"revenue_sprint_route_{safe_id(name, 'route')}"


def route_requires_approval(request: RevenueSprintRouteCreate) -> bool:
    return money_requires_approval(request.action_type, request.investment_required_usd)


def priority_for_route(request: RevenueSprintRouteCreate) -> str:
    if request.priority:
        return request.priority
    text = f"{request.name} {request.hypothesis} {request.risk}".lower()
    if any(term in text for term in ("dcft", "usd 6,000", "ingreso", "comercial", "e-commerce")):
        return "p1"
    return "p2"


def evidence_status_for_route(request: RevenueSprintRouteCreate) -> RevenueSprintEvidenceStatus:
    if request.evidence_status:
        return request.evidence_status
    if request.evidence_available and request.evidence_missing:
        return RevenueSprintEvidenceStatus.partial
    if request.evidence_available:
        return RevenueSprintEvidenceStatus.available
    return RevenueSprintEvidenceStatus.missing


def build_sprint_route(request: RevenueSprintRouteCreate, *, route_id: str | None = None) -> RevenueSprintRoute:
    now = utc_now()
    approval_required = route_requires_approval(request)
    evidence_status = evidence_status_for_route(request)
    status_value = (
        RevenueSprintRouteStatus.waiting_ceo_approval
        if approval_required
        else RevenueSprintRouteStatus.needs_more_data
        if evidence_status == RevenueSprintEvidenceStatus.missing
        else RevenueSprintRouteStatus.opportunity
    )
    return RevenueSprintRoute(
        id=route_id or sprint_route_id(request.name),
        name=request.name,
        status=status_value,
        owner=request.owner,
        hypothesis=request.hypothesis,
        next_actions=request.next_actions or ["Validar demanda sin dinero real."],
        investment_required_usd=request.investment_required_usd,
        approval_required=approval_required,
        action_type=request.action_type,
        potential_estimated_usd=request.potential_estimated_usd,
        evidence_available=request.evidence_available,
        evidence_missing=request.evidence_missing or ["evidencia comercial", "metricas", "ROI"],
        evidence_status=evidence_status,
        ecommerce_separate=request.ecommerce_separate,
        priority=priority_for_route(request),
        roi_status="not_estimated" if request.potential_estimated_usd is None else "estimated_not_real",
        risk=request.risk,
        created_at=now,
        updated_at=now,
    )


def save_sprint_route(route: RevenueSprintRoute) -> RevenueSprintRoute:
    route.updated_at = utc_now()
    upsert_payload(REVENUE_SPRINT_ROUTES_TABLE, route.id, route.model_dump_json())
    return route


def list_sprint_routes() -> list[RevenueSprintRoute]:
    ensure_sprint_defaults()
    routes = [RevenueSprintRoute(**payload) for payload in fetch_payloads(REVENUE_SPRINT_ROUTES_TABLE)]
    priority_order = {"p0": 0, "p1": 1, "p2": 2, "p3": 3}
    return sorted(routes, key=lambda route: (priority_order.get(route.priority, 9), route.name))


def get_sprint_route(route_id: str) -> RevenueSprintRoute:
    ensure_sprint_defaults()
    payload = fetch_payload(REVENUE_SPRINT_ROUTES_TABLE, route_id)
    if payload is None:
        raise RevenueError(404, {"error": "revenue_sprint_route_not_found", "route_id": route_id})
    return RevenueSprintRoute(**payload)


def save_sprint_state(status_value: RevenueSprintStatusValue, actor: AuthenticatedUser | None = None) -> None:
    now = utc_now()
    payload = {
        "id": "revenue_sprint_30_day",
        "status": status_value.value,
        "global_goal_usd": GLOBAL_MONTHLY_GOAL_USD,
        "ecommerce_goal_usd": ECOMMERCE_MONTHLY_GOAL_USD,
        "actor": actor_name(actor) if actor else "system",
        "actual_revenue_usd": 0,
        "actual_revenue_status": "no_real_revenue_reported",
        "updated_at": now,
        "created_at": now,
    }
    upsert_payload(REVENUE_SPRINT_STATE_TABLE, payload["id"], json.dumps(payload, ensure_ascii=False))


def get_sprint_state() -> dict:
    ensure_revenue_schema()
    payload = fetch_payload(REVENUE_SPRINT_STATE_TABLE, "revenue_sprint_30_day")
    if payload is None:
        save_sprint_state(RevenueSprintStatusValue.prepared)
        payload = fetch_payload(REVENUE_SPRINT_STATE_TABLE, "revenue_sprint_30_day") or {}
    return payload


def ensure_sprint_defaults(actor: AuthenticatedUser | None = None) -> None:
    seed_revenue_defaults()
    get_sprint_state()
    if fetch_payloads(REVENUE_SPRINT_ROUTES_TABLE):
        return
    for request in initial_sprint_route_requests():
        route = build_sprint_route(request)
        upsert_payload(REVENUE_SPRINT_ROUTES_TABLE, route.id, route.model_dump_json())
    audit_revenue_action(
        actor=actor,
        action="seed_revenue_sprint_routes",
        status="prepared",
        detail="Revenue Sprint configured initial opportunities without real sales.",
        metadata={"routes": len(initial_sprint_route_requests()), "actual_revenue_usd": 0},
    )


def create_sprint_route(request: RevenueSprintRouteCreate, actor: AuthenticatedUser) -> RevenueSprintRoute:
    ensure_sprint_defaults(actor)
    route = build_sprint_route(request, route_id=f"{sprint_route_id(request.name)}_{uuid4().hex[:8]}")
    save_sprint_route(route)
    audit_revenue_action(
        actor=actor,
        action="create_revenue_sprint_route",
        status=route.status.value,
        detail="Revenue Sprint registered a route as opportunity, not real sale.",
        metadata={
            "route_id": route.id,
            "approval_required": route.approval_required,
            "ecommerce_separate": route.ecommerce_separate,
            "real_revenue_confirmed": False,
        },
    )
    return route


def list_sprint_missions() -> list[RevenueSprintMission]:
    ensure_sprint_defaults()
    return [RevenueSprintMission(**payload) for payload in fetch_payloads(REVENUE_SPRINT_MISSIONS_TABLE)]


def save_sprint_mission(mission: RevenueSprintMission) -> RevenueSprintMission:
    mission.updated_at = utc_now()
    upsert_payload(REVENUE_SPRINT_MISSIONS_TABLE, mission.id, mission.model_dump_json())
    return mission


def create_revenue_sprint_mission(
    request: RevenueSprintMissionCreate,
    actor: AuthenticatedUser,
) -> RevenueSprintMission:
    from app.schemas.missions import MissionLoopCreate
    from app.services.missions import create_loop_mission

    route = get_sprint_route(request.route_id)
    departments = request.departments or [route.owner, "MARKETING", "AUDITORIA"]
    if route.ecommerce_separate and "E-COMMERCE" not in departments:
        departments.append("E-COMMERCE")
    title = request.title or f"Sprint ingresos: {route.name}"
    mission = create_loop_mission(
        MissionLoopCreate(
            title=title,
            ceo_instruction=(
                f"CEREBRO convierte la ruta '{route.name}' en mision de validacion. "
                "No cobrar, no pagar, no lanzar campana pagada real."
            ),
            source="revenue_execution_sprint",
            leader_department="CEREBRO",
            involved_departments=departments,
            priority=route.priority,
            action_type=request.action_type,
            expected_business_impact=(
                "Ruta global hacia USD 6,000 mensual."
                if not route.ecommerce_separate
                else "Ruta e-commerce separada hacia USD 10,000 mensual."
            ),
            revenue_goal_link="global_6000_usd" if not route.ecommerce_separate else None,
            ecommerce_goal_link="ecommerce_10000_usd" if route.ecommerce_separate else None,
            requires_money=route.investment_required_usd > 0,
            requires_ceo_approval=route.approval_required,
            approval_reason=(
                "money_or_paid_campaign_requires_ceo"
                if route.approval_required
                else "organic_validation_no_money"
            ),
            investment_required=route.investment_required_usd,
            ecommerce_separate=route.ecommerce_separate,
            risk=route.risk,
        ),
        actor,
    )
    now = utc_now()
    sprint_mission = RevenueSprintMission(
        id=f"revenue_sprint_mission_{uuid4()}",
        route_id=route.id,
        mission_id=mission.id,
        title=mission.title,
        owner=route.owner,
        departments=departments,
        status=mission.status.value if hasattr(mission.status, "value") else str(mission.status),
        approval_required=route.approval_required,
        ecommerce_separate=route.ecommerce_separate,
        expected_output=request.expected_output,
        created_at=now,
        updated_at=now,
    )
    route.status = (
        RevenueSprintRouteStatus.waiting_ceo_approval
        if route.approval_required
        else RevenueSprintRouteStatus.mission_created
    )
    save_sprint_route(route)
    save_sprint_mission(sprint_mission)
    audit_revenue_action(
        actor=actor,
        action="create_revenue_sprint_mission",
        status=sprint_mission.status,
        detail="CEREBRO created a local revenue sprint mission without real payment execution.",
        metadata={"route_id": route.id, "mission_id": mission.id},
    )
    return sprint_mission


def start_revenue_sprint(actor: AuthenticatedUser) -> RevenueSprintStatus:
    ensure_sprint_defaults(actor)
    save_sprint_state(RevenueSprintStatusValue.running, actor)
    existing_route_ids = {mission.route_id for mission in list_sprint_missions()}
    for route in list_sprint_routes():
        if route.id in existing_route_ids:
            continue
        if route.priority == "p1" and not route.approval_required:
            create_revenue_sprint_mission(
                RevenueSprintMissionCreate(route_id=route.id, expected_output="Validacion organica sin venta real."),
                actor,
            )
            existing_route_ids.add(route.id)
        if len(existing_route_ids) >= 3:
            break
    return get_revenue_sprint_status()


def get_revenue_sprint_status() -> RevenueSprintStatus:
    ensure_sprint_defaults()
    state = get_sprint_state()
    routes = list_sprint_routes()
    missions = list_sprint_missions()
    approval_needed = [route for route in routes if route.approval_required]
    missing = [route for route in routes if route.evidence_status == RevenueSprintEvidenceStatus.missing]
    prioritized = [route for route in routes if route.priority in {"p0", "p1"}]
    ecommerce_routes = [route for route in routes if route.ecommerce_separate]
    return RevenueSprintStatus(
        status="revenue_execution_sprint_prepared_internal",
        sprint_status=RevenueSprintStatusValue(state.get("status") or RevenueSprintStatusValue.prepared.value),
        global_goal_usd=GLOBAL_MONTHLY_GOAL_USD,
        ecommerce_goal_usd=ECOMMERCE_MONTHLY_GOAL_USD,
        actual_revenue_usd=0,
        actual_revenue_status="no_real_revenue_reported",
        routes=len(routes),
        prioritized_routes=len(prioritized),
        missions=len(missions),
        approval_needed=len(approval_needed),
        missing_evidence=len(missing),
        ecommerce_routes=len(ecommerce_routes),
        paid_campaigns_launched=0,
        top_routes=routes[:6],
        plan_30_days=sprint_plan_30_days(),
        next_action=(
            "CEREBRO debe convertir rutas p1 en misiones organicas y pedir aprobacion solo si hay inversion."
        ),
        external_connection_enabled=False,
        runtime_connected=False,
        payment_connected=False,
        generated_at=utc_now(),
    )


def get_revenue_sprint_daily() -> RevenueSprintDaily:
    status = get_revenue_sprint_status()
    top = status.top_routes[:3]
    return RevenueSprintDaily(
        status="revenue_sprint_daily_prepared",
        day=1,
        headline="Sprint 30 dias: validar ingresos sin inventar ventas",
        plan_30_days=status.plan_30_days,
        today_focus=[
            f"{route.owner}: {route.next_actions[0] if route.next_actions else 'validar demanda'}"
            for route in top
        ],
        daily_tracking=[
            "ingresos reales: 0",
            "campanas pagadas reales: 0",
            "rutas e-commerce separadas",
            "aprobacion CEO solo si hay inversion",
        ],
        generated_at=utc_now(),
    )


def get_revenue_sprint_risks() -> list[dict]:
    routes = list_sprint_routes()
    risks = [
        {
            "id": f"risk:{route.id}",
            "route_id": route.id,
            "title": route.name,
            "risk": route.risk,
            "status": route.status.value,
        }
        for route in routes
        if route.risk and route.risk != "controlled"
    ]
    risks.extend(
        [
            {
                "id": "risk:no_fake_sales",
                "title": "No inventar ventas",
                "risk": "actual_revenue_usd debe permanecer 0 hasta evidencia real autorizada.",
                "status": "guardrail",
            },
            {
                "id": "risk:no_paid_campaign",
                "title": "No lanzar campana pagada real",
                "risk": "Toda inversion requiere aprobacion CEO y ROI.",
                "status": "guardrail",
            },
        ]
    )
    return risks


def get_revenue_sprint_approval_needed() -> list[RevenueSprintRoute]:
    return [route for route in list_sprint_routes() if route.approval_required]


def create_revenue_sprint_report(
    request: RevenueSprintReportCreate,
    actor: AuthenticatedUser,
) -> RevenueSprintReport:
    now = utc_now()
    report = RevenueSprintReport(
        id=f"revenue_sprint_report_{uuid4()}",
        summary=request.summary,
        risks=request.risks,
        next_actions=request.next_actions,
        actual_revenue_usd=0,
        real_revenue_confirmed=False,
        created_at=now,
    )
    upsert_payload(REVENUE_SPRINT_REPORTS_TABLE, report.id, report.model_dump_json())
    save_sprint_state(RevenueSprintStatusValue.reported, actor)
    audit_revenue_action(
        actor=actor,
        action="create_revenue_sprint_report",
        status="reported",
        detail="Revenue Sprint report created without real revenue claims.",
        metadata={"report_id": report.id, "actual_revenue_usd": 0},
    )
    return report


def get_daily_report() -> RevenueDailyReport:
    status = get_revenue_status()
    recommendations = [
        "CEREBRO debe priorizar oportunidades con utilidad neta clara y bajo riesgo.",
        "Si hay dinero real, pedir aprobacion CEO antes de ejecutar.",
        "Separar e-commerce de la meta global; no mezclar pipeline.",
    ]
    if status.opportunities_needing_data:
        recommendations.insert(0, "Completar matriz economica de oportunidades sin ROI calculable.")
    if status.approval_requests:
        recommendations.insert(0, "CEO, hay solicitudes de dinero esperando decision.")
    return RevenueDailyReport(
        status="revenue_daily_report_prepared",
        headline="Revenue OS: avance economico preparado",
        summary=(
            f"Pipeline global estimado USD {status.estimated_global_pipeline_usd}; "
            f"pipeline e-commerce estimado USD {status.estimated_ecommerce_pipeline_usd}. "
            "Ingresos reales no reportados."
        ),
        global_goal_usd=GLOBAL_MONTHLY_GOAL_USD,
        ecommerce_goal_usd=ECOMMERCE_MONTHLY_GOAL_USD,
        global_pipeline_usd=status.estimated_global_pipeline_usd,
        ecommerce_pipeline_usd=status.estimated_ecommerce_pipeline_usd,
        approvals_pending=status.approval_requests,
        opportunities_needing_data=status.opportunities_needing_data,
        recommended_actions=recommendations,
        risks=[
            "No inventar ingresos reales.",
            "No ejecutar campanas pagadas sin aprobacion CEO.",
            "No conectar pasarelas de pago ni cuentas externas desde este bloque.",
        ],
        generated_at=utc_now(),
    )
