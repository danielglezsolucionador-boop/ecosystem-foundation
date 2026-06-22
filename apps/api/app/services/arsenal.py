from datetime import UTC, datetime
import json
import re
from uuid import uuid4

from app.core.config import get_settings
from app.core.database import connect, initialize_database, sql_placeholder
from app.core.safe_data import safe_payload
from app.schemas.arsenal import (
    ArsenalAuditStatus,
    ArsenalBrokerCapability,
    ArsenalBrokerOffice,
    ArsenalBrokerRequest,
    ArsenalBrokerResponse,
    ArsenalBrokerStatus,
    ArsenalCatalogItem,
    ArsenalCatalogItemCreate,
    ArsenalCatalogItemEvaluateRequest,
    ArsenalCatalogItemStatus,
    ArsenalCategory,
    ArsenalLinkedInOAuthStartResponse,
    ArsenalLinkedInPostRequest,
    ArsenalLinkedInPostResponse,
    ArsenalLinkedInStatus,
    ArsenalOffice,
    ArsenalPermissionRule,
    ArsenalReadiness,
    ArsenalResource,
    ArsenalResourceCreate,
    ArsenalResourceStatus,
    ArsenalResourceType,
    ArsenalRisk,
    ArsenalRiskCreate,
    ArsenalStatus,
)
from app.schemas.audit import AuditCategory, AuditEventCreate, AuditSeverity
from app.schemas.auth import AuthenticatedUser
from app.schemas.cerebro import CerebroTaskCreate
from app.schemas.revenue import RevenueOpportunityCreate
from app.services.audit import create_audit_event
from app.services.cerebro import create_cerebro_task
from app.services.revenue import create_opportunity

ARSENAL_CATALOG_TABLE = "arsenal_catalog_items"
ARSENAL_RISKS_TABLE = "arsenal_risks"
ARSENAL_RESOURCES_TABLE = "arsenal_core_resources"
MANAGED_CORE_RESOURCE_IDS = {"arsenal-tool-header-csp-auditor"}

SECRET_VALUE_PATTERN = re.compile(r"sk-[A-Za-z0-9_-]{8,}")
SECRET_KEYS = {
    "api_key",
    "apikey",
    "secret",
    "secret_value",
    "client_secret",
    "token",
    "password",
    "credential",
    "credentials",
    "private_key",
}
ALLOWED_SECRET_FLAG_KEYS = {"requires_secret", "secrets_stored"}

CATEGORIES = [
    ("apis_internas", "APIs internas", "Capacidades API para uso interno del ecosistema."),
    ("apis_vendibles", "APIs vendibles", "APIs que podrian convertirse en producto tecnico vendible."),
    ("skills_internas", "Skills internas", "Skills para productividad y operacion interna."),
    ("skills_vendibles", "Skills vendibles", "Skills empaquetables para venta futura."),
    ("modelos_ia", "Modelos IA", "Modelos, evaluaciones y configuraciones de IA."),
    ("conectores", "Conectores", "Puentes preparados hacia sistemas o servicios, sin conexion real."),
    ("automatizaciones", "Automatizaciones", "Flujos internos repetibles sin runtime externo."),
    ("prompts_sistemas", "Prompts/sistemas", "Prompts, instrucciones y sistemas reutilizables."),
    ("herramientas_contenido", "Herramientas de contenido", "Soporte a PLUMA y LENTE."),
    ("herramientas_marketing", "Herramientas de marketing", "Soporte a demanda, leads y embudos."),
    ("herramientas_ecommerce", "Herramientas de ecommerce", "Soporte a e-commerce y Sniff Amazon."),
    ("herramientas_ciberseguridad", "Herramientas de ciberseguridad", "Capacidades defensivas para SENTINELA futura."),
    ("herramientas_contables_tributarias", "Herramientas contables/tributarias", "Capacidades preparadas para DCFT, sin SUNAT real."),
    ("herramientas_cloud", "Herramientas cloud", "Capacidades de control cloud para NUBE."),
    ("herramientas_investigacion", "Herramientas de investigacion", "Buscador de tendencias e investigacion."),
    ("experimentos", "Experimentos", "Ideas y pruebas preparadas sin runtime."),
]

BROKER_PERMISSIONS = {
    ArsenalBrokerOffice.pluma: {
        ArsenalBrokerCapability.redaccion,
        ArsenalBrokerCapability.narrativa,
        ArsenalBrokerCapability.posts,
        ArsenalBrokerCapability.articulos,
    },
    ArsenalBrokerOffice.marca_personal: {
        ArsenalBrokerCapability.calendario,
        ArsenalBrokerCapability.adaptacion_posts,
        ArsenalBrokerCapability.posts,
        ArsenalBrokerCapability.linkedin_publicacion,
    },
    ArsenalBrokerOffice.centinela: {
        ArsenalBrokerCapability.riesgo,
        ArsenalBrokerCapability.alerta,
        ArsenalBrokerCapability.defensa,
    },
    ArsenalBrokerOffice.auditoria: {
        ArsenalBrokerCapability.resumen,
        ArsenalBrokerCapability.evidencias,
        ArsenalBrokerCapability.trazabilidad,
        ArsenalBrokerCapability.registro,
    },
    ArsenalBrokerOffice.cerebro: set(ArsenalBrokerCapability),
}

DEFENSIVE_RESOURCE_CATEGORIES = {
    "herramientas_ciberseguridad",
    "ciberseguridad",
    "defensivo",
    "defensive",
    "security",
}
EDITORIAL_RESOURCE_CATEGORIES = {
    "herramientas_contenido",
    "contenido",
    "editorial",
    "publishing",
    "marketing",
}
OBSOLETE_RESOURCE_STATUSES = {
    ArsenalResourceStatus.deprecated,
    ArsenalResourceStatus.replaced,
    ArsenalResourceStatus.disabled,
}

