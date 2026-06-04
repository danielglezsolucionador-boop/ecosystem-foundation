from app.schemas.platform import PlatformPhaseStatus, PlatformStatus
from app.schemas.control_center import ControlCenterState
from app.services.app_registry import summarize_registered_apps
from app.services.audit import list_audit_reports
from app.services.control_center import get_control_center_overview
from app.services.integrations import list_integration_contracts
from app.services.memory import get_memory_status
from app.services.observability import get_observability_status
from app.services.permissions import list_permission_roles
from app.services.storage import get_storage_status


def get_platform_status() -> PlatformStatus:
    registry = summarize_registered_apps()
    control_center = get_control_center_overview()
    roles = list_permission_roles()
    storage = get_storage_status()
    memory = get_memory_status()
    audit_reports = list_audit_reports()
    observability = get_observability_status()
    integrations = list_integration_contracts()

    phases = [
        PlatformPhaseStatus(
            id="A",
            name="Registro completo de aplicaciones",
            status="pass" if registry.total == 13 else "fail",
            evidence=f"{registry.total} apps registered.",
        ),
        PlatformPhaseStatus(
            id="B",
            name="Control Center API",
            status="pass"
            if control_center.status
            in {ControlCenterState.healthy, ControlCenterState.degraded, ControlCenterState.blocked}
            else "fail",
            evidence=control_center.status.value,
        ),
        PlatformPhaseStatus(
            id="C",
            name="Sistema de permisos",
            status="pass"
            if len(roles) >= 3 and all(not role.can_touch_external_apps for role in roles)
            else "fail",
            evidence=f"{len(roles)} local roles with external touch disabled.",
        ),
        PlatformPhaseStatus(
            id="D",
            name="Base de datos local",
            status="pass" if storage.status == "connected" else "fail",
            evidence=f"{storage.backend} schema {storage.schema_version}.",
        ),
        PlatformPhaseStatus(
            id="E",
            name="Memoria compartida local",
            status="pass" if memory.status == "local_operational" else "fail",
            evidence=f"{memory.entries} memory entries.",
        ),
        PlatformPhaseStatus(
            id="F",
            name="Auditoria automatica",
            status="pass" if len(audit_reports) >= 1 else "fail",
            evidence=f"{len(audit_reports)} audit reports.",
        ),
        PlatformPhaseStatus(
            id="G",
            name="Observabilidad",
            status="pass" if observability.status == "local_observable" else "fail",
            evidence=observability.status,
        ),
        PlatformPhaseStatus(
            id="H",
            name="Integracion interna preparada",
            status="pass" if len(integrations) >= 6 else "fail",
            evidence=f"{len(integrations)} integration contracts.",
        ),
    ]

    local_ready = all(phase.status == "pass" for phase in phases)

    phases.append(
        PlatformPhaseStatus(
            id="I",
            name="Plataforma V1 funcional local",
            status="pass" if local_ready else "fail",
            evidence="All local V1 phases pass." if local_ready else "One or more phases failed.",
        )
    )

    return PlatformStatus(
        status="PLATFORM_V1_LOCAL_OPERATIONAL" if local_ready else "PLATFORM_V1_LOCAL_DEGRADED",
        phases=phases,
        local_ready=local_ready,
        external_apps_connected=False,
    )
