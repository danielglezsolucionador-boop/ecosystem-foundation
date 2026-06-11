from datetime import UTC, datetime

from app.schemas.social_identity import SocialIdentityAccount, SocialIdentityRisk, SocialIdentityState, SocialIdentityStatus


class SocialIdentityError(Exception):
    def __init__(self, status_code: int, detail: dict[str, object]) -> None:
        self.status_code = status_code
        self.detail = detail
        super().__init__(str(detail))


PLATFORMS = [
    "TikTok",
    "Instagram",
    "YouTube",
    "YouTube Shorts",
    "LinkedIn",
    "X",
    "Facebook",
    "Blog/Web",
    "Newsletter",
    "Podcast",
]

AREAS = [
    "Ecosistema IA",
    "Marca Personal CEO",
    "PLUMA",
    "LENTE",
    "MARKETING",
    "Web Factory",
    "E-Commerce",
    "SNIFF AMAZON / CHIEF AMAZON",
    "DCFT",
    "SENTINELA",
    "APIs/Skills",
]


def utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def account(
    item_id: str,
    area: str,
    platform: str,
    state: SocialIdentityState,
    owner_internal: str,
    recommended_action: str,
    *,
    current_account: str = "unknown",
    proposed_account: str = "pending_ceo",
    evidence: str = "missing",
    requires_ceo: bool = False,
    requires_credentials: bool = False,
    requires_account_creation: bool = False,
    risk: SocialIdentityRisk = SocialIdentityRisk.medium,
    can_continue_prepared: bool = True,
    notes: str = "",
) -> SocialIdentityAccount:
    now = utc_now()
    return SocialIdentityAccount(
        id=item_id,
        area=area,
        platform=platform,
        current_account=current_account,
        proposed_account=proposed_account,
        state=state,
        evidence=evidence,
        owner_internal=owner_internal,
        requires_ceo=requires_ceo,
        requires_credentials=requires_credentials,
        requires_account_creation=requires_account_creation,
        risk=risk,
        recommended_action=recommended_action,
        can_continue_prepared=can_continue_prepared,
        notes=notes,
        account_connected=False,
        real_publication_enabled=False,
        external_connection_enabled=False,
        credentials_stored=False,
        created_at=now,
        updated_at=now,
    )


