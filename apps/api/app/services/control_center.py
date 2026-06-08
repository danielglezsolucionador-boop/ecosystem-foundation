from datetime import UTC, datetime
import json
from uuid import uuid4

from app.core.config import get_settings
from app.core.database import connect, initialize_database, sql_placeholder
from app.core.metadata import APP_COMMIT, APP_ENVIRONMENT, APP_NAME, APP_VERSION
from app.schemas.app_registry import AppStatus, EcosystemApp
from app.schemas.control_center import (
    AlertSeverity,
    AlertSummary,
    ControlCenterAction,
    ControlCenterApplicationStatus,
    ControlCenterAuditEvent,
    ControlCenterDependencyStatus,
    ControlCenterEvidence,
    ControlCenterMetric,
    ControlCenterOverview,
    ControlCenterResponse,
    ControlCenterRuntimeStatus,
    ControlCenterServiceStatus,
    ControlCenterState,
    ControlCenterStatus,
    ExecutiveSummary,
    OperationalSummary,
    ReadinessCheck,
    ReadinessSummary,
)
from app.schemas.storage import StorageStatus
from app.services.app_registry import list_registered_apps, summarize_registered_apps
from app.services.storage import get_storage_status


CONTROL_CENTER_AUDIT_TABLE = "control_center_audit_events"
REGISTRY_SOURCE = "local_controlled_registry"
EXTERNAL_CONNECTIONS_ENABLED = False


def utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def state_rank(status: ControlCenterState) -> int:
    return {
        ControlCenterState.healthy: 0,
        ControlCenterState.unknown: 1,
        ControlCenterState.degraded: 2,
        ControlCenterState.blocked: 3,
    }[status]


def worst_state(states: list[ControlCenterState]) -> ControlCenterState:
    if not states:
        return ControlCenterState.unknown

    return max(states, key=state_rank)


def app_status_to_control_state(status: AppStatus) -> ControlCenterState:
    if status == AppStatus.internal:
        return ControlCenterState.healthy
    if status == AppStatus.external:
        return ControlCenterState.degraded
    if status == AppStatus.blocked:
        return ControlCenterState.blocked
    return ControlCenterState.unknown


def storage_status_to_control_state(storage: StorageStatus) -> ControlCenterState:
    return (
        ControlCenterState.healthy
        if storage.status == "connected"
        else ControlCenterState.blocked
    )


def safe_storage_status() -> StorageStatus:
    try:
        return get_storage_status()
    except Exception:
        return StorageStatus(
            status="error",
            backend="unknown",
            configured=False,
            persistent=False,
            schema_version="unknown",
        )


