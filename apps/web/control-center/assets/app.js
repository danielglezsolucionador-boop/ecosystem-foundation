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
  cerebroMorning: "/api/v1/cerebro/brief/morning",
  cerebroEvening: "/api/v1/cerebro/brief/evening",
  cerebroDecisions: "/api/v1/cerebro/decisions",
  cerebroTasks: "/api/v1/cerebro/tasks"
};

const AUTH_TOKEN_KEY = "ecosystem_control_center_session_v1";

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
    role: "Operación local y cloud",
    capability: "URLs, deploys, costos, variables y backups.",
    preparedCopy: "Documentado para revisión; runtime apagado.",
    action: "Revisar NUBE",
    lane: "pending",
    displayStatus: "documented_only"
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
    capability: "Vigila agentes, permisos, datos, prompts, incidentes y riesgos. Futuro producto B2B.",
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
  const response = await fetch(url, {
    headers: authHeaders({ Accept: "application/json" }),
    cache: "no-store"
  });
  if (response.status === 401) {
    clearSession();
    showLogin("Tu sesión expiró. Entra nuevamente.");
  }
  if (!response.ok) throw new Error(`${response.status} ${response.statusText}`);
  return response.json();
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
  const results = await Promise.allSettled(entries.map(([name, url]) => fetchJson(name, url)));

  state.data = {};
  state.errors = {};

  results.forEach((result, index) => {
    const [name] = entries[index];
    if (result.status === "fulfilled") {
      if (name === "boundary") state.boundary = result.value;
      else state.data[name] = result.value;
    } else {
      state.errors[name] = result.reason.message;
    }
  });

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
    ["departments", "Deptos"],
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
  renderTrafficLights();
  renderCerebroDailyMeeting();
  renderCerebroOperational();
  renderQuickActions();
  renderPriorityApps();
  renderDepartmentalSimulationFlows();
  renderStatusLanes();
  renderDecisionRail();
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
      <summary>Mas acciones</summary>
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
  const roles = state.data.roles || [];

  $("#contracts-list").innerHTML = contracts.length ? contracts.map((contract) => listItem({
    title: contract.name || contract.id,
    body: contract.description,
    status: contract.status,
    meta: contract.app_id
  })).join("") : emptyState("No hay contratos activos. Las conexiones externas siguen bloqueadas.");

  $("#audit-list").innerHTML = [
    listItem({
      title: label(audit.status || "central_audit_operational"),
      body: `${number(audit.events)} eventos, ${number(audit.reports)} reportes, categorías: ${(audit.categories || []).length}`,
      status: "healthy",
      meta: "Auditoría"
    })
  ].join("");

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
