const endpoints = {
  health: "/health",
  readiness: "/readiness",
  runtime: "/runtime/status",
  version: "/version",
  apps: "/api/v1/apps",
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
  governanceAudit: "/api/v1/governance/audit"
};

const state = {
  data: {},
  errors: {},
  role: "ceo",
  boundary: null,
  view: "ceo",
  search: "",
  statusFilter: "all",
  lastUpdated: null,
  pendingAction: null
};

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
  if (["healthy", "ok", "ready", "operational", "connected", "approved", "closed"].includes(status)) return "healthy";
  if (["degraded", "planned", "staging", "info", "pending", "pending_review", "pending_approval", "escalated"].includes(status)) return "degraded";
  if (["blocked", "error", "failed", "critical", "rejected", "suspended"].includes(status)) return "blocked";
  return status;
}

function label(value) {
  const translated = {
    blocked: "Bloqueado",
    degraded: "Degradado",
    healthy: "Saludable",
    ready: "Listo",
    operational: "Operativo",
    connected: "Conectado",
    external: "Externo",
    internal: "Interno",
    planned: "Planeado",
    unknown: "Desconocido",
    staging: "Staging",
    production: "Produccion",
    sqlite: "SQLite",
    postgresql: "PostgreSQL",
    governance_attention_required: "Atencion requerida",
    governance_ready: "Governance listo",
    pending_review: "Revision pendiente",
    pending_approval: "Aprobacion pendiente",
    approved_for_discovery: "Discovery aprobado",
    approved_for_connection: "Conexion aprobada",
    not_ready: "No lista",
    suspended: "Suspendida",
    escalated: "Escalada",
    open: "Abierto",
    mitigated: "Mitigado",
    closed: "Cerrado",
    critical: "Critico",
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
    headers: { Accept: "application/json" },
    cache: "no-store"
  });
  if (!response.ok) throw new Error(`${response.status} ${response.statusText}`);
  return response.json();
}

async function loadData() {
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
}

function setLoading() {
  const banner = $("#state-banner");
  banner.className = "state-banner loading";
  banner.innerHTML = `
    <span class="pulse"></span>
    <strong>Actualizando cabina...</strong>
    <small>Conectando endpoints reales y boundary de permisos.</small>
  `;
}

function render() {
  renderStatus();
  renderRoleBoundary();
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

function renderStatus() {
  const runtime = state.data.runtime || {};
  const readiness = state.data.readiness || {};
  const control = state.data.controlCenter || {};
  const hasErrors = Object.keys(state.errors).length > 0;
  const status = hasErrors ? "error" : normalizeStatus(runtime.status || readiness.status);
  const db = runtime.database || readiness.dependencies?.database || {};

  $("#state-banner").className = `state-banner ${status === "healthy" ? "ready" : status}`;
  $("#state-banner").innerHTML = `
    <span class="pulse"></span>
    <strong>${hasErrors ? "Cabina con endpoints degradados" : "Backbone conectado"}</strong>
    <small>${escapeHtml(runtime.environment || "local")} / ${escapeHtml(runtime.commit || state.data.version?.commit || "commit pendiente")} / DB ${escapeHtml(db.backend || "desconocida")}</small>
  `;

  $("#global-status").textContent = label(control.status || runtime.status || "operational");
  $("#global-summary").textContent = control.overview?.executive_summary?.summary || "Cabina conectada a datos reales del backbone, con gobierno humano activo.";
  $("#sidebar-readiness").textContent = label(readiness.status || control.readiness?.status || "ready");
  $("#sidebar-db").textContent = `${label(db.backend)} / persistente: ${number(db.persistent)}`;
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

function renderMetrics() {
  const control = state.data.controlCenter || {};
  const runtime = state.data.runtime || {};
  const governance = state.data.governanceOverview || {};
  const cards = [
    { id: "apps", label: "Aplicaciones", value: (state.data.apps || []).length, status: "healthy" },
    { id: "pending", label: "Pendientes", value: (governance.pending_decisions || 0) + (governance.pending_approvals || 0), status: governance.pending_approvals ? "degraded" : "healthy" },
    { id: "blocked", label: "Apps bloqueadas", value: governance.blocked_apps || 0, status: governance.blocked_apps ? "blocked" : "healthy" },
    { id: "database", label: "Base de datos", value: runtime.database?.backend || "--", status: runtime.database?.postgres ? "healthy" : "degraded" }
  ];
  $("#metric-grid").innerHTML = cards.map((metric) => `
    <article class="metric">
      <span>${escapeHtml(metric.label)}</span>
      <strong>${number(metric.value)}</strong>
      <small>${badge(metric.status)}</small>
    </article>
  `).join("");

  const serviceCount = control.services?.length || 0;
  const healthyCount = (control.services || []).filter((item) => normalizeStatus(item.status) === "healthy").length;
  $("#service-score").textContent = serviceCount ? `${healthyCount}/${serviceCount}` : "--";
  $("#service-score-copy").textContent = serviceCount ? "servicios saludables" : "sin servicios reportados";
}

function renderApps() {
  const apps = state.data.apps || [];
  const query = state.search.toLowerCase();
  const filtered = apps.filter((app) => {
    const byStatus = state.statusFilter === "all" || app.status === state.statusFilter;
    const text = `${app.name} ${app.id} ${app.type} ${app.description}`.toLowerCase();
    return byStatus && text.includes(query);
  });

  $("#apps-grid").innerHTML = filtered.length ? filtered.map((app) => `
    <article class="app-card">
      <div class="badge-row">${badge(app.status, app.status)}<span class="badge">${label(app.type)}</span></div>
      <h3>${escapeHtml(app.name)}</h3>
      <p>${escapeHtml(app.description)}</p>
      <div class="badge-row">
        <span class="badge">${escapeHtml(label(app.touch_policy))}</span>
        <span class="badge">Depends: ${number(app.depends_on?.length || 0)}</span>
      </div>
    </article>
  `).join("") : emptyState("No hay aplicaciones para este filtro.");
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
  })).join("") : emptyState("Sin decisiones pendientes.", "La cabina queda lista para crear una nueva decision.");

  $("#ceo-risks").innerHTML = criticalRisks.length ? criticalRisks.slice(0, 4).map((item) => listItem({
    title: item.title,
    body: item.description,
    status: item.severity,
    meta: label(item.status),
    actions: `${actionButton("mitigate_risk", "Mitigar", item.id)}${actionButton("close_risk", "Cerrar", item.id)}`
  })).join("") : emptyState("Sin riesgos criticos abiertos.");

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
  })).join("") : emptyState("Sin decisiones registradas.", "Usa Crear decision para generar la primera entrada.");
}