def ensure_control_center_audit_schema() -> None:
    placeholder = sql_placeholder()

    with connect() as connection:
        connection.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {CONTROL_CENTER_AUDIT_TABLE} (
                id TEXT PRIMARY KEY,
                event_type TEXT NOT NULL,
                status TEXT NOT NULL,
                payload TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            INSERT INTO platform_metadata (key, value)
            VALUES ('control_center_schema_version', {placeholder})
            ON CONFLICT(key) DO UPDATE SET value = excluded.value
            """.format(placeholder=placeholder),
            ("1",),
        )
        connection.commit()


def record_control_center_audit_event(
    event_type: str,
    status: ControlCenterState,
    payload: dict[str, object],
) -> ControlCenterAuditEvent | None:
    try:
        initialize_database()
        ensure_control_center_audit_schema()
        event = ControlCenterAuditEvent(
            id=str(uuid4()),
            event_type=event_type,
            status=status,
            payload=payload,
            created_at=utc_now(),
        )

        placeholder = sql_placeholder()
        with connect() as connection:
            connection.execute(
                f"""
                INSERT INTO {CONTROL_CENTER_AUDIT_TABLE}
                    (id, event_type, status, payload, created_at)
                VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder})
                """,
                (
                    event.id,
                    event.event_type,
                    event.status.value,
                    json.dumps(event.payload, sort_keys=True),
                    event.created_at,
                ),
            )
            connection.commit()

        return event
    except Exception:
        return None


def build_application_status(app: EcosystemApp) -> ControlCenterApplicationStatus:
    status = app_status_to_control_state(app.status)
    evidence_detail = {
        AppStatus.internal: "Registered as an internal platform component.",
        AppStatus.external: "Registered as an external application reference only.",
        AppStatus.planned: "Registered as planned and not connected yet.",
        AppStatus.blocked: "Registered as blocked and unavailable for execution.",
        AppStatus.unknown: "Registered without verified operational state.",
    }[app.status]

    return ControlCenterApplicationStatus(
        id=app.id,
        name=app.name,
        type=app.type,
        registry_status=app.status.value,
        status=status,
        depends_on=app.depends_on,
        touch_policy=app.touch_policy,
        external_connection_enabled=False,
        evidence=[
            ControlCenterEvidence(
                source=REGISTRY_SOURCE,
                status=status,
                detail=evidence_detail,
            )
        ],
    )


def build_runtime_status(storage: StorageStatus) -> ControlCenterRuntimeStatus:
    storage_state = storage_status_to_control_state(storage)
    settings = get_settings()

    return ControlCenterRuntimeStatus(
        status=storage_state,
        service=APP_NAME,
        environment=APP_ENVIRONMENT,
        version=APP_VERSION,
        commit=APP_COMMIT,
        database_backend=storage.backend,
        database_persistent=storage.persistent,
        database_source=settings.database_url_source,
        external_connections_enabled=False,
        generated_at=utc_now(),
    )


def build_services(storage: StorageStatus) -> list[ControlCenterServiceStatus]:
    storage_state = storage_status_to_control_state(storage)
    registry = summarize_registered_apps()

    return [
        ControlCenterServiceStatus(
            id="api_runtime",
            name="FastAPI Runtime",
            category="runtime",
            status=ControlCenterState.healthy,
            detail="The local API runtime is importable and serving internal endpoints.",
            evidence=[
                ControlCenterEvidence(
                    source="/health",
                    status=ControlCenterState.healthy,
                    detail="Health endpoint is registered in the local application.",
                )
            ],
        ),
        ControlCenterServiceStatus(
            id="app_registry",
            name="App Registry",
            category="registry",
            status=ControlCenterState.healthy if registry.total >= 13 else ControlCenterState.degraded,
            detail=f"{registry.total} ecosystem applications are registered locally.",
            evidence=[
                ControlCenterEvidence(
                    source="/api/v1/apps",
                    status=ControlCenterState.healthy,
                    detail="Controlled registry is loaded from repository data.",
                )
            ],
        ),
        ControlCenterServiceStatus(
            id="storage",
            name="Storage Layer",
            category="database",
            status=storage_state,
            detail=f"Database backend is {storage.backend} with schema {storage.schema_version}.",
            evidence=[
                ControlCenterEvidence(
                    source="database.initialize_database",
                    status=storage_state,
                    detail=f"Storage status reported {storage.status}.",
                )
            ],
        ),
        ControlCenterServiceStatus(
            id="audit_log",
            name="Control Center Audit",
            category="audit",
            status=ControlCenterState.healthy if storage.status == "connected" else ControlCenterState.degraded,
            detail="Control Center reads are registered when the database is reachable.",
            evidence=[
                ControlCenterEvidence(
                    source=CONTROL_CENTER_AUDIT_TABLE,
                    status=ControlCenterState.healthy if storage.status == "connected" else ControlCenterState.degraded,
                    detail="Audit storage is initialized on demand.",
                )
            ],
        ),
        ControlCenterServiceStatus(
            id="health_readiness",
            name="Health and Readiness",
            category="operations",
            status=storage_state,
            detail="Readiness is tied to database connectivity and internal runtime status.",
            evidence=[
                ControlCenterEvidence(
                    source="/readiness",
                    status=storage_state,
                    detail="Readiness is healthy when the database is connected.",
                )
            ],
        ),
        ControlCenterServiceStatus(
            id="external_app_connectors",
            name="External App Connectors",
            category="integration",
            status=ControlCenterState.degraded,
            detail="External runtime connections are intentionally disabled in the backbone stage.",
            evidence=[
                ControlCenterEvidence(
                    source="touch_policy",
                    status=ControlCenterState.degraded,
                    detail=(
                        "FORJA y CEREBRO estan preparados para revision; "
                        "DCFT permanece protegido y sin conexion real."
                    ),
                )
            ],
        ),
    ]


def build_dependencies(
    storage: StorageStatus,
    applications: list[ControlCenterApplicationStatus],
) -> list[ControlCenterDependencyStatus]:
    storage_state = storage_status_to_control_state(storage)
    external_apps = [
        app for app in applications if app.registry_status == AppStatus.external.value
    ]

    return [
        ControlCenterDependencyStatus(
            id="database",
            name="Configured Database",
            type="storage",
            required=True,
            status=storage_state,
            detail=(
                f"{storage.backend} database is connected."
                if storage.status == "connected"
                else "Database is not connected."
            ),
            evidence=[
                ControlCenterEvidence(
                    source="DATABASE_URL",
                    status=storage_state,
                    detail="Database URL is resolved without exposing secret values.",
                )
            ],
        ),
        ControlCenterDependencyStatus(
            id="postgresql_database",
            name="PostgreSQL Production Database",
            type="storage",
            required=False,
            status=ControlCenterState.healthy
            if storage.backend == "postgresql"
            else ControlCenterState.degraded,
            detail=(
                "PostgreSQL is active."
                if storage.backend == "postgresql"
                else "Local execution can run on SQLite; production should use DATABASE_URL with PostgreSQL."
            ),
            evidence=[
                ControlCenterEvidence(
                    source="storage.backend",
                    status=ControlCenterState.healthy
                    if storage.backend == "postgresql"
                    else ControlCenterState.degraded,
                    detail=f"Current backend: {storage.backend}.",
                )
            ],
        ),
        ControlCenterDependencyStatus(
            id="external_app_runtime",
            name="External App Runtime Connections",
            type="external_app",
            required=False,
            status=ControlCenterState.degraded,
            detail=(
                f"{len(external_apps)} external apps are cataloged but deliberately not connected."
            ),
            evidence=[
                ControlCenterEvidence(
                    source=REGISTRY_SOURCE,
                    status=ControlCenterState.degraded,
                    detail="External apps remain registry references until contracts are approved.",
                )
            ],
        ),
        ControlCenterDependencyStatus(
            id="integration_contracts",
            name="Integration Contracts",
            type="governance",
            required=True,
            status=ControlCenterState.blocked,
            detail="External integration contracts are required before connecting real apps.",
            evidence=[
                ControlCenterEvidence(
                    source="docs/ecosystem",
                    status=ControlCenterState.blocked,
                    detail="Backbone phase is local-first and does not touch existing apps.",
                )
            ],
        ),
    ]


def build_alerts(
    storage: StorageStatus,
    applications: list[ControlCenterApplicationStatus],
) -> list[AlertSummary]:
    alerts: list[AlertSummary] = []

    if storage.status != "connected":
        alerts.append(
            AlertSummary(
                id="database_unavailable",
                severity=AlertSeverity.critical,
                status=ControlCenterState.blocked,
                message="Database is unavailable; Control Center cannot persist audit events.",
                source="database",
                action_required=True,
            )
        )

    if storage.backend != "postgresql":
        alerts.append(
            AlertSummary(
                id="postgres_not_active",
                severity=AlertSeverity.medium,
                status=ControlCenterState.degraded,
                message="Local database is not PostgreSQL; production must provide DATABASE_URL.",
                source="storage.backend",
                action_required=False,
            )
        )

    external_count = len(
        [app for app in applications if app.registry_status == AppStatus.external.value]
    )
    if external_count:
        alerts.append(
            AlertSummary(
                id="external_apps_not_connected",
                severity=AlertSeverity.info,
                status=ControlCenterState.degraded,
                message=f"{external_count} external apps are cataloged but isolated by policy.",
                source=REGISTRY_SOURCE,
                action_required=False,
            )
        )

    blocked_count = len(
        [app for app in applications if app.status == ControlCenterState.blocked]
    )
    if blocked_count:
        alerts.append(
            AlertSummary(
                id="blocked_registry_items",
                severity=AlertSeverity.high,
                status=ControlCenterState.blocked,
                message=f"{blocked_count} registered app is marked blocked.",
                source=REGISTRY_SOURCE,
                action_required=True,
            )
        )

    return alerts


def build_metrics(
    storage: StorageStatus,
    applications: list[ControlCenterApplicationStatus],
    services: list[ControlCenterServiceStatus],
    dependencies: list[ControlCenterDependencyStatus],
    alerts: list[AlertSummary],
) -> list[ControlCenterMetric]:
    state_counts = {state.value: 0 for state in ControlCenterState}
    for item in [*applications, *services, *dependencies]:
        state_counts[item.status.value] += 1

    return [
        ControlCenterMetric(
            id="registered_apps",
            label="Registered Applications",
            value=len(applications),
            unit="apps",
            status=ControlCenterState.healthy,
            source=REGISTRY_SOURCE,
        ),
        ControlCenterMetric(
            id="internal_apps",
            label="Internal Applications",
            value=len([app for app in applications if app.registry_status == AppStatus.internal.value]),
            unit="apps",
            status=ControlCenterState.healthy,
            source=REGISTRY_SOURCE,
        ),
        ControlCenterMetric(
            id="external_references",
            label="External App References",
            value=len([app for app in applications if app.registry_status == AppStatus.external.value]),
            unit="apps",
            status=ControlCenterState.degraded,
            source=REGISTRY_SOURCE,
        ),
        ControlCenterMetric(
            id="services_tracked",
            label="Services Tracked",
            value=len(services),
            unit="services",
            status=worst_state([service.status for service in services]),
            source="control_center.services",
        ),
        ControlCenterMetric(
            id="dependencies_tracked",
            label="Dependencies Tracked",
            value=len(dependencies),
            unit="dependencies",
            status=worst_state([dependency.status for dependency in dependencies]),
            source="control_center.dependencies",
        ),
        ControlCenterMetric(
            id="active_alerts",
            label="Active Alerts",
            value=len(alerts),
            unit="alerts",
            status=ControlCenterState.healthy if not alerts else worst_state([alert.status for alert in alerts]),
            source="control_center.alerts",
        ),
        ControlCenterMetric(
            id="storage_backend",
            label="Storage Backend",
            value=storage.backend,
            status=storage_status_to_control_state(storage),
            source="database.initialize_database",
        ),
        ControlCenterMetric(
            id="external_connections_enabled",
            label="External Connections Enabled",
            value=False,
            status=ControlCenterState.healthy,
            source="touch_policy",
        ),
    ]


def build_readiness(
    storage: StorageStatus,
    applications: list[ControlCenterApplicationStatus],
    dependencies: list[ControlCenterDependencyStatus],
) -> ReadinessSummary:
    checks = [
        ReadinessCheck(
            id="app_registry_loaded",
            label="App Registry Loaded",
            status=ControlCenterState.healthy if len(applications) >= 13 else ControlCenterState.degraded,
            required=True,
            detail=f"{len(applications)} applications are available in the controlled registry.",
        ),
        ReadinessCheck(
            id="database_connected",
            label="Database Connected",
            status=storage_status_to_control_state(storage),
            required=True,
            detail=f"Database status: {storage.status}.",
        ),
        ReadinessCheck(
            id="external_apps_isolated",
            label="External Apps Isolated",
            status=ControlCenterState.healthy,
            required=True,
            detail="No real FORJA, CEREBRO or DCFT runtime is contacted.",
        ),
        ReadinessCheck(
            id="postgres_for_production",
            label="PostgreSQL For Production",
            status=ControlCenterState.healthy
            if storage.backend == "postgresql"
            else ControlCenterState.degraded,
            required=False,
            detail=(
                "PostgreSQL is active."
                if storage.backend == "postgresql"
                else "Local mode uses SQLite; Vercel/staging should set DATABASE_URL."
            ),
        ),
        ReadinessCheck(
            id="contracts_required_before_external_connections",
            label="Contracts Required Before External Connections",
            status=ControlCenterState.blocked,
            required=True,
            detail="Integration contracts must exist before enabling external app connections.",
        ),
    ]
    required_states = [check.status for check in checks if check.required]

    return ReadinessSummary(
        status=worst_state(required_states),
        ready_for_external_connections=False,
        checks=checks,
    )


def build_operational_summary(
    services: list[ControlCenterServiceStatus],
    dependencies: list[ControlCenterDependencyStatus],
    alerts: list[AlertSummary],
) -> OperationalSummary:
    tracked_items = [*services, *dependencies]
    blocked_items = len(
        [item for item in tracked_items if item.status == ControlCenterState.blocked]
    )
    unknown_items = len(
        [item for item in tracked_items if item.status == ControlCenterState.unknown]
    )
    degraded_services = len(
        [service for service in services if service.status == ControlCenterState.degraded]
    )

    notes = [
        "Control Center is local-first and registry-backed.",
        "External app runtime connections remain disabled.",
    ]
    if alerts:
        notes.append(f"{len(alerts)} alert(s) require operational awareness.")

    return OperationalSummary(
        status=worst_state([item.status for item in tracked_items]),
        active_services=len([service for service in services if service.status == ControlCenterState.healthy]),
        degraded_services=degraded_services,
        blocked_items=blocked_items,
        unknown_items=unknown_items,
        external_connections_enabled=False,
        notes=notes,
    )


def build_executive_summary(
    status: ControlCenterState,
    readiness: ReadinessSummary,
) -> ExecutiveSummary:
    decision_required = readiness.status == ControlCenterState.blocked

    return ExecutiveSummary(
        status=status,
        headline="Ecosystem backbone is visible and controlled.",
        summary=(
            "La cabina muestra el estado operativo del ecosistema sin conectar apps "
            "protegidas ni tocar produccion."
        ),
        decision_required=decision_required,
        focus=[
            "Keep external applications isolated until contracts are approved.",
            "Use PostgreSQL through DATABASE_URL for staging and production.",
            "Advance next backbone block only after tests remain green.",
        ],
    )


def build_next_actions(storage: StorageStatus) -> list[ControlCenterAction]:
    actions = [
        ControlCenterAction(
            id="approve_integration_contracts",
            label="Approve external integration contracts before connecting apps.",
            priority="p0",
            blocked=True,
            owner_view="ceo",
            reason="Runtime connections remain disabled until explicit contract approval.",
        ),
        ControlCenterAction(
            id="keep_app_registry_current",
            label="Keep the controlled app registry current.",
            priority="p1",
            blocked=False,
            owner_view="operational",
            reason="Control Center depends on registry quality for executive summaries.",
        ),
        ControlCenterAction(
            id="run_backbone_tests",
            label="Run compile, pytest and secret scan before every backbone block.",
            priority="p1",
            blocked=False,
            owner_view="operational",
            reason="Backbone progression requires verified local stability.",
        ),
    ]

    if storage.backend != "postgresql":
        actions.append(
            ControlCenterAction(
                id="configure_postgres_for_cloud",
                label="Configure DATABASE_URL with PostgreSQL before cloud readiness.",
                priority="p2",
                blocked=False,
                owner_view="operational",
                reason="SQLite is acceptable locally but not the final cloud dependency.",
            )
        )

    return actions


def build_risks(storage: StorageStatus) -> list[str]:
    risks = [
        "External app runtime is not connected by design during backbone construction.",
        "Integration contracts are required before any FORJA, CEREBRO or DCFT runtime connection.",
    ]

    if storage.backend != "postgresql":
        risks.append("DATABASE_URL is not pointing to PostgreSQL in this execution context.")

    if storage.status != "connected":
        risks.append("Database connectivity is blocked; audit persistence is unavailable.")

    return risks


def assemble_control_center(record_audit: bool = True) -> ControlCenterResponse:
    storage = safe_storage_status()
    registry_apps = list_registered_apps()
    applications = [build_application_status(app) for app in registry_apps]
    runtime = build_runtime_status(storage)
    services = build_services(storage)
    dependencies = build_dependencies(storage, applications)
    alerts = build_alerts(storage, applications)
    metrics = build_metrics(storage, applications, services, dependencies, alerts)
    readiness = build_readiness(storage, applications, dependencies)

    status = worst_state(
        [
            runtime.status,
            worst_state([service.status for service in services]),
            worst_state([dependency.status for dependency in dependencies]),
            readiness.status,
        ]
    )

    operational_summary = build_operational_summary(services, dependencies, alerts)
    executive_summary = build_executive_summary(status, readiness)
    overview = ControlCenterOverview(
        status=status,
        registry_source=REGISTRY_SOURCE,
        external_connections_enabled=False,
        executive_summary=executive_summary,
        operational_summary=operational_summary,
        metrics=metrics,
        next_actions=build_next_actions(storage),
        risks=build_risks(storage),
    )
    status_summary = ControlCenterStatus(
        status=status,
        runtime=runtime,
        applications=applications,
        services=services,
        dependencies=dependencies,
    )

    audit_event = None
    if record_audit:
        audit_event = record_control_center_audit_event(
            event_type="control_center_read",
            status=status,
            payload={
                "registered_apps": len(applications),
                "services": len(services),
                "dependencies": len(dependencies),
                "alerts": len(alerts),
                "external_connections_enabled": False,
            },
        )

    return ControlCenterResponse(
        status=status,
        generated_at=utc_now(),
        audit_event_id=audit_event.id if audit_event else None,
        overview=overview,
        status_summary=status_summary,
        applications=applications,
        services=services,
        dependencies=dependencies,
        metrics=metrics,
        alerts=alerts,
        readiness=readiness,
        executive_view=executive_summary,
        operational_view=operational_summary,
    )


def get_control_center() -> ControlCenterResponse:
    return assemble_control_center()


def get_control_center_overview() -> ControlCenterOverview:
    return assemble_control_center(record_audit=False).overview


def get_control_center_status() -> ControlCenterStatus:
    return assemble_control_center(record_audit=False).status_summary


def list_control_center_apps() -> list[ControlCenterApplicationStatus]:
    return assemble_control_center(record_audit=False).applications


def list_control_center_services() -> list[ControlCenterServiceStatus]:
    return assemble_control_center(record_audit=False).services


def list_control_center_dependencies() -> list[ControlCenterDependencyStatus]:
    return assemble_control_center(record_audit=False).dependencies


def list_control_center_metrics() -> list[ControlCenterMetric]:
    return assemble_control_center(record_audit=False).metrics


def list_control_center_alerts() -> list[AlertSummary]:
    return assemble_control_center(record_audit=False).alerts


def get_control_center_readiness() -> ReadinessSummary:
    return assemble_control_center(record_audit=False).readiness
