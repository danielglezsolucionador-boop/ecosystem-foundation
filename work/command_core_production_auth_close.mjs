import fs from "node:fs";
import path from "node:path";
import { createRequire } from "node:module";
import { fileURLToPath } from "node:url";

const require = createRequire(import.meta.url);
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoDir = path.resolve(__dirname, "..");

const baseUrl = (process.env.ECOSYSTEM_PRODUCTION_BASE_URL || "https://ecosystem-foundation.vercel.app").replace(/\/+$/, "");
const email = process.env.CONTROL_CENTER_ADMIN_EMAIL || "";
const password = process.env.CONTROL_CENTER_ADMIN_PASSWORD || "";
const expectedCommit = process.env.EXPECTED_COMMAND_CORE_COMMIT || "";
const authTokenKey = "ecosystem_control_center_session_v1";
const outputsDir = path.join(repoDir, "outputs");
const defaultTimeoutMs = 30000;
const dailyCenterTimeoutMs = 45000;

let playwright;
try {
  playwright = require("./node_modules/playwright");
} catch {
  playwright = require("playwright");
}

const { chromium, request } = playwright;
fs.mkdirSync(outputsDir, { recursive: true });

class SafeValidationError extends Error {
  constructor(message, code = "BLOCKED_VALIDATION") {
    super(message);
    this.name = "SafeValidationError";
    this.code = code;
  }
}

function redactSensitive(value) {
  let text = typeof value === "string" ? value : JSON.stringify(value);
  if (!text) return "";
  const replacements = [
    email,
    password,
    process.env.CONTROL_CENTER_ADMIN_EMAIL || "",
    process.env.CONTROL_CENTER_ADMIN_PASSWORD || "",
  ].filter(Boolean);
  for (const secret of replacements) {
    text = text.split(secret).join("[REDACTED]");
  }
  return text
    .replace(/Authorization:\s*Bearer\s+[A-Za-z0-9._~+/=-]+/gi, "Authorization: Bearer [REDACTED]")
    .replace(/Bearer\s+[A-Za-z0-9._~+/=-]+/g, "Bearer [REDACTED]")
    .replace(/ccs_[A-Za-z0-9._-]+/g, "ccs_[REDACTED]")
    .replace(/"Authorization"\s*:\s*"[^"]+"/gi, "\"Authorization\":\"[REDACTED]\"")
    .replace(/authorization=\[[^\]]+\]/gi, "authorization=[REDACTED]");
}

function safeLogError(error) {
  const code = error?.code || "BLOCKED_VALIDATION";
  const message = redactSensitive(error?.message || String(error));
  console.error(`:: ${code}: ${message}`);
}

function pngSize(filePath) {
  const buffer = fs.readFileSync(filePath);
  return {
    width: buffer.readUInt32BE(16),
    height: buffer.readUInt32BE(20),
  };
}

async function launchBrowser() {
  try {
    return await chromium.launch({ channel: process.env.PLAYWRIGHT_CHANNEL || "chrome", headless: true });
  } catch {
    return await chromium.launch({ headless: true });
  }
}

async function parseJsonResponse(response, label) {
  const status = response.status();
  const text = await response.text();
  let payload = {};
  try {
    payload = text ? JSON.parse(text) : {};
  } catch {
    payload = {};
  }
  if (!response.ok()) {
    throw new SafeValidationError(`${label} expected 2xx, got ${status}: ${text.slice(0, 180).replace(/\s+/g, " ")}`);
  }
  return payload;
}

async function safeApiGet(api, endpoint, headers = {}, options = {}) {
  const timeout = options.timeout || (endpoint === "/api/v1/ceo/daily-center" ? dailyCenterTimeoutMs : defaultTimeoutMs);
  try {
    const response = await api.get(endpoint, { headers, timeout });
    return await parseJsonResponse(response, `GET ${endpoint}`);
  } catch (error) {
    const message = redactSensitive(error?.message || String(error));
    if (endpoint === "/api/v1/ceo/daily-center") {
      throw new SafeValidationError(`BLOCKED DAILY CENTER: GET ${endpoint} failed without exposing secrets. ${message}`, "BLOCKED_DAILY_CENTER");
    }
    throw new SafeValidationError(`GET ${endpoint} failed without exposing secrets. ${message}`, "BLOCKED_ENDPOINT");
  }
}