INITIAL_CORE_RESOURCES: list[dict[str, object]] = [
    {
        "id": "arsenal-provider-openai-api",
        "name": "OpenAI API provider",
        "type": ArsenalResourceType.provider,
        "category": "modelos_ia",
        "version": "placeholder-v1",
        "status": ArsenalResourceStatus.testing,
        "owner_office": ArsenalOffice.cerebro,
        "allowed_offices": [ArsenalOffice.cerebro, ArsenalOffice.forja, ArsenalOffice.auditoria],
        "location": "provider://openai",
        "runtime": "external_provider_pending_activation",
        "description": "Proveedor de modelos IA preparado como metadata interna, sin credenciales reales.",
        "input_schema": {"kind": "metadata_only"},
        "output_schema": {"kind": "metadata_only"},
        "replaces": None,
        "notes": "No guarda llaves reales. Activacion requiere canal seguro y aprobacion CEO.",
        "available_for_sombra": False,
        "readiness": "pending_secret",
    },
    {
        "id": "arsenal-integration-linkedin-oauth",
        "name": "LinkedIn OAuth connector",
        "type": ArsenalResourceType.integration,
        "category": "conectores",
        "version": "placeholder-v1",
        "status": ArsenalResourceStatus.testing,
        "owner_office": ArsenalOffice.forja,
        "allowed_offices": [
            ArsenalOffice.cerebro,
            ArsenalOffice.forja,
            ArsenalOffice.pluma,
            ArsenalOffice.marca_personal,
            ArsenalOffice.auditoria,
        ],
        "location": "connector://linkedin/oauth",
        "runtime": "oauth_connector_pending_credentials",
        "description": "Conector OAuth de LinkedIn preparado sin client id, client secret ni tokens.",
        "input_schema": {"kind": "oauth_metadata_only"},
        "output_schema": {"kind": "draft_or_auth_url_metadata"},
        "replaces": None,
        "notes": "Credenciales pendientes por canal seguro; publicacion real deshabilitada.",
        "available_for_sombra": False,
        "readiness": "pending_credentials",
    },
    {
        "id": "arsenal-tool-header-csp-auditor",
        "name": "Header/CSP Auditor",
        "type": ArsenalResourceType.tool,
        "category": "herramientas_ciberseguridad",
        "version": "1.0.0",
        "status": ArsenalResourceStatus.active,
        "owner_office": ArsenalOffice.centinela,
        "allowed_offices": [
            ArsenalOffice.cerebro,
            ArsenalOffice.sombra,
            ArsenalOffice.centinela,
            ArsenalOffice.auditoria,
        ],
        "location": "/api/v1/arsenal/tools/header-csp-auditor/analyze",
        "runtime": "internal_defensive_http_header_auditor",
        "description": "Auditor defensivo operativo para revisar headers HTTP, CSP, HSTS, framing, MIME, Referrer-Policy, Permissions-Policy y CORS basico dentro de scope autorizado.",
        "input_schema": {
            "url": "http_or_https_without_query",
            "requesting_office": "CEREBRO|SOMBRA|CENTINELA|AUDITORIA",
            "mode": "localhost|own_domain|authorized_scope",
            "authorization_reference": "required_for_non_localhost",
            "event_metadata": "optional_typed_event_metadata",
        },
        "output_schema": {
            "json_output": "object",
            "markdown_output": "string",
            "findings": "list",
            "classification": "defensivo|pendiente_evidencia|descartado|potencial_revision",
        },
        "replaces": None,
        "notes": "Herramienta activa con proteccion SSRF, sin credenciales, sin explotacion, sin publicacion y con auditoria de cada uso.",
        "available_for_sombra": True,
        "readiness": "operational_defensive",
    },
    {
        "id": "arsenal-tool-report-normalizer",
        "name": "Report Normalizer",
        "type": ArsenalResourceType.tool,
        "category": "herramientas_contenido",
        "version": "planned-v1",
        "status": ArsenalResourceStatus.testing,
        "owner_office": ArsenalOffice.pluma,
        "allowed_offices": [
            ArsenalOffice.cerebro,
            ArsenalOffice.pluma,
            ArsenalOffice.marca_personal,
            ArsenalOffice.auditoria,
        ],
        "location": "internal://arsenal/tools/report-normalizer",
        "runtime": "planned_internal_tool",
        "description": "Normalizador de reportes preparado para convertir hallazgos tecnicos en entregables.",
        "input_schema": {"report": "object"},
        "output_schema": {"normalized_report": "object"},
        "replaces": None,
        "notes": "Uso editorial y documental. Sin secretos ni publicacion automatica.",
        "available_for_sombra": False,
        "readiness": "planned",
    },
    {
        "id": "arsenal-toolbelt-sombra",
        "name": "Sombra Toolbelt",
        "type": ArsenalResourceType.tool,
        "category": "herramientas_ciberseguridad",
        "version": "external-v1",
        "status": ArsenalResourceStatus.active,
        "owner_office": ArsenalOffice.sombra,
        "allowed_offices": [
            ArsenalOffice.cerebro,
            ArsenalOffice.sombra,
            ArsenalOffice.centinela,
            ArsenalOffice.auditoria,
        ],
        "location": "external://sombra/toolbelt",
        "runtime": "external_registered_metadata_only",
        "description": "Registro externo del conjunto de herramientas disponible para SOMBRA.",
        "input_schema": {"tool_request": "object"},
        "output_schema": {"tool_result_metadata": "object"},
        "replaces": None,
        "notes": "ARSENAL solo registra metadata; no toca runtime de SOMBRA.",
        "available_for_sombra": True,
        "readiness": "external_registered",
    },
    {
        "id": "arsenal-module-centinela-defensive-rules",
        "name": "Centinela Defensive Rules",
        "type": ArsenalResourceType.module,
        "category": "herramientas_ciberseguridad",
        "version": "planned-v1",
        "status": ArsenalResourceStatus.testing,
        "owner_office": ArsenalOffice.centinela,
        "allowed_offices": [
            ArsenalOffice.cerebro,
            ArsenalOffice.centinela,
            ArsenalOffice.auditoria,
        ],
        "location": "internal://arsenal/modules/centinela-defensive-rules",
        "runtime": "planned_internal_module",
        "description": "Reglas defensivas planificadas para CENTINELA.",
        "input_schema": {"event": "object"},
        "output_schema": {"decision": "object"},
        "replaces": None,
        "notes": "Modulo defensivo preparado. Sin integracion externa activa.",
        "available_for_sombra": False,
        "readiness": "planned",
    },
]


class ArsenalError(Exception):
    def __init__(self, status_code: int, detail: dict[str, object]) -> None:
        self.status_code = status_code
        self.detail = detail
        super().__init__(str(detail))


def utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def normalize(value: object) -> str:
    return str(value or "").strip().lower().replace(" ", "_").replace("-", "_").replace("/", "_")


