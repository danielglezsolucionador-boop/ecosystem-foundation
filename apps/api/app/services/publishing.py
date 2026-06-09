from datetime import UTC, datetime
import json
from uuid import uuid4

from app.core.database import connect, initialize_database, sql_placeholder
from app.schemas.audit import AuditCategory, AuditEventCreate, AuditSeverity
from app.schemas.auth import AuthenticatedUser
from app.schemas.publishing import (
    PublishingAccountStatus,
    PublishingCalendarEntry,
    PublishingChannel,
    PublishingChannelCreate,
    PublishingContentCreate,
    PublishingContentItem,
    PublishingContentStatus,
    PublishingEvidenceStatus,
    PublishingGrowthMetric,
    PublishingGrowthMetricCreate,
    PublishingMarkPublishedRequest,
    PublishingMode,
    PublishingScheduleRequest,
    PublishingStatus,
)
from app.services.audit import create_audit_event

CONTENT_CAMPAIGNS_TABLE = "content_campaigns"
CONTENT_ITEMS_TABLE = "content_items"
PUBLISHING_CHANNELS_TABLE = "publishing_channels"
PUBLISHING_ACCOUNTS_TABLE = "publishing_accounts"
PUBLISHING_SCHEDULE_TABLE = "publishing_schedule"
PUBLISHING_EVENTS_TABLE = "publishing_events"
GROWTH_METRICS_TABLE = "growth_metrics"
CONTENT_APPROVALS_TABLE = "content_approvals"

PUBLISHING_TABLES = [
    CONTENT_CAMPAIGNS_TABLE,
    CONTENT_ITEMS_TABLE,
    PUBLISHING_CHANNELS_TABLE,
    PUBLISHING_ACCOUNTS_TABLE,
    PUBLISHING_SCHEDULE_TABLE,
    PUBLISHING_EVENTS_TABLE,
    GROWTH_METRICS_TABLE,
    CONTENT_APPROVALS_TABLE,
]

PAID_MODES = {
    PublishingMode.paid,
}


class PublishingError(Exception):
    def __init__(self, status_code: int, detail: dict[str, object]) -> None:
        self.status_code = status_code
        self.detail = detail
        super().__init__(str(detail))


def utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def normalize(value: object) -> str:
    return str(value or "").strip().lower().replace(" ", "_").replace("-", "_")


def safe_id(value: str, fallback: str) -> str:
    normalized = "".join(char if char.isalnum() else "_" for char in normalize(value))
    normalized = "_".join(part for part in normalized.split("_") if part)
    return normalized or fallback


def actor_name(user: AuthenticatedUser | None) -> str:
    if user is None:
        return "system"
    return user.email or user.name or user.id


def ensure_publishing_schema() -> None:
    initialize_database()
    with connect() as connection:
        for table_name in PUBLISHING_TABLES:
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


def upsert_payload(table_name: str, item_id: str, payload: str) -> None:
    placeholder = sql_placeholder()
    now = utc_now()
    with connect() as connection:
        connection.execute(
            f"""
            INSERT INTO {table_name} (id, payload_json, created_at, updated_at)
            VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder})
            ON CONFLICT(id) DO UPDATE SET
                payload_json = excluded.payload_json,
                updated_at = excluded.updated_at
            """,
            (item_id, payload, now, now),
        )
        connection.commit()


def fetch_payload(table_name: str, item_id: str) -> dict | None:
    ensure_publishing_schema()
    placeholder = sql_placeholder()
    with connect() as connection:
        row = connection.execute(
            f"SELECT payload_json FROM {table_name} WHERE id = {placeholder}",
            (item_id,),
        ).fetchone()
    if row is None:
        return None
    return json.loads(row[0])


def fetch_payloads(table_name: str) -> list[dict]:
    ensure_publishing_schema()
    with connect() as connection:
        rows = connection.execute(f"SELECT payload_json FROM {table_name}").fetchall()
    return [json.loads(row[0]) for row in rows]


