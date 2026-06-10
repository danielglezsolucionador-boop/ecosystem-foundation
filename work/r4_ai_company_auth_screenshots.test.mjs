import assert from "node:assert/strict";
import { describe, it } from "node:test";

import {
  evaluateAuthenticatedCabinReadiness,
  hasVisibleMojibake,
} from "./r4_ai_company_auth_screenshots.mjs";

describe("R4 authenticated screenshot readiness", () => {
  it("allows login attached when the authenticated cabin is ready", () => {
    const result = evaluateAuthenticatedCabinReadiness(
      {
        loginFormAttached: true,
        loginFormVisible: false,
        appAttached: true,
        appVisible: true,
        roleText: "CEO",
        visibleSignals: ["Empresa IA", "CEREBRO", "Revenue"],
      },
      { badResponses: [], requestFailures: [], consoleErrors: [] }
    );

    assert.equal(result.hasCabinSignals, true);
    assert.equal(result.authenticatedCabinReady, true);
    assert.equal(result.shouldFailForLogin, false);
  });

  it("fails when login is visible and the authenticated cabin is not ready", () => {
    const result = evaluateAuthenticatedCabinReadiness(
      {
        loginFormAttached: true,
        loginFormVisible: true,
        appAttached: false,
        appVisible: false,
        roleText: "",
        visibleSignals: [],
      },
      { badResponses: [], requestFailures: [], consoleErrors: [] }
    );

    assert.equal(result.authenticatedCabinReady, false);
    assert.equal(result.shouldFailForLogin, true);
  });

  it("detects visible mojibake variants", () => {
    assert.equal(hasVisibleMojibake("AUDITORÃA"), true);
    assert.equal(hasVisibleMojibake("AuditorÃƒÂ­a"), true);
    assert.equal(hasVisibleMojibake("operaciÃƒÂ³n"), true);
    assert.equal(hasVisibleMojibake("AUDITORÍA"), false);
  });

  it("allows app attached with CEO role and cabin signals", () => {
    const result = evaluateAuthenticatedCabinReadiness(
      {
        loginFormAttached: true,
        loginFormVisible: false,
        appAttached: true,
        appVisible: false,
        roleText: "CEO",
        visibleSignals: ["Empresa IA", "Revenue", "AUDITORÍA"],
      },
      { badResponses: [], requestFailures: [], consoleErrors: [] }
    );

    assert.equal(result.hasCabinSignals, true);
    assert.equal(result.authenticatedCabinReady, true);
    assert.equal(result.shouldFailForLogin, false);
  });
});
