from datetime import UTC, datetime
import json
from typing import Any
from uuid import uuid4

from app.core.database import connect, initialize_database, sql_placeholder
from app.core.metadata import APP_ENVIRONMENT, APP_NAME
from app.schemas.observability import (
    ObservabilityHealthService,
    ObservabilityIncident,
    ObservabilityIncidentCreate,
    ObservabilityLog,
    ObservabilityLogCreate,
    ObservabilityMetric,
    ObservabilityMetricCreate,
    ObservabilityObjective,
    ObservabilityOverview,
    ObservabilityStatus,
    ObservabilityTrace,
    ObservabilityTraceCreate,
)
from app.services.app_registry import summarize_registered_apps
from app.services.audit import get_audit_overview, list_audit_reports
from app.services.contracts import get_contract_status
from app.services.events import get_event_status
from app.services.integration_bus import get_bus_status
from app.services.memory import get_memory_status
from app.services.storage import get_storage_status

METRICS_TABLE = "observability_metrics"
LOGS_TABLE = "observability_logs"
TRACES_TABLE = "observability_traces"
INCIDENTS_TABLE = "observability_incidents"


def utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def row_value(row: Any, key: str) -> Any:
    return row[key]


def ensure_observability_schema() -> None:
    initialize_database()

    with connect() as connection:
        connection.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {METRICS_TABLE} (
                record_id TEXT PRIMARY KEY,
                id TEXT NOT NULL,
                value_json TEXT NOT NULL,
                status TEXT NOT NULL,
                source TEXT NOT NULL,
                unit TEXT,
                request_id TEXT,
                trace_id TEXT,
                created_at TEXT NOT NULL
            )
            """
        )
        connection.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {LOGS_TABLE} (
                id TEXT PRIMARY KEY,
                level TEXT NOT NULL,
                message TEXT NOT NULL,
                source TEXT NOT NULL,
                request_id TEXT,
                trace_id TEXT,
                metadata_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        connection.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {TRACES_TABLE} (
                id TEXT PRIMARY KEY,
                trace_id TEXT NOT NULL,
                span_id TEXT NOT NULL,
                parent_span_id TEXT,
                operation TEXT NOT NULL,
                status TEXT NOT NULL,
                duration_ms INTEGER NOT NULL,
                metadata_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        connection.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {INCIDENTS_TABLE} (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                severity TEXT NOT NULL,
                status TEXT NOT NULL,
                description TEXT NOT NULL,
                source TEXT NOT NULL,
                trace_id TEXT,
                created_at TEXT NOT NULL
            )
            """
        )
        connection.commit()


def create_metric(metric: ObservabilityMetricCreate) -> ObservabilityMetric:
    ensure_observability_schema()
    placeholder = sql_placeholder()
    record = ObservabilityMetric(
        id=metric.id,
        value=metric.value,
        status=metric.status,
        source=metric.source,
        unit=metric.unit,
        request_id=metric.request_id,
        trace_id=metric.trace_id,
        created_at=utc_now(),
    )

    with connect() as connection:
        connection.execute(
            f"""
            INSERT INTO {METRICS_TABLE} (
                record_id, id, value_json, status, source, unit,
                request_id, trace_id, created_at
            )
            VALUES (
                {placeholder}, {placeholder}, {placeholder}, {placeholder},
                {placeholder}, {placeholder}, {placeholder}, {placeholder},
                {placeholder}
            )
            """,
            (
                str(uuid4()),
                record.id,
                json.dumps(record.value),
                record.status,
                record.source,
                record.unit,
                record.request_id,
                record.trace_id,
                record.created_at,
            ),
        )
        connection.commit()

    return record


