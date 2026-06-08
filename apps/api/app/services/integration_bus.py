from datetime import UTC, datetime
from functools import lru_cache
import json
from pathlib import Path
from typing import Any
from uuid import uuid4

from app.core.database import connect, initialize_database, sql_placeholder
from app.schemas.events import EventCreate
from app.schemas.integration_bus import (
    IntegrationBusAuditEvent,
    IntegrationBusDependency,
    IntegrationBusOverview,
    IntegrationBusPreparedRoute,
    IntegrationBusRoute,
    IntegrationBusRouteCreate,
    IntegrationBusRouteStateUpdate,
    IntegrationBusService,
    IntegrationBusStatus,
    IntegrationDispatchRequest,
    IntegrationDispatchResult,
)
from app.services.events import get_event_catalog_item, publish_event
from app.services.integrations import list_integration_contracts

DATA_PATH = Path(__file__).resolve().parents[1] / "data"
BUS_SERVICES_PATH = DATA_PATH / "integration_bus_services.json"
PREPARED_ROUTES_PATH = DATA_PATH / "integration_bus_prepared_routes.json"
BUS_ROUTES_TABLE = "integration_bus_routes"
BUS_AUDIT_TABLE = "integration_bus_audit_events"
BUS_INTERNAL_DISPATCH_TABLE = "integration_bus_internal_dispatches"
INTERNAL_ROUTE_CREATED_AT = "2026-06-08T00:00:00Z"
ALLOWED_ROUTE_STATUSES = {"created", "queued", "dispatched", "prepared", "completed", "blocked", "rejected"}

INTERNAL_BLOCKED_TARGETS: dict[str, dict[str, str]] = {
    "doctor_contable_financiero_tributario": {
        "status": "blocked",
        "error": "dcft_protected_no_touch",
        "reason": "DCFT protected_no_touch: no SUNAT real, no credentials and no runtime connection.",
    },
    "centinela": {
        "status": "blocked",
        "error": "sentinela_pending_review_protected",
        "reason": "SENTINELA pending_review/protected: no productive security runtime is connected.",
    },
    "arsenal": {
        "status": "blocked",
        "error": "arsenal_planned_pending_integration",
        "reason": "ARSENAL planned/pending_integration: no runtime, secrets or real APIs are connected.",
    },
}

INTERNAL_HANDLERS: dict[str, dict[str, str]] = {
    "forja": {
        "action_type": "construction_brief",
        "result": "task_prepared",
        "detail": "FORJA internal route received a construction brief; no external code was executed.",
    },
    "hermes": {
        "action_type": "automation_or_notification",
        "result": "automation_prepared",
        "detail": "HERMES internal route prepared controlled automation/notification support.",
    },
    "creador_de_apis_y_skills": {
        "action_type": "api_skill_idea",
        "result": "api_skill_spec_prepared",
        "detail": "CREADOR DE APIS Y SKILLS prepared a local API/skill specification.",
    },
    "web_factory": {
        "action_type": "web_brief",
        "result": "landing_brief_prepared",
        "detail": "WEB FACTORY prepared a local landing/web brief; no deploy was executed.",
    },
    "buscador_de_tendencias": {
        "action_type": "research_request",
        "result": "research_request_prepared",
        "detail": "BUSCADOR DE TENDENCIAS prepared a local research request without scraping.",
    },
    "pluma": {
        "action_type": "content_request",
        "result": "draft_request_prepared",
        "detail": "PLUMA prepared a draft/content request; no external publishing occurred.",
    },
    "lente": {
        "action_type": "visual_request",
        "result": "visual_brief_prepared",
        "detail": "LENTE prepared a visual/video brief; no external video API was called.",
    },
    "marketing": {
        "action_type": "campaign_request",
        "result": "campaign_brief_prepared",
        "detail": "MARKETING prepared a local campaign/funnel brief; no ads were published.",
    },
    "marca_personal": {
        "action_type": "personal_brand_request",
        "result": "personal_brand_brief_prepared",
        "detail": "MARCA PERSONAL prepared CEO content; no LinkedIn/X publication occurred.",
    },
    "auditor": {
        "action_type": "audit_review",
        "result": "audit_review_created",
        "detail": "AUDITORIA created an internal review record for the requested task.",
    },
    "nube": {
        "action_type": "cloud_review",
        "result": "cloud_review_prepared",
        "detail": "NUBE profile prepared a cloud review; C:\\Users\\admin\\nube was not touched.",
    },
    "sniff_amazon": {
        "action_type": "amazon_opportunity_review",
        "result": "amazon_opportunity_review_prepared",
        "detail": "SNIFF AMAZON prepared an opportunity review; Amazon was not contacted.",
    },
    "comercio_autonomo": {
        "action_type": "commerce_plan",
        "result": "commerce_plan_prepared",
        "detail": "COMERCIO AUTONOMO prepared a commerce plan; no store, purchase or sale was executed.",
    },
}

