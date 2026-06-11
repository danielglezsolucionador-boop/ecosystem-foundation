const endpoints = {
  health: "/health",
  readiness: "/readiness",
  runtime: "/runtime/status",
  version: "/version",
  apps: "/api/v1/apps",
  integrationProfiles: "/api/v1/integrations/apps",
  controlCenter: "/api/v1/control-center",
  roles: "/api/v1/security/roles",
  memory: "/api/v1/memory",
  events: "/api/v1/events",
  integrationBus: "/api/v1/integration-bus",
  contracts: "/api/v1/contracts",
  audit: "/api/v1/audit",
  auditoriaStatus: "/api/v1/auditoria/status",
  auditoriaReviews: "/api/v1/auditoria/reviews",
  auditoriaQueue: "/api/v1/auditoria/queue",
  nubeStatus: "/api/v1/nube/status",
  nubeProjects: "/api/v1/nube/projects",
  nubeDeployments: "/api/v1/nube/deployments",
  nubeHealthChecks: "/api/v1/nube/health-checks",
  nubeRisks: "/api/v1/nube/risks",
  nubeCosts: "/api/v1/nube/costs",
  observability: "/api/v1/observability",
  governanceOverview: "/api/v1/governance",
  governance: "/api/v1/governance/reports",
  decisions: "/api/v1/governance/decisions",
  approvals: "/api/v1/governance/approvals",
  gates: "/api/v1/governance/integration-gates",
  policies: "/api/v1/governance/policies",
  risks: "/api/v1/governance/risks",
  governanceAudit: "/api/v1/governance/audit",
  cerebroStatus: "/api/v1/cerebro/status",
  cerebroChief: "/api/v1/cerebro/chief-of-staff/status",
  cerebroMorning: "/api/v1/cerebro/brief/morning",
  cerebroEvening: "/api/v1/cerebro/brief/evening",
  cerebroDecisions: "/api/v1/cerebro/decisions",
  cerebroTasks: "/api/v1/cerebro/tasks",
  ceoDailyCenter: "/api/v1/ceo/daily-center",
  ceoMorning: "/api/v1/ceo/morning",
  ceoEvening: "/api/v1/ceo/evening",
  ceoDecisions: "/api/v1/ceo/decisions",
  departments: "/api/v1/departments",
  departmentAudits: "/api/v1/departments/audits",
  revenueStatus: "/api/v1/revenue/status",
  revenueOpportunities: "/api/v1/revenue/opportunities",
  revenueApprovals: "/api/v1/revenue/approval-requests",
  revenueDepartments: "/api/v1/revenue/department-contribution",
  revenueDailyReport: "/api/v1/revenue/daily-report",
  revenueSprintStatus: "/api/v1/revenue/sprint/status",
  revenueSprintRoutes: "/api/v1/revenue/sprint/routes",
  revenueSprintMissions: "/api/v1/revenue/sprint/missions",
  revenueSprintDaily: "/api/v1/revenue/sprint/daily",
  revenueSprintRisks: "/api/v1/revenue/sprint/risks",
  revenueSprintApprovalNeeded: "/api/v1/revenue/sprint/approval-needed",
  ecommerceReadinessStatus: "/api/v1/ecommerce-readiness/status",
  ecommerceReadinessOpportunities: "/api/v1/ecommerce-readiness/opportunities",
  ecommerceReadinessApprovalNeeded: "/api/v1/ecommerce-readiness/approval-needed",
  amazonReadinessStatus: "/api/v1/amazon-readiness/status",
  amazonReadinessOpportunities: "/api/v1/amazon-readiness/opportunities",
  amazonReadinessRisks: "/api/v1/amazon-readiness/risks",
  publishingStatus: "/api/v1/publishing/status",
  publishingChannels: "/api/v1/publishing/channels",
  publishingCalendar: "/api/v1/publishing/calendar",
  publishingContent: "/api/v1/publishing/content",
  publishingGrowth: "/api/v1/publishing/growth",
  publishingPreparedStatus: "/api/v1/publishing-prepared/status",
  publishingPreparedCalendar: "/api/v1/publishing-prepared/calendar",
  publishingPreparedContent: "/api/v1/publishing-prepared/content",
  publishingPreparedBlocked: "/api/v1/publishing-prepared/blocked",
  marketingApprovalStatus: "/api/v1/marketing-approval/status",
  marketingApprovalCampaigns: "/api/v1/marketing-approval/campaigns",
  marketingApprovalApprovalNeeded: "/api/v1/marketing-approval/approval-needed",
  marketingApprovalRisks: "/api/v1/marketing-approval/risks",
  productReadinessStatus: "/api/v1/product-readiness/status",
  productReadinessDcft: "/api/v1/product-readiness/dcft",
  productReadinessSentinela: "/api/v1/product-readiness/sentinela",
  productReadinessGaps: "/api/v1/product-readiness/gaps",
  productReadinessMarketingPackage: "/api/v1/product-readiness/marketing-package",
  commercialReadinessStatus: "/api/v1/commercial-readiness/status",
  commercialReadinessDcft: "/api/v1/commercial-readiness/dcft",
  commercialReadinessSentinela: "/api/v1/commercial-readiness/sentinela",
  commercialReadinessMarketingPackage: "/api/v1/commercial-readiness/marketing-package",
  commercialReadinessApprovalNeeded: "/api/v1/commercial-readiness/approval-needed",
  realWorldStatus: "/api/v1/real-world/status",
  realWorldConnections: "/api/v1/real-world/connections",
  realWorldApprovalNeeded: "/api/v1/real-world/approval-needed",
  realWorldRisks: "/api/v1/real-world/risks",
  analyticsReadinessStatus: "/api/v1/analytics-readiness/status",
  analyticsReadinessMetrics: "/api/v1/analytics-readiness/metrics",
  analyticsReadinessSources: "/api/v1/analytics-readiness/sources",
  analyticsReadinessApprovalNeeded: "/api/v1/analytics-readiness/approval-needed",
  analyticsReadinessRisks: "/api/v1/analytics-readiness/risks",
  realWorldExecutionStatus: "/api/v1/real-world-execution/status",
  realWorldExecutionQueue: "/api/v1/real-world-execution/queue",
  realWorldExecutionApprovalNeeded: "/api/v1/real-world-execution/approval-needed",
  socialIdentityStatus: "/api/v1/social-identity/status",
  socialIdentityAccounts: "/api/v1/social-identity/accounts",
  socialIdentityApprovalNeeded: "/api/v1/social-identity/approval-needed",
  socialIdentityRisks: "/api/v1/social-identity/risks",
  arsenalStatus: "/api/v1/arsenal/status",
  arsenalCatalog: "/api/v1/arsenal/catalog",
  arsenalCategories: "/api/v1/arsenal/categories",
  arsenalRisks: "/api/v1/arsenal/risks",
  arsenalReadiness: "/api/v1/arsenal/readiness",
  missionsActive: "/api/v1/missions/active",
  missionDailyReport: "/api/v1/missions/reports/daily",
  workdayStatus: "/api/v1/workday/status",
  workdayMorning: "/api/v1/workday/morning",
  workdayMidday: "/api/v1/workday/midday",
  workdayEvening: "/api/v1/workday/evening",
  workdayAlerts: "/api/v1/workday/alerts",
  workdayPriorityChanges: "/api/v1/workday/priority-changes",
  workdayReport: "/api/v1/workday/report",
  upgradesStatus: "/api/v1/upgrades/status",
  upgradesPackages: "/api/v1/upgrades/packages"
};

const AUTH_TOKEN_KEY = "ecosystem_control_center_session_v1";
const DATA_FETCH_TIMEOUT_MS = 15000;
const DATA_FETCH_CONCURRENCY = 12;
const CRITICAL_DATA_NAMES = new Set([
  "health",
  "readiness",
  "runtime",
  "version",
  "controlCenter",
  "ceoDailyCenter",
  "ceoMorning",
  "ceoEvening",
  "revenueSprintStatus",
  "revenueSprintRoutes",
  "revenueSprintApprovalNeeded",
  "ecommerceReadinessStatus",
  "ecommerceReadinessOpportunities",
  "ecommerceReadinessApprovalNeeded",
  "amazonReadinessStatus",
  "amazonReadinessOpportunities",
  "amazonReadinessRisks",
  "publishingStatus",
  "publishingPreparedStatus",
  "publishingPreparedContent",
  "marketingApprovalStatus",
  "marketingApprovalCampaigns",
  "productReadinessStatus",
  "commercialReadinessStatus",
  "analyticsReadinessStatus",
  "analyticsReadinessMetrics",
  "realWorldStatus",
  "realWorldExecutionStatus",
  "realWorldExecutionQueue",
  "realWorldExecutionApprovalNeeded",
  "socialIdentityStatus",
  "boundary"
]);

function readStoredSession() {
  const persistentToken = localStorage.getItem(AUTH_TOKEN_KEY);
  if (persistentToken) return { token: persistentToken, remembered: true };
  const tabToken = sessionStorage.getItem(AUTH_TOKEN_KEY);
  if (tabToken) return { token: tabToken, remembered: false };
  return { token: "", remembered: false };
}

const initialSession = readStoredSession();

const state = {
  data: {},
  errors: {},
  token: initialSession.token,
  user: null,
  role: "ceo",
  boundary: null,
  view: "ceo",
  meeting: "morning",
  search: "",
  statusFilter: "all",
  lastUpdated: null,
  pendingAction: null,
  restoreAttempted: Boolean(initialSession.token),
  restoredNoticePending: false,
  sessionRemembered: initialSession.remembered
};

const humanAppCatalog = [
  {
    id: "cerebro",
    name: "CEREBRO",
    role: "Chief of Staff / Jefe de Gabinete IA",
    capability: "Mano derecha del CEO: coordina internamente decisiones, tareas, riesgos y prioridades.",
    preparedCopy: "Operativo interno; sin apps protegidas ni runtimes externos.",
    action: "Hablar con CEREBRO",
    lane: "real",
    priority: true,
    displayStatus: "operational_internal"
  },
  {
    id: "forja",
    name: "FORJA",
    role: "Construcción principal",
    capability: "Convierte decisiones aprobadas en entregables controlados.",
    preparedCopy: "Producción estable; no conectada desde ecosystem.",
    action: "Ver estado FORJA",
    lane: "prepared",
    displayStatus: "production_pass"
  },
  {
    id: "nube",
    name: "NUBE",
    role: "Torre de control cloud interna",
    capability: "URLs, deploys, costos, variables y backups.",
    preparedCopy: "Registra estado cloud; no despliega, no edita variables y no toca NUBE local.",
    action: "Revisar NUBE",
    lane: "prepared",
    displayStatus: "nube_internal_control_tower"
  },
  {
    id: "auditor",
    name: "AUDITORIA",
    role: "Control y calidad",
    capability: "Evidencia, permisos, riesgos y aprobaciones.",
    preparedCopy: "Preparada, sin conexión externa.",
    action: "Ver AUDITORIA",
    lane: "prepared",
    displayStatus: "discovery_prepared"
  },
  {
    id: "centinela",
    name: "SENTINELA",
    role: "Defensa del ecosistema",
    capability: "Vigila agentes, permisos, datos, prompts, incidentes y riesgos. En auditoría queda defensivo y sin meta de venta propia.",
    preparedCopy: "Representado, no conectado. pending_review / protected; sin runtime real.",
    action: "Ver SENTINELA",
    lane: "protected",
    displayStatus: "pending_review"
  },
  {
    id: "doctor_contable_financiero_tributario",
    name: "DCFT",
    role: "Contador financiero tributario de la empresa",
    capability: "Futuro responsable de contabilidad, finanzas, tributación, auditoría contable y auditoría financiera. Primer producto comercial prioritario previsto.",
    preparedCopy: "Representado, no conectado. protected_no_touch; sin SUNAT real, credenciales ni runtime.",
    action: "Revisar DCFT",
    lane: "protected",
    priority: true,
    displayStatus: "protected_no_touch"
  },
  {
    id: "hermes",
    name: "HERMES",
    role: "Apoyo ligero de construcción",
    capability: "Apoya a FORJA con preparación, coordinación y tareas técnicas ligeras.",
    preparedCopy: "Preparado, sin conexión real.",
    action: "Ver HERMES",
    lane: "prepared",
    displayStatus: "discovery_prepared"
  },
  {
    id: "pluma",
    name: "PLUMA",
    role: "Contenido y escritura",
    capability: "Prepara piezas editoriales, guiones y comunicación cuando sea conectada.",
    preparedCopy: "Preparado, sin conexión real.",
    action: "Ver ficha",
    lane: "prepared",
    displayStatus: "discovery_prepared"
  },
  {
    id: "lente",
    name: "LENTE",
    role: "Visual y audiovisual",
    capability: "Prepara mirada visual, video, análisis y criterios audiovisuales.",
    preparedCopy: "Preparado, sin conexión real.",
    action: "Ver ficha",
    lane: "prepared",
    displayStatus: "discovery_prepared"
  },
  {
    id: "web_factory",
    name: "WEB FACTORY",
    role: "Producción web",
    capability: "Prepara fabricación de sitios y experiencias digitales controladas.",
    preparedCopy: "Preparado, sin conexión real.",
    action: "Ver ficha",
    lane: "prepared",
    displayStatus: "discovery_prepared"
  },
  {
    id: "marketing",
    name: "MARKETING / GROWTH LAB",
    role: "Crecimiento y campañas",
    capability: "Prepara campañas, activación y crecimiento cuando reciba aprobación.",
    preparedCopy: "Preparado, sin conexión real.",
    action: "Ver ficha",
    lane: "prepared",
    displayStatus: "discovery_prepared"
  },
  {
    id: "marca_personal",
    name: "MARCA PERSONAL",
    role: "Marca del CEO",
    capability: "Ordena identidad, narrativa y presencia pública para ejecución futura.",
    preparedCopy: "Preparado, sin conexión real.",
    action: "Ver ficha",
    lane: "prepared",
    displayStatus: "discovery_prepared"
  },
  {
    id: "api_creator",
    name: "CREADOR DE APIS Y SKILLS",
    role: "Fábrica de APIs y skills",
    capability: "Prepara APIs internas, APIs vendibles, skills internas y skills vendibles.",
    preparedCopy: "Documentado para revisión; solo ruta interna, sin API externa real.",
    action: "Ver ficha",
    lane: "pending",
    displayStatus: "documented_only"
  },
  {
    id: "buscador_de_tendencias",
    name: "BUSCADOR DE TENDENCIAS",
    role: "Radar oficial",
    capability: "Detecta señales, oportunidades, amenazas y tendencias sin proveedores conectados.",
    preparedCopy: "Preparado, sin conexión real.",
    action: "Ver ficha",
    lane: "prepared",
    displayStatus: "discovery_prepared"
  },
  {
    id: "sniff_amazon",
    name: "SNIFF AMAZON",
    role: "Producto comercial Amazon",
    capability: "Prepara oportunidades Amazon como producto separado de Comercio Autonomo.",
    preparedCopy: "Documentado para revisión; sin acciones reales.",
    action: "Ver ficha",
    lane: "pending",
    displayStatus: "documented_only"
  },
  {
    id: "comercio_autonomo",
    name: "COMERCIO AUTONOMO",
    role: "Sistema propio de e-commerce/dropshipping/comercio",
    capability: "Prepara flujos comerciales propios sin activar ventas, pagos ni proveedores reales.",
    preparedCopy: "Preparado, sin conexión real.",
    action: "Ver ficha",
    lane: "prepared",
    displayStatus: "discovery_prepared"
  },
  {
    id: "arsenal",
    name: "ARSENAL",
    role: "Almacén estratégico",
    capability: "Inventario de APIs, modelos, skills, conectores, herramientas y capacidades.",
    preparedCopy: "planned / pending_integration; planificado, no conectado; sin cabina humana completa, runtime, secretos ni APIs reales.",
    action: "Ver Arsenal",
    lane: "pending",
    displayStatus: "pending_integration"
  }
];

const companyDepartments = [
  {
    id: "direccion",
    name: "DIRECCIÓN",
    shortName: "Dirección",
    accent: "gold",
    icon: "cerebro",
    apps: ["CEO", "CEREBRO"],
    appIds: ["cerebro"],
    function: "Decisiones, prioridades y coordinación.",
    action: "Abrir reunión",
    target: "cerebro"
  },
  {
    id: "construccion",
    name: "CONSTRUCCIÓN",
    shortName: "Construcción",
    accent: "amber",
    icon: "forja",
    apps: ["FORJA", "HERMES", "CREADOR DE APIS Y SKILLS", "WEB FACTORY"],
    appIds: ["forja", "hermes", "api_creator", "web_factory"],
    function: "Entregables, APIs, skills, webs y soporte técnico.",
    action: "Ver construcción",
    target: "forja"
  },
  {
    id: "inteligencia",
    name: "INTELIGENCIA",
    shortName: "Inteligencia",
    accent: "violet",
    icon: "buscador_de_tendencias",
    apps: ["BUSCADOR DE TENDENCIAS"],
    appIds: ["buscador_de_tendencias"],
    function: "Señales, novedades, amenazas y oportunidades.",
    action: "Ver señales",
    target: "buscador_de_tendencias"
  },
  {
    id: "productos_comerciales",
    name: "PRODUCTOS COMERCIALES",
    shortName: "Productos",
    accent: "emerald",
    icon: "doctor_contable_financiero_tributario",
    apps: ["DCFT", "SENTINELA", "SNIFF AMAZON", "COMERCIO AUTONOMO", "APIs vendibles", "Skills vendibles", "Apps vendibles"],
    appIds: ["doctor_contable_financiero_tributario", "centinela", "sniff_amazon", "comercio_autonomo", "api_creator", "arsenal"],
    function: "Activos con potencial de ingresos.",
    action: "Ver productos",
    target: "productos_comerciales"
  },
  {
    id: "contenido_crecimiento",
    name: "CONTENIDO Y CRECIMIENTO",
    shortName: "Crecimiento",
    accent: "cyan",
    icon: "lente",
    apps: ["PLUMA", "LENTE", "MARKETING", "MARCA PERSONAL"],
    appIds: ["pluma", "lente", "marketing", "marca_personal"],
    function: "Contenido, marca, campañas, video y crecimiento.",
    action: "Ver contenido",
    target: "pluma"
  },
  {
    id: "operacion",
    name: "OPERACIÓN",
    shortName: "Operación",
    accent: "cloud",
    icon: "nube",
    apps: ["NUBE"],
    appIds: ["nube"],
    function: "URLs, deploys, costos, variables, backups y health checks.",
    action: "Ver NUBE",
    target: "nube"
  },
  {
    id: "control_seguridad",
    name: "CONTROL Y SEGURIDAD",
    shortName: "Seguridad",
    accent: "military",
    icon: "centinela",
    apps: ["AUDITORIA", "SENTINELA"],
    appIds: ["auditor", "centinela"],
    function: "Calidad, riesgos, aprobación, seguridad y protección.",
    action: "Ver riesgos",
    target: "alerts"
  },
  {
    id: "almacen_estratégico",
    name: "ALMACEN ESTRATÉGICO",
    shortName: "Arsenal",
    accent: "copper",
    icon: "arsenal",
    apps: ["ARSENAL"],
    appIds: ["arsenal"],
    function: "APIs, modelos, skills, conectores, costos, límites, calidad, riesgos y mejor uso.",
    action: "Ver Arsenal",
    target: "arsenal"
  }
];

const dailyMeetingModels = {
  morning: {
    label: "Reunión de Mañana",
    headline: "CEO, esto requiere tu decisión.",
    summary: "CEREBRO separa lo real, lo preparado y lo protegido.",
    priority: "Validar cabina local sin abrir frentes nuevos.",
    decision: "Elegir siguiente revisión o pedir más evidencia.",
    opportunity: "Esto puede generar ingresos: APIs, skills y productos vendibles; sin ventas reales.",
    risk: "Esto está protegido y no se toca: DCFT, FORJA real, SENTINELA real, NUBE, Local Agent y SUNAT real.",
    approval: "Esto debe esperar aprobación CEO antes de cualquier conexión real.",
    tasks: [
      ["FORJA", "Esto puede pasar a FORJA solo como propuesta aprobada; nada real se ejecuta."],
      ["HERMES", "Puede apoyar con mensajes y coordinación ligera, sin enviar comunicaciónes reales."],
      ["CREADOR DE APIS Y SKILLS", "Debe preparar especificaciones; el bus interno no crea API externa real."],
      ["AUDITORIA", "Debe revisar evidencia, permisos y riesgos antes de avanzar."],
      ["NUBE", "Debe controlar estado documental; no tocar secretos ni deploys."],
      ["SENTINELA", "Debe proteger límites y datos; sigue pendiente de revisión."],
      ["INGRESOS", "Puede priorizar productos vendibles, manteniendo pagos y ventas reales apagados."]
    ]
  },
  evening: {
    label: "Reunión de Tarde",
    headline: "CEO, este es el cierre del día.",
    summary: "CEREBRO cierra avances locales sin prometer integraciones reales.",
    priority: "Registrar evidencia y dejar una acción concreta.",
    decision: "Mañana: definir paquete o corregir cabina.",
    opportunity: "Buscador de Tendencias queda preparado; sin APIs externas ni scraping real.",
    risk: "Esto debe auditarse antes de avanzar: bus real, proveedor, secreto o deploy.",
    approval: "Esto debe esperar aprobación CEO para pasar de preparado a ejecución.",
    tasks: [
      ["HECHO", "Se valida cabina local, documentos y pruebas locales cuando se ejecutan."],
      ["NO HECHO", "No se toca producción, no se conecta runtime externo y no se abre Local Agent."],
      ["BUSCADOR DE TENDENCIAS", "Puede reportar oportunidades preparadas, sin fuentes externas activadas."],
      ["FORJA", "No construyó en productivo; solo queda como construcción controlada futura."],
      ["HERMES", "No envió mensajes reales; puede preparar coordinación local."],
      ["CREADOR DE APIS Y SKILLS", "Preparó rutas internas seguras; no creó API externa real."],
      ["PLUMA / LENTE / MARKETING", "Pueden preparar contenido y visuales, sin publicar."],
      ["AUDITORIA / SENTINELA / NUBE", "Revisan, protegen y controlan; no ejecutan cambios reales."],
      ["MAÑANA", "Definir una sola decisión CEO y mantener DCFT protected_no_touch."]
    ]
  }
};

const dailyMeetingDataBoundaries = {
  real: ["login local", "cabina local", "App Registry", "documentos", "capturas", "validaciones locales", "CEREBRO operativo interno"],
  prepared: ["FORJA visual/preparada", "SENTINELA pendiente", "NUBE documental", "DCFT protected_no_touch", "Arsenal planned"]
};