def initial_social_accounts() -> list[SocialIdentityAccount]:
    a = account
    return [
        a("ecosystem_linkedin", "Ecosistema IA", "LinkedIn", SocialIdentityState.existing_unconfirmed, "MARKETING", "Confirmar si existe pagina oficial antes de usarla.", requires_ceo=True),
        a("ecosystem_x", "Ecosistema IA", "X", SocialIdentityState.unknown, "MARKETING", "Definir handle oficial o mantener prepared.", requires_ceo=True),
        a("ecosystem_blog_web", "Ecosistema IA", "Blog/Web", SocialIdentityState.prepared, "WEB FACTORY", "Preparar home y blog local sin publicar dominio real.", evidence="internal_docs", risk=SocialIdentityRisk.low),
        a("ecosystem_newsletter", "Ecosistema IA", "Newsletter", SocialIdentityState.needs_credentials, "MARKETING", "Definir herramienta y credenciales por canal seguro.", requires_ceo=True, requires_credentials=True, requires_account_creation=True, risk=SocialIdentityRisk.sensitive),
        a("marca_personal_tiktok", "Marca Personal CEO", "TikTok", SocialIdentityState.unknown, "MARCA PERSONAL", "Confirmar cuenta oficial existente o proponer nueva.", requires_ceo=True),
        a("marca_personal_instagram", "Marca Personal CEO", "Instagram", SocialIdentityState.unknown, "MARCA PERSONAL", "Confirmar cuenta oficial antes de publicar.", requires_ceo=True),
        a("marca_personal_youtube", "Marca Personal CEO", "YouTube", SocialIdentityState.needs_ceo_definition, "MARCA PERSONAL", "Definir canal principal y criterio de autoridad.", requires_ceo=True),
        a("marca_personal_linkedin", "Marca Personal CEO", "LinkedIn", SocialIdentityState.existing_unconfirmed, "MARCA PERSONAL", "CEO debe confirmar perfil/pagina oficial.", requires_ceo=True),
        a("marca_personal_x", "Marca Personal CEO", "X", SocialIdentityState.unknown, "MARCA PERSONAL", "Confirmar handle oficial.", requires_ceo=True),
        a("marca_personal_podcast", "Marca Personal CEO", "Podcast", SocialIdentityState.proposed_new, "MARCA PERSONAL", "Proponer identidad de podcast sin crear cuenta.", requires_ceo=True, requires_account_creation=True),
        a("pluma_blog", "PLUMA", "Blog/Web", SocialIdentityState.prepared, "PLUMA", "Preparar articulos sin publicar dominio real.", evidence="internal_docs", risk=SocialIdentityRisk.low),
        a("pluma_newsletter", "PLUMA", "Newsletter", SocialIdentityState.proposed_new, "PLUMA", "Definir newsletter antes de crear herramienta externa.", requires_ceo=True, requires_credentials=True, requires_account_creation=True, risk=SocialIdentityRisk.high),
        a("pluma_linkedin", "PLUMA", "LinkedIn", SocialIdentityState.prepared, "PLUMA", "Preparar piezas para LinkedIn, sin cuenta conectada.", risk=SocialIdentityRisk.low),
        a("lente_youtube", "LENTE", "YouTube", SocialIdentityState.proposed_new, "LENTE", "Definir canales y nichos antes de crear canal.", requires_ceo=True, requires_account_creation=True),
        a("lente_youtube_shorts", "LENTE", "YouTube Shorts", SocialIdentityState.proposed_new, "LENTE", "Preparar formato Shorts sin publicar real.", requires_ceo=True, requires_account_creation=True),
        a("lente_tiktok", "LENTE", "TikTok", SocialIdentityState.proposed_new, "LENTE", "Definir canales por nicho antes de crearlos.", requires_ceo=True, requires_account_creation=True),
        a("lente_instagram", "LENTE", "Instagram", SocialIdentityState.proposed_new, "LENTE", "Definir Reels/canal visual oficial.", requires_ceo=True, requires_account_creation=True),
        a("lente_podcast", "LENTE", "Podcast", SocialIdentityState.needs_ceo_definition, "LENTE", "Definir avatar/podcast antes de identidad publica.", requires_ceo=True),
        a("marketing_instagram", "MARKETING", "Instagram", SocialIdentityState.unknown, "MARKETING", "No lanzar campana ni publicar sin cuenta confirmada.", requires_ceo=True),
        a("marketing_facebook", "MARKETING", "Facebook", SocialIdentityState.unknown, "MARKETING", "Confirmar pagina oficial antes de usar.", requires_ceo=True),
        a("marketing_linkedin", "MARKETING", "LinkedIn", SocialIdentityState.existing_unconfirmed, "MARKETING", "Validar pagina/owner oficial.", requires_ceo=True),
        a("marketing_x", "MARKETING", "X", SocialIdentityState.unknown, "MARKETING", "Confirmar o proponer handle.", requires_ceo=True),
        a("web_factory_blog", "Web Factory", "Blog/Web", SocialIdentityState.prepared, "WEB FACTORY", "Preparar landings locales sin dominio real.", evidence="internal_docs", risk=SocialIdentityRisk.low),
        a("web_factory_newsletter", "Web Factory", "Newsletter", SocialIdentityState.needs_credentials, "WEB FACTORY", "Definir formularios y destino de datos por canal seguro.", requires_ceo=True, requires_credentials=True, risk=SocialIdentityRisk.sensitive),
        a("ecommerce_instagram", "E-Commerce", "Instagram", SocialIdentityState.proposed_new, "E-COMMERCE", "Definir marca/tienda antes de crear cuenta.", requires_ceo=True, requires_account_creation=True),
        a("ecommerce_facebook", "E-Commerce", "Facebook", SocialIdentityState.proposed_new, "E-COMMERCE", "Definir pagina de tienda sin publicar real.", requires_ceo=True, requires_account_creation=True),
        a("ecommerce_tiktok", "E-Commerce", "TikTok", SocialIdentityState.proposed_new, "E-COMMERCE", "Definir estrategia organica antes de crear cuenta.", requires_ceo=True, requires_account_creation=True),
        a("ecommerce_newsletter", "E-Commerce", "Newsletter", SocialIdentityState.needs_credentials, "E-COMMERCE", "No guardar clientes ni emails reales sin herramienta aprobada.", requires_ceo=True, requires_credentials=True, requires_account_creation=True, risk=SocialIdentityRisk.sensitive),
        a("sniff_amazon_youtube", "SNIFF AMAZON / CHIEF AMAZON", "YouTube", SocialIdentityState.proposed_new, "SNIFF AMAZON", "Definir canal de reviews/analisis sin claims falsos.", requires_ceo=True, requires_account_creation=True),
        a("sniff_amazon_tiktok", "SNIFF AMAZON / CHIEF AMAZON", "TikTok", SocialIdentityState.proposed_new, "SNIFF AMAZON", "Preparar piezas sin publicar ni vender.", requires_ceo=True, requires_account_creation=True),
        a("sniff_amazon_blog", "SNIFF AMAZON / CHIEF AMAZON", "Blog/Web", SocialIdentityState.prepared, "SNIFF AMAZON", "Preparar analisis sin afiliados ni tienda real.", risk=SocialIdentityRisk.low),
        a("dcft_linkedin", "DCFT", "LinkedIn", SocialIdentityState.proposed_new, "MARKETING", "MARKETING puede proponer canal; DCFT real no se toca.", requires_ceo=True, requires_account_creation=True),
        a("dcft_youtube", "DCFT", "YouTube", SocialIdentityState.proposed_new, "MARKETING", "Preparar educativo sin afirmar legal/tributario sin fuente.", requires_ceo=True, requires_account_creation=True, risk=SocialIdentityRisk.high),
        a("dcft_blog", "DCFT", "Blog/Web", SocialIdentityState.prepared, "WEB FACTORY", "Preparar landing local; no SUNAT real ni venta automatica.", evidence="internal_docs", risk=SocialIdentityRisk.low),
        a("sentinela_linkedin", "SENTINELA", "LinkedIn", SocialIdentityState.proposed_new, "MARKETING", "Preparar posicionamiento de seguridad sin claims no validados.", requires_ceo=True, requires_account_creation=True, risk=SocialIdentityRisk.high),
        a("sentinela_youtube", "SENTINELA", "YouTube", SocialIdentityState.proposed_new, "MARKETING", "Preparar contenido de seguridad sin producto real conectado.", requires_ceo=True, requires_account_creation=True, risk=SocialIdentityRisk.high),
        a("sentinela_blog", "SENTINELA", "Blog/Web", SocialIdentityState.prepared, "WEB FACTORY", "Preparar landing sin afirmar defensa productiva.", evidence="internal_docs", risk=SocialIdentityRisk.low),
        a("apis_skills_blog", "APIs/Skills", "Blog/Web", SocialIdentityState.prepared, "CREADOR APIs/SKILLS", "Preparar catalogo sin vender ni conectar APIs externas.", evidence="internal_docs", risk=SocialIdentityRisk.low),
        a("apis_skills_linkedin", "APIs/Skills", "LinkedIn", SocialIdentityState.proposed_new, "MARKETING", "Definir canal B2B antes de crear cuenta.", requires_ceo=True, requires_account_creation=True),
        a("apis_skills_youtube", "APIs/Skills", "YouTube", SocialIdentityState.proposed_new, "LENTE", "Preparar demos sin publicar ni usar credenciales.", requires_ceo=True, requires_account_creation=True),
    ]