def actor_name(user: AuthenticatedUser) -> str:
    return user.email or user.name or user.id


def ensure_arsenal_schema() -> None:
    initialize_database()
    with connect() as connection:
        for table_name in [ARSENAL_CATALOG_TABLE, ARSENAL_RISKS_TABLE, ARSENAL_RESOURCES_TABLE]:
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
    seed_initial_core_resources()


def seed_initial_core_resources() -> None:
    placeholder = sql_placeholder()
    now = utc_now()
    created: list[ArsenalResource] = []
    updated: list[ArsenalResource] = []
    with connect() as connection:
        for seed in INITIAL_CORE_RESOURCES:
            row = connection.execute(
                f"SELECT payload_json FROM {ARSENAL_RESOURCES_TABLE} WHERE id = {placeholder}",
                (seed["id"],),
            ).fetchone()
            if row:
                if seed["id"] in MANAGED_CORE_RESOURCE_IDS:
                    payload = safe_payload(row)
                    if payload is not None:
                        existing = ArsenalResource(**payload)
                        desired = ArsenalResourceCreate(**seed)
                        desired_payload = desired.model_dump(mode="json")
                        current_payload = {
                            key: getattr(existing, key)
                            for key in desired_payload
                        }
                        current_payload = {
                            key: (
                                value.value
                                if hasattr(value, "value")
                                else [
                                    item.value if hasattr(item, "value") else item
                                    for item in value
                                ]
                                if isinstance(value, list)
                                else value
                            )
                            for key, value in current_payload.items()
                        }
                        if current_payload != desired_payload:
                            promoted = ArsenalResource(
                                **{
                                    **desired_payload,
                                    "id": existing.id,
                                    "replaced_by": existing.replaced_by,
                                    "created_at": existing.created_at,
                                    "updated_at": now,
                                    "external_connection_enabled": False,
                                    "runtime_connected": False,
                                    "secrets_stored": False,
                                    "audit_event_ids": list(existing.audit_event_ids),
                                }
                            )
                            connection.execute(
                                f"""
                                UPDATE {ARSENAL_RESOURCES_TABLE}
                                SET payload_json = {placeholder}, updated_at = {placeholder}
                                WHERE id = {placeholder}
                                """,
                                (promoted.model_dump_json(), now, promoted.id),
                            )
                            updated.append(promoted)
                continue
            resource = ArsenalResource(
                **seed,
                created_at=now,
                updated_at=now,
                audit_event_ids=[],
            )
            connection.execute(
                f"""
                INSERT INTO {ARSENAL_RESOURCES_TABLE} (id, payload_json, created_at, updated_at)
                VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder})
                """,
                (resource.id, resource.model_dump_json(), resource.created_at, resource.updated_at),
            )
            created.append(resource)
        connection.commit()

    for resource in updated:
        event_id = audit_arsenal_action(
            actor=None,
            action="resource_promoted",
            status=resource.status.value,
            detail="ARSENAL CORE promoted Header/CSP Auditor to an operational defensive tool.",
            metadata={
                "resource_id": resource.id,
                "resource_name": resource.name,
                "version": resource.version,
                "readiness": resource.readiness,
                "available_for_sombra": resource.available_for_sombra,
            },
        )
        resource.audit_event_ids.append(event_id)
        _save_resource(resource)

    for resource in created:
        event_id = audit_arsenal_action(
            actor=None,
            action="resource_created",
            status=resource.status.value,
            detail="ARSENAL CORE seeded placeholder resource metadata without secrets.",
            metadata={
                "resource_id": resource.id,
                "resource_name": resource.name,
                "resource_type": resource.type.value,
                "version": resource.version,
                "readiness": resource.readiness,
                "available_for_sombra": resource.available_for_sombra,
            },
        )
        resource.audit_event_ids.append(event_id)
        _save_resource(resource)


def insert_payload(table_name: str, item_id: str, payload: str) -> None:
    ensure_arsenal_schema()
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
    ensure_arsenal_schema()
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
    ensure_arsenal_schema()
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


def fetch_payload(table_name: str, item_id: str) -> dict | None:
    ensure_arsenal_schema()
    placeholder = sql_placeholder()
    with connect() as connection:
        row = connection.execute(
            f"SELECT payload_json FROM {table_name} WHERE id = {placeholder}",
            (item_id,),
        ).fetchone()
    return safe_payload(row) if row else None


def audit_arsenal_action(
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
            source="arsenal.blueprint",
            action=action,
            status=status,
            detail=detail,
            metadata={
                "actor": actor_name(actor) if actor else "system",
                "external_connection_enabled": False,
                "runtime_connected": False,
                "payment_connected": False,
                "secrets_stored": False,
                **(metadata or {}),
            },
        )
    )
    return event.id


def contains_secret_payload(value: object, path: str = "payload") -> str | None:
    if isinstance(value, dict):
        for key, nested in value.items():
            normalized_key = normalize(key)
            if normalized_key in SECRET_KEYS and normalized_key not in ALLOWED_SECRET_FLAG_KEYS:
                return f"{path}.{key}"
            nested_finding = contains_secret_payload(nested, f"{path}.{key}")
            if nested_finding:
                return nested_finding
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            nested_finding = contains_secret_payload(nested, f"{path}[{index}]")
            if nested_finding:
                return nested_finding
    elif isinstance(value, str) and SECRET_VALUE_PATTERN.search(value):
        return path
    return None


def assert_no_secret_payload(payload: dict) -> None:
    finding = contains_secret_payload(payload)
    if finding:
        raise ArsenalError(
            400,
            {
                "error": "arsenal_secret_payload_rejected",
                "field": finding,
                "reason": "ARSENAL stores metadata only; do not send API keys, tokens, passwords or secrets.",
            },
        )


def build_resource_id(resource: ArsenalResourceCreate) -> str:
    if resource.id:
        return resource.id.strip()
    slug = re.sub(
        r"[^a-z0-9_]+",
        "_",
        normalize(f"{resource.name}_{resource.version}"),
    ).strip("_")
    return f"arsenal-resource-{slug[:140]}"


def coerce_resource_create(
    resource: ArsenalResourceCreate | dict[str, object],
) -> ArsenalResourceCreate:
    if isinstance(resource, ArsenalResourceCreate):
        return resource
    return ArsenalResourceCreate(**resource)


