import fs from "node:fs";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoDir = path.resolve(__dirname, "..");

const baseUrl = (process.env.ECOSYSTEM_PRODUCTION_BASE_URL || "https://ecosystem-foundation.vercel.app").replace(/\/+$/, "");
const email = process.env.CONTROL_CENTER_ADMIN_EMAIL || "";
const password = process.env.CONTROL_CENTER_ADMIN_PASSWORD || "";
const AUTH_TOKEN_KEY = "ecosystem_control_center_session_v1";
const MAX_BODY_CHARS = 1000;

let playwright;
try {
  playwright = require("./node_modules/playwright");
} catch {
  playwright = require("playwright");
}

const { chromium, request } = playwright;
const outputsDir = path.join(repoDir, "outputs");
const diagnosticsPath = path.join(outputsDir, "r4-auth-capture-diagnostics.json");
const debugScreenshotPath = path.join(outputsDir, "r4-debug-auth-failure-mobile.png");
fs.mkdirSync(outputsDir, { recursive: true });

export function hasVisibleMojibake(text) {
  return /Ãƒ|Ã‚|Ã¢|ï¿½|Ã|Â|â/.test(String(text || ""));
}

export function evaluateAuthenticatedCabinReadiness(checks, diagnostics = {}) {
  const visibleSignals = Array.isArray(checks?.visibleSignals) ? checks.visibleSignals : [];
  const roleText = String(checks?.roleText || "");
  const hasCabinSignals =
    visibleSignals.filter((signal) =>
      ["Empresa IA", "CEREBRO", "Revenue", "AUDITORÍA", "CEO"].includes(signal)
    ).length >= 2;
  const loginFormVisible = checks?.loginFormVisible === true;
  const appVisible = checks?.appVisible === true;
  const appAttached = checks?.appAttached === true;
  const hasRoleCeo = roleText.toUpperCase().includes("CEO");
  const hasNetworkFailures =
    (diagnostics.badResponses?.length || 0) > 0 || (diagnostics.requestFailures?.length || 0) > 0;
  const hasCriticalConsoleErrors = (diagnostics.consoleErrors || []).some((entry) => {
    const text = String(entry?.text || "");
    return !/favicon|manifest|source map/i.test(text);
  });
  const authenticatedCabinReady =
    (appVisible || appAttached) &&
    (hasRoleCeo || hasCabinSignals) &&
    !hasNetworkFailures &&
    !hasCriticalConsoleErrors;
  const shouldFailForLogin = loginFormVisible && appVisible !== true && hasCabinSignals !== true;
  return {
    hasCabinSignals,
    authenticatedCabinReady,
    hasCriticalConsoleErrors,
    shouldFailForLogin,
  };
}

function redactText(value) {
  if (value === undefined || value === null) return value;
  return String(value)
    .replace(/Bearer\s+[A-Za-z0-9._~+/=-]+/gi, "Bearer [REDACTED]")
    .replace(/ccs_[A-Za-z0-9._~+/=-]+/g, "ccs_[REDACTED]")
    .replace(/("?(?:token|access_token|refresh_token|authorization|password|cookie|set-cookie|secret)"?\s*[:=]\s*")([^"]+)(")/gi, "$1[REDACTED]$3")
    .replace(/((?:token|access_token|refresh_token|authorization|password|cookie|set-cookie|secret)=)([^&\s]+)/gi, "$1[REDACTED]");
}

function redactUrl(value) {
  try {
    const url = new URL(value);
    for (const key of [...url.searchParams.keys()]) {
      if (/token|auth|password|secret|key|cookie|session/i.test(key)) {
        url.searchParams.set(key, "[REDACTED]");
      }
    }
    return url.toString();
  } catch {
    return redactText(value);
  }
}

function extractJsonError(text) {
  try {
    const payload = JSON.parse(text);
    const summary = {};
    for (const key of ["error", "message", "detail", "code", "status"]) {
      if (payload && Object.prototype.hasOwnProperty.call(payload, key)) {
        summary[key] = redactText(typeof payload[key] === "string" ? payload[key] : JSON.stringify(payload[key]));
      }
    }
    return Object.keys(summary).length ? summary : null;
  } catch {
    return null;
  }
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
    throw new Error(`${label} expected 2xx, got ${status}: ${redactText(text).slice(0, 180).replace(/\s+/g, " ")}`);
  }
  return payload;
}

async function authenticate() {
  const api = await request.newContext({
    baseURL: baseUrl,
    extraHTTPHeaders: { Accept: "application/json" },
  });
  try {
    const login = await parseJsonResponse(
      await api.post("/api/v1/auth/login", {
        data: { email, password, remember_me: false },
        headers: { "Content-Type": "application/json", Accept: "application/json" },
      }),
      "POST /api/v1/auth/login"
    );
    const token = String(login.token || "");
    if (!token.startsWith("ccs_")) {
      throw new Error("POST /api/v1/auth/login did not return a Control Center session token.");
    }
    const authHeaders = { Authorization: `Bearer ${token}`, Accept: "application/json" };
    const me = await parseJsonResponse(await api.get("/api/v1/auth/me", { headers: authHeaders }), "GET /api/v1/auth/me");
    if (String(me.role || "").toUpperCase() !== "CEO") {
      throw new Error("GET /api/v1/auth/me did not return role CEO.");
    }
    await parseJsonResponse(await api.get("/api/v1/control-center", { headers: authHeaders }), "GET /api/v1/control-center");
    console.log("R4 authenticated API PASS");
    return token;
  } finally {
    await api.dispose();
  }
}