const departmentalSimulationFlows = [
  {
    id: "ai_video_opportunity",
    title: "Oportunidad IA / Video",
    trigger: "Buscador de Tendencias detecta una nueva IA de video.",
    status: ["simulated_local", "no_runtime"],
    departments: ["Buscador de Tendencias", "CEREBRO", "ARSENAL", "FORJA", "HERMES", "PLUMA", "LENTE", "MARKETING", "AUDITORÍA", "NUBE"],
    cerebro: "CEREBRO evalúa valor, riesgo y decisión CEO antes de pedir trabajo.",
    outcome: "ARSENAL registra capacidad futura, FORJA prepara posible integración, PLUMA/LENTE/MARKETING preparan piezas locales y CEREBRO reporta al CEO.",
    guardrail: "Sin ejecución externa, sin APIs externas y sin publicación."
  },
  {
    id: "sentinela_cybersecurity",
    title: "Ciberseguridad para SENTINELA",
    trigger: "Buscador de Tendencias detecta una amenaza nueva.",
    status: ["simulated_local", "sentinela_not_real", "no_runtime"],
    departments: ["Buscador de Tendencias", "CEREBRO", "SENTINELA", "FORJA", "AUDITORÍA", "HERMES"],
    cerebro: "CEREBRO evalúa el riesgo y lo eleva al CEO.",
    outcome: "SENTINELA queda informado como protección futura; FORJA solo podría construir si el CEO aprueba.",
    guardrail: "SENTINELA no productivo, sin runtime real ni conexión de seguridad activa."
  },
  {
    id: "dcft_regulation",
    title: "Regulación DCFT",
    trigger: "Buscador de Tendencias detecta cambio SUNAT, tributario o contable.",
    status: ["simulated_local", "dcft_protected_no_touch", "no_sunat_real"],
    departments: ["Buscador de Tendencias", "CEREBRO", "DCFT", "FORJA", "AUDITORÍA"],
    cerebro: "CEREBRO separa señal, riesgo y decisión; no ordena tocar DCFT.",
    outcome: "DCFT queda marcado como producto que debería actualizarse cuando esté listo; AUDITORÍA revisa riesgo.",
    guardrail: "DCFT protegido/no-touch: no integrado, no SUNAT real y FORJA no toca DCFT sin aprobación CEO."
  },
  {
    id: "sellable_api_skill",
    title: "API / Skill vendible",
    trigger: "Buscador de Tendencias detecta demanda comercial.",
    status: ["simulated_local", "no_runtime"],
    departments: ["Buscador de Tendencias", "CEREBRO", "CREADOR DE APIS Y SKILLS", "FORJA", "ARSENAL", "WEB FACTORY", "MARKETING", "AUDITORÍA", "NUBE", "SENTINELA"],
    cerebro: "CEREBRO evalúa oportunidad, alcance y ruta de aprobación.",
    outcome: "Creador de APIs y Skills prepara idea; ARSENAL registra capacidad futura; WEB FACTORY y MARKETING preparan salida futura.",
    guardrail: "ARSENAL no runtime, sin ruta interna activa hacia ARSENAL, sin deploy y sin venta real."
  },
  {
    id: "amazon_commerce",
    title: "Producto Amazon / Comercio",
    trigger: "Sniff Amazon detecta oportunidad Amazon.",
    status: ["simulated_local", "no_runtime"],
    departments: ["SNIFF AMAZON", "CEREBRO", "COMERCIO AUTÓNOMO", "MARKETING", "AUDITORÍA", "NUBE", "SENTINELA"],
    cerebro: "CEREBRO evalúa margen, riesgo y decisión de avance.",
    outcome: "Comercio Autónomo queda como ejecutor futuro; Marketing prepara estrategia; Auditoría revisa margen/riesgo.",
    guardrail: "Sin operación comercial real, sin proveedores, sin pagos, sin Local Agent y sin SUNAT."
  }
];

const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => Array.from(document.querySelectorAll(selector));

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function normalizeStatus(value) {
  const status = String(value || "unknown").toLowerCase();
  if (["healthy", "ok", "ready", "operational", "connected", "approved", "closed", "real_operational", "operational_internal", "cerebro_operational_internal", "production_pass", "local_pass"].includes(status)) return "healthy";
  if (["degraded", "planned", "staging", "info", "pending", "pending_review", "pending_approval", "pending_integration", "prepared", "prepared_for_discovery", "discovery_prepared", "documented_only", "escalated"].includes(status)) return "degraded";
  if (["blocked", "error", "failed", "critical", "rejected", "suspended", "protected_no_touch"].includes(status)) return "blocked";
  return status;
}

function label(value) {
  const translated = {
    blocked: "En revisión CEO",
    degraded: "Degradado",
    healthy: "Saludable",
    ready: "Listo",
    operational: "Operativo",
    connected: "Conectado",
    prepared: "Preparado",
    prepared_for_discovery: "Preparado para revisión",
    discovery_prepared: "Preparado, sin conexión real",
    documented_only: "Documentado",
    protected_no_touch: "Protegido, no conectado",
    production_pass: "Producción PASS",
    local_pass: "Local PASS",
    real_operational: "Real operativo",
    operational_internal: "Operativo interno",
    cerebro_operational_internal: "CEREBRO operativo interno",
    registry_only: "Solo registry",
    no_touch_external: "Protegida",
    integration_prepared_no_runtime_connection: "Preparada sin conexión",
    external: "Externo",
    internal: "Interno",
    planned: "Planeado",
    unknown: "Desconocido",
    staging: "Staging",
    production: "Producción",
    sqlite: "SQLite",
    postgresql: "PostgreSQL",
    governance_attention_required: "Atención requerida",
    governance_ready: "Governance listo",
    pending_review: "Pendiente CEO",
    pending_approval: "Aprobación pendiente",
    pending_integration: "Integración pendiente",
    approved_for_discovery: "Discovery aprobado",
    approved_for_connection: "Conexión aprobada",
    not_ready: "No lista",
    suspended: "Suspendida",
    escalated: "Escalada",
    open: "Abierto",
    mitigated: "Mitigado",
    closed: "Cerrado",
    critical: "Crítico",
    high: "Alto",
    medium: "Medio",
    low: "Bajo",
    ceo: "CEO",
    admin: "ADMIN",
    operator: "OPERATOR",
    auditor: "AUDITOR",
    service: "SERVICE"
  };
  const key = String(value || "").toLowerCase();
  if (translated[key]) return translated[key];
  return String(value || "Pendiente").replaceAll("_", " ").replace(/\b\w/g, (char) => char.toUpperCase());
}

function statusToneFor(value, fallback = "amber") {
  const normalized = normalizeStatus(value);
  if (normalized === "healthy") return "green";
  if (normalized === "blocked") return "red";
  return fallback;
}

function appIcon(appId) {
  const common = `viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"`;
  const icons = {
    cerebro: `<svg ${common} aria-hidden="true"><path d="M8.4 6.1c-.9-.7-2.5-.4-3.1.7-.9.2-1.6 1-1.6 2 0 .5.2 1 .5 1.4-.7.4-1.1 1.1-1.1 2 0 1.1.8 2 1.8 2.2-.1 1.4 1 2.6 2.4 2.6.6 0 1.1-.2 1.5-.5"/><path d="M15.6 6.1c.9-.7 2.5-.4 3.1.7.9.2 1.6 1 1.6 2 0 .5-.2 1-.5 1.4.7.4 1.1 1.1 1.1 2 0 1.1-.8 2-1.8 2.2.1 1.4-1 2.6-2.4 2.6-.6 0-1.1-.2-1.5-.5"/><path d="M12 5.5v13"/><path d="M8.7 9.2c1.1-.3 2.2.2 3.3 1"/><path d="M15.3 9.2c-1.1-.3-2.2.2-3.3 1"/><path d="M8.5 14c1.2.2 2.4-.3 3.5-1"/><path d="M15.5 14c-1.2.2-2.4-.3-3.5-1"/></svg>`,
    forja: `<svg ${common} aria-hidden="true"><path d="M5 9h14"/><path d="M7 9l2.2 9h5.6L17 9"/><path d="M8 6h8l1 3H7l1-3Z"/><path d="M4 19h16"/><path d="M10 13h4"/></svg>`,
    auditor: `<svg ${common} aria-hidden="true"><path d="M12 3v18"/><path d="M5 6h14"/><path d="M6 6l-3 6h6L6 6Z"/><path d="M18 6l-3 6h6l-3-6Z"/><path d="M8 21h8"/></svg>`,
    nube: `<svg ${common} aria-hidden="true"><path d="M7 18h10a4 4 0 0 0 .5-8 5.5 5.5 0 0 0-10.5-1.8A4.7 4.7 0 0 0 7 18Z"/><path d="M9 14h6"/></svg>`,
    centinela: `<svg ${common} aria-hidden="true"><path d="M12 3l7 3v5c0 4.2-2.7 7.7-7 9-4.3-1.3-7-4.8-7-9V6l7-3Z"/><path d="M8.5 12s1.2-2 3.5-2 3.5 2 3.5 2-1.2 2-3.5 2-3.5-2-3.5-2Z"/><circle cx="12" cy="12" r="1"/></svg>`,
    doctor_contable_financiero_tributario: `<svg ${common} aria-hidden="true"><path d="M7 3h7l4 4v14H7z"/><path d="M14 3v5h5"/><path d="M9.5 12h5"/><path d="M9.5 15h5"/><path d="M10 18h3"/></svg>`
  };
  return `<span class="app-icon" aria-hidden="true">${icons[appId] || `<svg ${common}><circle cx="12" cy="12" r="7"/><path d="M5 12h14"/><path d="M12 5a12 12 0 0 1 0 14"/><path d="M12 5a12 12 0 0 0 0 14"/></svg>`}</span>`;
}

function authHeaders(extra = {}) {
  return {
    ...extra,
    ...(state.token ? { Authorization: `Bearer ${state.token}` } : {})
  };
}

function roleFromUser(user) {
  return String(user?.role || "SERVICE").toLowerCase();
}

function number(value) {
  if (typeof value === "number") return new Intl.NumberFormat("es").format(value);
  if (value === false) return "No";
  if (value === true) return "Si";
  return value ?? "--";
}

function badge(value, extra = "") {
  const normalized = normalizeStatus(value);
  return `<span class="badge ${normalized} ${escapeHtml(extra)}">${escapeHtml(label(value))}</span>`;
}

function apps() {
  return Array.isArray(state.data.apps) ? state.data.apps : [];
}

function integrationProfiles() {
  return Array.isArray(state.data.integrationProfiles) ? state.data.integrationProfiles : [];
}

function appById(appId) {
  return apps().find((app) => app.id === appId);
}

function profileById(appId) {
  return integrationProfiles().find((profile) => profile.app_id === appId);
}

function connectedProfiles() {
  return integrationProfiles().filter((profile) => profile.external_connection_enabled === true);
}

function disconnectedProfiles() {
  return integrationProfiles().filter((profile) => profile.external_connection_enabled !== true);
}

function humanStateFor(appId) {
  const definition = humanAppCatalog.find((item) => item.id === appId);
  const app = appById(appId);
  const profile = profileById(appId);
  if (app?.controlled_state === "operational_internal") {
    return {
      status: "operational_internal",
      tone: "green",
      source: "Operativo interno",
      copy: "CEREBRO coordina dentro del backend/control center. Sin runtime externo.",
      real: true
    };
  }
  if (profile?.external_connection_enabled === true) {
    return {
      status: "connected",
      tone: "green",
      source: "Dato real conectado",
      copy: "Conexión real habilitada y reportada por Integration Bus.",
      real: true
    };
  }
  if (profile) {
    return {
      status: definition?.displayStatus || "prepared_for_discovery",
      tone: "amber",
      source: "Preparado, sin conexión real",
      copy: "Contrato y evidencia listos. Conexión externa apagada.",
      real: false
    };
  }
  if (app?.status === "external") {
    const tone = definition?.displayStatus === "protected_no_touch" ? "red" : "amber";
    return {
      status: definition?.displayStatus || "pending_integration",
      tone,
      source: "Protegido, no conectado",
      copy: definition?.preparedCopy || "Referenciada para seguimiento. Sin conexión ni integración real.",
      real: false
    };
  }
  if (app) {
    const tone = definition?.lane === "protected" || definition?.displayStatus === "protected_no_touch" ? "red" : statusToneFor(definition?.displayStatus || app.status, "amber");
    return {
      status: definition?.displayStatus || app.status || "planned",
      tone,
      source: "App Registry",
      copy: definition?.preparedCopy || "Registrada para seguimiento. Falta aprobación antes de conectar.",
      real: false
    };
  }
  if (definition?.displayStatus === "documented_only") {
    return {
      status: "documented_only",
      tone: "amber",
      source: "Documentado para revisión",
      copy: "Visible para revisión local. Sin conexión real.",
      real: false
    };
  }
  if (definition?.displayStatus === "protected_no_touch") {
    return {
      status: "protected_no_touch",
      tone: "red",
      source: "Protegido, no conectado",
      copy: "No se toca ni se conecta sin aprobación CEO.",
      real: false
    };
  }
  return {
    status: definition?.displayStatus || "pending_integration",
    tone: "amber",
    source: "No registrada",
    copy: "Aun no aparece en el registro operativo.",
    real: false
  };
}

function nextDecision() {
  if (appById("doctor_contable_financiero_tributario") && !profileById("doctor_contable_financiero_tributario")) {
    return {
      title: "En revisión CEO",
      body: "DCFT sigue protegido; está representado, no conectado: protected_no_touch, sin SUNAT real, credenciales ni runtime."
    };
  }
  if (appById("centinela") && !profileById("centinela")) {
    return {
      title: "En revisión CEO",
      body: "SENTINELA está representado, no conectado: pending_review / protected, sin runtime productivo."
    };
  }
  if (disconnectedProfiles().length) {
    return {
      title: "Cabina lista para validar",
      body: `${disconnectedProfiles().length} perfiles preparados. Todas las conexiones externas siguen apagadas.`
    };
  }
  return {
    title: "Sin decisión urgente",
    body: "La cabina no detecta acciones ejecutivas inmediatas."
  };
}

function scrollToSection(targetId) {
  const targetMap = {
    cerebro: "cerebro-chief-of-staff",
    workday: "workday-os",
    upgrades: "department-upgrade-pipeline",
    mission: "mission-execution-loop",
    sprint: "revenue-execution-sprint",
    ecommerceamazon: "ecommerce-amazon-readiness",
    publishing: "publishing-growth-engine",
    publishingprepared: "publishing-prepared",
    marketingapproval: "marketing-approval-gate",
    readiness: "product-readiness-dcft-sentinela",
    commercialreadiness: "commercial-readiness",
    realworld: "real-world-connections",
    analyticsreadiness: "analytics-readiness",
    executionqueue: "real-world-execution-queue",
    socialidentity: "social-identity-map",
    revenue: "revenue-os",
    arsenal: "arsenal-blueprint",
    forja: "construccion",
    hermes: "construccion",
    api_creator: "construccion",
    web_factory: "construccion",
    auditor: "control_seguridad",
    centinela: "control_seguridad",
    nube: "operacion",
    buscador_de_tendencias: "inteligencia",
    sniff_amazon: "productos_comerciales",
    comercio_autonomo: "productos_comerciales",
    doctor_contable_financiero_tributario: "productos_comerciales",
    pluma: "contenido_crecimiento",
    lente: "contenido_crecimiento",
    marketing: "contenido_crecimiento",
    marca_personal: "contenido_crecimiento",
    ecosystem: "departments"
  };
  const target = document.getElementById(targetMap[targetId] || targetId);
  if (!target) return;
  target.scrollIntoView({ behavior: "smooth", block: "start" });
}

function emptyState(text, detail = "") {
  return `<div class="empty"><strong>${escapeHtml(text)}</strong>${detail ? `<small>${escapeHtml(detail)}</small>` : ""}</div>`;
}

function actionById(actionId) {
  return (state.boundary?.actions || []).find((action) => action.id === actionId);
}

function can(actionId) {
  return actionById(actionId)?.allowed === true;
}

function actionButton(actionId, labelText, targetId = "", tone = "ghost") {
  const action = actionById(actionId);
  const allowed = action?.allowed === true;
  const reason = action?.reason || "permission_not_loaded";
  return `
    <button
      class="${tone === "primary" ? "primary-action" : "mini-action"} ${allowed ? "" : "forbidden"}"
      type="button"
      data-action="${escapeHtml(actionId)}"
      data-target-id="${escapeHtml(targetId)}"
      ${allowed ? "" : "aria-disabled=\"true\""}
      title="${escapeHtml(allowed ? action.description : reason)}"
    >
      ${escapeHtml(labelText)}
    </button>
  `;
}

function listItem({ title, body, meta, status, actions = "" }) {
  return `
    <article class="list-item">
      <div class="badge-row">${status ? badge(status) : ""}${meta ? `<span class="badge">${escapeHtml(meta)}</span>` : ""}</div>
      <strong>${escapeHtml(title)}</strong>
      ${body ? `<p>${escapeHtml(body)}</p>` : ""}
      ${actions ? `<div class="item-actions">${actions}</div>` : ""}
    </article>
  `;
}

async function fetchJson(name, url) {
  const controller = new AbortController();
  const timeoutId = window.setTimeout(() => controller.abort(), DATA_FETCH_TIMEOUT_MS);
  let response;
  try {
    response = await fetch(url, {
      headers: authHeaders({ Accept: "application/json" }),
      cache: "no-store",
      signal: controller.signal
    });
  } catch (error) {
    if (error.name === "AbortError") {
      throw new Error(`${name} timeout`);
    }
    throw error;
  } finally {
    window.clearTimeout(timeoutId);
  }
  if (response.status === 401) {
    clearSession();
    showLogin("Tu sesión expiró. Entra nuevamente.");
  }
  if (!response.ok) throw new Error(`${response.status} ${response.statusText}`);
  return response.json();
}

async function allSettledLimited(items, worker, limit = DATA_FETCH_CONCURRENCY) {
  const results = new Array(items.length);
  let nextIndex = 0;
  const workers = Array.from({ length: Math.min(limit, items.length) }, async () => {
    while (nextIndex < items.length) {
      const currentIndex = nextIndex;
      nextIndex += 1;
      try {
        results[currentIndex] = {
          status: "fulfilled",
          value: await worker(items[currentIndex], currentIndex)
        };
      } catch (reason) {
        results[currentIndex] = { status: "rejected", reason };
      }
    }
  });
  await Promise.all(workers);
  return results;
}

async function loadCurrentUser() {
  if (!state.token) {
    showLogin();
    return false;
  }
  if (state.restoreAttempted) {
    setLoginStatus("Validando sesión guardada en este dispositivo.");
  }
  const response = await fetch("/api/v1/auth/me", {
    headers: authHeaders({ Accept: "application/json" }),
    cache: "no-store"
  });
  if (!response.ok) {
    clearSession();
    showLogin(state.restoreAttempted ? "La sesión guardada expiró. Entra nuevamente." : "No hay sesión activa.");
    state.restoreAttempted = false;
    return false;
  }
  state.user = await response.json();
  state.role = roleFromUser(state.user);
  state.restoredNoticePending = state.restoreAttempted;
  state.restoreAttempted = false;
  showApp();
  renderUserShell();
  return true;
}

function persistSession(token, rememberSession) {
  localStorage.removeItem(AUTH_TOKEN_KEY);
  sessionStorage.removeItem(AUTH_TOKEN_KEY);
  if (rememberSession) {
    localStorage.setItem(AUTH_TOKEN_KEY, token);
  } else {
    sessionStorage.setItem(AUTH_TOKEN_KEY, token);
  }
  state.sessionRemembered = rememberSession;
}

function clearSession() {
  state.token = "";
  state.user = null;
  state.boundary = null;
  state.restoreAttempted = false;
  state.restoredNoticePending = false;
  state.sessionRemembered = false;
  localStorage.removeItem(AUTH_TOKEN_KEY);
  sessionStorage.removeItem(AUTH_TOKEN_KEY);
}

function setLoginStatus(message = "") {
  const status = $("#login-session-status");
  status.textContent = message;
  status.classList.toggle("hidden", !message);
}

function showLogin(message = "") {
  $("#login-screen").classList.remove("hidden");
  $("#app").classList.add("hidden");
  $("#login-error").textContent = message;
  $("#login-error").classList.toggle("hidden", !message);
  if (!message) setLoginStatus("");
}

function showApp() {
  renderCompanyShell();
  $("#login-screen").classList.add("hidden");
  $("#app").classList.remove("hidden");
  setLoginStatus("");
}

function renderUserShell() {
  if (!state.user) return;
  $("#active-user-name").textContent = state.user.name;
  $("#active-user-role").textContent = label(state.user.role);
  $("#active-user-email").textContent = state.user.email;
  $("#role-boundary-copy").textContent = `Sesión real: ${state.user.name} / ${label(state.user.role)}. Cargando permisos.`;
}

async function loadData() {
  if (!state.user) {
    const hasUser = await loadCurrentUser();
    if (!hasUser) return;
  }
  setLoading();
  const boundaryUrl = `/api/v1/governance/auth-boundary?role_id=${encodeURIComponent(state.role)}`;
  const entries = [...Object.entries(endpoints), ["boundary", boundaryUrl]];
  const criticalEntries = entries.filter(([name]) => CRITICAL_DATA_NAMES.has(name));
  const secondaryEntries = entries.filter(([name]) => !CRITICAL_DATA_NAMES.has(name));

  state.data = {};
  state.errors = {};

  const applyResults = (batchEntries, results) => {
    results.forEach((result, index) => {
      const [name] = batchEntries[index];
      if (result.status === "fulfilled") {
        if (name === "boundary") state.boundary = result.value;
        else state.data[name] = result.value;
      } else {
        state.errors[name] = result.reason.message;
      }
    });
  };

  const criticalResults = await allSettledLimited(criticalEntries, ([name, url]) => fetchJson(name, url));
  applyResults(criticalEntries, criticalResults);
  state.lastUpdated = new Date();
  render();

  const secondaryResults = await allSettledLimited(secondaryEntries, ([name, url]) => fetchJson(name, url));
  applyResults(secondaryEntries, secondaryResults);
  state.lastUpdated = new Date();
  render();
  if (state.restoredNoticePending) {
    state.restoredNoticePending = false;
    showFeedback("Sesión restaurada en este dispositivo.", "success");
  }
}

function setLoading() {
  const banner = $("#state-banner");
  banner.className = "state-banner loading";
  banner.innerHTML = `
    <span class="pulse"></span>
    <strong>Local / revisión CEO</strong>
    <small>Preparando cabina local.</small>
  `;
}

function render() {
  renderCompanyShell();
  renderStatus();
  renderRoleBoundary();
  renderExecutiveHome();
  renderMetrics();
  renderApps();
  renderAlerts();
  renderCeo();
  renderGovernance();
  renderOperator();
  renderAuditor();
  renderSystem();
  renderNubeControlTower();
  renderView();
  bindActionButtons();
}

function setText(selector, text) {
  const element = $(selector);
  if (element) element.textContent = text;
}

