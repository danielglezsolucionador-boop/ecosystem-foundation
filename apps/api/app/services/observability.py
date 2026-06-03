from app.core.metadata import APP_ENVIRONMENT, APP_NAME
from app.schemas.observability import ObservabilityMetric, ObservabilityStatus
from app.services.app_registry import summarize_registered_apps
from app.services.audit import list_audit_reports
from app.services.memory import get_memory_status
from app.services.storage import get_storage_status


def get_observability_status() -> ObservabilityStatus:
    registry = summarize_registered_apps()
    storage = get_storage_status()
    memory = get_memory_status()
    audit_reports = list_audit_reports()

    metrics = [
        ObservabilityMetric(
            id="registered_apps",
            value=registry.total,
            status="ok",
        ),
        ObservabilityMetric(
            id="external_connections_enabled",
            value=registry.external_connections_enabled,
            status="ok" if not registry.external_connections_enabled else "warning",
        ),
        ObservabilityMetric(
            id="storage_backend",
            value=storage.backend,
            status="ok" if storage.status == "connected" else "fail",
        ),
        ObservabilityMetric(
            id="memory_entries",
            value=memory.entries,
            status="ok",
        ),
        ObservabilityMetric(
            id="audit_reports",
            value=len(audit_reports),
            status="ok",
        ),
    ]

    return ObservabilityStatus(
        status="local_observable",
        service=APP_NAME,
        environment=APP_ENVIRONMENT,
        metrics=metrics,
    )