async function settle(page) {
  await page.waitForLoadState("domcontentloaded", { timeout: 60000 });
  try {
    await page.waitForLoadState("networkidle", { timeout: 10000 });
  } catch {
    console.log("R4 networkidle not reached; continuing after deterministic render wait");
  }
  await page.waitForFunction(() => document.readyState !== "loading", null, { timeout: 30000 });
  await page.waitForSelector("body", { state: "attached", timeout: 30000 });
  await page.waitForTimeout(2500);
}

async function writeDiagnostics(page, diagnostics, error) {
  const payload = {
    ...diagnostics,
    failedAt: new Date().toISOString(),
    error: redactText(error?.message || error),
  };
  try {
    payload.pageState = await page.evaluate(() => {
      const bodyText = document.body?.innerText || "";
      return {
        url: window.location.href,
        path: window.location.pathname,
        title: document.title,
        bodyTextLength: bodyText.length,
        loginFormAttached: Boolean(document.querySelector("#login-form")),
        loginFormVisible: Boolean(document.querySelector("#login-form")?.offsetParent),
        appAttached: Boolean(document.querySelector("#app")),
        appVisible: Boolean(document.querySelector("#app")?.offsetParent),
        roleText: document.querySelector("#active-user-role")?.textContent?.trim() || "",
        visibleSignals: [
          "Empresa IA",
          "CEREBRO",
          "CEO",
          "Centro CEO",
          "Departamentos",
          "Revenue",
          "Publishing",
          "Product Readiness",
          "NUBE",
          "AUDITORIA",
          "AUDITORÍA",
        ].filter((text) => bodyText.includes(text)),
        overflow: document.documentElement.scrollWidth > window.innerWidth + 1,
        hasMojibake: /Ãƒ|Ã‚|Ã¢|ï¿½|Ã|Â|â/.test(bodyText),
      };
    });
    payload.pageState = {
      ...payload.pageState,
      ...evaluateAuthenticatedCabinReadiness(payload.pageState, payload),
    };
  } catch (stateError) {
    payload.pageStateError = redactText(stateError?.message || stateError);
  }

  try {
    await page.screenshot({ path: debugScreenshotPath, fullPage: false });
    payload.debugScreenshot = debugScreenshotPath;
  } catch (screenshotError) {
    payload.debugScreenshotError = redactText(screenshotError?.message || screenshotError);
  }

  fs.writeFileSync(diagnosticsPath, JSON.stringify(payload, null, 2), "utf8");
  console.log(`R4 diagnostics saved ${diagnosticsPath}`);
  if (payload.debugScreenshot) console.log(`R4 debug screenshot saved ${debugScreenshotPath}`);
}

function summarizeHttpFailure(diagnostics) {
  const bad = diagnostics.badResponses[0];
  if (bad) {
    return `${bad.method} ${bad.url} status=${bad.status}`;
  }
  const failed = diagnostics.requestFailures[0];
  if (failed) {
    return `${failed.method} ${failed.url} failed=${failed.errorText}`;
  }
  return "no failing URL captured";
}