function renderCompanyShell() {
  setText(".brand strong", "Empresa IA");
  setText(".brand small", "Centro CEO");
  const topbar = $(".topbar");
  if (topbar && !topbar.querySelector(".mobile-brand-chip")) {
    topbar.insertAdjacentHTML("afterbegin", `
      <div class="mobile-brand-chip" aria-label="Empresa IA local">
        <span class="brand-mark ecosystem-mark" aria-hidden="true"><span class="globe-core"></span></span>
        <span>
          <strong>Empresa IA</strong>
          <small>Local / revisión CEO</small>
        </span>
      </div>
    `);
  }
  setText(".topbar .eyebrow", "Empresa IA");
  setText(".topbar h1", "Local / revisión CEO");
  setText(".topbar p", "Cabina ejecutiva local. Sin producción tocada.");
  setText(".search-box span", "Buscar");
  const search = $("#search");
  if (search) search.placeholder = "Buscar...";

  const hero = $(".hero-card");
  if (hero) hero.id = "cerebro";
  const heroActions = $(".hero-actions");
  if (heroActions) {
    heroActions.innerHTML = `
      <div class="cerebro-chips" aria-label="Resumen CEREBRO">
        <span>Decisiones</span>
        <span>Oportunidades</span>
        <span>Riesgos</span>
      </div>
      <button class="primary-action" data-quick="cerebro" type="button">Hablar con CEREBRO</button>
    `;
  }

  const quickBand = $(".quick-actions-band");
  if (quickBand) quickBand.id = "opportunities";
  setText(".quick-actions-band .eyebrow", "Mando rapido");
  setText(".quick-actions-band h2", "Acciones");

  const departmentsBand = $(".priority-apps-band");
  if (departmentsBand) departmentsBand.id = "departments";
  setText(".priority-apps-band .eyebrow", "Departamentos");
  setText(".priority-apps-band h2", "Áreas clave");

  setText(".status-lanes-band .eyebrow", "Datos separados");
  setText(".status-lanes-band h2", "Estados");
  setText("#ecosystem .eyebrow", "Mapa técnico");
  setText("#ecosystem h2", "Registro protegido y fuente del dato");
  setText("#alerts .eyebrow", "Riesgos");
  setText("#alerts h2", "Alertas ejecutivas");
  setText(".rail-primary-actions .eyebrow", "Mando rapido");
  setText(".rail-primary-actions h2", "Acciones CEO");
  setText(".decision-rail .rail-panel:nth-of-type(2) .eyebrow", "Departamentos");
  setText(".decision-rail .rail-panel:nth-of-type(2) h2", "Áreas clave");
  setText(".decision-rail .rail-panel:nth-of-type(3) .eyebrow", "Decisiones y riesgos");
  setText(".decision-rail .rail-panel:nth-of-type(3) h2", "Control humano");

  const viewLabels = [
    ["ceo", "Inicio"],
    ["governance", "CEREBRO"],
    ["operator", "Departamentos"],
    ["auditor", "Riesgos"],
    ["system", "Decisiones"]
  ];
  viewLabels.forEach(([view, text]) => {
    const button = $(`#view-tabs button[data-view="${view}"]`);
    if (button) button.textContent = text;
  });

  const bottomItems = [
    ["top", "Inicio"],
    ["cerebro", "CEREBRO"],
    ["revenue", "Revenue"],
    ["alerts", "Riesgos"],
    ["profile", "Perfil"]
  ];
  $$("#bottom-nav button").forEach((button, index) => {
    const item = bottomItems[index];
    if (!item) return;
    button.dataset.bottomTarget = item[0];
    button.textContent = item[1];
  });
}

function companySnapshot() {
  const governance = state.data.governance || {};
  const decisions = Array.isArray(state.data.decisions) ? state.data.decisions : [];
  const risks = Array.isArray(state.data.risks) ? state.data.risks : [];
  const pendingDecisions = decisions.filter((item) => !["approved", "rejected", "closed"].includes(String(item.status || "").toLowerCase())).length
    || governance.pending_decisions?.length
    || 0;
  const activeRisks = risks.filter((risk) => String(risk.status || "").toLowerCase() !== "closed").length
    || governance.critical_risks?.length
    || 0;
  const preparedOpportunities = humanAppCatalog.filter((definition) => (
    ["sniff_amazon", "comercio_autonomo", "api_creator", "buscador_de_tendencias", "arsenal"].includes(definition.id)
  )).length;
  const constructionTasks = companyDepartments.find((department) => department.id === "construccion")?.appIds.length || 0;
  return {
    pendingDecisions,
    activeRisks,
    preparedOpportunities,
    constructionTasks,
    connected: connectedProfiles().length,
    prepared: integrationProfiles().length
  };
}

function departmentState(department) {
  const snapshot = companySnapshot();
  const tones = department.appIds.map((appId) => humanStateFor(appId).tone);
  const hasRed = tones.includes("red");
  const hasAmber = tones.includes("amber");
  let tone = hasRed ? "red" : hasAmber ? "amber" : "green";
  let status = "Estable";
  let issues = department.appIds.length;

  if (department.id === "direccion") {
    tone = snapshot.pendingDecisions ? "amber" : "green";
    status = snapshot.pendingDecisions ? "Decisión pendiente" : "Agenda clara";
    issues = snapshot.pendingDecisions;
  } else if (department.id === "construccion") {
    tone = "amber";
    status = "Preparado";
    issues = department.appIds.length;
  } else if (department.id === "inteligencia") {
    tone = "amber";
    status = "Radar preparado";
    issues = 1;
  } else if (department.id === "productos_comerciales") {
    tone = "amber";
    status = "Oportunidades preparadas";
    issues = snapshot.preparedOpportunities;
  } else if (department.id === "control_seguridad") {
    tone = snapshot.activeRisks ? "red" : "green";
    status = snapshot.activeRisks ? "Riesgo activo" : "Protegido";
    issues = snapshot.activeRisks;
  } else if (department.id === "almacen_estratégico") {
    tone = "amber";
    status = "Planned / pending integration";
    issues = 1;
  } else if (department.id === "operacion") {
    tone = "amber";
    status = "Documentado";
    issues = 1;
  }

  return { tone, status, issues };
}

function renderStatus() {
  const runtime = state.data.runtime || {};
  const readiness = state.data.readiness || {};
  const control = state.data.controlCenter || {};
  const hasErrors = Object.keys(state.errors).length > 0;
  const status = hasErrors ? "error" : normalizeStatus(runtime.status || readiness.status);
  const db = runtime.database || readiness.dependencies?.database || {};
  const snapshot = companySnapshot();

  $("#state-banner").className = `state-banner ${status === "healthy" ? "ready" : status}`;
  $("#state-banner").innerHTML = `
    <span class="pulse"></span>
    <strong>${hasErrors ? "Cabina local con áreas en revisión" : "Local / revisión CEO"}</strong>
    <small>${hasErrors ? "Revisión local" : "Sin conexión real"}</small>
  `;

  $("#global-status").textContent = "Reunión con CEREBRO";
  $("#global-summary").textContent = "Buenos dias, CEO. Tengo tu resumen.";
  $("#next-decision").innerHTML = `
    <span>Próxima decisión CEO</span>
    <strong>En revisión CEO</strong>
    <small>DCFT, SENTINELA y ARSENAL visibles como representados o planificados; ninguno conectado.</small>
  `;
  $("#sidebar-readiness").textContent = label(readiness.status || control.readiness?.status || "ready");
  $("#sidebar-db").textContent = `${snapshot.connected} reales · ${snapshot.prepared} preparados`;
}

function renderRoleBoundary() {
  const boundary = state.boundary;
  const allowedActions = (boundary?.actions || []).filter((action) => action.allowed).length;
  const totalActions = boundary?.actions?.length || 0;
  $("#role-boundary-copy").textContent = boundary
    ? `${allowedActions}/${totalActions} acciones habilitadas. Vistas: ${boundary.views_allowed.map(label).join(", ")}.`
    : "Boundary de permisos pendiente.";

  $$("#view-tabs button").forEach((button) => {
    const view = button.dataset.view;
    const allowed = !boundary || boundary.views_allowed.includes(view);
    button.classList.toggle("restricted", !allowed);
    button.disabled = !allowed;
  });
  if (boundary && !boundary.views_allowed.includes(state.view)) {
    state.view = boundary.views_allowed[0] || "system";
  }
}

function renderExecutiveHome() {
  renderCeoDailyCenter();
  renderWorkdayOs();
  renderCerebroChiefOfStaff();
  renderMissionExecutionLoop();
  renderDepartmentUpgradePipeline();
  renderRevenueSprint();
  renderEcommerceAmazonReadiness();
  renderPublishingGrowth();
  renderPublishingPrepared();
  renderMarketingApprovalGate();
  renderProductReadiness();
  renderCommercialReadiness();
  renderRealWorldConnections();
  renderAnalyticsReadiness();
  renderRealWorldExecutionQueue();
  renderSocialIdentityMap();
  renderRevenueOs();
  renderArsenalBlueprint();
  renderDepartmentAudits();
  renderTrafficLights();
  renderCerebroDailyMeeting();
  renderCerebroOperational();
  renderQuickActions();
  renderPriorityApps();
  renderDepartmentalSimulationFlows();
  renderStatusLanes();
  renderDecisionRail();
}

function renderCeoDailyCenter() {
  const summary = $("#ceo-daily-center-summary");
  const actions = $("#ceo-daily-center-actions");
  if (!summary || !actions) return;

  const center = state.data.ceoDailyCenter || {};
  const morning = center.morning || state.data.ceoMorning || {};
  const evening = center.evening || state.data.ceoEvening || {};
  const decisions = Array.isArray(center.decisions) ? center.decisions : [];
  const morningDecisions = Array.isArray(morning.decisions) ? morning.decisions : [];
  const risks = Array.isArray(morning.risks) ? morning.risks : [];
  const tasks = Array.isArray(morning.tasks) ? morning.tasks : [];
  const blockages = Array.isArray(morning.blockages) ? morning.blockages : [];
  const opportunities = Array.isArray(morning.opportunities) ? morning.opportunities : [];
  const nube = center.nube || {};
  const auditoria = center.auditoria || {};
  const revenue = center.revenue || state.data.revenueStatus || {};
  const revenueSprint = center.revenue_sprint || state.data.revenueSprintStatus || {};
  const ecommerceReadiness = center.ecommerce_readiness || state.data.ecommerceReadinessStatus || {};
  const amazonReadiness = center.amazon_readiness || state.data.amazonReadinessStatus || {};
  const publishing = center.publishing || state.data.publishingStatus || {};
  const productReadiness = center.product_readiness || state.data.productReadinessStatus || {};
  const realWorld = center.real_world || state.data.realWorldStatus || {};
  const realWorldExecution = center.real_world_execution || state.data.realWorldExecutionStatus || {};
  const socialIdentity = center.social_identity || state.data.socialIdentityStatus || {};
  const missionReport = center.missions || state.data.missionDailyReport || {};
  const activeMissions = Array.isArray(state.data.missionsActive) ? state.data.missionsActive : [];
  const workday = center.workday || state.data.workdayStatus || {};
  const upgrades = center.upgrades || state.data.upgradesStatus || {};
  const firstDecision = decisions[0] || morningDecisions[0];
  const firstRisk = risks[0];
  const firstTask = tasks[0];
  const firstBlockage = blockages[0];
  const firstOpportunity = opportunities[0];
  const compactTask = firstTask
    ? (String(firstTask.title || "").includes("CREADOR_DE_APIS_Y_SKILLS") ? "APIs y Skills" : firstTask.title)
    : "";
  const compactOpportunity = firstOpportunity
    ? (String(firstOpportunity.title || "").includes("CREADOR_DE_APIS_Y_SKILLS") ? "APIs y Skills" : firstOpportunity.title)
    : "";
  const compactBlockage = firstBlockage
    ? (String(firstBlockage.title || "").includes("Doctor Contable") ? "DCFT" : firstBlockage.title)
    : "";
  const compactNextAction = (center.next_action || morning.cerebro_recommendation || evening.cerebro_recommendation || "CEO, pide reporte a CEREBRO.")
    .replace("CEO, esto requiere tu decisión: revisar decisiones pendientes y mantener bloqueadas apps protegidas.", "CEO, revisa decisiones y mantiene apps protegidas.");

  summary.innerHTML = [
    listItem({
      title: "Centro Diario del CEO",
      body: `${number(center.decisions_waiting_ceo)} decisiones | ${number(center.risks)} riesgos | ${number(center.opportunities)} oportunidades | ${number(center.blocked_items)} bloqueos.`,
      status: "internal",
      meta: "10 segundos"
    }),
    listItem({
      title: "Decisión pendiente",
      body: firstDecision
        ? `${firstDecision.title || firstDecision.reference}: requiere CEO.`
        : "Sin decisiones pendientes.",
      status: firstDecision?.status || "ready",
      meta: `${number(center.decisions_waiting_ceo)} esperando`
    }),
    listItem({
      title: "Riesgos y bloqueos",
      body: firstBlockage
        ? `${compactBlockage}: bloqueado.`
        : (firstRisk ? `${firstRisk.title}: ${label(firstRisk.status)}` : "Sin riesgo crítico nuevo."),
      status: firstBlockage?.status || firstRisk?.status || "healthy",
      meta: `${number(center.blocked_items)} bloqueos`
    }),
    listItem({
      title: "AUDITORÍA y NUBE",
      body: `AUDITORÍA: ${number(auditoria.queue)} cola / ${number(auditoria.blocked_reviews)} bloqueadas. NUBE: ${nube.production_public_status || "unknown"}.`,
      status: auditoria.blocked_reviews ? "warning" : "healthy",
      meta: "evidencia"
    }),
    listItem({
      title: "Tareas y oportunidades",
      body: firstTask
        ? `${compactTask}: ${label(firstTask.status)}.`
        : (firstOpportunity ? `${compactOpportunity}: oportunidad preparada.` : `Revenue OS: pipeline global USD ${number(revenue.estimated_global_pipeline_usd || 0)}.`),
      status: firstTask?.status || firstOpportunity?.status || "prepared",
      meta: `${number(center.active_tasks)} tareas`
    }),
    listItem({
      title: "Mission Execution Loop",
      body: activeMissions[0]
        ? `${activeMissions[0].title}: ${label(activeMissions[0].status)}.`
        : `${number(missionReport.active_missions || 0)} misiones activas; sin ejecución externa.`,
      status: activeMissions[0]?.status || "internal",
      meta: `${number(missionReport.waiting_audit || 0)} auditoría / ${number(missionReport.waiting_forge || 0)} FORJA`
    }),
    listItem({
      title: "Workday OS",
      body: `Día ${workday.date || "local"}: ${number(workday.relevant_alerts || 0)} alertas relevantes, ${number(workday.priority_changes || 0)} cambios de prioridad.`,
      status: workday.scheduler_status || "prepared",
      meta: workday.manual_trigger_available ? "manual" : "scheduler"
    }),
    listItem({
      title: "Upgrade Pipeline",
      body: `${number(upgrades.packages || 0)} paquetes, ${number(upgrades.open_gaps || 0)} brechas abiertas; FORJA preparada y AUDITORÍA revisa.`,
      status: upgrades.status || "prepared",
      meta: `${number(upgrades.waiting_audit || 0)} auditoría`
    }),
    listItem({
      title: "Revenue Sprint 30 días",
      body: `${number(revenueSprint.routes || 0)} rutas, ${number(revenueSprint.missions || 0)} misiones; ingresos reales 0.`,
      status: revenueSprint.sprint_status || "prepared",
      meta: `${number(revenueSprint.approval_needed || 0)} aprobación`
    }),
    listItem({
      title: "E-Commerce & Amazon",
      body: `E-commerce USD ${number(ecommerceReadiness.monthly_goal_usd || 10000)} separado; ${number(ecommerceReadiness.opportunities || 0)} oportunidades. Amazon radar: ${number(amazonReadiness.opportunities || 0)} senales.`,
      status: ecommerceReadiness.status || "prepared",
      meta: `${number(ecommerceReadiness.approval_needed || 0)} CEO`
    }),
    listItem({
      title: "Publishing & Growth",
      body: `${number(publishing.content_items || 0)} contenidos, ${number(publishing.channels || 0)} canales; publicaciones reales no inventadas.`,
      status: publishing.status || "prepared",
      meta: `${number(publishing.approvals_needed || 0)} aprobación`
    }),
    listItem({
      title: "Siguiente acción",
      title: "Readiness DCFT/SENTINELA",
      body: `${number(productReadiness.open_gaps || 0)} brechas; MARKETING vende, productos validan evidencia.`,
      status: productReadiness.status || "requires_validation",
      meta: `${number(productReadiness.requires_validation || 0)} validaciones`
    }),
    listItem({
      title: "Real World Connections",
      body: `${number(realWorld.total_connections || 0)} conexiones; ${number(realWorld.needs_ceo || 0)} requieren CEO, ${number(realWorld.needs_credentials || 0)} credenciales.`,
      status: realWorld.status || "prepared",
      meta: `${number(realWorld.needs_paid_approval || 0)} dinero`
    }),
    listItem({
      title: "Execution Queue",
      body: `${number(realWorldExecution.total_items || 0)} acciones; ${number(realWorldExecution.ready_internal || 0)} internas, ${number(realWorldExecution.approval_needed || 0)} requieren CEO.`,
      status: realWorldExecution.status || "prepared",
      meta: `${number(realWorldExecution.blocked || 0)} bloqueadas`
    }),
    listItem({
      title: "Social Identity Map",
      body: `${number(socialIdentity.total_accounts || 0)} cuentas/canales; ${number(socialIdentity.unknown || 0)} unknown, ${number(socialIdentity.proposed_new || 0)} propuestas.`,
      status: socialIdentity.status || "prepared",
      meta: `${number(socialIdentity.needs_ceo || 0)} CEO`
    }),
    listItem({
      title: "Siguiente accion",
      body: compactNextAction,
      status: "waiting_ceo",
      meta: "CEREBRO"
    })
  ].join("");

  actions.innerHTML = [
    { label: "Pedir reporte", target: "cerebro", detail: "CEREBRO" },
    { label: "Workday", target: "workday", detail: "Día" },
    { label: "Upgrades", target: "upgrades", detail: "Brechas" },
    { label: "Misiones", target: "mission", detail: "Loop" },
    { label: "Sprint 30 días", target: "sprint", detail: "Ingresos" },
    { label: "E-Commerce", target: "ecommerceamazon", detail: "S.5" },
    { label: "Publishing", target: "publishing", detail: "Contenido" },
    { label: "Readiness", target: "readiness", detail: "DCFT/SENT" },
    { label: "Conexiones", target: "realworld", detail: "S.1" },
    { label: "Ejecucion", target: "executionqueue", detail: "S.8" },
    { label: "Identidad", target: "socialidentity", detail: "S.2" },
    { label: "Revenue OS", target: "revenue", detail: "Ingresos" },
    { label: "Ver decisiones", target: "ceo-daily-center", detail: "CEO" },
    { label: "Ver AUDITORÍA", target: "auditor", detail: "Evidencia" },
    { label: "Ver NUBE", target: "nube", detail: "Cloud" },
    { label: "Ver riesgos", target: "alerts", detail: "Bloqueos" }
  ].map((action) => `
    <button class="mini-action" data-quick-target="${escapeHtml(action.target)}" type="button">
      <strong>${escapeHtml(action.label)}</strong>
      <span>${escapeHtml(action.detail)}</span>
    </button>
  `).join("");
}

function renderWorkdayOs() {
  const container = $("#workday-os-grid");
  if (!container) return;

  const status = state.data.workdayStatus || state.data.ceoDailyCenter?.workday || {};
  const morning = state.data.workdayMorning || {};
  const midday = state.data.workdayMidday || {};
  const evening = state.data.workdayEvening || {};
  const alerts = Array.isArray(state.data.workdayAlerts) ? state.data.workdayAlerts : [];
  const priorities = Array.isArray(state.data.workdayPriorityChanges) ? state.data.workdayPriorityChanges : [];
  const report = state.data.workdayReport || {};
  const revenue = status.revenue_progress || {};
  const ecommerce = status.ecommerce_progress || {};
  const blockers = Array.isArray(status.blockers) ? status.blockers : [];
  const ceoRequests = Array.isArray(status.CEO_requests) ? status.CEO_requests : [];
  const topAlert = alerts[0];
  const topPriority = priorities[0];

  container.innerHTML = `
    <article class="workday-os-card primary">
      <span class="eyebrow">Workday OS</span>
      <strong>${escapeHtml(status.date || "Día local")}</strong>
      <p>CEREBRO opera mañana, mediodía y tarde/noche. Scheduler preparado; disparo manual disponible.</p>
      <div class="workday-kpis">
        <small><b>${number(status.active_missions || 0)}</b>misiones</small>
        <small><b>${number(status.relevant_alerts || alerts.length)}</b>alertas</small>
        <small><b>${number(status.priority_changes || priorities.length)}</b>prioridades</small>
      </div>
    </article>
    <article class="workday-os-card">
      <span class="eyebrow">Mañana 08:00</span>
      <strong>${escapeHtml(morning.headline || "Plan pendiente")}</strong>
      <p>${escapeHtml(morning.summary || "Meta USD 6,000 global y USD 10,000 e-commerce; revisar misiones y riesgos.")}</p>
      <small>${escapeHtml(morning.report || "manual_trigger_available=true")}</small>
    </article>
    <article class="workday-os-card">
      <span class="eyebrow">Mediodía 13:00</span>
      <strong>${escapeHtml(midday.headline || "Checkpoint preparado")}</strong>
      <p>${escapeHtml(midday.report || "Avances, cambios de prioridad, bloqueos y alertas relevantes.")}</p>
      <small>CEREBRO puede cambiar prioridad sin aprobación si no hay gasto real.</small>
    </article>
    <article class="workday-os-card">
      <span class="eyebrow">Tarde/Noche 19:00</span>
      <strong>${escapeHtml(evening.headline || "Reporte preparado")}</strong>
      <p>${escapeHtml(evening.report || report.status || "Qué se hizo, qué se bloqueó y plan de mañana.")}</p>
      <small>Sin publicación externa, pagos, SUNAT ni APIs con costo.</small>
    </article>
    <article class="workday-os-card">
      <span class="eyebrow">Alertas</span>
      <strong>${escapeHtml(topAlert?.title || "Sin alerta relevante")}</strong>
      <p>${topAlert ? escapeHtml(topAlert.why_it_matters) : "CEREBRO filtra ruido y no interrumpe señales bajas."}</p>
      <small>${topAlert ? `${number(topAlert.relevance_score)} score / ${label(topAlert.category)}` : "solo alto impacto"}</small>
    </article>
    <article class="workday-os-card">
      <span class="eyebrow">Prioridad</span>
      <strong>${escapeHtml(topPriority?.new_priority || "Sin cambio nuevo")}</strong>
      <p>${topPriority ? escapeHtml(topPriority.reason) : "El tiempo es dinero: CEREBRO puede reordenar el día y reportarlo."}</p>
      <small>${topPriority ? "audit registrado" : "no requiere CEO si es interno"}</small>
    </article>
    <article class="workday-os-card">
      <span class="eyebrow">Ingresos</span>
      <strong>USD ${number(revenue.pipeline_usd || 0)} / ${number(revenue.goal_usd || 6000)}</strong>
      <p>E-commerce separado: USD ${number(ecommerce.pipeline_usd || 0)} / ${number(ecommerce.goal_usd || 10000)}.</p>
      <small>No se declaran ingresos reales sin evidencia.</small>
    </article>
    <article class="workday-os-card wide">
      <span class="eyebrow">Bloqueos y CEO</span>
      <p>${
        (ceoRequests.length ? ceoRequests : blockers).slice(0, 5)
          .map((item) => `<span>${escapeHtml(item)}</span>`)
          .join("") || "<span>Sin bloqueo crítico nuevo</span>"
      }</p>
      <small>Dinero real, riesgo sensible, SUNAT, cuentas externas y APIs con costo esperan aprobación CEO.</small>
    </article>
  `;
}

