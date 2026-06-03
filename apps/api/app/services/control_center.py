from app.schemas.control_center import (
    ControlCenterAction,
    ControlCenterMetric,
    ControlCenterOverview,
)
from app.services.app_registry import summarize_registered_apps


def get_control_center_overview() -> ControlCenterOverview:
    registry = summarize_registered_apps()
    by_status = registry.by_status

    metrics = [
        ControlCenterMetric(
            id="registered_apps",
            label="Registered apps",
            value=registry.total,
            status="ok",
        ),
        ControlCenterMetric(
            id="planned_apps",
            label="Planned apps",
            value=by_status["planned"],
            status="attention",
        ),
        ControlCenterMetric(
            id="external_references",
            label="External references",
            value=by_status["external"],
            status="controlled",
        ),
        ControlCenterMetric(
            id="blocked_apps",
            label="Blocked apps",
            value=by_status["blocked"],
            status="ok",
        ),
    ]

    next_actions = [
        ControlCenterAction(
            id="define_permissions",
            label="Define local permission contracts",
            priority="p0",
            blocked=False,
        ),
        ControlCenterAction(
            id="prepare_local_storage",
            label="Prepare local platform storage",
            priority="p0",
            blocked=False,
        ),
        ControlCenterAction(
            id="keep_external_apps_isolated",
            label="Keep external applications isolated until contracts exist",
            priority="p0",
            blocked=False,
        ),
    ]

    return ControlCenterOverview(
        status="local_operational",
        registry_source=registry.source,
        external_connections_enabled=registry.external_connections_enabled,
        metrics=metrics,
        next_actions=next_actions,
        risks=[
            "External app runtime is not connected by design.",
            "No database is enabled yet for platform state.",
        ],
    )