def audit_publishing_action(
    *,
    actor: AuthenticatedUser | None,
    action: str,
    status: str,
    detail: str,
    metadata: dict[str, object] | None = None,
) -> None:
    create_audit_event(
        AuditEventCreate(
            category=AuditCategory.event,
            severity=AuditSeverity.info,
            source="publishing.growth_engine",
            action=action,
            status=status,
            detail=detail,
            metadata={
                "actor": actor_name(actor),
                "external_connection_enabled": False,
                "runtime_connected": False,
                "payment_connected": False,
                **(metadata or {}),
            },
        )
    )


def initial_channel_requests() -> list[PublishingChannelCreate]:
    return [
        PublishingChannelCreate(name="TikTok", platform="TikTok"),
        PublishingChannelCreate(name="Instagram", platform="Instagram"),
        PublishingChannelCreate(name="YouTube", platform="YouTube"),
        PublishingChannelCreate(name="YouTube Shorts", platform="YouTube"),
        PublishingChannelCreate(name="LinkedIn", platform="LinkedIn"),
        PublishingChannelCreate(name="X", platform="X"),
        PublishingChannelCreate(name="Facebook", platform="Facebook"),
        PublishingChannelCreate(name="Blog/Web", platform="Blog/Web"),
        PublishingChannelCreate(name="Newsletter", platform="Newsletter"),
    ]


def initial_content_requests() -> list[PublishingContentCreate]:
    return [
        PublishingContentCreate(
            title="Post autoridad CEO para validar demanda organica",
            format="post",
            department_owner="MARCA PERSONAL",
            channel="LinkedIn",
            niche="autoridad CEO IA",
            revenue_link="global_6000_usd",
            content_brief="Marca Personal prepara autoridad sin crear cuenta externa nueva.",
        ),
        PublishingContentCreate(
            title="Guion PLUMA sobre DCFT sin claims legales",
            format="script",
            department_owner="PLUMA",
            channel="Blog/Web",
            niche="contabilidad tributaria",
            revenue_link="dcft_marketing_prepared",
            content_brief="PLUMA prepara contenido comercial revisable; no declarar funcionalidad legal completa.",
        ),
        PublishingContentCreate(
            title="Short LENTE de tendencia IA pendiente de nicho final",
            format="short",
            department_owner="LENTE",
            channel="YouTube Shorts",
            niche=None,
            niche_status="needs_ceo_definition",
            revenue_link="trend_digital_products",
            content_brief="LENTE prepara visual sin fijar nicho infantil, cristiano, IA o tendencias sin definicion CEO.",
        ),
        PublishingContentCreate(
            title="Campana organica MARKETING para DCFT/SENTINELA",
            format="campaign_brief",
            department_owner="MARKETING",
            channel="Instagram",
            niche="producto preparado",
            revenue_link="global_6000_usd",
            content_brief="Marketing prepara validacion organica; no pago real ni cuenta nueva.",
        ),
        PublishingContentCreate(
            title="Senal SNIFF AMAZON para contenido e-commerce",
            format="insight",
            department_owner="SNIFF AMAZON",
            channel="Blog/Web",
            niche="e-commerce",
            revenue_link="ecommerce_10000_usd",
            content_brief="SNIFF AMAZON prepara insight sin compra, inventario ni metrica inventada.",
        ),
    ]


def channel_id(name: str) -> str:
    return f"publishing_channel_{safe_id(name, 'channel')}"


def content_id(title: str) -> str:
    return f"publishing_content_{safe_id(title, 'content')}_{uuid4().hex[:8]}"


def channel_requires_approval(request: PublishingChannelCreate) -> tuple[bool, str]:
    if request.new_external_account_requested:
        return True, "new_external_account_requires_ceo_approval"
    if request.api_connected and request.account_status != PublishingAccountStatus.connected:
        return True, "api_connection_requires_real_configuration"
    return False, "none"