INTERNAL_EVENT_TYPES: dict[str, str] = {
    "forja": "platform.forja.discovery.completed",
    "hermes": "platform.hermes.discovery.completed",
    "creador_de_apis_y_skills": "platform.creador_de_apis_y_skills.discovery.completed",
    "web_factory": "platform.web_factory.discovery.completed",
    "buscador_de_tendencias": "platform.buscador_de_tendencias.discovery.completed",
    "pluma": "platform.pluma.discovery.completed",
    "lente": "platform.lente.discovery.completed",
    "marketing": "platform.marketing.discovery.completed",
    "marca_personal": "platform.marca_personal.discovery.completed",
    "auditor": "platform.auditor.discovery.completed",
    "nube": "platform.nube.discovery.completed",
    "sniff_amazon": "platform.sniff_amazon.discovery.completed",
    "comercio_autonomo": "platform.comercio_autonomo.discovery.completed",
    "doctor_contable_financiero_tributario": "platform.control_center.read",
    "centinela": "platform.control_center.read",
    "arsenal": "platform.control_center.read",
}


class IntegrationBusValidationError(RuntimeError):
    def __init__(self, detail: dict[str, object], status_code: int = 400) -> None:
        self.detail = detail
        self.status_code = status_code
        super().__init__(str(detail))


def utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def row_value(row: Any, key: str) -> Any:
    return row[key]


@lru_cache
def list_bus_services() -> tuple[IntegrationBusService, ...]:
    raw_services = json.loads(BUS_SERVICES_PATH.read_text(encoding="utf-8"))
    return tuple(IntegrationBusService(**item) for item in raw_services)


@lru_cache
def list_prepared_routes() -> tuple[IntegrationBusPreparedRoute, ...]:
    raw_routes = json.loads(PREPARED_ROUTES_PATH.read_text(encoding="utf-8"))
    return tuple(IntegrationBusPreparedRoute(**item) for item in raw_routes)


def get_bus_service(service_id: str) -> IntegrationBusService | None:
    normalized_service = service_id.strip().lower()
    return next(
        (service for service in list_bus_services() if service.id == normalized_service),
        None,
    )