def list_metrics() -> list[ObservabilityMetric]:
    ensure_observability_schema()
    dynamic_metrics = get_core_metrics()

    with connect() as connection:
        rows = connection.execute(
            f"""
            SELECT id, value_json, status, source, unit, request_id, trace_id, created_at
            FROM {METRICS_TABLE}
            ORDER BY created_at DESC
            """
        ).fetchall()

    stored_metrics = [
        ObservabilityMetric(
            id=row_value(row, "id"),
            value=json.loads(row_value(row, "value_json")),
            status=row_value(row, "status"),
            source=row_value(row, "source"),
            unit=row_value(row, "unit"),
            request_id=row_value(row, "request_id"),
            trace_id=row_value(row, "trace_id"),
            created_at=row_value(row, "created_at"),
        )
        for row in rows
    ]
    return [*dynamic_metrics, *stored_metrics]


def create_log(log: ObservabilityLogCreate) -> ObservabilityLog:
    ensure_observability_schema()
    placeholder = sql_placeholder()
    record = ObservabilityLog(
        id=str(uuid4()),
        level=log.level.lower(),
        message=log.message,
        source=log.source,
        request_id=log.request_id,
        trace_id=log.trace_id,
        metadata=log.metadata,
        created_at=utc_now(),
    )

    with connect() as connection:
        connection.execute(
            f"""
            INSERT INTO {LOGS_TABLE} (
                id, level, message, source, request_id, trace_id,
                metadata_json, created_at
            )
            VALUES (
                {placeholder}, {placeholder}, {placeholder}, {placeholder},
                {placeholder}, {placeholder}, {placeholder}, {placeholder}
            )
            """,
            (
                record.id,
                record.level,
                record.message,
                record.source,
                record.request_id,
                record.trace_id,
                json.dumps(record.metadata, sort_keys=True),
                record.created_at,
            ),
        )
        connection.commit()

    return record


def list_logs(level: str | None = None) -> list[ObservabilityLog]:
    ensure_observability_schema()
    placeholder = sql_placeholder()
    where = ""
    params: tuple[str, ...] = ()
    if level:
        where = f"WHERE level = {placeholder}"
        params = (level.lower(),)

    with connect() as connection:
        rows = connection.execute(
            f"""
            SELECT id, level, message, source, request_id, trace_id, metadata_json, created_at
            FROM {LOGS_TABLE}
            {where}
            ORDER BY created_at DESC
            """,
            params,
        ).fetchall()

    return [
        ObservabilityLog(
            id=row_value(row, "id"),
            level=row_value(row, "level"),
            message=row_value(row, "message"),
            source=row_value(row, "source"),
            request_id=row_value(row, "request_id"),
            trace_id=row_value(row, "trace_id"),
            metadata=json.loads(row_value(row, "metadata_json")),
            created_at=row_value(row, "created_at"),
        )
        for row in rows
    ]


def create_trace(trace: ObservabilityTraceCreate) -> ObservabilityTrace:
    ensure_observability_schema()
    placeholder = sql_placeholder()
    record = ObservabilityTrace(
        id=str(uuid4()),
        trace_id=trace.trace_id or str(uuid4()),
        span_id=trace.span_id,
        parent_span_id=trace.parent_span_id,
        operation=trace.operation,
        status=trace.status,
        duration_ms=trace.duration_ms,
        metadata=trace.metadata,
        created_at=utc_now(),
    )

    with connect() as connection:
        connection.execute(
            f"""
            INSERT INTO {TRACES_TABLE} (
                id, trace_id, span_id, parent_span_id, operation, status,
                duration_ms, metadata_json, created_at
            )
            VALUES (
                {placeholder}, {placeholder}, {placeholder}, {placeholder},
                {placeholder}, {placeholder}, {placeholder}, {placeholder},
                {placeholder}
            )
            """,
            (
                record.id,
                record.trace_id,
                record.span_id,
                record.parent_span_id,
                record.operation,
                record.status,
                record.duration_ms,
                json.dumps(record.metadata, sort_keys=True),
                record.created_at,
            ),
        )
        connection.commit()

    return record