def build_channel(request: PublishingChannelCreate, *, item_id: str | None = None) -> PublishingChannel:
    now = utc_now()
    requires_approval, reason = channel_requires_approval(request)
    publication_mode = (
        PublishingMode.organic
        if request.account_status == PublishingAccountStatus.connected and request.organic_enabled
        else PublishingMode.prepared
    )
    return PublishingChannel(
        id=item_id or channel_id(request.name),
        name=request.name,
        platform=request.platform or request.name,
        account_name=request.account_name,
        account_status=request.account_status,
        publication_mode=publication_mode,
        official_account=request.official_account,
        api_connected=request.api_connected,
        organic_enabled=request.organic_enabled,
        requires_approval=requires_approval,
        approval_reason=reason,
        external_connection_enabled=False,
        runtime_connected=False,
        created_at=now,
        updated_at=now,
    )


def save_channel(channel: PublishingChannel) -> PublishingChannel:
    channel.updated_at = utc_now()
    upsert_payload(PUBLISHING_CHANNELS_TABLE, channel.id, channel.model_dump_json())
    upsert_payload(PUBLISHING_ACCOUNTS_TABLE, channel.id, channel.model_dump_json())
    return channel


def list_channels() -> list[PublishingChannel]:
    ensure_publishing_defaults()
    channels = [PublishingChannel(**payload) for payload in fetch_payloads(PUBLISHING_CHANNELS_TABLE)]
    return sorted(channels, key=lambda item: item.name)


def get_channel_by_name(name: str) -> PublishingChannel | None:
    normalized = normalize(name)
    ensure_publishing_schema()
    for payload in fetch_payloads(PUBLISHING_CHANNELS_TABLE):
        channel = PublishingChannel(**payload)
        if normalize(channel.name) == normalized or normalize(channel.platform) == normalized:
            return channel
    return None


def content_requires_approval(
    request: PublishingContentCreate,
    account_status: PublishingAccountStatus,
) -> tuple[bool, str]:
    if request.requires_approval is not None:
        return request.requires_approval, "explicit_request"
    if request.publication_mode in PAID_MODES:
        return True, "paid_campaign_requires_ceo_approval"
    if account_status == PublishingAccountStatus.not_connected:
        return False, "account_not_connected_prepared"
    return False, "organic_configured_account_no_approval"


def effective_publication_mode(
    requested_mode: PublishingMode,
    account_status: PublishingAccountStatus,
) -> PublishingMode:
    if account_status == PublishingAccountStatus.not_connected and requested_mode != PublishingMode.paid:
        return PublishingMode.prepared
    return requested_mode


def publication_status_for(
    status_value: PublishingContentStatus,
    account_status: PublishingAccountStatus,
    mode: PublishingMode,
    requires_approval: bool,
) -> str:
    if requires_approval:
        return "waiting_ceo_approval"
    if account_status == PublishingAccountStatus.not_connected:
        return "prepared"
    if mode == PublishingMode.organic and status_value == PublishingContentStatus.scheduled:
        return "scheduled"
    if mode == PublishingMode.organic and status_value == PublishingContentStatus.published:
        return "published_recorded"
    return "prepared"