function renderCerebroChiefOfStaff() {
  const container = $("#cerebro-chief-grid");
  if (!container) return;

  const chiefFromCeo = state.data.ceoDailyCenter?.cerebro?.chief_of_staff || {};
  const chief = Object.keys(state.data.cerebroChief || {}).length
    ? state.data.cerebroChief
    : chiefFromCeo;
  const goals = Array.isArray(chief.company_goals) ? chief.company_goals : [];
  const departments = Array.isArray(chief.department_goals) ? chief.department_goals : [];
  const missions = Array.isArray(chief.active_missions) ? chief.active_missions : [];
  const alerts = Array.isArray(chief.alerts) ? chief.alerts : [];
  const approvals = Array.isArray(chief.approval_requests) ? chief.approval_requests : [];
  const authority = Array.isArray(chief.authority_matrix) ? chief.authority_matrix : [];
  const noApproval = authority.filter((item) => item.level === "NO_APPROVAL_REQUIRED");
  const ceoRequired = authority.filter((item) => item.level === "CEO_APPROVAL_REQUIRED");
  const globalGoal = goals.find((goal) => goal.ecommerce_separate === false) || goals[0] || {};
  const ecommerceGoal = goals.find((goal) => goal.ecommerce_separate === true) || {};
  const topMission = missions[0];
  const topAlert = alerts[0];
  const topApproval = approvals[0];

  container.innerHTML = `
    <article class="cerebro-chief-card primary">
      <span class="eyebrow">Chief of Staff OS</span>
      <strong>${escapeHtml(chief.motto || "El tiempo es dinero")}</strong>
      <p>${escapeHtml(chief.autonomy_summary || "CEREBRO puede mover misiones internas sin gasto real ni runtime externo.")}</p>
      <div class="chief-kpis">
        <small><b>${number(globalGoal.monthly_target_usd)}</b>USD meta global</small>
        <small><b>${number(ecommerceGoal.monthly_target_usd)}</b>USD e-commerce</small>
      </div>
    </article>
    <article class="cerebro-chief-card">
      <span class="eyebrow">Misiones</span>
      <strong>${number(missions.length)} activas</strong>
      <p>${topMission ? `${topMission.title}: ${label(topMission.state)}` : "Sin misión activa; CEREBRO puede crear una desde instrucción CEO."}</p>
      <small>${topMission ? escapeHtml(topMission.relation_to_monthly_goal || "Impacto por estimar.") : "Preparado localmente."}</small>
    </article>
    <article class="cerebro-chief-card">
      <span class="eyebrow">Alertas útiles</span>
      <strong>${number(alerts.length)} relevantes</strong>
      <p>${topAlert ? `${topAlert.title}: ${label(topAlert.relevance)}` : "Las señales bajas no interrumpen al CEO."}</p>
      <small>${topAlert ? `DAFO y matriz económica disponibles.` : "Filtro por relevancia activo."}</small>
    </article>
    <article class="cerebro-chief-card">
      <span class="eyebrow">Aprobación CEO</span>
      <strong>${number(approvals.length)} sensibles</strong>
      <p>${topApproval ? `${topApproval.title}: ${label(topApproval.status)}` : "Sin dinero real pendiente."}</p>
      <small>Pagos, campañas pagadas, credenciales y riesgo alto esperan decisión CEO.</small>
    </article>
    <article class="cerebro-chief-card">
      <span class="eyebrow">Autonomía</span>
      <strong>${number(noApproval.length)} acciones sin aprobación</strong>
      <p>Prioridades, misiones, tareas a FORJA, posts orgánicos y deploy controlado quedan preparados.</p>
      <small>${number(ceoRequired.length)} tipos requieren CEO.</small>
    </article>
    <article class="cerebro-chief-card wide">
      <span class="eyebrow">Departamentos</span>
      <p>${departments.slice(0, 12).map((item) => `<span>${escapeHtml(item.department)}</span>`).join("")}</p>
      <small>Todos preparados: sin runtime externo, sin SUNAT real y sin secretos.</small>
    </article>
  `;
}

function renderMissionExecutionLoop() {
  const container = $("#mission-loop-grid");
  if (!container) return;

  const report = state.data.missionDailyReport || state.data.ceoDailyCenter?.missions || {};
  const active = Array.isArray(state.data.missionsActive) ? state.data.missionsActive : [];
  const missions = active.length ? active : (Array.isArray(report.missions) ? report.missions : []);
  const topMission = missions[0];
  const topSteps = Array.isArray(topMission?.steps) ? topMission.steps.slice(0, 3) : [];
  const topAssignments = Array.isArray(topMission?.assignments) ? topMission.assignments.slice(0, 4) : [];
  const activeCount = report.active_missions ?? missions.length;
  const waitingAudit = report.waiting_audit ?? missions.filter((item) => item.status === "waiting_audit").length;
  const waitingForge = report.waiting_forge ?? missions.filter((item) => item.status === "waiting_forge").length;
  const waitingCeo = report.waiting_ceo_approval ?? missions.filter((item) => item.status === "waiting_ceo_approval").length;
  const unknownImpact = report.economic_impact_unknown ?? missions.filter((item) => item.expected_business_impact === "unknown").length;

  container.innerHTML = `
    <article class="mission-loop-card primary">
      <span class="eyebrow">Mission Execution Loop</span>
      <strong>${number(activeCount)} misiones activas</strong>
      <p>CEO -> CEREBRO -> misión -> departamentos -> AUDITORÍA -> FORJA preparada -> reporte CEO.</p>
      <div class="mission-loop-kpis">
        <small><b>${number(waitingAudit)}</b>auditoría</small>
        <small><b>${number(waitingForge)}</b>FORJA</small>
        <small><b>${number(waitingCeo)}</b>CEO</small>
      </div>
    </article>
    <article class="mission-loop-card">
      <span class="eyebrow">Misión prioritaria</span>
      <strong>${escapeHtml(topMission?.title || "Sin misión activa")}</strong>
      <p>${topMission ? escapeHtml(topMission.next_action || "CEREBRO reporta siguiente acción.") : "CEREBRO puede crear misiones internas desde una orden del CEO."}</p>
      <small>${topMission ? `${label(topMission.status)} / ${escapeHtml(topMission.leader_department)}` : "Preparado localmente."}</small>
    </article>
    <article class="mission-loop-card">
      <span class="eyebrow">Departamentos</span>
      <strong>${number(topMission?.involved_departments?.length || 0)} involucrados</strong>
      <p>${
        (topAssignments.length ? topAssignments.map((item) => item.department) : topMission?.involved_departments || [])
          .slice(0, 6)
          .map((item) => `<span>${escapeHtml(item)}</span>`)
          .join("") || "<span>CEREBRO</span><span>AUDITORÍA</span>"
      }</p>
      <small>Asignaciones internas; sin runtime externo ni APIs reales.</small>
    </article>
    <article class="mission-loop-card">
      <span class="eyebrow">Pasos</span>
      <strong>${number(topMission?.steps?.length || 0)} pasos</strong>
      <p>${topSteps.map((step) => `${escapeHtml(step.owner_department)}: ${escapeHtml(step.title)}`).join("<br>") || "Plan pendiente de CEREBRO."}</p>
      <small>Estados: planned, assigned, in_progress, waiting_audit, waiting_forge.</small>
    </article>
    <article class="mission-loop-card">
      <span class="eyebrow">Revenue</span>
      <strong>${number(topMission?.revenue_links?.length || 0)} links</strong>
      <p>${topMission?.expected_business_impact && topMission.expected_business_impact !== "unknown" ? escapeHtml(topMission.expected_business_impact) : "Impacto económico por estimar; no se inventan ventas."}</p>
      <small>${number(unknownImpact)} misiones requieren matriz económica.</small>
    </article>
    <article class="mission-loop-card wide">
      <span class="eyebrow">Autonomía y límites</span>
      <p><span>Local Agent interno preparado</span><span>FORJA interna permitida</span><span>AUDITORÍA interna permitida</span><span>dinero real bloqueado</span><span>SUNAT bloqueado</span><span>APIs externas bloqueadas</span></p>
      <small>CEREBRO avanza sin pedir permiso solo cuando no hay gasto real, secreto, cuenta externa ni riesgo legal alto.</small>
    </article>
  `;
}

function renderDepartmentUpgradePipeline() {
  const container = $("#department-upgrade-grid");
  if (!container) return;

  const status = state.data.upgradesStatus || state.data.ceoDailyCenter?.upgrades || {};
  const packages = Array.isArray(state.data.upgradesPackages) ? state.data.upgradesPackages : [];
  const topPackage = packages[0] || (Array.isArray(status.top_packages) ? status.top_packages[0] : null);
  const topGaps = Array.isArray(topPackage?.gaps) ? topPackage.gaps.slice(0, 3) : [];
  const changes = Array.isArray(topPackage?.required_changes) ? topPackage.required_changes.slice(0, 3) : [];
  const supported = Array.isArray(status.supported_departments) ? status.supported_departments : [];
  const nextAction = topPackage
    ? (topPackage.status === "sent_to_forja"
      ? "Esperar evidencia o mantener pending_execution."
      : topPackage.status === "implemented_pending_audit"
        ? "AUDITORÍA debe revisar antes de aprobar."
        : topPackage.status === "waiting_audit"
          ? "AUDITORÍA revisa el paquete."
          : "Enviar paquete preparado a FORJA si aplica.")
    : "AUDITORÍA debe generar brechas para crear paquetes.";

  container.innerHTML = `
    <article class="upgrade-pipeline-card primary">
      <span class="eyebrow">Department Upgrade Pipeline</span>
      <strong>${number(status.packages || packages.length)} paquetes</strong>
      <p>AUDITORÍA detecta brecha, CEREBRO prioriza, FORJA recibe tarea preparada, AUDITORÍA revisa y CEREBRO reporta CEO.</p>
      <div class="upgrade-kpis">
        <small><b>${number(status.open_gaps || 0)}</b>brechas</small>
        <small><b>${number(status.waiting_forge || 0)}</b>FORJA</small>
        <small><b>${number(status.waiting_audit || 0)}</b>AUDITORÍA</small>
      </div>
    </article>
    <article class="upgrade-pipeline-card">
      <span class="eyebrow">Paquete</span>
      <strong>${escapeHtml(topPackage?.department || "Sin paquete activo")}</strong>
      <p>${topPackage ? escapeHtml(topPackage.business_impact) : "Crear paquete desde brecha o auditoría automatizada."}</p>
      <small>${topPackage ? `${label(topPackage.status)} / ${escapeHtml(topPackage.priority)}` : "prepared"}</small>
    </article>
    <article class="upgrade-pipeline-card">
      <span class="eyebrow">Brechas</span>
      <strong>${number(topPackage?.gaps?.length || status.open_gaps || 0)} abiertas</strong>
      <p>${topGaps.map((gap) => `<span>${escapeHtml(gap)}</span>`).join("") || "<span>Sin brecha activa</span>"}</p>
      <small>No se inventan datos si el departamento falta.</small>
    </article>
    <article class="upgrade-pipeline-card">
      <span class="eyebrow">FORJA</span>
      <strong>${escapeHtml(label(topPackage?.forge_status || "not_sent"))}</strong>
      <p>${changes.map((change) => `<span>${escapeHtml(change)}</span>`).join("") || "<span>Tarea preparada pendiente</span>"}</p>
      <small>${escapeHtml(label(topPackage?.technical_status || "pending_execution"))}</small>
    </article>
    <article class="upgrade-pipeline-card">
      <span class="eyebrow">AUDITORÍA</span>
      <strong>${escapeHtml(label(topPackage?.audit_status || "not_requested"))}</strong>
      <p>No se declara aprobado sin revisión AUDITORÍA enlazada.</p>
      <small>${topPackage?.audit_review_id ? escapeHtml(topPackage.audit_review_id) : "review pendiente"}</small>
    </article>
    <article class="upgrade-pipeline-card">
      <span class="eyebrow">Gobernados</span>
      <strong>${number(status.governed_packages || 0)} paquetes</strong>
      <p>DCFT, SENTINELA y ARSENAL pueden tener paquete gobernado, no ejecución real.</p>
      <small>Sin SUNAT, secretos, pagos ni runtimes externos.</small>
    </article>
    <article class="upgrade-pipeline-card">
      <span class="eyebrow">Siguiente acción</span>
      <strong>${escapeHtml(nextAction)}</strong>
      <p>${topPackage ? escapeHtml(topPackage.risk || "controlled") : "AUDITORÍA debe detectar brecha primero."}</p>
      <small>CEREBRO reporta al CEO.</small>
    </article>
    <article class="upgrade-pipeline-card wide">
      <span class="eyebrow">Departamentos soportados</span>
      <p>${supported.slice(0, 12).map((item) => `<span>${escapeHtml(item)}</span>`).join("") || "<span>PLUMA</span><span>LENTE</span><span>MARKETING</span>"}</p>
      <small>Si el departamento no existe en datos reales, queda missing/unknown.</small>
    </article>
  `;
}

function renderRevenueOs() {
  const container = $("#revenue-os-grid");
  if (!container) return;

  const status = state.data.revenueStatus || state.data.ceoDailyCenter?.revenue || {};
  const opportunities = Array.isArray(state.data.revenueOpportunities) ? state.data.revenueOpportunities : [];
  const approvals = Array.isArray(state.data.revenueApprovals) ? state.data.revenueApprovals : [];
  const departments = Array.isArray(state.data.revenueDepartments) ? state.data.revenueDepartments : [];
  const globalGoal = status.global_goal || {};
  const ecommerceGoal = status.ecommerce_goal || {};
  const topOpportunity = (Array.isArray(status.top_opportunities) ? status.top_opportunities[0] : null)
    || opportunities.find((item) => item.economic_matrix?.status === "calculated")
    || opportunities[0];
  const topApproval = approvals[0];
  const directDepartments = departments.filter((item) => item.target_scope !== "indirect").slice(0, 6);
  const moneyRule = "Dinero real, pauta pagada, APIs con costo o inventario esperan CEO.";

  container.innerHTML = `
    <article class="revenue-os-card primary">
      <span class="eyebrow">Meta global</span>
      <strong>USD ${number(globalGoal.monthly_target_usd || 6000)}</strong>
      <p>Pipeline estimado USD ${number(status.estimated_global_pipeline_usd || 0)}. Ingresos reales no reportados.</p>
      <div class="revenue-kpis">
        <small><b>${number(status.global_progress_percent || 0)}%</b>avance estimado</small>
        <small><b>${number(status.opportunities || opportunities.length)}</b>oportunidades</small>
      </div>
    </article>
    <article class="revenue-os-card">
      <span class="eyebrow">E-COMMERCE separado</span>
      <strong>USD ${number(ecommerceGoal.monthly_target_usd || 10000)}</strong>
      <p>No cuenta dentro de la meta global. Pipeline USD ${number(status.estimated_ecommerce_pipeline_usd || 0)}.</p>
      <small>${number(status.ecommerce_progress_percent || 0)}% avance estimado e-commerce.</small>
    </article>
    <article class="revenue-os-card">
      <span class="eyebrow">Oportunidad prioritaria</span>
      <strong>${escapeHtml(topOpportunity?.title || "Sin oportunidad calculada")}</strong>
      <p>${topOpportunity ? `Utilidad neta USD ${number(topOpportunity.economic_matrix?.expected_net_profit_usd || 0)}.` : "CEREBRO puede registrar oportunidades sin inventar ingresos."}</p>
      <small>${topOpportunity ? escapeHtml(topOpportunity.economic_matrix?.recommendation || "Matriz pendiente.") : "actual_revenue=0"}</small>
    </article>
    <article class="revenue-os-card">
      <span class="eyebrow">Aprobacion CEO</span>
      <strong>${number(approvals.length || status.approval_requests || 0)} solicitudes</strong>
      <p>${topApproval ? `${topApproval.title}: ${label(topApproval.status)}.` : "Sin gasto real pendiente de decision."}</p>
      <small>${escapeHtml(moneyRule)}</small>
    </article>
    <article class="revenue-os-card wide">
      <span class="eyebrow">Departamentos que monetizan</span>
      <p>${directDepartments.map((item) => `<span>${escapeHtml(item.department_name)}</span>`).join("") || "<span>CEREBRO</span><span>MARKETING</span>"}</p>
      <small>PLUMA, LENTE, MARKETING, MARCA PERSONAL, TENDENCIAS, APIs/SKILLS, WEB FACTORY y E-COMMERCE contribuyen sin ejecucion externa.</small>
    </article>
    <article class="revenue-os-card">
      <span class="eyebrow">Riesgo</span>
      <strong>${number(status.opportunities_needing_data || 0)} sin ROI</strong>
      <p>Si faltan datos, queda needs_more_data. No se inventa retorno ni venta real.</p>
      <small>Pagos, pasarelas, cuentas externas y SUNAT siguen fuera.</small>
    </article>
  `;
}

function renderRevenueSprint() {
  const container = $("#revenue-sprint-grid");
  if (!container) return;

  const status = state.data.revenueSprintStatus || state.data.ceoDailyCenter?.revenue_sprint || {};
  const routes = Array.isArray(state.data.revenueSprintRoutes) ? state.data.revenueSprintRoutes : [];
  const missions = Array.isArray(state.data.revenueSprintMissions) ? state.data.revenueSprintMissions : [];
  const daily = state.data.revenueSprintDaily || {};
  const risks = Array.isArray(state.data.revenueSprintRisks) ? state.data.revenueSprintRisks : [];
  const approvalPayload = state.data.revenueSprintApprovalNeeded || {};
  const approvals = Array.isArray(approvalPayload) ? approvalPayload : (Array.isArray(approvalPayload.items) ? approvalPayload.items : []);
  const approvalCount = Number.isFinite(Number(approvalPayload.count)) ? Number(approvalPayload.count) : approvals.length;
  const topRoute = (Array.isArray(status.top_routes) ? status.top_routes[0] : null) || routes[0];
  const topMission = missions[0];
  const plan = Array.isArray(status.plan_30_days) ? status.plan_30_days : (Array.isArray(daily.plan_30_days) ? daily.plan_30_days : []);
  const week = plan[0] || {};
  const ecommerceRoutes = routes.filter((route) => route.ecommerce_separate);
  const routeActions = Array.isArray(topRoute?.next_actions) ? topRoute.next_actions.slice(0, 3) : [];
  const todayFocus = Array.isArray(daily.today_focus) ? daily.today_focus.slice(0, 3) : [];

  container.innerHTML = `
    <article class="revenue-sprint-card primary">
      <span class="eyebrow">Revenue Sprint 30 días</span>
      <strong>USD ${number(status.global_goal_usd || 6000)} / mes</strong>
      <p>E-commerce USD ${number(status.ecommerce_goal_usd || 10000)} separado. Ingresos reales: ${number(status.actual_revenue_usd || 0)}.</p>
      <div class="revenue-sprint-kpis">
        <small><b>${number(status.routes || routes.length)}</b>rutas</small>
        <small><b>${number(status.missions || missions.length)}</b>misiones</small>
        <small><b>${number(status.approval_needed || approvalCount)}</b>CEO</small>
      </div>
    </article>
    <article class="revenue-sprint-card">
      <span class="eyebrow">Ruta prioritaria</span>
      <strong>${escapeHtml(topRoute?.name || "Sin ruta activa")}</strong>
      <p>${escapeHtml(topRoute?.hypothesis || "CEREBRO debe priorizar rutas sin inventar ventas.")}</p>
      <small>${topRoute ? `${label(topRoute.status)} / ${escapeHtml(topRoute.priority || "p1")}` : "prepared"}</small>
    </article>
    <article class="revenue-sprint-card">
      <span class="eyebrow">Siguiente acción</span>
      <strong>${escapeHtml(routeActions[0] || status.next_action || "Validar demanda orgánica.")}</strong>
      <p>${routeActions.map((action) => `<span>${escapeHtml(action)}</span>`).join("") || "<span>Preparar evidencia</span>"}</p>
      <small>${escapeHtml(label(topRoute?.evidence_status || "missing"))}</small>
    </article>
    <article class="revenue-sprint-card">
      <span class="eyebrow">CEREBRO</span>
      <strong>${escapeHtml(topMission?.title || "Misiones preparadas")}</strong>
      <p>${topMission ? escapeHtml(topMission.expected_output) : "CEREBRO crea misiones para Marketing, PLUMA, LENTE y Web Factory."}</p>
      <small>${topMission ? label(topMission.status) : "sin ejecución externa"}</small>
    </article>
    <article class="revenue-sprint-card">
      <span class="eyebrow">Aprobaciones</span>
      <strong>${number(approvalCount || status.approval_needed || 0)} requieren CEO</strong>
      <p>Dinero real, pauta pagada, cuentas externas y servicios con costo quedan bloqueados.</p>
      <small>Orgánico no requiere aprobación de dinero.</small>
    </article>
    <article class="revenue-sprint-card">
      <span class="eyebrow">E-COMMERCE</span>
      <strong>${number(status.ecommerce_routes || ecommerceRoutes.length)} rutas separadas</strong>
      <p>No se mezcla con la meta global. SNIFF AMAZON solo prepara señales.</p>
      <small>Sin compra, cobro ni inventario real.</small>
    </article>
    <article class="revenue-sprint-card wide">
      <span class="eyebrow">Plan 30 días</span>
      <strong>${escapeHtml(week.title || "Semana 1: auditoría y preparación")}</strong>
      <p>${todayFocus.map((focus) => `<span>${escapeHtml(focus)}</span>`).join("") || "<span>Auditoría</span><span>Contenido</span><span>Landing</span><span>ROI</span>"}</p>
      <small>${escapeHtml(week.output || "Lista priorizada de rutas y misiones internas.")}</small>
    </article>
    <article class="revenue-sprint-card">
      <span class="eyebrow">Riesgo</span>
      <strong>${number(risks.length)} alertas</strong>
      <p>No inventar ingresos, métricas, ventas ni campañas reales.</p>
      <small>${number(status.missing_evidence || 0)} rutas con evidencia faltante.</small>
    </article>
  `;
}