def ensure_integration_bus_schema() -> None:
    initialize_database()

    with connect() as connection:
        connection.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {BUS_ROUTES_TABLE} (
                id TEXT PRIMARY KEY,
                source_service TEXT NOT NULL,
                target_service TEXT NOT NULL,
                event_type TEXT NOT NULL,
                channel TEXT NOT NULL,
                status TEXT NOT NULL,
                retry_policy TEXT NOT NULL,
                dead_letter_enabled INTEGER NOT NULL,
                external_connection_enabled INTEGER NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        connection.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {BUS_AUDIT_TABLE} (
                id TEXT PRIMARY KEY,
                action TEXT NOT NULL,
                status TEXT NOT NULL,
                detail TEXT NOT NULL,
                route_id TEXT,
                event_id TEXT,
                created_at TEXT NOT NULL
            )
            """
        )
        connection.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {BUS_INTERNAL_DISPATCH_TABLE} (
                id TEXT PRIMARY KEY,
                route_id TEXT NOT NULL,
                source_service TEXT NOT NULL,
                target_service TEXT NOT NULL,
                action_type TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                status TEXT NOT NULL,
                allowed INTEGER NOT NULL,
                requires_ceo_approval INTEGER NOT NULL,
                external_connection_enabled INTEGER NOT NULL,
                runtime_connected INTEGER NOT NULL,
                audit_event_id TEXT,
                event_id TEXT,
                handler_result_json TEXT NOT NULL,
                blocked_reason TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        connection.commit()


def row_to_route(row: Any) -> IntegrationBusRoute:
    source_service = row_value(row, "source_service")
    target_service = row_value(row, "target_service")
    event_type = row_value(row, "event_type")
    return IntegrationBusRoute(
        id=row_value(row, "id"),
        route_id=row_value(row, "id"),
        source=source_service,
        target=target_service,
        action_type=event_type,
        payload={},
        source_service=source_service,
        target_service=target_service,
        event_type=event_type,
        channel=row_value(row, "channel"),
        status=row_value(row, "status"),
        allowed=True,
        requires_ceo_approval=False,
        retry_policy=row_value(row, "retry_policy"),
        dead_letter_enabled=bool(row_value(row, "dead_letter_enabled")),
        external_connection_enabled=bool(row_value(row, "external_connection_enabled")),
        runtime_connected=False,
        audit_event_id=None,
        handler_result={},
        blocked_reason=None,
        created_at=row_value(row, "created_at"),
        updated_at=row_value(row, "created_at"),
    )


def insert_bus_audit(
    connection: Any,
    action: str,
    status: str,
    detail: str,
    placeholder: str,
    route_id: str | None = None,
    event_id: str | None = None,
) -> IntegrationBusAuditEvent:
    audit = IntegrationBusAuditEvent(
        id=str(uuid4()),
        action=action,
        status=status,
        detail=detail,
        route_id=route_id,
        event_id=event_id,
        created_at=utc_now(),
    )
    connection.execute(
        f"""
        INSERT INTO {BUS_AUDIT_TABLE}
            (id, action, status, detail, route_id, event_id, created_at)
        VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder})
        """,
        (
            audit.id,
            audit.action,
            audit.status,
            audit.detail,
            audit.route_id,
            audit.event_id,
            audit.created_at,
        ),
    )
    return audit


def normalize_service_id(value: str) -> str:
    normalized = str(value or "").strip().lower().replace("-", "_").replace(" ", "_")
    aliases = {
        "auditoria": "auditor",
        "auditoría": "auditor",
        "sentinela": "centinela",
        "dcft": "doctor_contable_financiero_tributario",
        "doctor_contable": "doctor_contable_financiero_tributario",
        "creador_apis_skills": "creador_de_apis_y_skills",
        "creador_de_apis": "creador_de_apis_y_skills",
        "nube_documental": "nube",
        "amazon": "sniff_amazon",
    }
    return aliases.get(normalized, normalized)


def route_definition_for_id(route_id: str) -> IntegrationBusPreparedRoute | None:
    normalized_route = str(route_id or "").strip().lower()
    return next(
        (route for route in list_prepared_routes() if route.id == normalized_route),
        None,
    )


def route_id_for_cerebro_target(target: str) -> str | None:
    normalized_target = normalize_service_id(target)
    return next(
        (
            route.id
            for route in list_prepared_routes()
            if route.source == "cerebro" and normalize_service_id(route.target) == normalized_target
        ),
        None,
    )


def is_internal_route(route_id: str) -> bool:
    return route_definition_for_id(route_id) is not None


def internal_route_event_type(target: str) -> str:
    return INTERNAL_EVENT_TYPES.get(normalize_service_id(target), "platform.control_center.read")


def internal_route_action_type(target: str, requested_action: str | None = None) -> str:
    if requested_action:
        return requested_action.strip().lower()
    return INTERNAL_HANDLERS.get(normalize_service_id(target), {}).get("action_type", "internal_request")


def latest_internal_dispatch(route_id: str) -> dict[str, Any] | None:
    ensure_integration_bus_schema()
    placeholder = sql_placeholder()
    with connect() as connection:
        row = connection.execute(
            f"""
            SELECT *
            FROM {BUS_INTERNAL_DISPATCH_TABLE}
            WHERE route_id = {placeholder}
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (route_id,),
        ).fetchone()
    return dict(row) if row else None