def build_content_item(
    request: PublishingContentCreate,
    *,
    item_id: str | None = None,
) -> PublishingContentItem:
    now = utc_now()
    channel = get_channel_by_name(request.channel)
    account_status = request.account_status or (channel.account_status if channel else PublishingAccountStatus.not_connected)
    requires_approval, reason = content_requires_approval(request, account_status)
    mode = effective_publication_mode(request.publication_mode, account_status)
    status_value = request.status or (
        PublishingContentStatus.waiting_ceo_approval
        if requires_approval
        else PublishingContentStatus.prepared
    )
    return PublishingContentItem(
        id=item_id or content_id(request.title),
        title=request.title,
        format=request.format,
        department_owner=request.department_owner,
        channel=request.channel,
        account_status=account_status,
        language=request.language,
        niche=request.niche,
        niche_status=request.niche_status or ("needs_ceo_definition" if request.niche is None else "defined"),
        status=status_value,
        scheduled_at=request.scheduled_at,
        publication_mode=mode,
        publication_status=publication_status_for(status_value, account_status, mode, requires_approval),
        requires_approval=requires_approval,
        approval_reason=reason,
        revenue_link=request.revenue_link,
        metrics=request.metrics,
        metrics_status=PublishingEvidenceStatus.available if request.metrics else PublishingEvidenceStatus.missing,
        campaign_id=request.campaign_id,
        content_brief=request.content_brief,
        actual_publication_confirmed=False,
        paid_campaign_launched=False,
        external_connection_enabled=False,
        runtime_connected=False,
        created_at=now,
        updated_at=now,
    )


def save_content_item(item: PublishingContentItem) -> PublishingContentItem:
    item.updated_at = utc_now()
    upsert_payload(CONTENT_ITEMS_TABLE, item.id, item.model_dump_json())
    return item


def list_content_items() -> list[PublishingContentItem]:
    ensure_publishing_defaults()
    items = [PublishingContentItem(**payload) for payload in fetch_payloads(CONTENT_ITEMS_TABLE)]
    return sorted(items, key=lambda item: (item.scheduled_at or "9999", item.title))


def get_content_item(item_id: str) -> PublishingContentItem:
    ensure_publishing_defaults()
    payload = fetch_payload(CONTENT_ITEMS_TABLE, item_id)
    if payload is None:
        raise PublishingError(404, {"error": "publishing_content_not_found", "content_id": item_id})
    return PublishingContentItem(**payload)


def create_channel(request: PublishingChannelCreate, actor: AuthenticatedUser) -> PublishingChannel:
    ensure_publishing_defaults(actor)
    channel = build_channel(request, item_id=f"{channel_id(request.name)}_{uuid4().hex[:8]}")
    save_channel(channel)
    if channel.requires_approval:
        upsert_payload(
            CONTENT_APPROVALS_TABLE,
            f"approval_channel_{channel.id}",
            json.dumps(
                {
                    "id": f"approval_channel_{channel.id}",
                    "target_id": channel.id,
                    "target_type": "channel",
                    "reason": channel.approval_reason,
                    "status": "pending_ceo",
                    "created_at": utc_now(),
                },
                ensure_ascii=False,
            ),
        )
    audit_publishing_action(
        actor=actor,
        action="create_publishing_channel",
        status=channel.publication_mode.value,
        detail="Publishing channel registered without creating external accounts.",
        metadata={"channel_id": channel.id, "requires_approval": channel.requires_approval},
    )
    return channel


def create_content_item(request: PublishingContentCreate, actor: AuthenticatedUser) -> PublishingContentItem:
    ensure_publishing_defaults(actor)
    item = build_content_item(request)
    save_content_item(item)
    if item.requires_approval:
        upsert_payload(
            CONTENT_APPROVALS_TABLE,
            f"approval_content_{item.id}",
            json.dumps(
                {
                    "id": f"approval_content_{item.id}",
                    "target_id": item.id,
                    "target_type": "content",
                    "reason": item.approval_reason,
                    "status": "pending_ceo",
                    "created_at": utc_now(),
                },
                ensure_ascii=False,
            ),
        )
    audit_publishing_action(
        actor=actor,
        action="create_content_item",
        status=item.publication_status,
        detail="Content item prepared without real publishing claim.",
        metadata={
            "content_id": item.id,
            "publication_mode": item.publication_mode.value,
            "account_status": item.account_status.value,
        },
    )
    return item