def coerce_office(office: ArsenalOffice | str) -> ArsenalOffice:
    if isinstance(office, ArsenalOffice):
        return office
    normalized = str(office or "").strip().upper().replace(" ", "_").replace("-", "_")
    try:
        return ArsenalOffice(normalized)
    except ValueError as exc:
        raise ArsenalError(
            400,
            {"error": "arsenal_unknown_office", "office": str(office)},
        ) from exc


def resource_matches_name(resource: ArsenalResource, resource_name: str) -> bool:
    normalized = normalize(resource_name)
    return resource.id == resource_name or normalize(resource.name) == normalized


def is_defensive_resource(resource: ArsenalResource) -> bool:
    category = normalize(resource.category)
    return (
        category in DEFENSIVE_RESOURCE_CATEGORIES
        or resource.owner_office == ArsenalOffice.centinela
        or "ciber" in category
        or "security" in category
        or "defens" in category
    )


def is_editorial_resource(resource: ArsenalResource) -> bool:
    category = normalize(resource.category)
    return (
        category in EDITORIAL_RESOURCE_CATEGORIES
        or resource.owner_office
        in {ArsenalOffice.pluma, ArsenalOffice.marca_personal}
        or "contenido" in category
        or "editor" in category
        or "marketing" in category
    )


def office_can_access_resource(
    office: ArsenalOffice,
    resource: ArsenalResource,
) -> bool:
    allowed = set(resource.allowed_offices)
    if office in {ArsenalOffice.cerebro, ArsenalOffice.auditoria, ArsenalOffice.ceo}:
        return True
    if office == ArsenalOffice.sombra:
        return resource.available_for_sombra and office in allowed
    if office == ArsenalOffice.centinela:
        return office in allowed and is_defensive_resource(resource)
    if office in {ArsenalOffice.pluma, ArsenalOffice.marca_personal}:
        return office in allowed and is_editorial_resource(resource)
    if office == ArsenalOffice.forja:
        return office in allowed or resource.owner_office == ArsenalOffice.forja
    return office in allowed


def _save_resource(resource: ArsenalResource) -> None:
    placeholder = sql_placeholder()
    with connect() as connection:
        connection.execute(
            f"""
            INSERT INTO {ARSENAL_RESOURCES_TABLE} (id, payload_json, created_at, updated_at)
            VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder})
            ON CONFLICT(id) DO UPDATE SET
                payload_json = excluded.payload_json,
                updated_at = excluded.updated_at
            """,
            (
                resource.id,
                resource.model_dump_json(),
                resource.created_at,
                resource.updated_at,
            ),
        )
        connection.commit()


def _resource_from_payload(payload: dict) -> ArsenalResource:
    return ArsenalResource(**payload)


def list_all_resources() -> list[ArsenalResource]:
    ensure_arsenal_schema()
    resources: list[ArsenalResource] = []
    for payload in fetch_payloads(ARSENAL_RESOURCES_TABLE):
        try:
            resources.append(_resource_from_payload(payload))
        except Exception:
            continue
    return resources


def get_resource(resource_id: str) -> ArsenalResource:
    payload = fetch_payload(ARSENAL_RESOURCES_TABLE, resource_id)
    if payload is None:
        raise ArsenalError(
            404,
            {"error": "arsenal_resource_not_found", "resource_id": resource_id},
        )
    return _resource_from_payload(payload)


def find_active_replacement(resource: ArsenalResource) -> ArsenalResource | None:
    for candidate in list_all_resources():
        if candidate.id == resource.id or candidate.status != ArsenalResourceStatus.active:
            continue
        if candidate.replaces == resource.id:
            return candidate
        if (
            normalize(candidate.name) == normalize(resource.name)
            and candidate.type == resource.type
        ):
            return candidate
    return None


def validate_resource_payload(resource: ArsenalResourceCreate) -> None:
    assert_no_secret_payload(resource.model_dump(mode="json"))
    if not resource.allowed_offices:
        raise ArsenalError(400, {"error": "arsenal_allowed_offices_required"})
    if (
        resource.available_for_sombra
        and ArsenalOffice.sombra not in set(resource.allowed_offices)
    ):
        raise ArsenalError(
            400,
            {
                "error": "arsenal_sombra_availability_mismatch",
                "reason": "available_for_sombra requires SOMBRA in allowed_offices.",
            },
        )


def register_resource(
    resource: ArsenalResourceCreate | dict[str, object],
    actor: AuthenticatedUser | None = None,
) -> ArsenalResource:
    request = coerce_resource_create(resource)
    validate_resource_payload(request)
    ensure_arsenal_schema()

    now = utc_now()
    resource_id = build_resource_id(request)
    existing: ArsenalResource | None = None
    try:
        existing = get_resource(resource_id)
    except ArsenalError as error:
        if error.status_code != 404:
            raise

    active_siblings = [
        item
        for item in list_all_resources()
        if item.id != resource_id
        and item.status == ArsenalResourceStatus.active
        and item.type == request.type
        and normalize(item.name) == normalize(request.name)
    ]
    if (
        active_siblings
        and not request.replaces
        and request.status == ArsenalResourceStatus.active
    ):
        raise ArsenalError(
            409,
            {
                "error": "arsenal_active_version_exists",
                "resource_name": request.name,
                "active_resource_id": active_siblings[0].id,
                "reason": (
                    "Use replace_resource to preserve version history and prevent "
                    "obsolete usage."
                ),
            },
        )

    if request.owner_office not in set(request.allowed_offices):
        request = request.model_copy(
            update={
                "allowed_offices": [
                    *request.allowed_offices,
                    request.owner_office,
                ]
            }
        )

    payload = request.model_dump(mode="json")
    payload["id"] = resource_id
    saved = ArsenalResource(
        **payload,
        replaced_by=existing.replaced_by if existing else None,
        created_at=existing.created_at if existing else now,
        updated_at=now,
        audit_event_ids=list(existing.audit_event_ids) if existing else [],
    )
    _save_resource(saved)

    if saved.replaces:
        old = get_resource(saved.replaces)
        old.status = ArsenalResourceStatus.replaced
        old.replaced_by = saved.id
        old.updated_at = now
        old.notes = f"{old.notes} Replaced by {saved.id}.".strip()
        old_event_id = audit_arsenal_action(
            actor=actor,
            action="resource_updated",
            status=old.status.value,
            detail="ARSENAL CORE marked an older resource version as replaced.",
            metadata={
                "resource_id": old.id,
                "replacement_id": saved.id,
                "resource_name": old.name,
                "version": old.version,
            },
        )
        replace_event_id = audit_arsenal_action(
            actor=actor,
            action="version_replaced",
            status=saved.status.value,
            detail=(
                "ARSENAL CORE registered a new active version and preserved "
                "the previous version."
            ),
            metadata={
                "old_resource_id": old.id,
                "new_resource_id": saved.id,
                "resource_name": saved.name,
                "old_version": old.version,
                "new_version": saved.version,
            },
        )
        old.audit_event_ids.extend([old_event_id, replace_event_id])
        saved.audit_event_ids.append(replace_event_id)
        _save_resource(old)

    event_id = audit_arsenal_action(
        actor=actor,
        action="resource_updated" if existing else "resource_created",
        status=saved.status.value,
        detail="ARSENAL CORE registered resource metadata without storing secrets.",
        metadata={
            "resource_id": saved.id,
            "resource_name": saved.name,
            "resource_type": saved.type.value,
            "version": saved.version,
            "owner_office": saved.owner_office.value,
            "allowed_offices": [
                office.value for office in saved.allowed_offices
            ],
            "available_for_sombra": saved.available_for_sombra,
        },
    )
    saved.audit_event_ids.append(event_id)
    _save_resource(saved)
    return saved


