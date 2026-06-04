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
  observability: "/api/v1/observability"
};

const state = {
  data: {},
  errors: {},
  view: "ceo",
  search: "",
  statusFilter: "all",
  lastUpdated: null
};

const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => Array.from(document.querySelectorAll(selector));

function normalizeStatus(value) {
  const status = String(value || "unknown").toLowerCase();
  if (["healthy", "ok", "ready", "operational", "connected"].includes(status)) return "healthy";
  if (["degraded", "planned", "staging", "info"].includes(status)) return "degraded";
  if (["blocked", "error", "failed", "critical"].includes(status)) return "blocked";
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
    postgresql: "PostgreSQL"
  };
  if (translated[String(value || "").toLowerCase()]) {
    return translated[String(value || "").toLowerCase()];
  }
  return String(value || "Pendiente")
    .replaceAll("_", " ")
    .replace(/\b\w/g, (char) => char.toUpperCase());
}

function number(value) {
  if (typeof value === "number") return new Intl.NumberFormat("es").format(value);
  if (value === false) return "No";
  if (value === true) return "Si";
  return value ?? "--";
}

function humanSummary(value) {
  if (!value) return "Cabina conectada a los datos reales del backbone.";
  if (value.includes("CEO-level and operational view")) {
    return "El backbone presenta una vista ejecutiva y operativa desde registros, runtime y almacenamiento sin contactar aplicaciones protegidas.";
  }
  return value;
}

function metricLabel(metric) {
  const labels = {
    registered_apps: "Aplicaciones registradas",
    internal_apps: "Aplicaciones internas",
    external_references: "Referencias externas",
    services_tracked: "Servicios monitoreados",
    dependencies_tracked: "Dependencias",
    active_alerts: "Alertas activas",
    storage_backend: "Base de datos",
    external_connections_enabled: "Conexiones externas"
  };
  return labels[metric.id] || metric.label || label(metric.id);
}

function badge(value, extra = "") {
  const normalized = normalizeStatus(value);
  return `<span class="badge ${normalized} ${extra}">${label(value)}</span>`;
}

function emptyState(text) {
  return `<div class="empty">${text}</div>`;
}

function listItem({ title, body, meta, status }) {
  return `
    <article class="list-item">
      <div class="badge-row">${status ? badge(status) : ""}${meta ? `<span class="badge">${meta}</span>` : ""}</div>
      <strong>${title}</strong>
      ${body ? `<p>${body}</p>` : ""}
    </article>
  `;
}

async function fetchJson(name, url) {
  const response = await fetch(url, {
    headers: { "Accept": "application/json" },
    cache: "no-store"
  });

  if (!response.ok) {
    throw new Error(`${response.status} ${response.statusText}`);
  }

  return response.json();
}

async function loadData() {
  setLoading();
  const entries = Object.entries(endpoints);
  const results = await Promise.allSettled(entries.map(([name, url]) => fetchJson(name, url)));

  state.data = {};
  state.errors = {};

  results.forEach((result, index) => {
    const [name] = entries[index];
    if (result.status === "fulfilled") {
      state.data[name] = result.value;
    } else {
      state.errors[name] = result.reason.message;
    }
  });

  state.lastUpdated = new Date();
  render();
}

function setLoading() {
  $("#state-banner").className = "state-banner loading";
  $("#state-banner").innerHTML = `
    <span class="pulse"></span>
    <strong>Actualizando cabina...</strong>
    <small>Conectando con endpoints reales del backbone.</small>
  `;
}