def schedule_content_item(
    item_id: str,
    request: PublishingScheduleRequest,
    actor: AuthenticatedUser,
) -> PublishingContentItem:
    item = get_content_item(item_id)
    if request.channel:
        item.channel = request.channel
        channel = get_channel_by_name(request.channel)
        item.account_status = channel.account_status if channel else PublishingAccountStatus.not_connected
    if request.publication_mode:
        item.publication_mode = effective_publication_mode(request.publication_mode, item.account_status)
        if request.publication_mode == PublishingMode.paid:
            item.requires_approval = True
            item.approval_reason = "paid_campaign_requires_ceo_approval"
    item.scheduled_at = request.scheduled_at
    item.status = (
        PublishingContentStatus.waiting_ceo_approval
        if item.requires_approval
        else PublishingContentStatus.prepared
        if item.account_status == PublishingAccountStatus.not_connected
        else PublishingContentStatus.scheduled
    )
    item.publication_status = publication_status_for(
        item.status,
        item.account_status,
        item.publication_mode,
        item.requires_approval,
    )
    save_content_item(item)
    entry = PublishingCalendarEntry(
        id=f"publishing_schedule_{uuid4()}",
        content_id=item.id,
        title=item.title,
        channel=item.channel,
        scheduled_at=item.scheduled_at,
        publication_mode=item.publication_mode,
        publication_status=item.publication_status,
        requires_approval=item.requires_approval,
        created_at=utc_now(),
    )
    upsert_payload(PUBLISHING_SCHEDULE_TABLE, entry.id, entry.model_dump_json())
    audit_publishing_action(
        actor=actor,
        action="schedule_content_item",
        status=item.publication_status,
        detail="Content scheduled or kept prepared according to account connection.",
        metadata={"content_id": item.id, "scheduled_at": item.scheduled_at},
    )
    return item


def mark_content_published(
    item_id: str,
    request: PublishingMarkPublishedRequest,
    actor: AuthenticatedUser,
) -> PublishingContentItem:
    item = get_content_item(item_id)
    if item.requires_approval:
        item.status = PublishingContentStatus.waiting_ceo_approval
        item.publication_status = "waiting_ceo_approval"
    elif item.account_status == PublishingAccountStatus.not_connected:
        item.status = PublishingContentStatus.prepared
        item.publication_status = "prepared"
        item.actual_publication_confirmed = False
    else:
        item.status = PublishingContentStatus.published
        item.publication_status = "published_recorded"
        item.actual_publication_confirmed = bool(request.evidence)
        item.metrics.update(request.metrics)
        item.metrics_status = PublishingEvidenceStatus.available if request.metrics else item.metrics_status
    item.paid_campaign_launched = False
    save_content_item(item)
    event_id = f"publishing_event_{uuid4()}"
    upsert_payload(
        PUBLISHING_EVENTS_TABLE,
        event_id,
        json.dumps(
            {
                "id": event_id,
                "content_id": item.id,
                "event": "mark_published",
                "publication_status": item.publication_status,
                "evidence": "provided" if request.evidence else "missing",
                "created_at": utc_now(),
            },
            ensure_ascii=False,
        ),
    )
    audit_publishing_action(
        actor=actor,
        action="mark_content_published",
        status=item.publication_status,
        detail="Publication mark processed without launching paid campaign or external API.",
        metadata={"content_id": item.id, "actual_publication_confirmed": item.actual_publication_confirmed},
    )
    return item


def list_calendar_entries() -> list[PublishingCalendarEntry]:
    ensure_publishing_defaults()
    entries = [PublishingCalendarEntry(**payload) for payload in fetch_payloads(PUBLISHING_SCHEDULE_TABLE)]
    if entries:
        return sorted(entries, key=lambda item: item.scheduled_at or "9999")
    return [
        PublishingCalendarEntry(
            id=f"calendar:{item.id}",
            content_id=item.id,
            title=item.title,
            channel=item.channel,
            scheduled_at=item.scheduled_at,
            publication_mode=item.publication_mode,
            publication_status=item.publication_status,
            requires_approval=item.requires_approval,
            created_at=item.created_at,
        )
        for item in list_content_items()[:8]
    ]