def replace_resource(
    old_id: str,
    new_resource: ArsenalResourceCreate | dict[str, object],
    actor: AuthenticatedUser | None = None,
) -> ArsenalResource:
    old = get_resource(old_id)
    request = coerce_resource_create(new_resource).model_copy(
        update={
            "status": ArsenalResourceStatus.active,
            "replaces": old.id,
        }
    )
    return register_resource(request, actor)


def disable_resource(
    resource_id: str,
    actor: AuthenticatedUser | None = None,
) -> ArsenalResource:
    resource = get_resource(resource_id)
    resource.status = ArsenalResourceStatus.disabled
    resource.updated_at = utc_now()
    event_id = audit_arsenal_action(
        actor=actor,
        action="resource_updated",
        status=resource.status.value,
        detail="ARSENAL CORE disabled a resource.",
        severity=AuditSeverity.medium,
        metadata={
            "resource_id": resource.id,
            "resource_name": resource.name,
            "version": resource.version,
        },
    )
    resource.audit_event_ids.append(event_id)
    _save_resource(resource)
    audit_arsenal_action(
        actor=actor,
        action="resource_disabled",
        status=resource.status.value,
        detail="ARSENAL CORE resource disabled and unavailable for office usage.",
        severity=AuditSeverity.medium,
        metadata={"resource_id": resource.id, "resource_name": resource.name},
    )
    return resource


def list_resources_for_office(
    office: ArsenalOffice | str,
    *,
    include_obsolete: bool = False,
    actor: AuthenticatedUser | None = None,
) -> list[ArsenalResource]:
    target_office = coerce_office(office)
    resources = [
        resource
        for resource in list_all_resources()
        if office_can_access_resource(target_office, resource)
    ]
    if not include_obsolete:
        resources = [
            resource
            for resource in resources
            if resource.status not in OBSOLETE_RESOURCE_STATUSES
        ]
    audit_arsenal_action(
        actor=actor,
        action="resource_consulted_by_office",
        status="listed",
        detail=f"ARSENAL CORE resources consulted by {target_office.value}.",
        metadata={
            "office": target_office.value,
            "resource_count": len(resources),
            "include_obsolete": include_obsolete,
        },
    )
    return resources


def get_resource_for_office(
    office: ArsenalOffice | str,
    resource_name: str,
    actor: AuthenticatedUser | None = None,
) -> ArsenalResource:
    target_office = coerce_office(office)
    matches = [
        resource
        for resource in list_all_resources()
        if resource_matches_name(resource, resource_name)
    ]
    if not matches:
        raise ArsenalError(
            404,
            {"error": "arsenal_resource_not_found", "resource_name": resource_name},
        )

    accessible = [
        resource
        for resource in matches
        if office_can_access_resource(target_office, resource)
    ]
    if not accessible:
        raise ArsenalError(
            403,
            {
                "error": "arsenal_resource_not_authorized_for_office",
                "office": target_office.value,
                "resource_name": resource_name,
            },
        )

    exact = next(
        (resource for resource in accessible if resource.id == resource_name),
        None,
    )
    if exact and exact.status in OBSOLETE_RESOURCE_STATUSES:
        replacement = find_active_replacement(exact)
        raise ArsenalError(
            409,
            {
                "error": "arsenal_resource_obsolete",
                "resource_id": exact.id,
                "status": exact.status.value,
                "active_resource_id": replacement.id if replacement else None,
                "reason": (
                    "CEREBRO and SOMBRA must not use obsolete ARSENAL resources."
                ),
            },
        )

    usable = [
        resource
        for resource in accessible
        if resource.status not in OBSOLETE_RESOURCE_STATUSES
    ]
    if not usable:
        raise ArsenalError(
            409,
            {
                "error": "arsenal_resource_not_usable",
                "office": target_office.value,
                "resource_name": resource_name,
            },
        )

    usable.sort(
        key=lambda item: (
            item.status != ArsenalResourceStatus.active,
            item.updated_at,
        )
    )
    selected = next(
        (
            item
            for item in usable
            if item.status == ArsenalResourceStatus.active
        ),
        usable[0],
    )
    audit_arsenal_action(
        actor=actor,
        action="resource_consulted_by_office",
        status=selected.status.value,
        detail=f"ARSENAL CORE resource consulted by {target_office.value}.",
        metadata={
            "office": target_office.value,
            "resource_id": selected.id,
            "resource_name": selected.name,
            "version": selected.version,
            "available_for_sombra": selected.available_for_sombra,
        },
    )
    return selected