def prepared_route_to_route(
    prepared_route: IntegrationBusPreparedRoute,
    latest: dict[str, Any] | None = None,
) -> IntegrationBusRoute:
    target = normalize_service_id(prepared_route.target)
    blocked = target in INTERNAL_BLOCKED_TARGETS
    status = "blocked" if blocked else "prepared"
    audit_event_id = None
    payload: dict[str, Any] = {}
    handler_result: dict[str, Any] = {}
    created_at = INTERNAL_ROUTE_CREATED_AT
    updated_at = INTERNAL_ROUTE_CREATED_AT
    if latest:
        status = latest["status"]
        audit_event_id = latest.get("audit_event_id")
        payload = json.loads(latest["payload_json"])
        handler_result = json.loads(latest["handler_result_json"])
        created_at = latest["created_at"]
        updated_at = latest["updated_at"]

    return IntegrationBusRoute(
        id=prepared_route.id,
        route_id=prepared_route.id,
        source=prepared_route.source,
        target=target,
        action_type=internal_route_action_type(target),
        payload=payload,
        source_service=prepared_route.source,
        target_service=target,
        event_type=internal_route_event_type(target),
        channel="internal",
        status=status,
        allowed=not blocked,
        requires_ceo_approval=blocked,
        retry_policy="standard",
        dead_letter_enabled=True,
        external_connection_enabled=False,
        runtime_connected=False,
        audit_event_id=audit_event_id,
        handler_result=handler_result,
        blocked_reason=(
            INTERNAL_BLOCKED_TARGETS[target]["reason"]
            if blocked
            else "Internal route active inside ecosystem-foundation only."
        ),
        created_at=created_at,
        updated_at=updated_at,
    )


def list_internal_routes() -> list[IntegrationBusRoute]:
    return [
        prepared_route_to_route(route, latest_internal_dispatch(route.id))
        for route in list_prepared_routes()
    ]


def internal_handler_result(target: str, request: IntegrationDispatchRequest) -> dict[str, Any]:
    normalized_target = normalize_service_id(target)
    handler = INTERNAL_HANDLERS[normalized_target]
    return {
        "handler": normalized_target,
        "result": handler["result"],
        "detail": handler["detail"],
        "action_type": internal_route_action_type(normalized_target, request.action_type),
        "external_connection_enabled": False,
        "runtime_connected": False,
        "local_agent_enabled": False,
        "sunat_enabled": False,
        "payload_received": bool(request.payload),
    }


def insert_internal_dispatch(
    connection: Any,
    *,
    route_id: str,
    source_service: str,
    target_service: str,
    action_type: str,
    payload: dict[str, Any],
    status: str,
    allowed: bool,
    requires_ceo_approval: bool,
    audit_event_id: str | None,
    event_id: str | None,
    handler_result: dict[str, Any],
    blocked_reason: str | None,
    placeholder: str,
) -> str:
    dispatch_id = str(uuid4())
    now = utc_now()
    connection.execute(
        f"""
        INSERT INTO {BUS_INTERNAL_DISPATCH_TABLE} (
            id, route_id, source_service, target_service, action_type,
            payload_json, status, allowed, requires_ceo_approval,
            external_connection_enabled, runtime_connected, audit_event_id,
            event_id, handler_result_json, blocked_reason, created_at, updated_at
        )
        VALUES (
            {placeholder}, {placeholder}, {placeholder}, {placeholder},
            {placeholder}, {placeholder}, {placeholder}, {placeholder},
            {placeholder}, {placeholder}, {placeholder}, {placeholder},
            {placeholder}, {placeholder}, {placeholder}, {placeholder},
            {placeholder}
        )
        """,
        (
            dispatch_id,
            route_id,
            source_service,
            target_service,
            action_type,
            json.dumps(payload, sort_keys=True),
            status,
            1 if allowed else 0,
            1 if requires_ceo_approval else 0,
            0,
            0,
            audit_event_id,
            event_id,
            json.dumps(handler_result, sort_keys=True),
            blocked_reason,
            now,
            now,
        ),
    )
    return dispatch_id


def validate_route(route: IntegrationBusRouteCreate) -> None:
    source = get_bus_service(route.source_service)
    target = get_bus_service(route.target_service)

    if source is None:
        raise IntegrationBusValidationError(
            {
                "error": "source_service_not_found",
                "source_service": route.source_service,
            }
        )
    if target is None:
        raise IntegrationBusValidationError(
            {
                "error": "target_service_not_found",
                "target_service": route.target_service,
            }
        )
    if source.external_connection_enabled or target.external_connection_enabled:
        raise IntegrationBusValidationError(
            {
                "error": "external_service_not_allowed",
                "source_service": route.source_service,
                "target_service": route.target_service,
            }
        )
    if get_event_catalog_item(route.event_type) is None:
        raise IntegrationBusValidationError(
            {
                "error": "event_type_not_registered",
                "event_type": route.event_type,
            }
        )