def list_social_identity_accounts() -> list[SocialIdentityAccount]:
    return sorted(initial_social_accounts(), key=lambda item: (item.area, item.platform, item.id))


def get_social_identity_account(account_id: str) -> SocialIdentityAccount:
    for item in list_social_identity_accounts():
        if item.id == account_id:
            return item
    raise SocialIdentityError(404, {"error": "social_identity_account_not_found", "account_id": account_id})


def account_needs_approval(account_item: SocialIdentityAccount) -> bool:
    return (
        account_item.requires_ceo
        or account_item.requires_credentials
        or account_item.requires_account_creation
        or account_item.state
        in {
            SocialIdentityState.proposed_new,
            SocialIdentityState.needs_ceo_definition,
            SocialIdentityState.needs_credentials,
            SocialIdentityState.needs_account_creation,
            SocialIdentityState.blocked,
        }
    )


def list_social_identity_approval_needed() -> list[SocialIdentityAccount]:
    return [item for item in list_social_identity_accounts() if account_needs_approval(item)]


def list_social_identity_risks() -> list[SocialIdentityAccount]:
    return [
        item
        for item in list_social_identity_accounts()
        if item.risk in {SocialIdentityRisk.high, SocialIdentityRisk.sensitive}
    ]


def get_social_identity_status() -> SocialIdentityStatus:
    accounts = list_social_identity_accounts()
    approvals = list_social_identity_approval_needed()
    risks = list_social_identity_risks()
    return SocialIdentityStatus(
        total_accounts=len(accounts),
        unknown=len([item for item in accounts if item.state == SocialIdentityState.unknown]),
        existing_unconfirmed=len([item for item in accounts if item.state == SocialIdentityState.existing_unconfirmed]),
        confirmed_existing=len([item for item in accounts if item.state == SocialIdentityState.confirmed_existing]),
        proposed_new=len([item for item in accounts if item.state == SocialIdentityState.proposed_new]),
        prepared=len([item for item in accounts if item.state == SocialIdentityState.prepared]),
        needs_ceo=len([item for item in accounts if item.requires_ceo]),
        needs_credentials=len([item for item in accounts if item.requires_credentials]),
        needs_account_creation=len([item for item in accounts if item.requires_account_creation]),
        high_risk=len([item for item in risks if item.risk == SocialIdentityRisk.high]),
        sensitive=len([item for item in risks if item.risk == SocialIdentityRisk.sensitive]),
        approval_needed_count=len(approvals),
        platforms=PLATFORMS,
        areas=AREAS,
        next_steps=[
            "Confirmar cuentas existentes oficiales.",
            "Definir cuentas nuevas propuestas antes de crearlas.",
            "Mantener publication_status prepared si la cuenta no esta confirmada.",
            "Gestionar credenciales solo por canal seguro aprobado.",
            "No publicar contenido real desde S.2.",
        ],
        accounts_snapshot=accounts[:12],
        account_connected=False,
        real_publication_enabled=False,
        external_connection_enabled=False,
        credentials_stored=False,
        generated_at=utc_now(),
    )