def list_resources(
    *,
    name: str | None = None,
    resource_type: ArsenalResourceType | str | None = None,
    office: ArsenalOffice | str | None = None,
    category: str | None = None,
    status: ArsenalResourceStatus | str | None = None,
    active_only: bool = False,
    actor: AuthenticatedUser | None = None,
) -> list[ArsenalResource]:
    include_obsolete = status is not None
    resources = (
        list_resources_for_office(
            office,
            include_obsolete=include_obsolete,
            actor=actor,
        )
        if office
        else list_all_resources()
    )
    if name:
        normalized_name = normalize(name)
        resources = [
            resource
            for resource in resources
            if resource.id == name or normalize(resource.name) == normalized_name
        ]
    if resource_type:
        target_type = (
            resource_type
            if isinstance(resource_type, ArsenalResourceType)
            else ArsenalResourceType(str(resource_type).upper())
        )
        resources = [
            resource for resource in resources if resource.type == target_type
        ]
    if category:
        normalized_category = normalize(category)
        resources = [
            resource
            for resource in resources
            if normalize(resource.category) == normalized_category
        ]
    if status:
        target_status = (
            status
            if isinstance(status, ArsenalResourceStatus)
            else ArsenalResourceStatus(str(status).lower())
        )
        resources = [
            resource for resource in resources if resource.status == target_status
        ]
    if active_only:
        resources = [
            resource
            for resource in resources
            if resource.status == ArsenalResourceStatus.active
        ]
    return sorted(
        resources,
        key=lambda item: (normalize(item.name), item.version, item.id),
    )


def permission_rules() -> list[ArsenalPermissionRule]:
    return [
        ArsenalPermissionRule(
            action="view",
            allowed_roles=["ceo", "admin", "operator", "auditor"],
            notes="Lectura interna protegida del blueprint.",
        ),
        ArsenalPermissionRule(
            action="add_catalog_item",
            allowed_roles=["ceo", "admin", "operator"],
            notes="CEREBRO y operacion pueden registrar metadata, nunca secretos.",
        ),
        ArsenalPermissionRule(
            action="evaluate",
            allowed_roles=["ceo", "admin", "operator", "auditor"],
            notes="Evaluacion local preparada sin conectar APIs externas.",
        ),
        ArsenalPermissionRule(
            action="approve_cost_or_secret",
            allowed_roles=["ceo", "admin"],
            requires_ceo_approval=True,
            notes="Costo, credenciales o cuentas externas requieren CEO.",
        ),
        ArsenalPermissionRule(
            action="send_to_forja",
            allowed_roles=["ceo", "admin", "operator"],
            notes="FORJA recibe tarea preparada, no runtime externo.",
        ),
        ArsenalPermissionRule(
            action="mark_sellable",
            allowed_roles=["ceo", "admin", "operator"],
            requires_auditoria=True,
            notes="Vendible requiere revision de AUDITORIA antes de venta real.",
        ),
    ]


def list_catalog_items() -> list[ArsenalCatalogItem]:
    ensure_arsenal_schema()
    items: list[ArsenalCatalogItem] = []
    for payload in fetch_payloads(ARSENAL_CATALOG_TABLE):
        try:
            items.append(ArsenalCatalogItem(**payload))
        except Exception:
            continue
    return items


def get_catalog_item(item_id: str) -> ArsenalCatalogItem:
    payload = fetch_payload(ARSENAL_CATALOG_TABLE, item_id)
    if payload is None:
        raise ArsenalError(404, {"error": "arsenal_catalog_item_not_found", "item_id": item_id})
    return ArsenalCatalogItem(**payload)


def list_categories() -> list[ArsenalCategory]:
    items = list_catalog_items()
    rows: list[ArsenalCategory] = []
    for category_id, name, description in CATEGORIES:
        related = [
            item
            for item in items
            if normalize(item.category) == category_id or normalize(item.category) == normalize(name)
        ]
        rows.append(
            ArsenalCategory(
                id=category_id,
                name=name,
                description=description,
                status="prepared" if related else "empty/prepared",
                items=len(related),
                sellable_items=len([item for item in related if item.is_sellable]),
            )
        )
    return rows


def status_for_item(request: ArsenalCatalogItemCreate) -> ArsenalCatalogItemStatus:
    if request.status is not None:
        return request.status
    if request.cost_usd > 0 or request.requires_secret:
        return ArsenalCatalogItemStatus.needs_ceo_approval
    if request.is_sellable:
        return ArsenalCatalogItemStatus.needs_audit
    return ArsenalCatalogItemStatus.prepared


def audit_status_for_item(request: ArsenalCatalogItemCreate) -> ArsenalAuditStatus:
    if request.is_sellable:
        return ArsenalAuditStatus.requires_auditoria
    return ArsenalAuditStatus.pending if request.requires_external_api else ArsenalAuditStatus.not_required


def create_catalog_item(
    request: ArsenalCatalogItemCreate,
    actor: AuthenticatedUser,
) -> ArsenalCatalogItem:
    assert_no_secret_payload(request.model_dump(mode="json"))
    now = utc_now()
    requires_ceo = request.cost_usd > 0 or request.requires_secret
    item = ArsenalCatalogItem(
        id=f"arsenal_item_{uuid4()}",
        name=request.name,
        item_type=request.item_type,
        category=request.category,
        internal_use=request.internal_use,
        sellable_use=request.sellable_use,
        is_sellable=request.is_sellable,
        cost_usd=request.cost_usd,
        requires_secret=request.requires_secret,
        requires_external_api=request.requires_external_api,
        requires_ceo_approval=requires_ceo,
        requires_auditoria=request.is_sellable,
        status=status_for_item(request),
        risk=request.risk,
        monetization=request.monetization,
        owner=request.owner,
        audit_status=audit_status_for_item(request),
        metadata=request.metadata,
        created_at=now,
        updated_at=now,
    )
    insert_payload(ARSENAL_CATALOG_TABLE, item.id, item.model_dump_json())
    audit_arsenal_action(
        actor=actor,
        action="create_catalog_item",
        status=item.status.value,
        detail="ARSENAL registered metadata for a capability without storing secrets.",
        metadata={
            "item_id": item.id,
            "category": item.category,
            "requires_ceo_approval": item.requires_ceo_approval,
            "requires_auditoria": item.requires_auditoria,
        },
    )
    return item