def create_route(route: IntegrationBusRouteCreate) -> IntegrationBusRoute:
    ensure_integration_bus_schema()
    validate_route(route)
    placeholder = sql_placeholder()
    bus_route = IntegrationBusRoute(
        id=str(uuid4()),
        source_service=route.source_service.strip().lower(),
        target_service=route.target_service.strip().lower(),
        event_type=route.event_type.strip(),
        channel=route.channel.strip().lower(),
        status="active",
        retry_policy=route.retry_policy.strip().lower(),
        dead_letter_enabled=route.dead_letter_enabled,
        external_connection_enabled=False,
        created_at=utc_now(),
    )

    with connect() as connection:
        connection.execute(
            f"""
            INSERT INTO {BUS_ROUTES_TABLE} (
                id, source_service, target_service, event_type, channel, status,
                retry_policy, dead_letter_enabled, external_connection_enabled, created_at
            )
            VALUES (
                {placeholder}, {placeholder}, {placeholder}, {placeholder},
                {placeholder}, {placeholder}, {placeholder}, {placeholder},
                {placeholder}, {placeholder}
            )
            """,
            (
                bus_route.id,
                bus_route.source_service,
                bus_route.target_service,
                bus_route.event_type,
                bus_route.channel,
                bus_route.status,
                bus_route.retry_policy,
                1 if bus_route.dead_letter_enabled else 0,
                0,
                bus_route.created_at,
            ),
        )
        insert_bus_audit(
            connection,
            action="route_registered",
            status="success",
            detail="Internal route registered without external connections.",
            route_id=bus_route.id,
            event_id=None,
            placeholder=placeholder,
        )
        connection.commit()

    return bus_route


def list_routes() -> list[IntegrationBusRoute]:
    ensure_integration_bus_schema()

    with connect() as connection:
        rows = connection.execute(
            f"""
            SELECT
                id, source_service, target_service, event_type, channel, status,
                retry_policy, dead_letter_enabled, external_connection_enabled, created_at
            FROM {BUS_ROUTES_TABLE}
            ORDER BY created_at DESC
            """
        ).fetchall()

    return [*list_internal_routes(), *[row_to_route(row) for row in rows]]


def get_route(route_id: str) -> IntegrationBusRoute | None:
    ensure_integration_bus_schema()
    internal_route = route_definition_for_id(route_id)
    if internal_route is not None:
        return prepared_route_to_route(internal_route, latest_internal_dispatch(internal_route.id))

    placeholder = sql_placeholder()

    with connect() as connection:
        row = connection.execute(
            f"""
            SELECT
                id, source_service, target_service, event_type, channel, status,
                retry_policy, dead_letter_enabled, external_connection_enabled, created_at
            FROM {BUS_ROUTES_TABLE}
            WHERE id = {placeholder}
            """,
            (route_id,),
        ).fetchone()

    return row_to_route(row) if row else None