function render() {
  renderStatus();
  renderMetrics();
  renderApps();
  renderAlerts();
  renderCeo();
  renderOperator();
  renderAuditor();
  renderSystem();
  renderView();
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
    <small>${runtime.environment || "local"} / ${runtime.commit || state.data.version?.commit || "commit pendiente"} / DB ${db.backend || "desconocida"}</small>
  `;

  $("#global-status").textContent = label(control.status || runtime.status || "operational");
  $("#global-summary").textContent = humanSummary(control.overview?.executive_summary?.summary);
  $("#sidebar-readiness").textContent = label(readiness.status || control.readiness?.status || "ready");
  $("#sidebar-db").textContent = `${label(db.backend)} / persistente: ${number(db.persistent)}`;
}

function renderMetrics() {
  const control = state.data.controlCenter || {};
  const runtime = state.data.runtime || {};
  const apps = state.data.apps || [];
  const metrics = control.metrics || [];
  const fallback = [
    { id: "registered_apps", label: "Aplicaciones", value: apps.length, status: "healthy" },
    { id: "services", label: "Servicios", value: control.services?.length || 0, status: "healthy" },
    { id: "alerts", label: "Alertas", value: control.alerts?.length || 0, status: control.alerts?.length ? "degraded" : "healthy" },
    { id: "storage", label: "Storage", value: runtime.database?.backend || "--", status: runtime.database?.postgres ? "healthy" : "degraded" }
  ];
  const cards = (metrics.length ? metrics.slice(0, 4) : fallback);
  $("#metric-grid").innerHTML = cards.map((metric) => `
    <article class="metric">
      <span>${metricLabel(metric)}</span>
      <strong>${number(metric.value)}</strong>
      <small>${badge(metric.status || "healthy")} ${metric.unit || ""}</small>
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
      <h3>${app.name}</h3>
      <p>${app.description}</p>
      <div class="badge-row">
        <span class="badge">${label(app.touch_policy)}</span>
        <span class="badge">Depends: ${app.depends_on?.length || 0}</span>
      </div>
    </article>
  `).join("") : emptyState("No hay aplicaciones para este filtro.");
}

function renderAlerts() {
  const alerts = state.data.controlCenter?.alerts || [];
  const rawIncidents = state.data.observability?.incidents;
  const incidents = Array.isArray(rawIncidents) ? rawIncidents : [];
  const combined = [
    ...alerts.map((item) => ({ title: item.message, body: item.source, status: item.status || item.severity, meta: label(item.severity) })),
    ...incidents.map((item) => ({ title: item.title || item.id, body: item.description, status: item.status, meta: "Incidente" }))
  ];

  $("#alerts-list").innerHTML = combined.length ? combined.map(listItem).join("") : emptyState("Sin alertas ni incidentes abiertos.");
}

function renderCeo() {
  const control = state.data.controlCenter || {};
  const actions = control.overview?.next_actions || [];
  const dependencies = control.dependencies || [];
  const timeline = buildTimeline();

  $("#next-actions").innerHTML = actions.length ? actions.map((item) => listItem({
    title: item.label,
    body: item.reason,
    status: item.blocked ? "blocked" : "healthy",
    meta: label(item.priority)
  })).join("") : emptyState("No hay prioridades ejecutivas pendientes.");

  $("#dependencies-list").innerHTML = dependencies.length ? dependencies.map((item) => listItem({
    title: item.name,
    body: item.detail,
    status: item.status,
    meta: item.required ? "requerida" : "opcional"
  })).join("") : emptyState("Sin dependencias registradas.");

  $("#timeline").innerHTML = timeline.map((item) => `
    <article class="timeline-item">
      <strong>${item.title}</strong>
      <p>${item.body}</p>
      <small>${item.meta}</small>
    </article>
  `).join("");
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
  const items = [
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
      title: "Readiness evaluado",
      body: `Estado ${label(readiness.status)} con memoria ${readiness.dependencies?.memory || "pendiente"}.`,
      meta: "readiness"
    }
  ];
  return items;
}

function renderView() {
  $$("#view-tabs button").forEach((button) => {
    button.classList.toggle("active", button.dataset.view === state.view);
  });
  $$(".view-panel").forEach((panel) => {
    panel.classList.toggle("active", panel.dataset.panel === state.view);
  });
}

function bindEvents() {
  $("#refresh").addEventListener("click", loadData);
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
}

bindEvents();
loadData().catch((error) => {
  state.errors.bootstrap = error.message;
  $("#state-banner").className = "state-banner error";
  $("#state-banner").innerHTML = `
    <span class="pulse"></span>
    <strong>No se pudo iniciar la cabina</strong>
    <small>${error.message}</small>
  `;
});