def create_growth_metric(
    request: PublishingGrowthMetricCreate,
    actor: AuthenticatedUser,
) -> PublishingGrowthMetric:
    evidence_status = request.evidence_status or (
        PublishingEvidenceStatus.available if request.evidence else PublishingEvidenceStatus.missing
    )
    metric = PublishingGrowthMetric(
        id=f"growth_metric_{uuid4()}",
        content_id=request.content_id,
        channel=request.channel,
        metric_name=request.metric_name,
        value=request.value,
        evidence=request.evidence,
        evidence_status=evidence_status,
        real_metric_confirmed=evidence_status == PublishingEvidenceStatus.available,
        created_at=utc_now(),
    )
    upsert_payload(GROWTH_METRICS_TABLE, metric.id, metric.model_dump_json())
    audit_publishing_action(
        actor=actor,
        action="record_growth_metric",
        status=metric.evidence_status.value,
        detail="Growth metric recorded with explicit evidence status; no invented metrics.",
        metadata={"metric_id": metric.id, "real_metric_confirmed": metric.real_metric_confirmed},
    )
    return metric


def list_growth_metrics() -> list[PublishingGrowthMetric]:
    ensure_publishing_defaults()
    return [PublishingGrowthMetric(**payload) for payload in fetch_payloads(GROWTH_METRICS_TABLE)]


def ensure_publishing_defaults(actor: AuthenticatedUser | None = None) -> None:
    ensure_publishing_schema()
    if not fetch_payloads(PUBLISHING_CHANNELS_TABLE):
        for request in initial_channel_requests():
            channel = build_channel(request)
            save_channel(channel)
    if not fetch_payloads(CONTENT_ITEMS_TABLE):
        for request in initial_content_requests():
            item = build_content_item(request)
            save_content_item(item)
    if actor is not None:
        audit_publishing_action(
            actor=actor,
            action="ensure_publishing_defaults",
            status="prepared",
            detail="Publishing defaults prepared locally without connected accounts.",
            metadata={"channels": len(initial_channel_requests()), "content": len(initial_content_requests())},
        )


def get_publishing_status() -> PublishingStatus:
    ensure_publishing_defaults()
    channels = list_channels()
    content = list_content_items()
    connected = [channel for channel in channels if channel.account_status == PublishingAccountStatus.connected]
    approvals = [item for item in content if item.requires_approval]
    return PublishingStatus(
        status="publishing_growth_engine_prepared_internal",
        mode="prepared_local",
        channels=len(channels),
        connected_accounts=len(connected),
        not_connected_accounts=len(channels) - len(connected),
        content_items=len(content),
        prepared_items=len([item for item in content if item.publication_status == "prepared"]),
        scheduled_items=len([item for item in content if item.status == PublishingContentStatus.scheduled]),
        published_records=len([item for item in content if item.publication_status == "published_recorded"]),
        approvals_needed=len(approvals) + len([channel for channel in channels if channel.requires_approval]),
        paid_campaigns_launched=0,
        real_metrics_confirmed=len([metric for metric in list_growth_metrics() if metric.real_metric_confirmed]),
        next_content=content[:6],
        channels_snapshot=channels,
        cerebro_coordination={
            "PLUMA": "prepara posts, articulos, newsletters, guiones, libros y autoridad.",
            "LENTE": "prepara shorts, reels, miniaturas, avatares y visuales; nichos sin definir quedan needs_ceo_definition.",
            "MARKETING": "coordina organico, demanda y ROI para paid campaigns.",
            "MARCA PERSONAL": "prepara autoridad CEO en canales oficiales si existen.",
            "E-COMMERCE": "mantiene ruta separada y no inventa ventas.",
            "SNIFF AMAZON": "genera senales, no compras ni inventario.",
            "approval_rule": "organico conectado no requiere CEO; paid o cuenta nueva si requiere.",
        },
        external_connection_enabled=False,
        runtime_connected=False,
        payment_connected=False,
        generated_at=utc_now(),
    )