def list_traces(trace_id: str | None = None) -> list[ObservabilityTrace]:
    ensure_observability_schema()
    placeholder = sql_placeholder()
    where = ""
    params: tuple[str, ...] = ()
    if trace_id:
        where = f"WHERE trace_id = {placeholder}"
        params = (trace_id,)

    with connect() as connection:
        rows = connection.execute(
            f"""
            SELECT
                id, trace_id, span_id, parent_span_id, operation, status,
                duration_ms, metadata_json, created_at
            FROM {TRACES_TABLE}
            {where}
            ORDER BY created_at DESC
            """,
            params,
        ).fetchall()

    return [
        ObservabilityTrace(
            id=row_value(row, "id"),
            trace_id=row_value(row, "trace_id"),
            span_id=row_value(row, "span_id"),
            parent_span_id=row_value(row, "parent_span_id"),
            operation=row_value(row, "operation"),
            status=row_value(row, "status"),
            duration_ms=row_value(row, "duration_ms"),
            metadata=json.loads(row_value(row, "metadata_json")),
            created_at=row_value(row, "created_at"),
        )
        for row in rows
    ]


def create_incident(
    incident: ObservabilityIncidentCreate,
) -> ObservabilityIncident:
    ensure_observability_schema()
    placeholder = sql_placeholder()
    record = ObservabilityIncident(
        id=str(uuid4()),
        title=incident.title,
        severity=incident.severity,
        status=incident.status,
        description=incident.description,
        source=incident.source,
        trace_id=incident.trace_id,
        created_at=utc_now(),
    )

    with connect() as connection:
        connection.execute(
            f"""
            INSERT INTO {INCIDENTS_TABLE} (
                id, title, severity, status, description, source, trace_id, created_at
            )
            VALUES (
                {placeholder}, {placeholder}, {placeholder}, {placeholder},
                {placeholder}, {placeholder}, {placeholder}, {placeholder}
            )
            """,
            (
                record.id,
                record.title,
                record.severity,
                record.status,
                record.description,
                record.source,
                record.trace_id,
                record.created_at,
            ),
        )
        connection.commit()

    return record


def list_incidents() -> list[ObservabilityIncident]:
    ensure_observability_schema()

    with connect() as connection:
        rows = connection.execute(
            f"""
            SELECT id, title, severity, status, description, source, trace_id, created_at
            FROM {INCIDENTS_TABLE}
            ORDER BY created_at DESC
            """
        ).fetchall()

    return [
        ObservabilityIncident(
            id=row_value(row, "id"),
            title=row_value(row, "title"),
            severity=row_value(row, "severity"),
            status=row_value(row, "status"),
            description=row_value(row, "description"),
            source=row_value(row, "source"),
            trace_id=row_value(row, "trace_id"),
            created_at=row_value(row, "created_at"),
        )
        for row in rows
    ]


def count_table(table: str) -> int:
    ensure_observability_schema()
    with connect() as connection:
        row = connection.execute(f"SELECT COUNT(*) AS count FROM {table}").fetchone()
    return row_value(row, "count")


def get_core_metrics() -> list[ObservabilityMetric]:
    registry = summarize_registered_apps()
    storage = get_storage_status()
    memory = get_memory_status()
    audit_reports = list_audit_reports()
    events = get_event_status()
    contracts = get_contract_status()
    integration_bus = get_bus_status()

    return [
        ObservabilityMetric(
            id="registered_apps",
            value=registry.total,
            status="ok",
            source="app_registry",
        ),
        ObservabilityMetric(
            id="external_connections_enabled",
            value=registry.external_connections_enabled,
            status="ok" if not registry.external_connections_enabled else "warning",
            source="app_registry",
        ),
        ObservabilityMetric(
            id="storage_backend",
            value=storage.backend,
            status="ok" if storage.status == "connected" else "fail",
            source="storage",
        ),
        ObservabilityMetric(
            id="memory_entries",
            value=memory.entries,
            status="ok",
            source="memory",
        ),
        ObservabilityMetric(
            id="audit_reports",
            value=len(audit_reports),
            status="ok",
            source="audit",
        ),
        ObservabilityMetric(
            id="internal_events",
            value=events.events,
            status="ok",
            source="events",
        ),
        ObservabilityMetric(
            id="contracts",
            value=contracts.contracts,
            status="ok",
            source="contracts",
        ),
        ObservabilityMetric(
            id="integration_routes",
            value=integration_bus.routes,
            status="ok",
            source="integration_bus",
        ),
    ]