function renderApprovalCenter() {
  const approvals = state.data.approvals || [];
  $("#governance-approvals").innerHTML = approvals.length ? approvals.slice(0, 8).map((item) => listItem({
    title: item.title,
    body: item.description,
    status: item.status,
    meta: label(item.approval_type),
    actions: `${actionButton("approve_approval", "Aprobar", item.id)}${actionButton("reject_approval", "Rechazar", item.id)}${actionButton("escalate_approval", "Escalar", item.id)}`
  })).join("") : emptyState("Sin solicitudes registradas.", "Crea una solicitud para probar el flujo de aprobacion.");
}

function renderIntegrationGates() {
  const gates = state.data.gates || [];
  $("#governance-gates").innerHTML = gates.length ? gates.slice(0, 10).map((item) => listItem({
    title: item.app_name,
    body: item.reason || "Gate controlado por politica humana.",
    status: item.state,
    meta: item.protected ? "Protegida" : "Disponible",
    actions: `${actionButton("request_discovery", "Solicitar discovery", item.app_id)}${actionButton("approve_discovery", "Aprobar discovery", item.app_id)}${actionButton("approve_connection", "Conexion futura", item.app_id)}${actionButton("block_gate", "Bloquear", item.app_id)}${actionButton("suspend_gate", "Suspender", item.app_id)}`
  })).join("") : emptyState("Sin gates de integracion.");
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
  })).join("") : emptyState("Sin eventos governance auditados todavia.");
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
      body: `${number((state.data.decisions || []).length)} decisiones, ${number((state.data.approvals || []).length)} solicitudes, ${number((state.data.risks || []).length)} riesgos, ${number((state.data.gates || []).length)} gates.`,
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
  })).join("") : emptyState("No hay eventos internos registrados todavia.");

  $("#memory-list").innerHTML = memory.length ? memory.map((entry) => listItem({
    title: entry.title || entry.id,
    body: entry.content || entry.summary,
    status: entry.status,
    meta: entry.app_id || "memoria"
  })).join("") : emptyState("Memoria compartida preparada, sin entradas todavia.");
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
      body: `${number(audit.events)} eventos, ${number(audit.reports)} reportes, categorias: ${(audit.categories || []).length}`,
      status: "healthy",
      meta: "Auditoria"
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
    ...(integration.services || []).map((item) => listItem({
      title: item.name,
      body: `Categoria ${label(item.category)}. Conexion externa: ${number(item.external_connection_enabled)}`,
      status: item.status,
      meta: "servicio"
    })),
    ...(integration.dependencies || []).map((item) => listItem({
      title: item.name,
      body: item.dependency_type,
      status: item.status,
      meta: item.required ? "required" : "optional"
    }))
  ].join("") || emptyState("Integration Bus preparado, sin rutas activas.");
}

function buildTimeline() {
  const runtime = state.data.runtime || {};
  const readiness = state.data.readiness || {};
  const version = state.data.version || {};
  return [
    {
      title: "Deploy conectado",
      body: `Commit ${runtime.commit || version.commit || "desconocido"} ejecutando en ${runtime.environment || "local"}.`,
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
  $("#refresh").addEventListener("click", loadData);
  $("#role-select").addEventListener("change", (event) => {
    state.role = event.target.value;
    loadData();
  });
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
  $("#confirm-action").addEventListener("click", executePendingAction);
}

function resolveTarget(actionId, explicitTarget) {
  if (explicitTarget) return explicitTarget;
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
  $("#action-reason").value = action.requires_reason ? action.payload_template.reason || "Razon validada desde Control Center." : "";
  $("#action-evidence").value = action.requires_evidence ? action.payload_template.evidence || "Evidencia validada desde Control Center." : "";
  $("#action-dialog").showModal();
}

function buildPayload(action) {
  const payload = structuredClone(action.payload_template || {});
  if (action.requires_reason) payload.reason = $("#action-reason").value || "Razon registrada desde Control Center.";
  if (action.requires_evidence) payload.evidence = $("#action-evidence").value || "Evidencia registrada desde Control Center.";

  if (action.id === "create_decision") {
    payload.title = `Decision Control Center ${new Date().toISOString()}`;
    payload.description = "Decision creada desde la Cabina Humana Premium ECO-035.";
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
      headers: { "Content-Type": "application/json", Accept: "application/json" },
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