function renderEcommerceAmazonReadiness() {
  const container = $("#ecommerce-amazon-grid");
  if (!container) return;

  const ecommerce = state.data.ecommerceReadinessStatus || state.data.ceoDailyCenter?.ecommerce_readiness || {};
  const amazon = state.data.amazonReadinessStatus || state.data.ceoDailyCenter?.amazon_readiness || {};
  const ecommerceItems = Array.isArray(state.data.ecommerceReadinessOpportunities)
    ? state.data.ecommerceReadinessOpportunities
    : (Array.isArray(ecommerce.opportunities_snapshot) ? ecommerce.opportunities_snapshot : []);
  const amazonItems = Array.isArray(state.data.amazonReadinessOpportunities)
    ? state.data.amazonReadinessOpportunities
    : (Array.isArray(amazon.opportunities_snapshot) ? amazon.opportunities_snapshot : []);
  const approvals = Array.isArray(state.data.ecommerceReadinessApprovalNeeded) ? state.data.ecommerceReadinessApprovalNeeded : [];
  const amazonRisks = Array.isArray(state.data.amazonReadinessRisks) ? state.data.amazonReadinessRisks : [];
  const combined = [...ecommerceItems, ...amazonItems];
  const prepared = combined.filter((item) => item.state === "prepared");
  const unknown = combined.filter((item) => item.state === "unknown" || item.state === "idea");
  const investment = combined.filter((item) => item.requires_inventory || item.requires_paid_tool || item.requires_payment_provider || item.investment_needed !== "unknown");
  const externalAccounts = combined.filter((item) => item.requires_external_account);
  const topApproval = approvals[0] || combined.find((item) => item.requires_ceo) || {};
  const topAmazonRisk = amazonRisks[0] || {};
  const nextSteps = Array.isArray(ecommerce.next_steps) ? ecommerce.next_steps : [];
  const amazonSteps = Array.isArray(amazon.next_steps) ? amazon.next_steps : [];

  container.innerHTML = `
    <article class="ecommerce-amazon-card primary">
      <span class="eyebrow">E-Commerce & Amazon Readiness</span>
      <strong>USD ${number(ecommerce.monthly_goal_usd || 10000)} separado</strong>
      <p>No se mezcla con USD ${number(ecommerce.global_goal_usd || 6000)} global. Ventas reales: ${number(ecommerce.actual_revenue_usd || 0)}.</p>
      <div class="ecommerce-amazon-kpis">
        <small><b>${number(ecommerce.opportunities || ecommerceItems.length)}</b>e-commerce</small>
        <small><b>${number(amazon.opportunities || amazonItems.length)}</b>Amazon</small>
        <small><b>${number(ecommerce.approval_needed || approvals.length)}</b>CEO</small>
      </div>
    </article>
    <article class="ecommerce-amazon-card">
      <span class="eyebrow">Prepared</span>
      <strong>${number(prepared.length)} oportunidades</strong>
      <p>Tienda, contenido, radar y tablero pueden quedar preparados sin vender ni conectar.</p>
      <small>store_created=false / payment_connected=false</small>
    </article>
    <article class="ecommerce-amazon-card">
      <span class="eyebrow">Unknown / research</span>
      <strong>${number(unknown.length + (ecommerce.needs_market_research || 0) + (amazon.needs_market_research || 0))} pendientes</strong>
      <p>Si falta evidencia, se pide research. No se inventan productos ganadores ni margen.</p>
      <small>margin_estimated=unknown_not_estimated</small>
    </article>
    <article class="ecommerce-amazon-card">
      <span class="eyebrow">Inversion</span>
      <strong>${number(investment.length)} bloqueos</strong>
      <p>Inventario, herramientas pagadas, proveedor y pasarela requieren ROI y decision CEO.</p>
      <small>inventory_purchased=false</small>
    </article>
    <article class="ecommerce-amazon-card">
      <span class="eyebrow">Cuenta externa</span>
      <strong>${number(externalAccounts.length)} requieren cuenta</strong>
      <p>Marketplace y Amazon Seller no se crean ni conectan desde S.5.</p>
      <small>amazon_seller_connected=false</small>
    </article>
    <article class="ecommerce-amazon-card">
      <span class="eyebrow">Amazon radar</span>
      <strong>${escapeHtml(label(amazon.mode || "radar_prepared_local"))}</strong>
      <p>SNIFF AMAZON / CHIEF AMAZON detecta senales preparadas; no scrapea sitios prohibidos.</p>
      <small>prohibited_scraping_enabled=false</small>
    </article>
    <article class="ecommerce-amazon-card">
      <span class="eyebrow">Riesgos</span>
      <strong>${escapeHtml(topAmazonRisk.product_category || "Sin producto ganador")}</strong>
      <p>${escapeHtml(topAmazonRisk.next_action || "No declarar margen, ventas, inventario ni producto ganador sin evidencia.")}</p>
      <small>${number(amazon.risks || amazonRisks.length)} riesgos Amazon</small>
    </article>
    <article class="ecommerce-amazon-card">
      <span class="eyebrow">CEREBRO / Revenue</span>
      <strong>Meta separada</strong>
      <p>CEREBRO puede pedir research, Marketing/Publishing/Web Factory; no puede gastar ni vender real.</p>
      <small>separated_from_global_goal=true</small>
    </article>
    <article class="ecommerce-amazon-card wide">
      <span class="eyebrow">Siguiente paso</span>
      <strong>${escapeHtml(nextSteps[0] || "Research antes de producto")}</strong>
      <p>${[...nextSteps.slice(0, 3), ...amazonSteps.slice(0, 2)].map((step) => `<span>${escapeHtml(step)}</span>`).join("") || "<span>Research</span><span>CEO</span><span>Sin pagos</span>"}</p>
      <small>${escapeHtml(topApproval.next_action || "Preparado para decision CEO posterior, sin ejecucion externa.")}</small>
    </article>
  `;
}

function renderPublishingGrowth() {
  const container = $("#publishing-growth-grid");
  if (!container) return;

  const status = state.data.publishingStatus || state.data.ceoDailyCenter?.publishing || {};
  const channels = Array.isArray(state.data.publishingChannels) ? state.data.publishingChannels : (Array.isArray(status.channels_snapshot) ? status.channels_snapshot : []);
  const content = Array.isArray(state.data.publishingContent) ? state.data.publishingContent : (Array.isArray(status.next_content) ? status.next_content : []);
  const calendar = Array.isArray(state.data.publishingCalendar) ? state.data.publishingCalendar : [];
  const growth = Array.isArray(state.data.publishingGrowth) ? state.data.publishingGrowth : [];
  const connected = channels.filter((channel) => channel.account_status === "connected");
  const notConnected = channels.filter((channel) => channel.account_status !== "connected");
  const next = content[0] || {};
  const pluma = content.find((item) => (item.department_owner || "").toUpperCase().includes("PLUMA"));
  const lente = content.find((item) => (item.department_owner || "").toUpperCase().includes("LENTE"));
  const marketing = content.find((item) => (item.department_owner || "").toUpperCase().includes("MARKETING"));
  const marca = content.find((item) => (item.department_owner || "").toUpperCase().includes("MARCA"));
  const paidBlocked = content.filter((item) => item.requires_approval);
  const channelNames = channels.slice(0, 7).map((channel) => channel.name);

  container.innerHTML = `
    <article class="publishing-growth-card primary">
      <span class="eyebrow">Publishing & Growth</span>
      <strong>${number(status.content_items || content.length)} piezas preparadas</strong>
      <p>${number(status.channels || channels.length)} canales. ${number(status.connected_accounts || connected.length)} cuentas conectadas; ${number(status.not_connected_accounts || notConnected.length)} no conectadas.</p>
      <div class="publishing-kpis">
        <small><b>${number(status.prepared_items || 0)}</b>prepared</small>
        <small><b>${number(status.scheduled_items || 0)}</b>agenda</small>
        <small><b>${number(status.approvals_needed || paidBlocked.length)}</b>CEO</small>
      </div>
    </article>
    <article class="publishing-growth-card">
      <span class="eyebrow">Canales</span>
      <strong>${channelNames.slice(0, 3).map(escapeHtml).join(" / ") || "Canales preparados"}</strong>
      <p>${channelNames.map((name) => `<span>${escapeHtml(name)}</span>`).join("") || "<span>TikTok</span><span>Instagram</span><span>YouTube</span>"}</p>
      <small>Si la cuenta no esta conectada, publication_status=prepared.</small>
    </article>
    <article class="publishing-growth-card">
      <span class="eyebrow">Proximo contenido</span>
      <strong>${escapeHtml(next.title || "Sin pieza priorizada")}</strong>
      <p>${escapeHtml(next.content_brief || "CEREBRO coordina piezas sin publicar real si no hay conexion.")}</p>
      <small>${escapeHtml(label(next.publication_status || "prepared"))}</small>
    </article>
    <article class="publishing-growth-card">
      <span class="eyebrow">PLUMA</span>
      <strong>${escapeHtml(pluma?.format || "posts / guiones / articulos")}</strong>
      <p>${escapeHtml(pluma?.title || "Posts, newsletters, guiones, libros, autoridad y contenido comercial.")}</p>
      <small>Español e ingles preparados.</small>
    </article>
    <article class="publishing-growth-card">
      <span class="eyebrow">LENTE</span>
      <strong>${escapeHtml(lente?.format || "shorts / reels / miniaturas")}</strong>
      <p>${escapeHtml(lente?.title || "Videos, shorts, reels, avatares, animaciones y visuales.")}</p>
      <small>${escapeHtml(label(lente?.niche_status || "needs_ceo_definition"))}</small>
    </article>
    <article class="publishing-growth-card">
      <span class="eyebrow">MARKETING</span>
      <strong>${escapeHtml(marketing?.publication_mode || "organico preparado")}</strong>
      <p>${escapeHtml(marketing?.title || "Campañas organicas, embudos y validacion de demanda.")}</p>
      <small>Paid campaigns requieren ROI y aprobacion CEO.</small>
    </article>
    <article class="publishing-growth-card">
      <span class="eyebrow">MARCA PERSONAL</span>
      <strong>${escapeHtml(marca?.channel || "CEO autoridad")}</strong>
      <p>${escapeHtml(marca?.title || "Autoridad CEO en TikTok, Instagram, LinkedIn, X y YouTube si existen cuentas.")}</p>
      <small>Cuenta nueva externa requiere aprobacion.</small>
    </article>
    <article class="publishing-growth-card">
      <span class="eyebrow">Metricas</span>
      <strong>${number(status.real_metrics_confirmed || 0)} reales confirmadas</strong>
      <p>${number(growth.length)} metricas registradas. Si falta evidencia, queda missing.</p>
      <small>No inventar alcance, ventas, views ni conversion.</small>
    </article>
    <article class="publishing-growth-card wide">
      <span class="eyebrow">CEREBRO coordina</span>
      <strong>${number(calendar.length || content.length)} piezas en calendario preparado</strong>
      <p><span>PLUMA escribe</span><span>LENTE diseña</span><span>MARKETING valida</span><span>E-COMMERCE separado</span><span>SNIFF AMAZON señala</span></p>
      <small>Organico conectado no pide CEO; pagado o cuenta externa nueva si pide aprobacion.</small>
    </article>
  `;
}

function renderPublishingPrepared() {
  const container = $("#publishing-prepared-grid");
  if (!container) return;

  const status = state.data.publishingPreparedStatus || {};
  const content = Array.isArray(state.data.publishingPreparedContent)
    ? state.data.publishingPreparedContent
    : (Array.isArray(status.content_snapshot) ? status.content_snapshot : []);
  const calendar = Array.isArray(state.data.publishingPreparedCalendar) ? state.data.publishingPreparedCalendar : [];
  const blocked = Array.isArray(state.data.publishingPreparedBlocked)
    ? state.data.publishingPreparedBlocked
    : (Array.isArray(status.blocked_snapshot) ? status.blocked_snapshot : []);
  const nextContent = content[0] || {};
  const blockedPublish = blocked.find((item) => item.blocked_action === "real_publication") || blocked[0] || {};
  const accountUnknown = content.filter((item) => ["unknown", "not_connected"].includes(item.account_status));

  container.innerHTML = `
    <article class="publishing-growth-card primary">
      <span class="eyebrow">S3 Publishing Prepared</span>
      <strong>${number(status.prepared_items || content.length)} piezas prepared</strong>
      <p>Pipeline organico listo para ordenar contenido sin publicar real ni conectar cuentas externas.</p>
      <div class="publishing-kpis">
        <small><b>${number(status.published_items || 0)}</b>publicadas</small>
        <small><b>${number(status.external_accounts_connected || 0)}</b>cuentas</small>
        <small><b>${number(status.real_metrics_confirmed || 0)}</b>metricas</small>
      </div>
    </article>
    <article class="publishing-growth-card">
      <span class="eyebrow">Contenido</span>
      <strong>${escapeHtml(nextContent.title || "Sin pieza publicada")}</strong>
      <p>${escapeHtml(nextContent.next_action || "Mantener prepared hasta confirmar cuenta oficial.")}</p>
      <small>${escapeHtml(label(nextContent.publication_status || "prepared"))}</small>
    </article>
    <article class="publishing-growth-card">
      <span class="eyebrow">Bloqueo seguro</span>
      <strong>${escapeHtml(label(blockedPublish.reason || "official_accounts_unknown"))}</strong>
      <p>Cuenta desconocida o no conectada bloquea publicacion real. El fallback es publication_status=prepared.</p>
      <small>${escapeHtml(label(blockedPublish.safe_fallback || "publication_status=prepared"))}</small>
    </article>
    <article class="publishing-growth-card">
      <span class="eyebrow">Calendario</span>
      <strong>${number(calendar.length)} etapas preparadas</strong>
      <p>${calendar.map((item) => `<span>${escapeHtml(item.period || item.id)}</span>`).join("") || "<span>week_1</span><span>week_2</span>"}</p>
      <small>Sin post real desde este bloque.</small>
    </article>
    <article class="publishing-growth-card">
      <span class="eyebrow">Cuentas</span>
      <strong>${number(accountUnknown.length)} unknown/not_connected</strong>
      <p>Si la cuenta oficial no esta confirmada, CEREBRO solo prepara la pieza y escala definicion.</p>
      <small>external_connection_enabled=false</small>
    </article>
    <article class="publishing-growth-card wide">
      <span class="eyebrow">Regla S3</span>
      <strong>Organico preparado no significa publicado</strong>
      <p><span>PLUMA escribe</span><span>LENTE prepara</span><span>MARKETING valida</span><span>sin cuentas reales</span><span>sin metricas falsas</span></p>
      <small>${escapeHtml(status.next_action || "CEO confirma cuentas antes de publicacion real.")}</small>
    </article>
  `;
}

function renderMarketingApprovalGate() {
  const container = $("#marketing-approval-grid");
  if (!container) return;

  const status = state.data.marketingApprovalStatus || {};
  const campaigns = Array.isArray(state.data.marketingApprovalCampaigns)
    ? state.data.marketingApprovalCampaigns
    : (Array.isArray(status.campaigns_snapshot) ? status.campaigns_snapshot : []);
  const approvals = Array.isArray(state.data.marketingApprovalApprovalNeeded) ? state.data.marketingApprovalApprovalNeeded : [];
  const risks = Array.isArray(state.data.marketingApprovalRisks) ? state.data.marketingApprovalRisks : [];
  const paid = campaigns.filter((campaign) => campaign.campaign_type === "paid");
  const organic = campaigns.filter((campaign) => campaign.campaign_type === "organic");
  const topApproval = approvals[0] || paid[0] || {};
  const topRisk = risks[0] || {};

  container.innerHTML = `
    <article class="publishing-growth-card primary">
      <span class="eyebrow">S4 Marketing Gate</span>
      <strong>${number(approvals.length || status.approval_needed || 0)} decisiones CEO</strong>
      <p>Campana pagada requiere ROI, presupuesto y aprobacion CEO. No hay gasto ni lanzamiento real.</p>
      <div class="publishing-kpis">
        <small><b>${number(paid.length)}</b>paid</small>
        <small><b>${number(organic.length)}</b>organic</small>
        <small><b>${number(status.paid_campaigns_launched || 0)}</b>launched</small>
      </div>
    </article>
    <article class="publishing-growth-card">
      <span class="eyebrow">Paid</span>
      <strong>${escapeHtml(topApproval.name || "Paid bloqueado")}</strong>
      <p>${escapeHtml(topApproval.next_action || "Preparar ROI y esperar aprobacion CEO.")}</p>
      <small>${escapeHtml(label(topApproval.roi_status || "missing"))}</small>
    </article>
    <article class="publishing-growth-card">
      <span class="eyebrow">Organico</span>
      <strong>${number(organic.length)} prepared</strong>
      <p>Contenido organico preparado no requiere gasto, pero publicar real depende de cuentas oficiales conectadas.</p>
      <small>budget_spent=${number(status.budget_spent || 0)}</small>
    </article>
    <article class="publishing-growth-card">
      <span class="eyebrow">Riesgo</span>
      <strong>${escapeHtml(label(topRisk.risk || "paid_campaign_without_roi"))}</strong>
      <p>${escapeHtml(topRisk.control || "requires_ceo_approval=true")}</p>
      <small>${escapeHtml(label(topRisk.severity || "high"))}</small>
    </article>
    <article class="publishing-growth-card">
      <span class="eyebrow">Estado seguro</span>
      <strong>0 pagos, 0 campanas reales</strong>
      <p>No se cobra, no se activa pauta, no se conectan cuentas externas y no se inventa ROI.</p>
      <small>paid_campaign_launched=false</small>
    </article>
    <article class="publishing-growth-card wide">
      <span class="eyebrow">Regla S4</span>
      <strong>Pagado solo con ROI aprobado</strong>
      <p><span>ROI missing bloquea</span><span>CEO aprueba</span><span>cuentas externas bloqueadas</span><span>sin gasto real</span></p>
      <small>${escapeHtml(status.next_action || "Paid campaigns requieren aprobacion CEO con ROI antes de lanzar.")}</small>
    </article>
  `;
}

function renderProductReadiness() {
  const container = $("#product-readiness-grid");
  if (!container) return;

  const status = state.data.productReadinessStatus || state.data.ceoDailyCenter?.product_readiness || {};
  const dcft = state.data.productReadinessDcft || {};
  const sentinela = state.data.productReadinessSentinela || {};
  const gaps = Array.isArray(state.data.productReadinessGaps) ? state.data.productReadinessGaps : [];
  const marketingPackage = state.data.productReadinessMarketingPackage || status.marketing_package || {};
  const items = Array.isArray(marketingPackage.items) ? marketingPackage.items : [];
  const dcftGaps = gaps.filter((gap) => gap.product_id === "dcft");
  const sentinelaGaps = gaps.filter((gap) => gap.product_id === "sentinela");
  const forjaGaps = gaps.filter((gap) => gap.forge_status === "prepared");
  const topGap = gaps[0] || {};
  const dcftPackage = items.find((item) => item.product_id === "dcft") || {};
  const sentinelaPackage = items.find((item) => item.product_id === "sentinela") || {};

  container.innerHTML = `
    <article class="product-readiness-card primary">
      <span class="eyebrow">Readiness</span>
      <strong>${number(status.products || 2)} productos, ${number(status.open_gaps || gaps.length)} brechas</strong>
      <p>DCFT y SENTINELA no tienen meta propia. MARKETING vende cuando evidencia y auditoria validen.</p>
      <div class="product-readiness-kpis">
        <small><b>${number(status.products_with_own_sales_goal || 0)}</b>meta propia</small>
        <small><b>${number(status.requires_validation || 0)}</b>validar</small>
        <small><b>${number(status.unknown_items || 0)}</b>unknown</small>
      </div>
    </article>
    <article class="product-readiness-card">
      <span class="eyebrow">DCFT</span>
      <strong>${escapeHtml(label(dcft.commercial_status || status.dcft_status || "requires_validation"))}</strong>
      <p>${escapeHtml(dcft.value_proposition || "Producto contable/financiero/tributario; claims legales requieren fuente oficial.")}</p>
      <small>Sin SUNAT real, sin runtime externo, sin venta automatica.</small>
    </article>
    <article class="product-readiness-card">
      <span class="eyebrow">SENTINELA</span>
      <strong>${escapeHtml(label(sentinela.commercial_status || status.sentinela_status || "requires_validation"))}</strong>
      <p>${escapeHtml(sentinela.description || "Sistema/producto de seguridad preparado para comercializacion cuando MARKETING lo empuje.")}</p>
      <small>Sin activacion real ni claims de seguridad sin evidencia.</small>
    </article>
    <article class="product-readiness-card">
      <span class="eyebrow">Brechas</span>
      <strong>${escapeHtml(topGap.title || "Evidencia pendiente")}</strong>
      <p>${number(dcftGaps.length)} DCFT / ${number(sentinelaGaps.length)} SENTINELA. Faltantes quedan unknown o requires_validation.</p>
      <small>${escapeHtml(label(topGap.evidence_status || "missing"))}</small>
    </article>
    <article class="product-readiness-card">
      <span class="eyebrow">Marketing package</span>
      <strong>${escapeHtml(label(marketingPackage.status || "prepared_requires_validation"))}</strong>
      <p>Owner: MARKETING. DCFT/SENTINELA no venden solos ni tienen meta propia.</p>
      <small>${number(items.length)} paquetes sin claims legales/seguridad no validados.</small>
    </article>
    <article class="product-readiness-card">
      <span class="eyebrow">FORJA</span>
      <strong>${number(forjaGaps.length)} tareas preparadas</strong>
      <p>Brechas tecnicas pueden pasar a FORJA, pero no se declaran implementadas sin evidencia.</p>
      <small>technical_status=pending_execution</small>
    </article>
    <article class="product-readiness-card">
      <span class="eyebrow">AUDITORIA</span>
      <strong>${escapeHtml(label(dcft.audit_status || "requires_validation"))}</strong>
      <p>Legal, seguridad, pricing, onboarding, tiendas y soporte requieren revision antes de avanzar.</p>
      <small>No hay App Store/Play Store ni campana pagada real.</small>
    </article>
    <article class="product-readiness-card">
      <span class="eyebrow">PLUMA / LENTE</span>
      <strong>${number((dcftPackage.required_pieces || []).length + (sentinelaPackage.required_pieces || []).length)} piezas requeridas</strong>
      <p>PLUMA prepara guiones/FAQ; LENTE prepara visuales. Todo requiere validacion.</p>
      <small>Sin publicacion real desde este bloque.</small>
    </article>
    <article class="product-readiness-card wide">
      <span class="eyebrow">Regla comercial</span>
      <strong>MARKETING vende; producto valida readiness</strong>
      <p><span>no SUNAT real</span><span>no tiendas reales</span><span>no paid real</span><span>no claims sin fuente</span><span>FORJA preparada</span></p>
      <small>Si falta informacion: status=unknown o requires_validation.</small>
    </article>
  `;
}

function renderCommercialReadiness() {
  const container = $("#commercial-readiness-grid");
  if (!container) return;

  const status = state.data.commercialReadinessStatus || {};
  const dcft = state.data.commercialReadinessDcft || {};
  const sentinela = state.data.commercialReadinessSentinela || {};
  const marketingPackage = state.data.commercialReadinessMarketingPackage || {};
  const approvals = Array.isArray(state.data.commercialReadinessApprovalNeeded) ? state.data.commercialReadinessApprovalNeeded : [];
  const items = Array.isArray(marketingPackage.items) ? marketingPackage.items : [];
  const dcftItem = items.find((item) => item.product_id === "dcft") || {};
  const sentinelaItem = items.find((item) => item.product_id === "sentinela") || {};
  const topApproval = approvals[0] || {};

  container.innerHTML = `
    <article class="product-readiness-card primary">
      <span class="eyebrow">S6 Commercial Readiness</span>
      <strong>MARKETING es owner de venta</strong>
      <p>DCFT y SENTINELA se preparan comercialmente, pero no tienen meta propia ni activacion real.</p>
      <div class="product-readiness-kpis">
        <small><b>${number(status.products || 2)}</b>productos</small>
        <small><b>${number(status.products_with_own_sales_goal || 0)}</b>meta propia</small>
        <small><b>${number(status.requires_validation || approvals.length)}</b>validar</small>
      </div>
    </article>
    <article class="product-readiness-card">
      <span class="eyebrow">DCFT</span>
      <strong>${escapeHtml(label(dcft.commercial_status || status.dcft_status || "requires_validation"))}</strong>
      <p>${escapeHtml(dcft.next_action || "Auditar evidencia, landing, pricing y fuentes legales antes del empuje comercial.")}</p>
      <small>sunat_enabled=${String(Boolean(dcft.sunat_enabled))}</small>
    </article>
    <article class="product-readiness-card">
      <span class="eyebrow">SENTINELA</span>
      <strong>${escapeHtml(label(sentinela.commercial_status || status.sentinela_status || "requires_validation"))}</strong>
      <p>${escapeHtml(sentinela.next_action || "Validar claims de seguridad, onboarding y soporte antes del empuje comercial.")}</p>
      <small>runtime_connected=${String(Boolean(sentinela.runtime_connected))}</small>
    </article>
    <article class="product-readiness-card">
      <span class="eyebrow">Marketing package</span>
      <strong>${escapeHtml(label(marketingPackage.status || "prepared_requires_validation"))}</strong>
      <p>${number(items.length)} paquetes sin claims legales o de seguridad no validados.</p>
      <small>claims_invented=${String(Boolean(marketingPackage.claims_invented))}</small>
    </article>
    <article class="product-readiness-card">
      <span class="eyebrow">Piezas</span>
      <strong>${number((dcftItem.required_pieces || []).length + (sentinelaItem.required_pieces || []).length)} requeridas</strong>
      <p>Landing, FAQ, objeciones, onboarding y evidencia quedan en estado preparado.</p>
      <small>requires_validation=true</small>
    </article>
    <article class="product-readiness-card">
      <span class="eyebrow">Aprobacion</span>
      <strong>${escapeHtml(topApproval.product || "Claims pendientes")}</strong>
      <p>${escapeHtml(topApproval.decision || "CEO revisa claims y readiness antes de cualquier empuje real.")}</p>
      <small>${escapeHtml(label(topApproval.status || "pending"))}</small>
    </article>
    <article class="product-readiness-card wide">
      <span class="eyebrow">Regla S6</span>
      <strong>Producto preparado no significa vendido ni conectado</strong>
      <p><span>Marketing vende</span><span>productos validan</span><span>FORJA prepared</span><span>AUDITORIA revisa</span><span>sin SUNAT real</span></p>
      <small>Si falta evidencia, queda missing/unknown/requires_validation.</small>
    </article>
  `;
}