async function capture(token, label, viewport, fileName, debugOnFailure = false) {
  const browser = await launchBrowser();
  const context = await browser.newContext({ viewport });
  await context.addInitScript(
    ({ key, value }) => {
      window.localStorage.setItem(key, value);
    },
    { key: AUTH_TOKEN_KEY, value: token }
  );
  const page = await context.newPage();
  const diagnostics = {
    label,
    viewport,
    startedAt: new Date().toISOString(),
    baseUrl,
    badResponses: [],
    requestFailures: [],
    consoleErrors: [],
    pageErrors: [],
  };

  page.on("requestfailed", (request) => {
    diagnostics.requestFailures.push({
      url: redactUrl(request.url()),
      method: request.method(),
      errorText: redactText(request.failure()?.errorText || "unknown"),
    });
  });

  page.on("response", async (response) => {
    const status = response.status();
    if (status < 400) return;
    const request = response.request();
    const headers = response.headers();
    const contentType = headers["content-type"] || "";
    let body = "";
    let bodyError = null;
    try {
      body = await response.text();
    } catch (error) {
      bodyError = redactText(error?.message || error);
    }
    const redactedBody = redactText(body).slice(0, MAX_BODY_CHARS);
    diagnostics.badResponses.push({
      url: redactUrl(response.url()),
      method: request.method(),
      status,
      contentType,
      body: redactedBody,
      jsonSummary: contentType.includes("json") ? extractJsonError(body) : null,
      bodyError,
    });
  });

  page.on("console", (message) => {
    if (message.type() !== "error") return;
    const location = message.location();
    diagnostics.consoleErrors.push({
      text: redactText(message.text()),
      location: location
        ? {
            url: redactUrl(location.url || ""),
            lineNumber: location.lineNumber,
            columnNumber: location.columnNumber,
          }
        : null,
    });
  });
  page.on("pageerror", (error) => diagnostics.pageErrors.push(redactText(error.message)));

  try {
    await page.goto(`${baseUrl}/control-center?audit=R4-ai-company-operating-system`, {
      waitUntil: "domcontentloaded",
      timeout: 60000,
    });
    await settle(page);

    const checks = await page.evaluate(() => {
      const bodyText = document.body?.innerText || "";
      const visibleSignals = [
        "Empresa IA",
        "CEREBRO",
        "CEO",
        "Centro CEO",
        "Departamentos",
        "Revenue",
        "Publishing",
        "Product Readiness",
        "NUBE",
        "AUDITORIA",
        "AUDITORÍA",
      ].filter((text) => bodyText.includes(text));
      return {
        finalUrl: window.location.href,
        finalPath: window.location.pathname,
        overflow: document.documentElement.scrollWidth > window.innerWidth + 1,
        loginFormAttached: Boolean(document.querySelector("#login-form")),
        loginFormVisible: Boolean(document.querySelector("#login-form")?.offsetParent),
        appAttached: Boolean(document.querySelector("#app")),
        appVisible: Boolean(document.querySelector("#app")?.offsetParent),
        roleText: document.querySelector("#active-user-role")?.textContent?.trim() || "",
        bodyTextLength: bodyText.trim().length,
        hasMojibake: /Ãƒ|Ã‚|Ã¢|ï¿½|Ã|Â|â/.test(bodyText),
        visibleSignals,
      };
    });
    diagnostics.checks = {
      ...checks,
      ...evaluateAuthenticatedCabinReadiness(checks, diagnostics),
    };

    if (diagnostics.badResponses.length || diagnostics.requestFailures.length) {
      throw new Error(`network/render failure: ${summarizeHttpFailure(diagnostics)}`);
    }
    if (diagnostics.checks.hasCriticalConsoleErrors) {
      throw new Error(`console errors: ${diagnostics.consoleErrors.map((entry) => entry.text).join(" | ")}`);
    }
    if (diagnostics.pageErrors.length) throw new Error(`page errors: ${diagnostics.pageErrors.join(" | ")}`);
    if (checks.overflow) throw new Error("horizontal overflow detected");
    if (diagnostics.checks.shouldFailForLogin) throw new Error("login form is visible and authenticated cabin is not ready");
    if (!checks.finalPath.includes("/control-center")) throw new Error(`unexpected final URL: ${checks.finalUrl}`);
    if (checks.bodyTextLength <= 0) throw new Error("document body is empty");
    if (checks.hasMojibake) throw new Error("visible mojibake detected");
    if (!diagnostics.checks.authenticatedCabinReady) {
      throw new Error(`missing authenticated cabin signals: ${JSON.stringify(checks.visibleSignals)}`);
    }
    const actualViewport = page.viewportSize();
    if (!actualViewport || actualViewport.width !== viewport.width || actualViewport.height !== viewport.height) {
      throw new Error(`viewport mismatch: expected ${viewport.width}x${viewport.height}, got ${JSON.stringify(actualViewport)}`);
    }

    const outputPath = path.join(outputsDir, fileName);
    await page.screenshot({ path: outputPath, fullPage: false });
    const stat = fs.statSync(outputPath);
    if (stat.size <= 0) throw new Error(`screenshot file is empty: ${outputPath}`);

    console.log(`R4 ${label} screenshot PASS ${outputPath}`);
    console.log(
      `R4 ${label} validation ${JSON.stringify({
        viewport,
        bytes: stat.size,
        consoleErrors: 0,
        overflow: false,
        loginFormVisible: checks.loginFormVisible,
        authenticatedCabinReady: diagnostics.checks.authenticatedCabinReady,
        visibleSignals: diagnostics.checks.visibleSignals,
      })}`
    );
  } catch (error) {
    if (debugOnFailure) await writeDiagnostics(page, diagnostics, error);
    throw error;
  } finally {
    await context.close();
    await browser.close();
  }
}

async function main() {
  if (!email || !password) {
    throw new Error("CAPTURES_BLOCKED_AUTH: CONTROL_CENTER_ADMIN_EMAIL and CONTROL_CENTER_ADMIN_PASSWORD are required.");
  }
  const token = await authenticate();
  await capture(
    token,
    "mobile 390x844",
    { width: 390, height: 844 },
    "ecosystem-ai-company-operating-system-production-auth-mobile-390x844.png",
    true
  );
  await capture(
    token,
    "desktop 1280x720",
    { width: 1280, height: 720 },
    "ecosystem-ai-company-operating-system-production-auth-desktop-1280x720.png",
    true
  );
  console.log("R4 authenticated production screenshots PASS");
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  await main();
}