async function safeLogin(api) {
  try {
    const response = await api.post("/api/v1/auth/login", {
      data: { email, password },
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      timeout: defaultTimeoutMs,
    });
    return await parseJsonResponse(response, "POST /api/v1/auth/login");
  } catch (error) {
    throw new SafeValidationError(`POST /api/v1/auth/login failed without exposing secrets. ${redactSensitive(error?.message || String(error))}`, "BLOCKED_AUTH");
  }
}

async function validatePublicRuntime() {
  const api = await request.newContext({ baseURL: baseUrl, extraHTTPHeaders: { Accept: "application/json" } });
  try {
    for (const endpoint of ["/", "/health", "/readiness", "/runtime/status", "/version", "/control-center"]) {
      await safeApiGet(api, endpoint);
      console.log(`:: public ${endpoint} PASS`);
    }
    const version = await safeApiGet(api, "/version");
    const runtime = await safeApiGet(api, "/runtime/status");
    const commit = String(version.commit || runtime.commit || "");
    if (expectedCommit && !commit.startsWith(expectedCommit)) {
      throw new SafeValidationError(`production commit mismatch: expected ${expectedCommit}, got ${commit}`, "BLOCKED_DEPLOY");
    }
    const database = runtime.database || {};
    if (database.postgres !== true || database.sqlite !== false || database.persistent !== true) {
      throw new SafeValidationError(`runtime database flags invalid: ${JSON.stringify(database)}`, "BLOCKED_RUNTIME");
    }
    console.log(":: public runtime PASS");
  } finally {
    await api.dispose();
  }
}

async function validateAuthenticatedApi() {
  if (!email || !password) {
    throw new SafeValidationError("CONTROL_CENTER_ADMIN_EMAIL and CONTROL_CENTER_ADMIN_PASSWORD are required.", "BLOCKED_AUTH");
  }

  const api = await request.newContext({ baseURL: baseUrl, extraHTTPHeaders: { Accept: "application/json" } });
  try {
    const login = await safeLogin(api);
    const token = String(login.token || "");
    if (!token.startsWith("ccs_")) {
      throw new SafeValidationError("POST /api/v1/auth/login did not return a Control Center session token.", "BLOCKED_AUTH");
    }
    const headers = { Authorization: `Bearer ${token}`, Accept: "application/json" };
    const endpoints = [
      "/api/v1/auth/me",
      "/api/v1/control-center",
      "/api/v1/control-center/apps",
      "/api/v1/cerebro/status",
      "/api/v1/cerebro/brief/morning",
      "/api/v1/cerebro/brief/evening",
      "/api/v1/cerebro/tasks",
      "/api/v1/integration-bus/status",
      "/api/v1/integration-bus/routes",
      "/api/v1/auditoria/status",
      "/api/v1/auditoria/reviews",
      "/api/v1/auditoria/queue",
      "/api/v1/nube/status",
      "/api/v1/nube/projects",
      "/api/v1/nube/deployments",
      "/api/v1/nube/health-checks",
      "/api/v1/nube/risks",
      "/api/v1/nube/costs",
      "/api/v1/ceo/daily-center",
      "/api/v1/ceo/morning",
      "/api/v1/ceo/evening",
      "/api/v1/ceo/decisions",
      "/api/v1/governance",
      "/api/v1/audit",
      "/api/v1/observability/status",
    ];
    for (const endpoint of endpoints) {
      await safeApiGet(api, endpoint, headers);
      console.log(`:: authenticated ${endpoint} PASS`);
    }
    const routes = await safeApiGet(api, "/api/v1/integration-bus/routes", headers);
    const preparedAllowed = routes.filter((route) => route.status === "prepared" && route.allowed === true).length;
    const blocked = routes.filter((route) => route.status === "blocked" && route.allowed === false && route.requires_ceo_approval === true).length;
    const externalConnections = routes.filter((route) => route.external_connection_enabled === true).length;
    const runtimeConnected = routes.filter((route) => route.runtime_connected === true).length;
    if (routes.length !== 16 || preparedAllowed !== 13 || blocked !== 3 || externalConnections !== 0 || runtimeConnected !== 0) {
      throw new SafeValidationError(
        `route safeguards mismatch: ${JSON.stringify({ total: routes.length, preparedAllowed, blocked, externalConnections, runtimeConnected })}`,
        "BLOCKED_ROUTES",
      );
    }
    console.log(":: authenticated route safeguards PASS");
    return token;
  } finally {
    await api.dispose();
  }
}