function renderRealWorldConnections() {
  const container = $("#real-world-grid");
  if (!container) return;

  const status = state.data.realWorldStatus || state.data.ceoDailyCenter?.real_world || {};
  const connections = Array.isArray(state.data.realWorldConnections)
    ? state.data.realWorldConnections
    : (Array.isArray(status.connections_snapshot) ? status.connections_snapshot : []);
  const approvals = Array.isArray(state.data.realWorldApprovalNeeded) ? state.data.realWorldApprovalNeeded : [];
  const risks = Array.isArray(state.data.realWorldRisks) ? state.data.realWorldRisks : [];
  const unknown = connections.filter((item) => item.state === "unknown");
  const prepared = connections.filter((item) => item.state === "prepared");
  const credentials = connections.filter((item) => item.requires_credentials);
  const money = connections.filter((item) => item.requires_money || item.state === "needs_paid_approval");
  const sensitive = risks.filter((item) => item.risk === "sensitive");
  const topApproval = approvals[0] || {};
  const topRisk = risks[0] || {};
  const nextSteps = Array.isArray(status.next_steps) ? status.next_steps : [];

  container.innerHTML = `
    <article class="real-world-card primary">
      <span class="eyebrow">Real World Connections</span>
      <strong>${number(status.total_connections || connections.length)} conexiones inventariadas</strong>
      <p>${number(status.connected || 0)} conectadas. ${number(status.prepared || prepared.length)} prepared. ${number(status.unknown || unknown.length)} unknown. Sin ejecucion externa.</p>
      <div class="real-world-kpis">
        <small><b>${number(status.needs_ceo || approvals.length)}</b>CEO</small>
        <small><b>${number(status.needs_credentials || credentials.length)}</b>credenciales</small>
        <small><b>${number(status.needs_paid_approval || money.length)}</b>dinero</small>
      </div>
    </article>
    <article class="real-world-card">
      <span class="eyebrow">Estado seguro</span>
      <strong>${escapeHtml(status.mode ? label(status.mode) : "Prepared local")}</strong>
      <p>No se crean cuentas, no se cobran pagos, no se publican piezas y no se conectan APIs externas.</p>
      <small>external_connection_enabled=false</small>
    </article>
    <article class="real-world-card">
      <span class="eyebrow">Requiere CEO</span>
      <strong>${escapeHtml(topApproval.connection || "Definiciones pendientes")}</strong>
      <p>${escapeHtml(topApproval.recommended_action || "Cuentas nuevas, dinero, credenciales y publicacion real escalan al CEO.")}</p>
      <small>${number(status.approval_needed_count || approvals.length)} en lista approval-needed</small>
    </article>
    <article class="real-world-card">
      <span class="eyebrow">Credenciales</span>
      <strong>${number(credentials.length || status.needs_credentials || 0)} sensibles</strong>
      <p>Passwords, tokens, API keys, client secrets y Clave SOL no se guardan ni se imprimen.</p>
      <small>secrets_stored=false</small>
    </article>
    <article class="real-world-card">
      <span class="eyebrow">Dinero real</span>
      <strong>${number(money.length || status.needs_paid_approval || 0)} bloqueadas</strong>
      <p>Pagos, pasarelas, campanas pagadas, dominios, hosting, app stores y herramientas con costo requieren ROI y CEO.</p>
      <small>paid_campaign_launched=false</small>
    </article>
    <article class="real-world-card">
      <span class="eyebrow">Riesgos</span>
      <strong>${escapeHtml(topRisk.connection || `${number(status.high_risk || 0)} high / ${number(status.sensitive || sensitive.length)} sensitive`)}</strong>
      <p>${escapeHtml(topRisk.recommended_action || "Riesgos altos o sensibles quedan en revision antes de cualquier conexion real.")}</p>
      <small>${escapeHtml(label(topRisk.risk || "controlled"))}</small>
    </article>
    <article class="real-world-card">
      <span class="eyebrow">CEREBRO</span>
      <strong>Prepara, audita y prioriza</strong>
      <p>CEREBRO puede crear misiones internas; no puede ejecutar pagos, cuentas, SUNAT, APIs con costo ni publicacion real sin CEO.</p>
      <small>modo prepared/unknown</small>
    </article>
    <article class="real-world-card wide">
      <span class="eyebrow">Siguiente paso</span>
      <strong>${escapeHtml(nextSteps[0] || "Confirmar cuentas oficiales existentes")}</strong>
      <p>${nextSteps.slice(0, 5).map((step) => `<span>${escapeHtml(step)}</span>`).join("") || "<span>Inventario</span><span>Definicion CEO</span><span>Credenciales seguras</span>"}</p>
      <small>Preparado para futura conexion real, sin ejecutar nada externo.</small>
    </article>
  `;
}

function renderAnalyticsReadiness() {
  const container = $("#analytics-readiness-grid");
  if (!container) return;

  const status = state.data.analyticsReadinessStatus || {};
  const metrics = Array.isArray(state.data.analyticsReadinessMetrics)
    ? state.data.analyticsReadinessMetrics
    : (Array.isArray(status.metrics_snapshot) ? status.metrics_snapshot : []);
  const sources = Array.isArray(state.data.analyticsReadinessSources)
    ? state.data.analyticsReadinessSources
    : (Array.isArray(status.sources_snapshot) ? status.sources_snapshot : []);
  const approvals = Array.isArray(state.data.analyticsReadinessApprovalNeeded) ? state.data.analyticsReadinessApprovalNeeded : [];
  const risks = Array.isArray(state.data.analyticsReadinessRisks) ? state.data.analyticsReadinessRisks : [];
  const manualSources = sources.filter((source) => source.status === "manual_ready");
  const disconnectedSources = sources.filter((source) => source.api_connected === false);
  const topMetric = metrics[0] || {};
  const topSource = sources[0] || {};
  const topRisk = risks[0] || {};
  const topApproval = approvals[0] || {};

  container.innerHTML = `
    <article class="real-world-card primary">
      <span class="eyebrow">S7 Analytics Readiness</span>
      <strong>${number(status.real_metrics_confirmed || 0)} metricas reales confirmadas</strong>
      <p>Metricas preparadas para seguimiento, sin inventar ventas, conversiones, views ni ROI.</p>
      <div class="real-world-kpis">
        <small><b>${number(metrics.length || status.metrics || 0)}</b>metricas</small>
        <small><b>${number(manualSources.length || status.manual_ready_sources || 0)}</b>manual</small>
        <small><b>${number(status.api_connected_sources || 0)}</b>APIs</small>
      </div>
    </article>
    <article class="real-world-card">
      <span class="eyebrow">Metrica base</span>
      <strong>${escapeHtml(label(topMetric.metric || "actual_revenue_usd"))}</strong>
      <p>Valor ${number(topMetric.value || 0)} porque no hay evidencia real conectada.</p>
      <small>${escapeHtml(label(topMetric.evidence_status || "missing"))}</small>
    </article>
    <article class="real-world-card">
      <span class="eyebrow">Fuentes</span>
      <strong>${escapeHtml(topSource.name || "Manual revenue register")}</strong>
      <p>${number(disconnectedSources.length)} fuentes sin API conectada. Manual ready permite registro sin secreto.</p>
      <small>${escapeHtml(label(topSource.status || "manual_ready"))}</small>
    </article>
    <article class="real-world-card">
      <span class="eyebrow">Aprobacion</span>
      <strong>${escapeHtml(topApproval.id || "external_analytics_credentials")}</strong>
      <p>${escapeHtml(topApproval.decision || "CEO aprueba ruta segura antes de conectar APIs de analitica.")}</p>
      <small>${escapeHtml(label(topApproval.status || "pending"))}</small>
    </article>
    <article class="real-world-card">
      <span class="eyebrow">Riesgo</span>
      <strong>${escapeHtml(label(topRisk.risk || "metric_without_source"))}</strong>
      <p>${escapeHtml(topRisk.control || "evidence_status=missing and invented=false")}</p>
      <small>${escapeHtml(label(topRisk.severity || "high"))}</small>
    </article>
    <article class="real-world-card wide">
      <span class="eyebrow">Regla S7</span>
      <strong>No hay datos, no hay claim</strong>
      <p><span>no ventas inventadas</span><span>no metricas falsas</span><span>manual ready</span><span>APIs no conectadas</span><span>secretos bloqueados</span></p>
      <small>external_connection_enabled=false</small>
    </article>
  `;
}

function renderRealWorldExecutionQueue() {
  const container = $("#real-world-execution-grid");
  if (!container) return;

  const status = state.data.realWorldExecutionStatus || state.data.ceoDailyCenter?.real_world_execution || {};
  const queue = Array.isArray(state.data.realWorldExecutionQueue)
    ? state.data.realWorldExecutionQueue
    : (Array.isArray(status.queue_snapshot) ? status.queue_snapshot : []);
  const approvals = Array.isArray(state.data.realWorldExecutionApprovalNeeded) ? state.data.realWorldExecutionApprovalNeeded : [];
  const prepared = queue.filter((item) => item.state === "prepared");
  const readyInternal = queue.filter((item) => item.state === "ready_internal");
  const waitingCeo = queue.filter((item) => item.requires_ceo || String(item.state || "").startsWith("waiting_"));
  const waitingCredentials = queue.filter((item) => item.requires_credentials || item.state === "waiting_credentials");
  const waitingPaid = queue.filter((item) => item.requires_money || item.state === "waiting_paid_approval");
  const blocked = queue.filter((item) => item.state === "blocked");
  const highPriority = queue.filter((item) => item.priority === "critical" || item.priority === "high");
  const next = queue[0] || {};
  const topApproval = approvals[0] || waitingCeo[0] || {};
  const nextSteps = Array.isArray(status.next_steps) ? status.next_steps : [];

  container.innerHTML = `
    <article class="execution-queue-card primary">
      <span class="eyebrow">Real World Execution Queue</span>
      <strong>${number(status.total_items || queue.length)} acciones preparadas</strong>
      <p>Cola local para priorizar acciones futuras. No ejecuta pagos, cuentas, publicaciones ni APIs externas.</p>
      <div class="execution-queue-kpis">
        <small><b>${number(status.ready_internal || readyInternal.length)}</b>internas</small>
        <small><b>${number(status.approval_needed || waitingCeo.length)}</b>CEO</small>
        <small><b>${number(status.blocked || blocked.length)}</b>bloqueadas</small>
      </div>
    </article>
    <article class="execution-queue-card">
      <span class="eyebrow">Prepared</span>
      <strong>${number(status.prepared || prepared.length)} acciones</strong>
      <p>Preparadas/documentales: pueden quedarse en backlog sin ejecutar nada real.</p>
      <small>external_execution_enabled=false</small>
    </article>
    <article class="execution-queue-card">
      <span class="eyebrow">Ready internal</span>
      <strong>${number(status.ready_internal || readyInternal.length)} internas</strong>
      <p>Trabajo interno manual permitido solo si no requiere dinero, credenciales ni cuenta externa.</p>
      <small>manual_execution_confirmed=false</small>
    </article>
    <article class="execution-queue-card">
      <span class="eyebrow">Waiting CEO</span>
      <strong>${number(status.approval_needed || approvals.length)} decisiones</strong>
      <p>${escapeHtml(topApproval.next_action || "CEO decide cuentas, dinero, credenciales o revision legal antes de avanzar.")}</p>
      <small>${escapeHtml(topApproval.id || "approval-needed")}</small>
    </article>
    <article class="execution-queue-card">
      <span class="eyebrow">Credenciales</span>
      <strong>${number(status.credentials_needed || waitingCredentials.length)} bloqueadas</strong>
      <p>No se guardan passwords, tokens, API keys, Clave SOL ni sesiones externas.</p>
      <small>credentials_stored=false</small>
    </article>
    <article class="execution-queue-card">
      <span class="eyebrow">Dinero</span>
      <strong>${number(status.money_needed || waitingPaid.length)} requieren ROI</strong>
      <p>Pagos, dominios, herramientas, anuncios e inventario quedan esperando aprobacion CEO.</p>
      <small>payment_executed=false</small>
    </article>
    <article class="execution-queue-card">
      <span class="eyebrow">Blocked</span>
      <strong>${number(status.blocked || blocked.length)} acciones</strong>
      <p>Acciones riesgosas o externas sin vault/aprobacion quedan bloqueadas por defecto.</p>
      <small>api_execution_confirmed=false</small>
    </article>
    <article class="execution-queue-card">
      <span class="eyebrow">Prioridad</span>
      <strong>${number(highPriority.length)} alta/critica</strong>
      <p>${escapeHtml(next.action || "CEREBRO prioriza segun impacto economico, riesgo y dependencia.")}</p>
      <small>${escapeHtml(label(next.priority || "medium"))}</small>
    </article>
    <article class="execution-queue-card wide">
      <span class="eyebrow">CEREBRO</span>
      <strong>Prioriza, bloquea o pide aprobacion</strong>
      <p>${nextSteps.slice(0, 5).map((step) => `<span>${escapeHtml(step)}</span>`).join("") || "<span>Priorizar</span><span>Pedir CEO</span><span>No ejecutar real</span>"}</p>
      <small>Vincula Revenue, Workday y Mission Loop como backlog preparado.</small>
    </article>
  `;
}

function renderSocialIdentityMap() {
  const container = $("#social-identity-grid");
  if (!container) return;

  const status = state.data.socialIdentityStatus || state.data.ceoDailyCenter?.social_identity || {};
  const accounts = Array.isArray(state.data.socialIdentityAccounts)
    ? state.data.socialIdentityAccounts
    : (Array.isArray(status.accounts_snapshot) ? status.accounts_snapshot : []);
  const approvals = Array.isArray(state.data.socialIdentityApprovalNeeded) ? state.data.socialIdentityApprovalNeeded : [];
  const risks = Array.isArray(state.data.socialIdentityRisks) ? state.data.socialIdentityRisks : [];
  const unknown = accounts.filter((item) => item.state === "unknown");
  const prepared = accounts.filter((item) => item.state === "prepared");
  const proposed = accounts.filter((item) => item.state === "proposed_new");
  const credentials = accounts.filter((item) => item.requires_credentials);
  const creation = accounts.filter((item) => item.requires_account_creation);
  const topApproval = approvals[0] || {};
  const topRisk = risks[0] || {};
  const platforms = Array.isArray(status.platforms) ? status.platforms : [];
  const nextSteps = Array.isArray(status.next_steps) ? status.next_steps : [];

  container.innerHTML = `
    <article class="social-identity-card primary">
      <span class="eyebrow">Social Identity Map</span>
      <strong>${number(status.total_accounts || accounts.length)} cuentas y canales</strong>
      <p>${number(status.confirmed_existing || 0)} confirmadas. ${number(status.prepared || prepared.length)} prepared. ${number(status.unknown || unknown.length)} unknown. Sin publicacion real.</p>
      <div class="social-identity-kpis">
        <small><b>${number(status.proposed_new || proposed.length)}</b>propuestas</small>
        <small><b>${number(status.needs_ceo || approvals.length)}</b>CEO</small>
        <small><b>${number(status.needs_credentials || credentials.length)}</b>credenciales</small>
      </div>
    </article>
    <article class="social-identity-card">
      <span class="eyebrow">Cuentas unknown</span>
      <strong>${number(status.unknown || unknown.length)} sin evidencia</strong>
      <p>Si no hay cuenta oficial confirmada, el estado queda unknown o existing_unconfirmed.</p>
      <small>account_connected=false</small>
    </article>
    <article class="social-identity-card">
      <span class="eyebrow">Nuevas propuestas</span>
      <strong>${number(status.proposed_new || proposed.length)} propuestas</strong>
      <p>Crear cuenta externa requiere definicion CEO; S.2 solo deja mapa y nombres pendientes.</p>
      <small>${number(status.needs_account_creation || creation.length)} requieren creacion</small>
    </article>
    <article class="social-identity-card">
      <span class="eyebrow">Requiere CEO</span>
      <strong>${escapeHtml(topApproval.platform || "Definicion pendiente")}</strong>
      <p>${escapeHtml(topApproval.recommended_action || "Cuentas nuevas, oficiales o sensibles quedan pendientes de CEO.")}</p>
      <small>${number(status.approval_needed_count || approvals.length)} en approval-needed</small>
    </article>
    <article class="social-identity-card">
      <span class="eyebrow">Credenciales</span>
      <strong>${number(status.needs_credentials || credentials.length)} bloqueadas</strong>
      <p>No se guardan passwords, tokens, API keys ni sesiones de redes sociales.</p>
      <small>credentials_stored=false</small>
    </article>
    <article class="social-identity-card">
      <span class="eyebrow">Riesgos</span>
      <strong>${escapeHtml(topRisk.area || `${number(status.high_risk || 0)} high / ${number(status.sensitive || 0)} sensitive`)}</strong>
      <p>${escapeHtml(topRisk.recommended_action || "Identidad publica, marca y cuentas sensibles requieren validacion.")}</p>
      <small>${escapeHtml(label(topRisk.risk || "controlled"))}</small>
    </article>
    <article class="social-identity-card">
      <span class="eyebrow">Plataformas</span>
      <strong>${number(platforms.length || 10)} soportadas</strong>
      <p>${platforms.slice(0, 6).map((platform) => `<span>${escapeHtml(platform)}</span>`).join("") || "<span>TikTok</span><span>Instagram</span><span>YouTube</span>"}</p>
      <small>Todas no conectadas por defecto.</small>
    </article>
    <article class="social-identity-card wide">
      <span class="eyebrow">Siguiente paso</span>
      <strong>${escapeHtml(nextSteps[0] || "Confirmar cuentas oficiales existentes")}</strong>
      <p>${nextSteps.slice(0, 5).map((step) => `<span>${escapeHtml(step)}</span>`).join("") || "<span>Confirmar existentes</span><span>Definir nuevas</span><span>Sin publicar</span>"}</p>
      <small>prepared no equivale a publicado, conectado ni aprobado para crear cuentas.</small>
    </article>
  `;
}

function renderArsenalBlueprint() {
  const container = $("#arsenal-blueprint-grid");
  if (!container) return;

  const status = state.data.arsenalStatus || {};
  const readiness = state.data.arsenalReadiness || status.readiness || {};
  const categories = Array.isArray(state.data.arsenalCategories) ? state.data.arsenalCategories : [];
  const catalog = Array.isArray(state.data.arsenalCatalog) ? state.data.arsenalCatalog : [];
  const risks = Array.isArray(state.data.arsenalRisks) ? state.data.arsenalRisks : [];
  const sellable = catalog.filter((item) => item.is_sellable);
  const ceoRequired = catalog.filter((item) => item.requires_ceo_approval);
  const topItem = catalog[0];
  const topRisk = risks[0];
  const activeCategories = categories.filter((item) => item.items > 0);
  const categorySample = (activeCategories.length ? activeCategories : categories).slice(0, 7);

  container.innerHTML = `
    <article class="arsenal-blueprint-card primary">
      <span class="eyebrow">Estado blueprint</span>
      <strong>${escapeHtml(label(status.status || "arsenal_blueprint_governed_prepared"))}</strong>
      <p>${escapeHtml(status.purpose || "Almacen estrategico de APIs, skills, modelos, conectores y capacidades.")}</p>
      <div class="arsenal-kpis">
        <small><b>${number(readiness.score ?? 0)}</b>readiness</small>
        <small><b>${number(status.catalog_items || catalog.length)}</b>items</small>
      </div>
    </article>
    <article class="arsenal-blueprint-card">
      <span class="eyebrow">Categorias</span>
      <strong>${number(status.categories || categories.length)} preparadas</strong>
      <p>${categorySample.map((item) => `<span>${escapeHtml(item.name)}</span>`).join("")}</p>
      <small>Sin datos reales: status empty/prepared. No se inventan recursos.</small>
    </article>
    <article class="arsenal-blueprint-card">
      <span class="eyebrow">Catalogo</span>
      <strong>${escapeHtml(topItem?.name || "Catalogo metadata")}</strong>
      <p>${topItem ? `${label(topItem.item_type)} / ${label(topItem.category)}.` : "Preparado para registrar APIs, skills, modelos, conectores y productos tecnicos."}</p>
      <small>${topItem ? escapeHtml(topItem.technical_status || "blueprint_prepared") : "Solo metadata, sin secretos."}</small>
    </article>
    <article class="arsenal-blueprint-card">
      <span class="eyebrow">Vendibles</span>
      <strong>${number(sellable.length)} candidatos</strong>
      <p>APIs y skills vendibles pasan por AUDITORIA y Revenue OS antes de vender.</p>
      <small>${number(ceoRequired.length)} requieren aprobacion CEO por costo o credenciales.</small>
    </article>
    <article class="arsenal-blueprint-card">
      <span class="eyebrow">Riesgos</span>
      <strong>${number(risks.length || status.risks_open || 0)} abiertos</strong>
      <p>${topRisk ? `${topRisk.title}: ${label(topRisk.severity)}.` : "Riesgos preparados: costos, secretos, calidad, seguridad y vendibilidad."}</p>
      <small>APIs externas, proveedores con costo y secretos siguen bloqueados.</small>
    </article>
    <article class="arsenal-blueprint-card wide">
      <span class="eyebrow">Gobernanza</span>
      <p><span>CEREBRO consulta</span><span>CREADOR aporta</span><span>FORJA prepara</span><span>AUDITORIA revisa</span><span>NUBE controla costos</span><span>Revenue OS evalua</span></p>
      <small>Blueprint gobernado: external_connection_enabled=false, runtime_connected=false, secrets_stored=false.</small>
    </article>
  `;
}

function renderDepartmentAudits() {
  const container = $("#department-audit-grid");
  if (!container) return;

  const departments = Array.isArray(state.data.departments) ? state.data.departments : [];
  const audits = Array.isArray(state.data.departmentAudits) ? state.data.departmentAudits : [];
  const latestByDepartment = new Map();
  audits.forEach((audit) => {
    if (!latestByDepartment.has(audit.department_id)) latestByDepartment.set(audit.department_id, audit);
  });
  const priorityIds = ["pluma", "lente", "marketing", "dcft", "sentinela", "ecommerce"];
  const priorityDepartments = priorityIds
    .map((id) => departments.find((department) => department.id === id))
    .filter(Boolean);
  const cards = (priorityDepartments.length ? priorityDepartments : departments.slice(0, 6));

  container.innerHTML = cards.length ? cards.map((department) => {
    const audit = latestByDepartment.get(department.id);
    const heart = audit?.heart_cabin || department.heart_cabin || {};
    const technical = audit?.technical_cabin || department.technical_cabin || {};
    const human = audit?.human_cabin || department.human_cabin || {};
    const gaps = Array.isArray(audit?.gaps) ? audit.gaps : (Array.isArray(department.missing_data) ? department.missing_data : []);
    const requiresForja = Boolean(audit?.requires_forja);
    const requiresCeo = Boolean(audit?.requires_ceo || ["dcft", "sentinela", "arsenal"].includes(department.id));
    return `
      <article class="department-audit-card">
        <div class="badge-row">
          ${badge(audit?.status || department.operational_status || "needs_audit")}
          <span class="badge">${escapeHtml(audit ? "audit" : "inventario")}</span>
        </div>
        <strong>${escapeHtml(department.name)}</strong>
        <p>${escapeHtml(audit?.recommendation || department.revenue_relation || "Pendiente de auditoria.")}</p>
        <div class="cabin-mini-grid" aria-label="Estado de cabinas">
          <small><b>Corazón</b>${escapeHtml(label(heart.status || "unknown"))}</small>
          <small><b>Técnica</b>${escapeHtml(label(technical.status || "unknown"))}</small>
          <small><b>Humana</b>${escapeHtml(label(human.status || "unknown"))}</small>
        </div>
        <div class="department-audit-flags">
          <span>${number(gaps.length)} brechas</span>
          <span>${requiresForja ? "FORJA preparada" : "sin FORJA"}</span>
          <span>${requiresCeo ? "CEO" : "sin CEO"}</span>
        </div>
        <small>${escapeHtml(audit?.economic_impact || department.revenue_relation || "Impacto por revisar.")}</small>
      </article>
    `;
  }).join("") : emptyState("Sin inventario de departamentos.", "La API de departamentos no respondio.");
}