def dispatch_internal_message(
    prepared_route: IntegrationBusPreparedRoute,
    request: IntegrationDispatchRequest,
) -> IntegrationDispatchResult:
    ensure_integration_bus_schema()
    placeholder = sql_placeholder()
    target = normalize_service_id(prepared_route.target)
    source = normalize_service_id(prepared_route.source)
    action_type = internal_route_action_type(target, request.action_type)

    if target in INTERNAL_BLOCKED_TARGETS:
        blocked_detail = INTERNAL_BLOCKED_TARGETS[target]
        with connect() as connection:
            audit = insert_bus_audit(
                connection,
                action="internal_dispatch_blocked",
                status="blocked",
                detail=blocked_detail["reason"],
                route_id=prepared_route.id,
                event_id=None,
                placeholder=placeholder,
            )
            insert_internal_dispatch(
                connection,
                route_id=prepared_route.id,
                source_service=source,
                target_service=target,
                action_type=action_type,
                payload=request.payload,
                status="blocked",
                allowed=False,
                requires_ceo_approval=True,
                audit_event_id=audit.id,
                event_id=None,
                handler_result={
                    "handler": target,
                    "result": "blocked",
                    "reason": blocked_detail["reason"],
                    "external_connection_enabled": False,
                    "runtime_connected": False,
                },
                blocked_reason=blocked_detail["reason"],
                placeholder=placeholder,
            )
            connection.commit()

        raise IntegrationBusValidationError(
            {
                "error": "internal_route_blocked",
                "route_id": prepared_route.id,
                "target": target,
                "reason": blocked_detail["error"],
                "detail": blocked_detail["reason"],
                "external_connection_enabled": False,
                "runtime_connected": False,
            },
            status_code=403,
        )

    handler_result = internal_handler_result(target, request)
    event = publish_event(
        EventCreate(
            type=internal_route_event_type(target),
            source=source,
            subject=request.subject,
            payload={
                "app_id": target,
                "status": handler_result["result"],
                "evidence_count": 1,
                "request_payload": request.payload,
            },
            metadata={
                **request.metadata,
                "integration_route_id": prepared_route.id,
                "target_service": target,
                "action_type": action_type,
                "external_connection_enabled": False,
                "runtime_connected": False,
                "internal_route": True,
            },
            route_to_dead_letter=False,
        )
    )

    with connect() as connection:
        audit = insert_bus_audit(
            connection,
            action="internal_dispatch",
            status="completed",
            detail=handler_result["detail"],
            route_id=prepared_route.id,
            event_id=event.id,
            placeholder=placeholder,
        )
        dispatch_id = insert_internal_dispatch(
            connection,
            route_id=prepared_route.id,
            source_service=source,
            target_service=target,
            action_type=action_type,
            payload=request.payload,
            status="completed",
            allowed=True,
            requires_ceo_approval=False,
            audit_event_id=audit.id,
            event_id=event.id,
            handler_result=handler_result,
            blocked_reason=None,
            placeholder=placeholder,
        )
        connection.commit()

    return IntegrationDispatchResult(
        id=dispatch_id,
        route_id=prepared_route.id,
        status="completed",
        event_id=event.id,
        target_service=target,
        action_type=action_type,
        allowed=True,
        blocked=False,
        blocked_reason=None,
        handler_result=handler_result,
        dead_letter_routed=False,
        audit_event_id=audit.id,
        external_connection_enabled=False,
        runtime_connected=False,
        created_at=utc_now(),
    )


def dispatch_message(
    request: IntegrationDispatchRequest,
) -> IntegrationDispatchResult | None:
    prepared_route = route_definition_for_id(request.route_id)
    if prepared_route is not None:
        return dispatch_internal_message(prepared_route, request)

    route = get_route(request.route_id)
    if route is None:
        return None

    ensure_integration_bus_schema()
    placeholder = sql_placeholder()
    event = publish_event(
        EventCreate(
            type=route.event_type,
            source=route.source_service,
            subject=request.subject,
            payload=request.payload,
            metadata={
                **request.metadata,
                "integration_route_id": route.id,
                "target_service": route.target_service,
            },
            route_to_dead_letter=request.route_to_dead_letter,
        )
    )
    status = "dead_letter_routed" if request.route_to_dead_letter else "dispatched"

    with connect() as connection:
        audit = insert_bus_audit(
            connection,
            action="dispatch",
            status=status,
            detail=f"Message dispatched through route {route.id}.",
            route_id=route.id,
            event_id=event.id,
            placeholder=placeholder,
        )
        connection.commit()

    return IntegrationDispatchResult(
        id=str(uuid4()),
        route_id=route.id,
        status=status,
        event_id=event.id,
        target_service=route.target_service,
        action_type=route.event_type,
        allowed=True,
        blocked=False,
        blocked_reason=None,
        handler_result={},
        dead_letter_routed=request.route_to_dead_letter,
        audit_event_id=audit.id,
        external_connection_enabled=False,
        runtime_connected=False,
        created_at=utc_now(),
    )


