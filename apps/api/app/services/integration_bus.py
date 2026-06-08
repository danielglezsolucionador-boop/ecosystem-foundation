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


class IntegrationBusValidationError(RuntimeError):
    def __init__(self, detail: dict[str, object]) -> None:
        self.detail = detail
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
        connection.commit()


def row_to_route(row: Any) -> IntegrationBusRoute:
    return IntegrationBusRoute(
        id=row_value(row, "id"),
        source_service=row_value(row, "source_service"),
        target_service=row_value(row, "target_service"),
        event_type=row_value(row, "event_type"),
        channel=row_value(row, "channel"),
        status=row_value(row, "status"),
        retry_policy=row_value(row, "retry_policy"),
        dead_letter_enabled=bool(row_value(row, "dead_letter_enabled")),
        external_connection_enabled=bool(row_value(row, "external_connection_enabled")),
        created_at=row_value(row, "created_at"),
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

    return [row_to_route(row) for row in rows]


def get_route(route_id: str) -> IntegrationBusRoute | None:
    ensure_integration_bus_schema()
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


def dispatch_message(
    request: IntegrationDispatchRequest,
) -> IntegrationDispatchResult | None:
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
        dead_letter_routed=request.route_to_dead_letter,
        audit_event_id=audit.id,
        created_at=utc_now(),
    )


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
        routes=row_value(routes_row, "count"),
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