function renderCerebroDailyMeeting() {
  const container = $("#daily-meeting-content");
  if (!container) return;
  const meeting = dailyMeetingModels[state.meeting] || dailyMeetingModels.morning;
  const boundaries = [
    {
      title: "Datos reales",
      items: dailyMeetingDataBoundaries.real
    },
    {
      title: "Datos preparados",
      items: dailyMeetingDataBoundaries.prepared
    }
  ];

  $$(".meeting-switch button").forEach((button) => {
    button.classList.toggle("active", button.dataset.meeting === state.meeting);
  });

  container.innerHTML = `
    <article class="meeting-summary-card">
      <span>${escapeHtml(meeting.label)}</span>
      <strong>${escapeHtml(meeting.headline)}</strong>
      <p>${escapeHtml(meeting.summary)}</p>
      <div class="meeting-focus-grid">
        <small><b>Prioridad</b>${escapeHtml(meeting.priority)}</small>
        <small><b>Decisión</b>${escapeHtml(meeting.decision)}</small>
        <small><b>Oportunidad</b>${escapeHtml(meeting.opportunity)}</small>
        <small><b>Riesgo</b>${escapeHtml(meeting.risk)}</small>
      </div>
      <em>${escapeHtml(meeting.approval)}</em>
    </article>
    <details class="meeting-detail-block">
      <summary>Tareas por departamento</summary>
      <div class="meeting-task-grid" aria-label="Tareas por departamento">
        ${meeting.tasks.map(([department, task]) => `
          <article>
            <span>${escapeHtml(department)}</span>
            <p>${escapeHtml(task)}</p>
          </article>
        `).join("")}
      </div>
    </details>
    <details class="meeting-detail-block">
      <summary>Datos reales vs preparados</summary>
      <div class="meeting-boundaries" aria-label="Datos reales y preparados">
        ${boundaries.map((boundary) => `
          <article>
            <strong>${escapeHtml(boundary.title)}</strong>
            <p>${boundary.items.map((item) => `<span>${escapeHtml(item)}</span>`).join("")}</p>
          </article>
        `).join("")}
      </div>
    </details>
  `;
}

function renderCerebroOperational() {
  const container = $("#cerebro-operational-grid");
  if (!container) return;

  const status = state.data.cerebroStatus || {};
  const decisions = Array.isArray(state.data.cerebroDecisions) ? state.data.cerebroDecisions : [];
  const tasks = Array.isArray(state.data.cerebroTasks) ? state.data.cerebroTasks : [];
  const brief = state.meeting === "evening"
    ? (state.data.cerebroEvening || {})
    : (state.data.cerebroMorning || {});
  const blocked = tasks.filter((task) => task.blocked || task.state === "blocked");
  const delegated = tasks.filter((task) => !task.blocked).slice(0, 4);
  const integration = state.data.integrationBus || {};
  const busRoutes = Array.isArray(integration.routes) ? integration.routes : [];
  const activeInternalRoutes = busRoutes.filter((route) => route.source === "cerebro" && route.allowed);
  const blockedInternalRoutes = busRoutes.filter((route) => route.source === "cerebro" && !route.allowed);
  const lastDispatch = busRoutes.find((route) => route.source === "cerebro" && route.audit_event_id);
  const pending = decisions.filter((decision) => (
    ["draft", "proposed", "waiting_ceo"].includes(String(decision.state || "").toLowerCase())
  )).slice(0, 4);
  const allowed = status.allowed_departments || [];
  const protectedTargets = status.protected_targets || ["DCFT", "SENTINELA", "ARSENAL"];

  container.innerHTML = `
    <article class="cerebro-operational-card">
      <span class="eyebrow">Estado CEREBRO</span>
      <strong>${escapeHtml(label(status.status || "cerebro_operational_internal"))}</strong>
      <p>${escapeHtml(brief.summary || "CEREBRO opera dentro del backend/control center, sin apps protegidas ni runtimes externos.")}</p>
      <div class="cerebro-operational-stats">
        <small><b>${number(status.decisions || decisions.length)}</b> decisiones</small>
        <small><b>${number(status.tasks || tasks.length)}</b> tareas</small>
        <small><b>${number(status.blocked_tasks || blocked.length)}</b> bloqueos</small>
      </div>
    </article>
    <article class="cerebro-operational-card">
      <span class="eyebrow">Decisiones CEO</span>
      ${pending.length ? pending.map((decision) => `
        <div class="mini-row">
          <strong>${escapeHtml(decision.title)}</strong>
          <small>${escapeHtml(label(decision.state))} · ${escapeHtml(decision.priority || "p1")}</small>
        </div>
      `).join("") : emptyState("Sin decisiones CEREBRO pendientes.", "CEREBRO puede preparar decisiones internas para revisión CEO.")}
    </article>
    <article class="cerebro-operational-card">
      <span class="eyebrow">Tareas internas</span>
      ${delegated.length ? delegated.map((task) => `
        <div class="mini-row">
          <strong>${escapeHtml(task.destination_label)}</strong>
          <small>${escapeHtml(task.title)} · ${escapeHtml(label(task.state))}</small>
        </div>
      `).join("") : emptyState("Sin tareas internas delegadas.", "Los destinos permitidos reciben intención, no ejecución externa.")}
    </article>
    <article class="cerebro-operational-card protected">
      <span class="eyebrow">Bloqueos activos</span>
      <p>${protectedTargets.map((target) => `<span>${escapeHtml(target)}</span>`).join("")}</p>
      <small>No-touch: DCFT, SENTINELA y ARSENAL no reciben ejecución real.</small>
    </article>
    <article class="cerebro-operational-card">
      <span class="eyebrow">Bus interno</span>
      <strong>${number(activeInternalRoutes.length)} rutas internas activas</strong>
      <p><span>${number(blockedInternalRoutes.length)} bloqueadas</span><span>sin runtime externo</span></p>
      <small>Último despacho: ${escapeHtml(lastDispatch ? label(lastDispatch.target || lastDispatch.target_service) : "sin dispatch registrado")}</small>
    </article>
    <article class="cerebro-operational-card wide">
      <span class="eyebrow">Departamentos permitidos</span>
      <p>${allowed.slice(0, 12).map((item) => `<span>${escapeHtml(item)}</span>`).join("")}</p>
    </article>
  `;
}

function renderTrafficLights() {
  const hasErrors = Object.keys(state.errors).length > 0;
  const snapshot = companySnapshot();

  const lights = [
    {
      title: "Dirección",
      tone: snapshot.pendingDecisions ? "amber" : "green",
      status: snapshot.pendingDecisions ? "Pendiente" : "Activa",
      body: snapshot.pendingDecisions ? "Revisar hoy." : "Local activo."
    },
    {
      title: "Construcción",
      tone: "amber",
      status: "Preparada",
      body: "Apps preparadas."
    },
    {
      title: "Seguridad",
      tone: hasErrors || snapshot.activeRisks ? "red" : "green",
      status: snapshot.activeRisks ? "Riesgo" : "Protegida",
      body: snapshot.activeRisks ? "Revisar riesgos." : "Protegido."
    },
    {
      title: "Ingresos",
      tone: "amber",
      status: "Pendiente",
      body: "Sin ventas reales."
    }
  ];

  $("#traffic-grid").innerHTML = lights.map((light) => `
    <article class="traffic-card ${escapeHtml(light.tone)}">
      <span class="traffic-dot" aria-hidden="true"></span>
      <div>
        <strong>${escapeHtml(light.title)}</strong>
        <small>${escapeHtml(light.status)}</small>
      </div>
      <p>${escapeHtml(light.body)}</p>
    </article>
  `).join("");
}

function renderQuickActions() {
  const commands = [
    { label: "Hablar con CEREBRO", detail: "Reunión diaria", target: "cerebro", appId: "cerebro" },
    { label: "Pedir trabajo a FORJA", detail: "Construcción controlada", target: "construccion", appId: "forja" },
    { label: "Ver AUDITORIA", detail: "Calidad y gates", target: "control_seguridad", appId: "auditor" },
    { label: "Ver NUBE", detail: "Operación local", target: "operacion", appId: "nube" },
    { label: "Ver riesgos", detail: "Riesgos CEO", target: "alerts" },
    { label: "Ver SENTINELA", detail: "Seguridad pendiente", target: "control_seguridad", appId: "centinela" },
    { label: "Ver DCFT protegido", detail: "Protección activa", target: "doctor_contable_financiero_tributario", appId: "doctor_contable_financiero_tributario" },
    { label: "Ver Arsenal", detail: "Almacén pendiente", target: "arsenal", appId: "arsenal" },
    { label: "Ver oportunidades", detail: "Productos e ingresos", target: "productos_comerciales" }
  ];

  const renderCommand = (command) => {
    const human = command.appId ? humanStateFor(command.appId) : { status: "ready", source: "Cabina", tone: "green" };
    const connected = human.real === true;
    const copy = command.appId
      ? (connected ? "Conexión real" : "Sin conexión real")
      : "Local activo";
    return `
      <button class="quick-command ${escapeHtml(human.tone)}" data-quick-target="${escapeHtml(command.target)}" type="button">
        ${command.appId ? appIcon(command.appId) : ""}
        <span>${escapeHtml(command.detail || copy)}</span>
        <strong>${escapeHtml(command.label)}</strong>
        <small>${escapeHtml(copy)}</small>
      </button>
    `;
  };
  const primaryCommands = commands.slice(0, 5);
  const secondaryCommands = commands.slice(5);
  $("#quick-actions").innerHTML = `
    ${primaryCommands.map(renderCommand).join("")}
    <details class="more-actions">
      <summary>Más acciones</summary>
      <div>${secondaryCommands.map(renderCommand).join("")}</div>
    </details>
  `;
  const map = $("#quick-actions-map");
  if (map) {
    map.innerHTML = primaryCommands.map((command) => {
      const human = command.appId ? humanStateFor(command.appId) : { tone: "green" };
      return `
        <button class="quick-command compact ${escapeHtml(human.tone)}" data-quick-target="${escapeHtml(command.target)}" type="button">
          ${command.appId ? appIcon(command.appId) : ""}
          <strong>${escapeHtml(command.label)}</strong>
        </button>
      `;
    }).join("");
  }
}

function renderPriorityApps() {
  const firstIds = ["direccion", "construccion", "control_seguridad"];
  const firstDepartments = firstIds.map((id) => companyDepartments.find((department) => department.id === id)).filter(Boolean);
  const restDepartments = companyDepartments.filter((department) => !firstIds.includes(department.id));
  const orderedDepartments = [...firstDepartments, ...restDepartments];
  $("#priority-apps").innerHTML = orderedDepartments.map((department, index) => {
    const stateInfo = departmentState(department);
    const anchorId = department.id === "almacen_estratégico" ? "arsenal" : department.id;
    const insertMore = index === firstDepartments.length;
    return `
      ${insertMore ? `
        <article class="departments-more-card" aria-label="Ver todos los departamentos">
          <strong>Ver todos</strong>
          <small>Más áreas quedan abajo.</small>
          <button class="mini-action" data-quick-target="${escapeHtml(anchorId)}" type="button">Ver todos</button>
        </article>
      ` : ""}
      <article class="department-card director-app-card ${escapeHtml(stateInfo.tone)} dept-${escapeHtml(department.accent)} ${index >= firstDepartments.length ? "mobile-secondary" : "mobile-primary"}" id="${escapeHtml(anchorId)}">
        <div class="department-card-head director-card-head">
          ${appIcon(department.icon)}
          <div>
            <span class="eyebrow">${escapeHtml(department.shortName)}</span>
            <h3>${escapeHtml(department.name)}</h3>
          </div>
          ${badge(stateInfo.status)}
        </div>
        <p>${escapeHtml(department.function)}</p>
        <div class="department-meta">
          <strong>${number(stateInfo.issues)} asuntos</strong>
          <small>${escapeHtml(stateInfo.status)}</small>
        </div>
        <div class="department-apps" aria-label="Apps del departamento ${escapeHtml(department.name)}">
          ${department.apps.slice(0, 4).map((name) => `<span>${escapeHtml(name)}</span>`).join("")}
          ${department.apps.length > 4 ? `<span>+${department.apps.length - 4}</span>` : ""}
        </div>
        <button class="mini-action premium-mini-action" data-quick-target="${escapeHtml(department.target)}" type="button">${escapeHtml(department.action)}</button>
      </article>
    `;
  }).join("");
}

function renderDepartmentalSimulationFlows() {
  const container = $("#departmental-flows");
  if (!container) return;

  container.innerHTML = departmentalSimulationFlows.map((flow) => `
    <article class="status-lane simulated-flow">
      <div class="lane-head">
        <span class="eyebrow">${escapeHtml(flow.title)}</span>
        <p>${escapeHtml(flow.trigger)}</p>
      </div>
      <div class="lane-list">
        <div class="lane-note">
          <strong>Simulación departamental</strong>
          <small>${escapeHtml(flow.cerebro)}</small>
        </div>
        <div class="lane-note">
          <strong>Sin ejecución externa</strong>
          <small>${escapeHtml(flow.guardrail)}</small>
        </div>
        ${flow.departments.slice(0, 3).map((department) => `
          <span class="lane-chip amber">
            <strong>${escapeHtml(department)}</strong>
            <small>${escapeHtml(flow.status.join(" / "))}</small>
          </span>
        `).join("")}
      </div>
    </article>
  `).join("");
}

function renderStatusLanes() {
  const snapshot = companySnapshot();
  const lanes = [
    {
      id: "real",
      title: "Datos reales",
      copy: "Local activo. Sin rutas externas.",
      apps: humanAppCatalog.filter((definition) => humanStateFor(definition.id).real)
    },
    {
      id: "prepared",
      title: "Datos preparados",
      copy: `${snapshot.prepared} perfiles. Runtimes apagados.`,
      apps: humanAppCatalog.filter((definition) => definition.lane !== "protected" && humanStateFor(definition.id).real !== true).slice(0, 7)
    },
    {
      id: "protected",
      title: "Protegido / no-touch",
      copy: "DCFT y SENTINELA representados, no conectados.",
      apps: humanAppCatalog.filter((definition) => definition.lane === "protected" || ["forja", "centinela", "nube"].includes(definition.id))
    },
    {
      id: "next",
      title: "Próximos pasos",
      copy: "ARSENAL planificado, sin runtime.",
      apps: humanAppCatalog.filter((definition) => definition.id === "arsenal")
    }
  ];

  $("#status-lanes").innerHTML = lanes.map((lane) => `
    <article class="status-lane ${escapeHtml(lane.id)}">
      <div class="lane-head">
        <span class="eyebrow">${escapeHtml(lane.title)}</span>
        <p>${escapeHtml(lane.copy)}</p>
      </div>
      <div class="lane-list">
        ${
          lane.apps.length
            ? lane.apps.map((definition) => {
              const human = humanStateFor(definition.id);
              return `
                <button class="lane-chip ${escapeHtml(human.tone)}" data-quick-target="${escapeHtml(definition.id)}" type="button">
                  <strong>${escapeHtml(definition.name)}</strong>
                  <small>${escapeHtml(label(definition.displayStatus || human.status))}</small>
                </button>
              `;
            }).join("")
            : `
              <div class="lane-note">
                <strong>Sin conexión nueva</strong>
                <small>Runtimes apagados.</small>
              </div>
            `
        }
      </div>
    </article>
  `).join("");
}

function renderDecisionRail() {
  const governance = state.data.governance || {};
  const decisions = governance.pending_decisions || [];
  const risks = governance.critical_risks || [];
  const decision = nextDecision();

  const railApps = $("#rail-priority-apps");
  if (railApps) {
    railApps.innerHTML = companyDepartments.slice(0, 6).map((department) => {
      const stateInfo = departmentState(department);
      return `
        <button class="rail-app ${escapeHtml(stateInfo.tone)} dept-${escapeHtml(department.accent)}" data-quick-target="${escapeHtml(department.id === "almacen_estratégico" ? "arsenal" : department.id)}" type="button">
          ${appIcon(department.icon)}
          <span>
            <strong>${escapeHtml(department.shortName)}</strong>
            <small>${number(stateInfo.issues)} asuntos / ${escapeHtml(stateInfo.status)}</small>
          </span>
        </button>
      `;
    }).join("");
  }

  const railDecisions = $("#rail-decisions");
  if (railDecisions) {
    const items = [
      {
        title: decision.title,
        body: decision.body,
        tone: "amber"
      },
      {
        title: `${connectedProfiles().length} conexiones reales`,
        body: `${integrationProfiles().length} perfiles preparados. Runtimes externos apagados.`,
        tone: connectedProfiles().length ? "red" : "green"
      },
      {
        title: risks.length ? `${risks.length} riesgos abiertos` : "Riesgos bajo control",
        body: risks[0]?.description || "Sin riesgo crítico abierto desde governance.",
        tone: risks.length ? "red" : "green"
      },
      {
        title: decisions.length ? `${decisions.length} decisiones pendientes` : "Sin cola crítica",
        body: decisions[0]?.description || "No hay decisión urgente creada desde governance.",
        tone: decisions.length ? "amber" : "green"
      }
    ];
    railDecisions.innerHTML = items.map((item) => `
      <article class="rail-note ${escapeHtml(item.tone)}">
        <span class="traffic-dot" aria-hidden="true"></span>
        <strong>${escapeHtml(item.title)}</strong>
        <small>${escapeHtml(item.body)}</small>
      </article>
    `).join("");
  }
}

function renderMetrics() {
  const snapshot = companySnapshot();
  const cards = [
    { id: "decisions", label: "Decisiones CEO", value: snapshot.pendingDecisions, status: snapshot.pendingDecisions ? "degraded" : "healthy" },
    { id: "opportunities", label: "Oportunidades", value: snapshot.preparedOpportunities, status: "degraded" },
    { id: "risks", label: "Riesgos", value: snapshot.activeRisks, status: snapshot.activeRisks ? "blocked" : "healthy" },
    { id: "construction", label: "En construcción", value: snapshot.constructionTasks, status: "degraded" }
  ];
  $("#metric-grid").innerHTML = cards.map((metric) => `
    <article class="metric">
      <span>${escapeHtml(metric.label)}</span>
      <strong>${number(metric.value)}</strong>
      <small>${badge(metric.status)}</small>
    </article>
  `).join("");

  $(".score-card span").textContent = "Conexiones reales";
  $("#service-score").textContent = `${snapshot.connected}`;
  $("#service-score-copy").textContent = `${snapshot.connected} conexiones reales activas · ${snapshot.prepared} perfiles preparados · runtimes externos apagados.`;
}

function renderApps() {
  const registeredApps = apps();
  const query = state.search.toLowerCase();
  const filtered = registeredApps.filter((app) => {
    const byStatus = state.statusFilter === "all" || app.status === state.statusFilter;
    const text = `${app.name} ${app.id} ${app.type} ${app.description}`.toLowerCase();
    return byStatus && text.includes(query);
  });

  $("#apps-grid").innerHTML = filtered.length ? filtered.map((app) => {
    const definition = humanAppCatalog.find((item) => item.id === app.id);
    const human = humanStateFor(app.id);
    const profile = profileById(app.id);
    return `
    <article class="app-card ${escapeHtml(human.tone)}">
      <div class="badge-row">${badge(human.status, app.status)}<span class="badge">${label(app.type)}</span></div>
      <h3>${escapeHtml(app.name)}</h3>
      <p>${escapeHtml(definition?.role || app.description)}</p>
      <small>${escapeHtml(definition?.capability || app.description)}</small>
      <div class="badge-row">
        <span class="badge">${escapeHtml(human.source)}</span>
        <span class="badge">${profile?.contract_id ? escapeHtml(profile.contract_id) : escapeHtml(label(app.touch_policy))}</span>
      </div>
    </article>
  `;
  }).join("") : emptyState("No hay aplicaciones para este filtro.");
}

function renderAlerts() {
  const alerts = state.data.controlCenter?.alerts || [];
  const incidents = Array.isArray(state.data.observability?.incidents) ? state.data.observability.incidents : [];
  const criticalRisks = state.data.governance?.critical_risks || [];
  const combined = [
    ...alerts.map((item) => ({ title: item.message, body: item.source, status: item.status || item.severity, meta: label(item.severity) })),
    ...incidents.map((item) => ({ title: item.title || item.id, body: item.description, status: item.status, meta: "Incidente" })),
    ...criticalRisks.map((item) => ({ title: item.title, body: item.description, status: item.severity, meta: "Riesgo governance" }))
  ];

  $("#alerts-list").innerHTML = combined.length ? combined.map(listItem).join("") : emptyState("Sin alertas ni incidentes abiertos.");
}

function renderCeo() {
  const governance = state.data.governance || {};
  const decisions = governance.pending_decisions || [];
  const criticalRisks = governance.critical_risks || [];
  const timeline = buildTimeline();

  $("#ceo-decisions").innerHTML = decisions.length ? decisions.slice(0, 4).map((item) => listItem({
    title: item.title,
    body: item.description,
    status: item.status,
    meta: `Solicita: ${label(item.requested_by)}`,
    actions: `${actionButton("approve_decision", "Aprobar", item.id)}${actionButton("reject_decision", "Rechazar", item.id)}${actionButton("block_decision", "Bloquear", item.id)}`
  })).join("") : emptyState("Sin decisiones pendientes.", "La cabina queda lista para crear una nueva decisión.");

  $("#ceo-risks").innerHTML = criticalRisks.length ? criticalRisks.slice(0, 4).map((item) => listItem({
    title: item.title,
    body: item.description,
    status: item.severity,
    meta: label(item.status),
    actions: `${actionButton("mitigate_risk", "Mitigar", item.id)}${actionButton("close_risk", "Cerrar", item.id)}`
  })).join("") : emptyState("Sin riesgos críticos abiertos.");

  $("#timeline").innerHTML = timeline.map((item) => `
    <article class="timeline-item">
      <strong>${escapeHtml(item.title)}</strong>
      <p>${escapeHtml(item.body)}</p>
      <small>${escapeHtml(item.meta)}</small>
    </article>
  `).join("");
}

function renderGovernance() {
  renderActionMatrix();
  renderDecisionCenter();
  renderApprovalCenter();
  renderIntegrationGates();
  renderPolicyCenter();
  renderRiskCenter();
  renderGovernanceAudit();
  renderGovernanceReport();
}