def update_route_state(route_id: str, update: IntegrationBusRouteStateUpdate) -> IntegrationBusRoute | None:
    route = get_route(route_id)
    if route is None:
        return None

    requested_status = update.status.strip().lower()
    if requested_status not in ALLOWED_ROUTE_STATUSES:
        raise IntegrationBusValidationError(
            {
                "error": "invalid_route_status",
                "route_id": route_id,
                "status": update.status,
                "allowed_statuses": sorted(ALLOWED_ROUTE_STATUSES),
            }
        )

    if is_internal_route(route_id):
        prepared_route = route_definition_for_id(route_id)
        assert prepared_route is not None
        target = normalize_service_id(prepared_route.target)
        if target in INTERNAL_BLOCKED_TARGETS and requested_status not in {"blocked", "rejected"}:
            raise IntegrationBusValidationError(
                {
                    "error": "protected_internal_route_state_locked",
                    "route_id": route_id,
                    "target": target,
                    "reason": INTERNAL_BLOCKED_TARGETS[target]["reason"],
                },
                status_code=403,
            )
        placeholder = sql_placeholder()
        with connect() as connection:
            audit = insert_bus_audit(
                connection,
                action="internal_route_state_update",
                status=requested_status,
                detail=update.reason,
                route_id=route_id,
                event_id=None,
                placeholder=placeholder,
            )
            insert_internal_dispatch(
                connection,
                route_id=route_id,
                source_service=prepared_route.source,
                target_service=target,
                action_type=internal_route_action_type(target),
                payload={},
                status=requested_status,
                allowed=target not in INTERNAL_BLOCKED_TARGETS,
                requires_ceo_approval=target in INTERNAL_BLOCKED_TARGETS,
                audit_event_id=audit.id,
                event_id=None,
                handler_result={"result": requested_status, "reason": update.reason},
                blocked_reason=INTERNAL_BLOCKED_TARGETS.get(target, {}).get("reason"),
                placeholder=placeholder,
            )
            connection.commit()
        return get_route(route_id)

    placeholder = sql_placeholder()
    with connect() as connection:
        connection.execute(
            f"UPDATE {BUS_ROUTES_TABLE} SET status = {placeholder} WHERE id = {placeholder}",
            (requested_status, route_id),
        )
        insert_bus_audit(
            connection,
            action="route_state_update",
            status=requested_status,
            detail=update.reason,
            route_id=route_id,
            event_id=None,
            placeholder=placeholder,
        )
        connection.commit()
    return get_route(route_id)


def list_bus_dependencies() -> list[IntegrationBusDependency]:
    contracts = list_integration_contracts()
    dependencies = [
        IntegrationBusDependency(
            id=f"contract:{contract.id}",
            name=contract.name,
            dependency_type="contract",
            status=contract.status,
            required=True,
            external_dependency=contract.external_dependency,
        )
        for contract in contracts
    ]
    dependencies.append(
        IntegrationBusDependency(
            id="internal-events",
            name="Internal Events",
            dependency_type="service",
            status="ready_local",
            required=True,
            external_dependency=False,
        )
    )
    return dependencies


def list_bus_audit() -> list[IntegrationBusAuditEvent]:
    ensure_integration_bus_schema()

    with connect() as connection:
        rows = connection.execute(
            f"""
            SELECT id, action, status, detail, route_id, event_id, created_at
            FROM {BUS_AUDIT_TABLE}
            ORDER BY created_at DESC
            """
        ).fetchall()

    return [
        IntegrationBusAuditEvent(
            id=row_value(row, "id"),
            action=row_value(row, "action"),
            status=row_value(row, "status"),
            detail=row_value(row, "detail"),
            route_id=row_value(row, "route_id"),
            event_id=row_value(row, "event_id"),
            created_at=row_value(row, "created_at"),
        )
        for row in rows
    ]


def get_bus_status() -> IntegrationBusStatus:
    ensure_integration_bus_schema()

    with connect() as connection:
        routes_row = connection.execute(
            f"SELECT COUNT(*) AS count FROM {BUS_ROUTES_TABLE}"
        ).fetchone()
        audit_row = connection.execute(
            f"SELECT COUNT(*) AS count FROM {BUS_AUDIT_TABLE}"
        ).fetchone()

    return IntegrationBusStatus(
        status="integration_bus_operational",
        routes=len(list_internal_routes()) + row_value(routes_row, "count"),
        prepared_routes=len(list_prepared_routes()),
        services=len(list_bus_services()),
        dependencies=len(list_bus_dependencies()),
        audit_events=row_value(audit_row, "count"),
        external_connections_enabled=False,
    )


def get_bus_overview() -> IntegrationBusOverview:
    return IntegrationBusOverview(
        status="integration_bus_operational",
        routes=list_routes(),
        prepared_routes=list(list_prepared_routes()),
        services=list(list_bus_services()),
        dependencies=list_bus_dependencies(),
        external_connections_enabled=False,
    )