async function waitForCommandCore(page) {
  await page.waitForLoadState("domcontentloaded", { timeout: 60000 });
  try {
    await page.waitForLoadState("networkidle", { timeout: 10000 });
  } catch {
    console.log(":: networkidle not reached; continuing after deterministic render wait");
  }
  await page.waitForSelector("#app:not(.hidden)", { timeout: 60000 });
  await page.waitForFunction(() => {
    const text = document.body?.innerText || "";
    const plain = text.normalize("NFD").replace(/\p{Diacritic}/gu, "").toLowerCase();
    return (
      plain.includes("empresa ia")
      && plain.includes("centro diario del ceo")
      && plain.includes("reunion con cerebro")
      && plain.includes("auditoria")
      && plain.includes("nube")
    );
  }, null, { timeout: 60000 });
  await page.evaluate(() => window.scrollTo(0, 0));
  await page.waitForTimeout(1500);
}

async function capture(token, label, viewport, fileName) {
  const browser = await launchBrowser();
  const context = await browser.newContext({ viewport });
  await context.addInitScript(
    ({ key, value }) => window.localStorage.setItem(key, value),
    { key: authTokenKey, value: token }
  );
  const page = await context.newPage();
  const consoleErrors = [];
  const badResponses = [];
  page.on("console", (message) => {
    if (message.type() === "error") consoleErrors.push(message.text());
  });
  page.on("pageerror", (error) => consoleErrors.push(error.message));
  page.on("response", (response) => {
    if (response.status() >= 400) badResponses.push(`${response.status()} ${response.url()}`);
  });
  try {
    await page.goto(`${baseUrl}/control-center?block=G-command-core`, { waitUntil: "domcontentloaded", timeout: 60000 });
    await waitForCommandCore(page);
    const checks = await page.evaluate(() => {
      const text = document.body?.innerText || "";
      const plain = text.normalize("NFD").replace(/\p{Diacritic}/gu, "").toLowerCase();
      return {
        width: window.innerWidth,
        height: window.innerHeight,
        overflow: document.documentElement.scrollWidth > window.innerWidth + 1,
        bodyTextLength: text.trim().length,
        hasCentroCeo: plain.includes("centro diario del ceo"),
        hasAuditoria: plain.includes("auditoria"),
        hasNube: plain.includes("nube"),
        hasCerebro: plain.includes("cerebro"),
        hasBus: plain.includes("bus") || plain.includes("rutas internas"),
        hasProtected: plain.includes("bloqueado") || plain.includes("protegido"),
      };
    });
    const outputPath = path.join(outputsDir, fileName);
    await page.screenshot({ path: outputPath, fullPage: false });
    const size = pngSize(outputPath);
    if (consoleErrors.length || badResponses.length) {
      throw new SafeValidationError(`${label} browser errors: ${redactSensitive({ consoleErrors, badResponses })}`, "BLOCKED_SCREENSHOT");
    }
    if (checks.width !== viewport.width || checks.height !== viewport.height) throw new SafeValidationError(`${label} viewport mismatch`, "BLOCKED_SCREENSHOT");
    if (size.width !== viewport.width || size.height !== viewport.height) throw new SafeValidationError(`${label} screenshot size mismatch`, "BLOCKED_SCREENSHOT");
    if (checks.overflow) throw new SafeValidationError(`${label} horizontal overflow detected`, "BLOCKED_SCREENSHOT");
    for (const signal of ["hasCentroCeo", "hasAuditoria", "hasNube", "hasCerebro", "hasBus", "hasProtected"]) {
      if (!checks[signal]) throw new SafeValidationError(`${label} missing ${signal}: ${JSON.stringify(checks)}`, "BLOCKED_SCREENSHOT");
    }
    console.log(`:: production ${label} screenshot PASS ${outputPath}`);
  } finally {
    await context.close();
    await browser.close();
  }
}

async function main() {
  await validatePublicRuntime();
  const token = await validateAuthenticatedApi();
  await capture(token, "mobile 390x844", { width: 390, height: 844 }, "ecosystem-command-core-production-auth-mobile-390x844.png");
  await capture(token, "desktop 1280x720", { width: 1280, height: 720 }, "ecosystem-command-core-production-auth-desktop-1280x720.png");
  console.log(":: command core production authenticated close PASS");
}

main().catch((error) => {
  safeLogError(error);
  process.exitCode = 1;
});