function renderActionMatrix() {
  const actions = state.boundary?.actions || [];
  const sections = ["Decision Center", "Approval Center", "Integration Gates", "Policy Center", "Risk Center"];
  $("#action-matrix").innerHTML = sections.map((section) => {
    const items = actions.filter((action) => action.section === section);
    return `
      <article class="action-section">
        <strong>${escapeHtml(section)}</strong>
        <div class="action-pills">
          ${items.map((action) => actionButton(action.id, action.label, "", action.allowed ? "ghost" : "ghost")).join("")}
        </div>
      </article>
    `;
  }).join("");
}

function renderDecisionCenter() {
  const decisions = state.data.decisions || [];
  $("#governance-decisions").innerHTML = decisions.length ? decisions.slice(0, 8).map((item) => listItem({
    title: item.title,
    body: item.description,
    status: item.status,
    meta: `Solicita: ${label(item.requested_by)}`,
    actions: `${actionButton("approve_decision", "Aprobar", item.id)}${actionButton("reject_decision", "Rechazar", item.id)}${actionButton("block_decision", "Bloquear", item.id)}`
  })).join("") : emptyState("Sin decisiones registradas.", "Usa Crear decisión para generar la primera entrada.");
}

function renderApprovalCenter() {
  const approvals = state.data.approvals || [];
  $("#governance-approvals").innerHTML = approvals.length ? approvals.slice(0, 8).map((item) => listItem({
    title: item.title,
    body: item.description,
    status: item.status,
    meta: label(item.approval_type),
    actions: `${actionButton("approve_approval", "Aprobar", item.id)}${actionButton("reject_approval", "Rechazar", item.id)}${actionButton("escalate_approval", "Escalar", item.id)}`
  })).join("") : emptyState("Sin solicitudes registradas.", "Crea una solicitud para probar el flujo de aprobación.");
}

function renderIntegrationGates() {
  const gates = state.data.gates || [];
  $("#governance-gates").innerHTML = gates.length ? gates.slice(0, 10).map((item) => listItem({
    title: item.app_name,
    body: item.reason || "Gate controlado por politica humana.",
    status: item.state,
    meta: item.protected ? "Protegida" : "Disponible",
    actions: `${actionButton("request_discovery", "Solicitar discovery", item.app_id)}${actionButton("approve_discovery", "Aprobar discovery", item.app_id)}${actionButton("approve_connection", "Conexión futura", item.app_id)}${actionButton("block_gate", "Bloquear", item.app_id)}${actionButton("suspend_gate", "Suspender", item.app_id)}`
  })).join("") : emptyState("Sin gates de integración.");
}

function renderPolicyCenter() {
  const policies = state.data.policies || [];
  $("#governance-policies").innerHTML = policies.length ? policies.map((item) => listItem({
    title: item.title,
    body: (item.rules || []).join(" "),
    status: item.enforced ? "healthy" : "degraded",
    meta: item.status,
    actions: actionButton("evaluate_policy", "Evaluar politica", item.id)
  })).join("") : emptyState("Sin politicas governance cargadas.");
}

function renderRiskCenter() {
  const risks = state.data.risks || [];
  $("#governance-risks").innerHTML = risks.length ? risks.slice(0, 8).map((item) => listItem({
    title: item.title,
    body: item.description,
    status: item.severity,
    meta: `${label(item.risk_type)} / ${label(item.status)}`,
    actions: `${actionButton("mitigate_risk", "Mitigar", item.id)}${actionButton("close_risk", "Cerrar", item.id)}`
  })).join("") : emptyState("Sin riesgos abiertos.", "Crea un riesgo para validar el Risk Center.");
}

function renderGovernanceAudit() {
  const auditHistory = state.data.governanceAudit || [];
  $("#governance-history").innerHTML = auditHistory.length ? auditHistory.slice(0, 10).map((item) => listItem({
    title: item.action,
    body: item.detail,
    status: item.status,
    meta: `${label(item.severity)} / ${item.source}`
  })).join("") : emptyState("Sin eventos governance auditados todavía.");
}

function renderGovernanceReport() {
  const governance = state.data.governance || {};
  $("#governance-report").innerHTML = [
    listItem({
      title: label(governance.status || "governance_ready"),
      body: `Protegidas bloqueadas: ${number(governance.protected_apps_blocked)}. Conexiones externas: ${number(governance.external_connections_enabled)}.`,
      status: governance.protected_apps_blocked ? "healthy" : "blocked",
      meta: "Resumen"
    }),
    listItem({
      title: "Cobertura de control",
      body: `${number((state.data.decisions || []).length)} decisions, ${number((state.data.approvals || []).length)} solicitudes, ${number((state.data.risks || []).length)} riesgos, ${number((state.data.gates || []).length)} gates.`,
      status: "healthy",
      meta: "Reporte"
    })
  ].join("");
}

function renderOperator() {
  const control = state.data.controlCenter || {};
  const services = control.services || [];
  const events = state.data.events || [];
  const memory = state.data.memory || [];

  $("#services-list").innerHTML = services.length ? services.map((service) => listItem({
    title: service.name,
    body: service.detail,
    status: service.status,
    meta: label(service.category)
  })).join("") : emptyState("Sin servicios reportados.");

  $("#events-list").innerHTML = events.length ? events.map((event) => listItem({
    title: event.type || event.id,
    body: event.payload ? JSON.stringify(event.payload).slice(0, 160) : event.source,
    status: event.status,
    meta: event.source
  })).join("") : emptyState("No hay eventos internos registrados todavía.");

  $("#memory-list").innerHTML = memory.length ? memory.map((entry) => listItem({
    title: entry.title || entry.id,
    body: entry.content || entry.summary,
    status: entry.status,
    meta: entry.app_id || "memoria"
  })).join("") : emptyState("Memoria compartida preparada, sin entradas todavía.");
}

function renderAuditor() {
  const contracts = state.data.contracts || [];
  const audit = state.data.audit || {};
  const auditoriaStatus = state.data.auditoriaStatus || {};
  const auditoriaReviews = Array.isArray(state.data.auditoriaReviews) ? state.data.auditoriaReviews : [];
  const auditoriaQueue = Array.isArray(state.data.auditoriaQueue) ? state.data.auditoriaQueue : [];
  const roles = state.data.roles || [];

  $("#contracts-list").innerHTML = contracts.length ? contracts.map((contract) => listItem({
    title: contract.name || contract.id,
    body: contract.description,
    status: contract.status,
    meta: contract.app_id
  })).join("") : emptyState("No hay contratos activos. Las conexiones externas siguen bloqueadas.");

  $("#audit-list").innerHTML = [
    listItem({
      title: label(auditoriaStatus.status || "auditoria_operational_internal"),
      body: `${number(auditoriaStatus.queue)} en cola, ${number(auditoriaStatus.approved_reviews)} aprobadas, ${number(auditoriaStatus.blocked_reviews)} bloqueadas.`,
      status: auditoriaStatus.blocked_reviews ? "warning" : "healthy",
      meta: "AUDITORÍA operativa"
    }),
    listItem({
      title: label(audit.status || "central_audit_operational"),
      body: `${number(audit.events)} eventos, ${number(audit.reports)} reportes, categorías: ${(audit.categories || []).length}`,
      status: "healthy",
      meta: "Auditoría central"
    })
  ].join("");

  $("#auditoria-operational-list").innerHTML = auditoriaReviews.length ? [
    ...auditoriaQueue.slice(0, 2).map((review) => listItem({
      title: `${label(review.object_type)}: ${review.reference}`,
      body: `CEO, esto requiere revisión de AUDITORÍA antes de avanzar. Fuente: ${label(review.source)}.`,
      status: review.status,
      meta: review.priority
    })),
    ...auditoriaReviews.filter((review) => !auditoriaQueue.some((item) => item.id === review.id)).slice(0, 3).map((review) => listItem({
      title: `${label(review.object_type)}: ${review.reference}`,
      body: review.blockages?.length
        ? review.blockages.join(" ")
        : (review.observations || []).join(" ") || "Sin observaciones críticas registradas.",
      status: review.status,
      meta: review.auditor || "AUDITORÍA"
    }))
  ].join("") : emptyState("AUDITORÍA operativa lista; no hay revisiones en cola.");

  $("#roles-list").innerHTML = roles.length ? roles.map((role) => listItem({
    title: role.label,
    body: role.description,
    status: role.can_touch_external_apps ? "blocked" : "healthy",
    meta: `${role.permissions?.length || 0} permisos`
  })).join("") : emptyState("Sin roles cargados.");
}

function renderSystem() {
  const readiness = state.data.controlCenter?.readiness?.checks || [];
  const observability = state.data.observability || {};
  const integration = state.data.integrationBus || {};

  $("#readiness-list").innerHTML = readiness.length ? readiness.map((check) => listItem({
    title: check.label,
    body: check.detail,
    status: check.status,
    meta: check.required ? "required" : "optional"
  })).join("") : emptyState("Readiness sin checks disponibles.");

  $("#observability-list").innerHTML = [
    ...(observability.health || []).map((item) => listItem({
      title: item.id,
      body: item.detail,
      status: item.status,
      meta: "health"
    })),
    ...(observability.metrics || []).slice(0, 4).map((item) => listItem({
      title: item.id,
      body: `Valor: ${number(item.value)} / fuente ${item.source}`,
      status: item.status,
      meta: "metric"
    }))
  ].join("") || emptyState("Observabilidad sin datos.");

  $("#integration-list").innerHTML = [
    ...(integration.routes || []).map((item) => listItem({
      title: `${label(item.source || item.source_service)} → ${label(item.target || item.target_service)}`,
      body: item.allowed
        ? `Ruta interna real: ${label(item.action_type || "internal_request")}. Sin runtime externo ni API real.`
        : `Ruta bloqueada: ${item.blocked_reason || "requiere revisión CEO"}.`,
      status: item.status,
      meta: item.allowed ? "interna activa" : "bloqueada"
    })),
    ...(integration.prepared_routes || [])
      .filter((item) => ["doctor_contable_financiero_tributario", "centinela", "arsenal"].includes(item.target))
      .map((item) => listItem({
        title: `${label(item.source)} → ${label(item.target)}`,
        body: `Protegida: ${(item.purpose || []).slice(0, 3).join(", ")}. Sin ejecución externa.`,
        status: item.status,
        meta: "protegida"
      })),
    ...(integration.services || []).map((item) => listItem({
      title: item.name,
      body: `Categoría ${label(item.category)}. Conexión externa: ${number(item.external_connection_enabled)}`,
      status: item.status,
      meta: "servicio"
    })),
    ...(integration.dependencies || []).map((item) => listItem({
      title: item.name,
      body: item.dependency_type,
      status: item.status,
      meta: item.required ? "required" : "optional"
    }))
  ].join("") || emptyState("Integration Bus sin datos disponibles.");
}

function renderNubeControlTower() {
  const container = $("#nube-control-tower-list");
  if (!container) return;

  const status = state.data.nubeStatus || {};
  const projects = Array.isArray(state.data.nubeProjects) ? state.data.nubeProjects : [];
  const deployments = Array.isArray(state.data.nubeDeployments) ? state.data.nubeDeployments : [];
  const healthChecks = Array.isArray(state.data.nubeHealthChecks) ? state.data.nubeHealthChecks : [];
  const risks = Array.isArray(state.data.nubeRisks) ? state.data.nubeRisks : [];
  const costs = Array.isArray(state.data.nubeCosts) ? state.data.nubeCosts : [];
  const variables = Array.isArray(status.variables) ? status.variables : [];
  const latestDeployment = deployments[0] || {};
  const latestHealth = healthChecks[0] || {};
  const cost = costs[0] || {};

  container.innerHTML = [
    listItem({
      title: "NUBE / Torre Cloud",
      body: `${status.production_url || "URL no registrada"} · Control Center: ${status.control_center_url || "sin URL"}`,
      status: status.status || "nube_internal_control_tower",
      meta: status.provider || "proveedor"
    }),
    listItem({
      title: "Producción registrada",
      body: `DB ${status.database || "unknown"} persistent=${number(status.persistent)} temporal=${number(status.temporal)}. Commit: ${status.last_commit || "unknown"}.`,
      status: status.production_public_status || "unknown",
      meta: "sin deploy automático"
    }),
    listItem({
      title: "Variables",
      body: variables.length
        ? variables.slice(0, 4).map((item) => `${item.name}: ${item.status} / ${item.value}`).join(" · ")
        : "Sin variables registradas.",
      status: "masked",
      meta: "sin valores"
    }),
    listItem({
      title: "Costos y riesgos",
      body: `Costos: ${cost.cost_status || status.cost_status || "unknown"}. Riesgos abiertos: ${number(risks.length || status.risks)}. Revisión manual: ${number(status.requires_manual_review)}.`,
      status: cost.cost_status || status.cost_status || "unknown",
      meta: "NUBE informa"
    }),
    listItem({
      title: "Evidencia cloud",
      body: `Proyectos: ${number(projects.length || status.projects)}. Deployments: ${number(deployments.length || status.deployments)}. Health: ${latestHealth.status || "unknown"}. Último deploy: ${latestDeployment.status || "registered"}.`,
      status: latestHealth.status || "registered",
      meta: "sin Vercel API"
    })
  ].join("");
}

function buildTimeline() {
  const runtime = state.data.runtime || {};
  const readiness = state.data.readiness || {};
  const version = state.data.version || {};
  return [
    {
      title: "Runtime local verificado",
      body: `Commit ${runtime.commit || version.commit || "desconocido"} observado en ${runtime.environment || "local"}; sin producción tocada.`,
      meta: state.lastUpdated ? state.lastUpdated.toLocaleString("es") : "ahora"
    },
    {
      title: "Base de datos verificada",
      body: `${label(runtime.database?.backend)} / persistente ${number(runtime.database?.persistent)} / fuente ${runtime.database?.source || "runtime"}.`,
      meta: "storage"
    },
    {
      title: "Boundary activo",
      body: `Rol ${label(state.role)} con ${(state.boundary?.actions || []).filter((action) => action.allowed).length} acciones permitidas.`,
      meta: "auth"
    },
    {
      title: "Readiness evaluado",
      body: `Estado ${label(readiness.status)} con memoria ${readiness.dependencies?.memory || "pendiente"}.`,
      meta: "readiness"
    }
  ];
}

function renderView() {
  $$("#view-tabs button").forEach((button) => {
    button.classList.toggle("active", button.dataset.view === state.view);
  });
  $$(".view-panel").forEach((panel) => {
    panel.classList.toggle("active", panel.dataset.panel === state.view);
  });
}

function bindActionButtons() {
  $$("[data-action]").forEach((button) => {
    const action = actionById(button.dataset.action);
    const allowed = action?.allowed === true;
    button.classList.toggle("forbidden", !allowed);
    if (allowed) {
      button.removeAttribute("aria-disabled");
      button.title = action.description;
    } else {
      button.setAttribute("aria-disabled", "true");
      button.title = action?.reason || "permission_not_loaded";
    }
    button.onclick = () => {
      if (button.getAttribute("aria-disabled") === "true") {
        showFeedback(`Acceso denegado para ${label(state.role)}: ${label(action?.reason || "sin permiso")}.`, "error");
        return;
      }
      openActionDialog(button.dataset.action, button.dataset.targetId || "");
    };
  });
}

function bindEvents() {
  $("#login-form").addEventListener("submit", loginFromForm);
  $("#refresh").addEventListener("click", loadData);
  $("#logout").addEventListener("click", logout);
  $("#search").addEventListener("input", (event) => {
    state.search = event.target.value;
    renderApps();
  });
  $("#status-filter").addEventListener("change", (event) => {
    state.statusFilter = event.target.value;
    renderApps();
  });
  $$("#view-tabs button").forEach((button) => {
    button.addEventListener("click", () => {
      state.view = button.dataset.view;
      renderView();
    });
  });
  $$("[data-view-jump]").forEach((button) => {
    button.addEventListener("click", () => {
      state.view = button.dataset.viewJump === "alerts" ? "ceo" : "system";
      renderView();
      document.getElementById(button.dataset.viewJump)?.scrollIntoView({ behavior: "smooth", block: "start" });
    });
  });
  document.addEventListener("click", (event) => {
    const meetingButton = event.target.closest("[data-meeting]");
    if (meetingButton) {
      state.meeting = meetingButton.dataset.meeting === "evening" ? "evening" : "morning";
      renderCerebroDailyMeeting();
      return;
    }
    const quick = event.target.closest("[data-quick-target], [data-quick]");
    if (!quick) return;
    const target = quick.dataset.quickTarget || quick.dataset.quick;
    if (target === "cerebro" || target === "forja" || target === "nube" || target === "auditor") {
      scrollToSection(target);
      return;
    }
    scrollToSection(target);
  });
  $$("#bottom-nav button").forEach((button) => {
    button.addEventListener("click", () => {
      $$("#bottom-nav button").forEach((item) => item.classList.toggle("active", item === button));
      scrollToSection(button.dataset.bottomTarget);
    });
  });
  $("#confirm-action").addEventListener("click", executePendingAction);
}

async function loginFromForm(event) {
  event.preventDefault();
  const email = $("#login-email").value.trim();
  const password = $("#login-password").value;
  const rememberSession = $("#login-remember").checked;
  const button = $("#login-submit");
  button.disabled = true;
  $("#login-error").classList.add("hidden");
  $("#login-error").textContent = "";
  setLoginStatus(rememberSession ? "Se activará sesión extendida en este navegador." : "");
  try {
    const response = await fetch("/api/v1/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify({ email, password, remember_me: rememberSession })
    });
    const result = await response.json().catch(() => ({}));
    if (!response.ok) {
      throw new Error(result.detail?.error || "login_failed");
    }
    state.token = result.token;
    state.user = result.user;
    state.role = roleFromUser(result.user);
    persistSession(state.token, rememberSession);
    $("#login-password").value = "";
    showApp();
    renderUserShell();
    showFeedback(rememberSession ? "Sesión recordada en este dispositivo." : "Sesión iniciada para esta pestaña.", "success");
    await loadData();
  } catch (error) {
    showLogin(error.message === "invalid_credentials" ? "Credenciales incorrectas." : "No se pudo iniciar sesión.");
  } finally {
    button.disabled = false;
  }
}

async function logout() {
  const token = state.token;
  clearSession();
  showLogin("Sesión cerrada.");
  if (!token) return;
  await fetch("/api/v1/auth/logout", {
    method: "POST",
    headers: { Authorization: `Bearer ${token}`, Accept: "application/json" }
  }).catch(() => {});
}

function resolveTarget(actionId, explicitTarget) {
  if (explicitTarget) return explicitTarget;
  if (["create_decision", "create_approval", "create_risk", "evaluate_policy"].includes(actionId)) {
    return "";
  }
  if (actionId.includes("decision")) {
    return (state.data.decisions || []).find((item) => item.status === "pending_review")?.id || (state.data.decisions || [])[0]?.id || "";
  }
  if (actionId.includes("approval")) {
    return (state.data.approvals || []).find((item) => item.status === "pending")?.id || (state.data.approvals || [])[0]?.id || "";
  }
  if (actionId.includes("risk")) {
    return (state.data.risks || []).find((item) => item.status !== "closed")?.id || (state.data.risks || [])[0]?.id || "";
  }
  if (["request_discovery", "approve_discovery", "approve_connection", "block_gate", "suspend_gate"].includes(actionId)) {
    return (state.data.gates || []).find((item) => !item.protected)?.app_id || (state.data.gates || [])[0]?.app_id || "";
  }
  return "";
}

function openActionDialog(actionId, explicitTarget = "") {
  const action = actionById(actionId);
  if (!action) {
    showFeedback("Accion no disponible en el boundary actual.", "error");
    return;
  }
  if (!action.allowed) {
    showFeedback(`Acceso denegado: ${label(action.reason)}.`, "error");
    return;
  }

  const targetId = resolveTarget(actionId, explicitTarget);
  const needsTarget = action.endpoint.includes("{");
  if (needsTarget && !targetId) {
    showFeedback(`No hay recurso disponible para ${action.label}. Crea primero el registro correspondiente.`, "error");
    return;
  }

  state.pendingAction = { action, targetId };
  $("#dialog-section").textContent = action.section;
  $("#dialog-title").textContent = action.label;
  $("#dialog-copy").textContent = `${action.description} Rol activo: ${label(state.role)}. ${targetId ? `Recurso: ${targetId}.` : ""}`;
  $("#reason-field").classList.toggle("hidden", !action.requires_reason);
  $("#evidence-field").classList.toggle("hidden", !action.requires_evidence);
  $("#action-reason").value = action.requires_reason ? action.payload_template.reason || "Razón validada desde Control Center." : "";
  $("#action-evidence").value = action.requires_evidence ? action.payload_template.evidence || "Evidencia validada desde Control Center." : "";
  $("#action-dialog").showModal();
}

function buildPayload(action) {
  const payload = structuredClone(action.payload_template || {});
  if (action.requires_reason) payload.reason = $("#action-reason").value || "Razón registrada desde Control Center.";
  if (action.requires_evidence) payload.evidence = $("#action-evidence").value || "Evidencia registrada desde Control Center.";

  if (action.id === "create_decision") {
    payload.title = `Decision Control Center ${new Date().toISOString()}`;
    payload.description = "Decisión creada desde la Cabina Humana Premium ECO-035.";
    payload.requested_by = state.role;
  }
  if (action.id === "create_approval") {
    payload.title = `Solicitud Control Center ${new Date().toISOString()}`;
    payload.description = "Solicitud creada desde la Cabina Humana Premium ECO-035.";
    payload.requested_by = state.role;
    payload.target_id = "pluma";
  }
  if (action.id === "create_risk") {
    payload.title = `Riesgo Control Center ${new Date().toISOString()}`;
    payload.description = "Riesgo creado desde la Cabina Humana Premium ECO-035.";
    payload.owner = state.role;
  }
  if (action.id === "evaluate_policy") {
    payload.role_id = state.role;
    payload.action = "approve";
    payload.resource = "platform";
  }

  return payload;
}

function buildEndpoint(action, targetId) {
  return action.endpoint
    .replace("{decision_id}", encodeURIComponent(targetId))
    .replace("{approval_id}", encodeURIComponent(targetId))
    .replace("{app_id}", encodeURIComponent(targetId))
    .replace("{risk_id}", encodeURIComponent(targetId));
}

async function executePendingAction() {
  const pending = state.pendingAction;
  if (!pending) return;
  const { action, targetId } = pending;
  const endpoint = buildEndpoint(action, targetId);
  const payload = buildPayload(action);

  $("#confirm-action").disabled = true;
  showFeedback(`Ejecutando ${action.label}...`, "loading");

  try {
    const response = await fetch(endpoint, {
      method: action.method,
      headers: authHeaders({ "Content-Type": "application/json", Accept: "application/json" }),
      body: JSON.stringify(payload)
    });
    const result = await response.json().catch(() => ({}));
    if (!response.ok) {
      throw new Error(result.detail?.reason || result.detail?.error || `${response.status} ${response.statusText}`);
    }
    $("#action-dialog").close();
    showFeedback(`${action.label} completada. Estado: ${label(result.status || result.state || result.reason || "ok")}.`, "success");
    await loadData();
  } catch (error) {
    showFeedback(`${action.label} fallo: ${error.message}`, "error");
  } finally {
    $("#confirm-action").disabled = false;
  }
}

function showFeedback(message, status = "info") {
  const feedback = $("#action-feedback");
  feedback.className = `feedback ${status}`;
  feedback.textContent = message;
}

bindEvents();
loadData().catch((error) => {
  state.errors.bootstrap = error.message;
  $("#state-banner").className = "state-banner error";
  $("#state-banner").innerHTML = `
    <span class="pulse"></span>
    <strong>No se pudo iniciar la cabina</strong>
    <small>${escapeHtml(error.message)}</small>
  `;
});