def evaluate_catalog_item(
    item_id: str,
    request: ArsenalCatalogItemEvaluateRequest,
    actor: AuthenticatedUser,
) -> ArsenalCatalogItem:
    assert_no_secret_payload(request.model_dump(mode="json"))
    item = get_catalog_item(item_id)
    item.risk = request.risk or item.risk
    item.monetization = request.monetization or item.monetization
    item.audit_status = request.audit_status or item.audit_status
    item.technical_status = request.technical_status or "blueprint_evaluated"
    if item.audit_status == ArsenalAuditStatus.requires_auditoria:
        item.requires_auditoria = True
    if item.cost_usd > 0 or item.requires_secret:
        item.requires_ceo_approval = True
        item.status = ArsenalCatalogItemStatus.needs_ceo_approval
    elif item.requires_auditoria:
        item.status = ArsenalCatalogItemStatus.needs_audit
    else:
        item.status = ArsenalCatalogItemStatus.evaluated

    if request.evaluate_revenue_os or (item.is_sellable and request.expected_revenue_usd is not None):
        revenue = create_opportunity(
            RevenueOpportunityCreate(
                title=f"ARSENAL: {item.name}",
                origin="ARSENAL",
                department="CREADOR DE APIS Y SKILLS",
                related_product=item.name,
                action_type="organic" if item.cost_usd == 0 else "paid_api",
                investment_usd=item.cost_usd,
                expected_revenue_usd=request.expected_revenue_usd,
                probability_percent=request.probability_percent,
                risk=item.risk,
                payback_time="not_estimated",
                ecommerce_separate=False,
                recommendation=item.monetization,
            ),
            actor,
        )
        item.revenue_opportunity_id = revenue.id

    if request.send_to_forja:
        task = create_cerebro_task(
            CerebroTaskCreate(
                title=f"Preparar capacidad ARSENAL: {item.name}",
                description=f"FORJA recibe blueprint preparado para {item.name}; sin runtime externo.",
                destination="forja",
                priority="p1" if item.is_sellable else "p2",
                reason="Tarea preparada desde ARSENAL blueprint.",
                requires_ceo_approval=item.requires_ceo_approval,
            ),
            actor,
        )
        item.forja_task_id = task.id

    item.updated_at = utc_now()
    update_payload(ARSENAL_CATALOG_TABLE, item.id, item.model_dump_json())
    audit_arsenal_action(
        actor=actor,
        action="evaluate_catalog_item",
        status=item.status.value,
        detail="ARSENAL evaluated a capability blueprint without external connection.",
        metadata={
            "item_id": item.id,
            "revenue_opportunity_id": item.revenue_opportunity_id,
            "forja_task_id": item.forja_task_id,
        },
    )
    return item


def send_catalog_item_to_forja(item_id: str, actor: AuthenticatedUser) -> dict[str, object]:
    item = get_catalog_item(item_id)
    task = create_cerebro_task(
        CerebroTaskCreate(
            title=f"Preparar capacidad ARSENAL: {item.name}",
            description=f"FORJA recibe blueprint preparado para {item.name}; sin runtime externo.",
            destination="forja",
            priority="p1" if item.is_sellable else "p2",
            reason="Tarea preparada desde ARSENAL blueprint.",
            requires_ceo_approval=item.requires_ceo_approval,
        ),
        actor,
    )
    item.forja_task_id = task.id
    item.updated_at = utc_now()
    update_payload(ARSENAL_CATALOG_TABLE, item.id, item.model_dump_json())
    audit_arsenal_action(
        actor=actor,
        action="send_catalog_item_to_forja",
        status="prepared",
        detail="ARSENAL sent a prepared task to FORJA without touching external FORJA runtime.",
        metadata={"item_id": item.id, "task_id": task.id},
    )
    return {
        "status": "forja_task_prepared",
        "item_id": item.id,
        "task_id": task.id,
        "destination": task.destination,
        "runtime_connected": False,
        "external_connection_enabled": False,
    }


def list_risks() -> list[ArsenalRisk]:
    ensure_arsenal_schema()
    return [
        ArsenalRisk(**payload)
        for payload in fetch_payloads(ARSENAL_RISKS_TABLE)
    ]


def create_risk(request: ArsenalRiskCreate, actor: AuthenticatedUser) -> ArsenalRisk:
    assert_no_secret_payload(request.model_dump(mode="json"))
    now = utc_now()
    risk = ArsenalRisk(
        id=f"arsenal_risk_{uuid4()}",
        title=request.title,
        category=request.category,
        severity=request.severity,
        detail=request.detail,
        mitigation=request.mitigation,
        related_item_id=request.related_item_id,
        created_at=now,
        updated_at=now,
    )
    insert_payload(ARSENAL_RISKS_TABLE, risk.id, risk.model_dump_json())
    audit_arsenal_action(
        actor=actor,
        action="create_risk",
        status=risk.status,
        detail="ARSENAL registered a blueprint risk.",
        severity=AuditSeverity.medium if risk.severity in {"high", "critical"} else AuditSeverity.info,
        metadata={"risk_id": risk.id, "category": risk.category},
    )
    return risk


def get_readiness() -> ArsenalReadiness:
    items = list_catalog_items()
    risks = list_risks()
    blockers: list[str] = []
    next_steps = [
        "Completar catalogo inicial sin secretos.",
        "Auditar items vendibles antes de vender.",
        "Pedir CEO si hay costo, credenciales o cuenta externa.",
        "Conectar Revenue OS solo como evaluacion de monetizacion.",
    ]
    cost_or_secret = [item for item in items if item.requires_ceo_approval]
    sellable = [item for item in items if item.is_sellable]
    if not items:
        blockers.append("catalog_empty")
    if any(risk.severity in {"high", "critical"} and risk.status == "open" for risk in risks):
        blockers.append("high_risk_open")
    if cost_or_secret:
        blockers.append("ceo_approval_required_for_cost_or_secret")
    if any(item.audit_status == ArsenalAuditStatus.requires_auditoria for item in sellable):
        blockers.append("auditoria_required_for_sellable_items")
    score = 60
    if items:
        score += 15
    if sellable:
        score += 10
    if risks:
        score += 5
    score -= min(len(blockers) * 8, 35)
    score = max(0, min(100, score))
    return ArsenalReadiness(
        status="blueprint_ready_for_review" if items else "blueprint_empty_prepared",
        score=score,
        ready_for_build=bool(items) and not blockers,
        blockers=blockers,
        next_steps=next_steps,
        categories_total=len(CATEGORIES),
        catalog_items=len(items),
        sellable_items=len(sellable),
        items_requiring_ceo_approval=len(cost_or_secret),
        risks_open=len([risk for risk in risks if risk.status == "open"]),
    )


def broker_provider_credentials() -> dict[str, bool]:
    settings = get_settings()
    return {
        "openrouter": bool(settings.openrouter_api_key),
        "anthropic": bool(settings.anthropic_api_key),
        "openai": bool(settings.openai_api_key),
    }