def get_health_aggregation() -> list[ObservabilityHealthService]:
    storage = get_storage_status()
    memory = get_memory_status()
    audit = get_audit_overview()
    events = get_event_status()
    integration_bus = get_bus_status()
    contracts = get_contract_status()

    return [
        ObservabilityHealthService(
            id="storage",
            status="healthy" if storage.status == "connected" else "blocked",
            detail=f"{storage.backend} schema {storage.schema_version}.",
        ),
        ObservabilityHealthService(
            id="memory",
            status="healthy" if memory.status == "local_operational" else "blocked",
            detail=f"{memory.entries} entries.",
        ),
        ObservabilityHealthService(
            id="audit",
            status="healthy"
            if audit.status == "central_audit_operational"
            else "blocked",
            detail=f"{audit.events} audit events.",
        ),
        ObservabilityHealthService(
            id="events",
            status="healthy"
            if events.status == "internal_events_operational"
            else "blocked",
            detail=f"{events.events} events.",
        ),
        ObservabilityHealthService(
            id="integration_bus",
            status="healthy"
            if integration_bus.status == "integration_bus_operational"
            else "blocked",
            detail=f"{integration_bus.routes} routes.",
        ),
        ObservabilityHealthService(
            id="contracts",
            status="healthy" if contracts.status == "contracts_operational" else "blocked",
            detail=f"{contracts.contracts} contracts.",
        ),
    ]


def get_sla_registry() -> list[ObservabilityObjective]:
    return [
        ObservabilityObjective(
            id="api_availability",
            label="API Availability",
            target="99.5%",
            status="prepared_local",
        ),
        ObservabilityObjective(
            id="database_persistence",
            label="Database Persistence",
            target="PostgreSQL for staging/production",
            status="prepared_local",
        ),
    ]


def get_slo_registry() -> list[ObservabilityObjective]:
    return [
        ObservabilityObjective(
            id="health_latency",
            label="Health Endpoint Latency",
            target="<500ms local target",
            status="prepared_local",
        ),
        ObservabilityObjective(
            id="test_stability",
            label="Backbone Test Stability",
            target="pytest PASS before every block",
            status="prepared_local",
        ),
    ]


def get_observability_status() -> ObservabilityStatus:
    ensure_observability_schema()
    return ObservabilityStatus(
        status="local_observable",
        service=APP_NAME,
        environment=APP_ENVIRONMENT,
        metrics=get_core_metrics(),
        logs=count_table(LOGS_TABLE),
        traces=count_table(TRACES_TABLE),
        incidents=count_table(INCIDENTS_TABLE),
        external_monitor_connected=False,
    )


def get_observability_overview() -> ObservabilityOverview:
    ensure_observability_schema()
    return ObservabilityOverview(
        status="central_observability_operational",
        service=APP_NAME,
        environment=APP_ENVIRONMENT,
        health=get_health_aggregation(),
        metrics=list_metrics(),
        logs=count_table(LOGS_TABLE),
        traces=count_table(TRACES_TABLE),
        incidents=count_table(INCIDENTS_TABLE),
        sla=get_sla_registry(),
        slo=get_slo_registry(),
        external_monitor_connected=False,
    )


def list_error_logs() -> list[ObservabilityLog]:
    return list_logs(level="error")