def broker_permission_payload() -> dict[str, list[str]]:
    return {
        office.value: sorted(capability.value for capability in capabilities)
        for office, capabilities in BROKER_PERMISSIONS.items()
    }


def get_broker_status() -> ArsenalBrokerStatus:
    settings = get_settings()
    return ArsenalBrokerStatus(
        status="integrated_prepared_pending_credentials",
        mode="central_api_broker_prepared_no_external_execution",
        default_provider=settings.arsenal_default_provider,
        default_model=settings.arsenal_default_model,
        execution_enabled=False,
        providers_configured=broker_provider_credentials(),
        permissions=broker_permission_payload(),
        offices=[office.value for office in ArsenalBrokerOffice],
        generated_at=utc_now(),
    )


def require_broker_permission(
    office: ArsenalBrokerOffice,
    capability: ArsenalBrokerCapability,
) -> None:
    allowed = BROKER_PERMISSIONS.get(office, set())
    if capability not in allowed:
        raise ArsenalError(
            403,
            {
                "error": "arsenal_broker_permission_denied",
                "office": office.value,
                "capability": capability.value,
            },
        )


def run_broker_request(
    request: ArsenalBrokerRequest,
    actor: AuthenticatedUser,
) -> ArsenalBrokerResponse:
    assert_no_secret_payload(request.model_dump(mode="json"))
    require_broker_permission(request.office, request.capability)
    settings = get_settings()
    provider = request.provider or settings.arsenal_default_provider
    model = request.model or settings.arsenal_default_model
    provider_ready = broker_provider_credentials().get(normalize(provider), False)
    status = (
        "prepared_pending_activation"
        if provider_ready
        else "prepared_pending_provider_credentials"
    )
    audit_event_id = audit_arsenal_action(
        actor=actor,
        action="api_broker_request_prepared",
        status=status,
        detail=(
            "ARSENAL/API Broker validated and audited an internal request in "
            "preparation mode; no external provider call was executed."
        ),
        metadata={
            "office": request.office.value,
            "capability": request.capability.value,
            "provider": provider,
            "model": model,
            "prompt_length": len(request.prompt),
            "provider_ready": provider_ready,
            "broker_execution_requested": settings.arsenal_api_broker_enabled,
            "external_call_executed": False,
        },
    )
    return ArsenalBrokerResponse(
        ok=True,
        status=status,
        office=request.office,
        capability=request.capability,
        provider=provider,
        model=model,
        result=(
            "ARSENAL/API Broker integrado y preparado. La solicitud fue validada "
            "por permisos, auditada y retenida sin llamada externa."
        ),
        cost_usd=0,
        audit_event_id=audit_event_id,
        generated_at=utc_now(),
    )


def linkedin_pending_credentials() -> list[str]:
    settings = get_settings()
    pending: list[str] = []
    if not settings.linkedin_client_id:
        pending.append("LINKEDIN_CLIENT_ID")
    if not settings.linkedin_client_secret:
        pending.append("LINKEDIN_CLIENT_SECRET")
    if not settings.linkedin_redirect_uri:
        pending.append("LINKEDIN_REDIRECT_URI")
    if not settings.linkedin_access_token:
        pending.append("LINKEDIN_ACCESS_TOKEN")
    if not settings.linkedin_person_urn:
        pending.append("LINKEDIN_PERSON_URN")
    return pending


def get_linkedin_status() -> ArsenalLinkedInStatus:
    settings = get_settings()
    pending = linkedin_pending_credentials()
    return ArsenalLinkedInStatus(
        status=(
            "prepared_pending_credentials"
            if pending
            else "prepared_pending_activation"
        ),
        client_configured=bool(
            settings.linkedin_client_id and settings.linkedin_client_secret
        ),
        redirect_configured=bool(settings.linkedin_redirect_uri),
        access_token_configured=bool(settings.linkedin_access_token),
        person_urn_configured=bool(settings.linkedin_person_urn),
        posting_requested=settings.linkedin_posting_enabled,
        posting_enabled=False,
        publication_allowed=False,
        pending_credentials=pending,
        generated_at=utc_now(),
    )


def build_linkedin_oauth_start() -> ArsenalLinkedInOAuthStartResponse:
    status = get_linkedin_status()
    return ArsenalLinkedInOAuthStartResponse(
        status=(
            "prepared_pending_credentials"
            if status.pending_credentials
            else "prepared_pending_activation"
        ),
        authorization_url=None,
        pending_credentials=status.pending_credentials,
        activation_required=True,
    )


def prepare_linkedin_post(
    request: ArsenalLinkedInPostRequest,
    actor: AuthenticatedUser,
) -> ArsenalLinkedInPostResponse:
    assert_no_secret_payload(request.model_dump(mode="json"))
    publish_blocked = request.publish_now
    result_status = (
        "blocked_publication_disabled"
        if publish_blocked
        else "draft_prepared_pending_ceo"
    )
    audit_event_id = audit_arsenal_action(
        actor=actor,
        action="linkedin_post_prepared",
        status=result_status,
        detail="ARSENAL prepared LinkedIn post metadata without publishing.",
        metadata={
            "content_length": len(request.content),
            "publish_now_requested": request.publish_now,
            "scheduled_for": request.scheduled_for,
            "publication_allowed": False,
            "external_call_executed": False,
        },
    )
    return ArsenalLinkedInPostResponse(
        ok=not publish_blocked,
        status=result_status,
        publication_allowed=False,
        publish_now_requested=request.publish_now,
        scheduled_for=request.scheduled_for,
        audit_event_id=audit_event_id,
        generated_at=utc_now(),
    )


def get_status() -> ArsenalStatus:
    categories = list_categories()
    items = list_catalog_items()
    risks = list_risks()
    readiness = get_readiness()
    return ArsenalStatus(
        status="arsenal_blueprint_governed_prepared",
        mode="metadata_only_no_external_runtime",
        purpose="Almacen estrategico de APIs, skills, modelos, conectores y capacidades.",
        categories=len(categories),
        catalog_items=len(items),
        sellable_items=len([item for item in items if item.is_sellable]),
        items_requiring_ceo_approval=len([item for item in items if item.requires_ceo_approval]),
        risks_open=len([risk for risk in risks if risk.status == "open"]),
        permissions=permission_rules(),
        readiness=readiness,
        generated_at=utc_now(),
    )
