"""Chromium smoke tests against the real app, using disposable local credentials."""
import os
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from urllib.request import urlopen
from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parents[1]
BASE = "http://127.0.0.1:8765"
ASSETS = BASE + "/control-center/assets/"
with tempfile.TemporaryDirectory(prefix="pe-browser-") as tmp:
    env = {k: v for k, v in os.environ.items()
           if not any(x in k.upper() for x in ("TOKEN", "SECRET", "API_KEY", "PASSWORD", "DATABASE_URL", "VERCEL", "LINKEDIN"))}
    email = "browser-audit@example.invalid"
    password = "Local-demo-audit-only-6384!"
    env.update(ECOSYSTEM_API_ENVIRONMENT="local",
               ECOSYSTEM_API_DATABASE_URL="sqlite:///" + str(Path(tmp) / "browser.db"),
               CONTROL_CENTER_AUTH_ENABLED="true",
               CONTROL_CENTER_ADMIN_EMAIL=email, CONTROL_CENTER_ADMIN_PASSWORD=password,
               CONTROL_CENTER_ADMIN_NAME="Browser Audit",
               CEREBRO_LLM_ENABLED="false", ARSENAL_API_BROKER_ENABLED="false",
               LINKEDIN_POSTING_ENABLED="false")
    server = subprocess.Popen([sys.executable, "-m", "uvicorn", "app.main:app",
        "--host", "127.0.0.1", "--port", "8765"], cwd=ROOT / "apps/api", env=env)
    try:
        for attempt in range(100):
            if server.poll() is not None:
                raise RuntimeError("Local server exited")
            try:
                with urlopen(BASE + "/", timeout=1) as response:
                    if response.status == 200:
                        break
            except OSError:
                time.sleep(.2)
        else:
            raise RuntimeError("Local server did not start")
        with sync_playwright() as p:
            browser = p.chromium.launch()
            for width, height in [(1440, 900), (390, 844)]:
                context = browser.new_context(viewport={"width": width, "height": height})
                context.route("**/*", lambda route: route.continue_()
                              if route.request.url.startswith(BASE + "/") else route.abort())
                page = context.new_page()
                errors = []
                page.on("pageerror", lambda error: errors.append(str(error)))
                page.goto(ASSETS + "storefront-pe.html")
                expect(page.locator(".product")).to_have_count(3)
                page.locator("#category").select_option("Hogar")
                expect(page.locator(".product")).to_have_count(1)
                page.locator(".product button").click()
                expect(page.locator("#product-title")).to_contain_text("Sello")
                page.locator(".pack button").nth(1).click()
                expect(page.locator("#cart-message")).to_contain_text("Total de demostración calculado")
                expect(page.locator("#total")).to_contain_text("172")
                page.locator("#region").select_option("provincia")
                expect(page.locator("#total")).to_contain_text("178")
                page.locator("#ack").check()
                page.locator("#submit").click()
                expect(page.locator("#checkout-message")).to_contain_text("Simulación completada")
                page.locator("#payment").select_option("anticipado_demo")
                page.locator("#ack").check()
                page.locator("#submit").click()
                expect(page.locator("#checkout-message")).to_contain_text("Sin cobro")
                page.locator("#clear").click()
                expect(page.locator("#submit")).to_be_disabled()
                assert page.evaluate("document.documentElement.scrollWidth <= innerWidth + 1"), "Horizontal overflow"
                assert not errors, errors
                print(f"PASS storefront {width}px: catalog, pack, cart, shipping, two demo payment modes")
                context.close()
            context = browser.new_context(viewport={"width": 1440, "height": 900})
            context.route("**/*", lambda route: route.continue_()
                          if route.request.url.startswith(BASE + "/") else route.abort())
            page = context.new_page()
            errors = []
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.goto(ASSETS + "dropshipping-pe.html")
            expect(page.locator("#workspace")).to_be_hidden()
            page.locator("#login input[name=email]").fill(email)
            page.locator("#login input[name=password]").fill(password)
            page.locator("#login button").click()
            expect(page.locator("#workspace")).to_be_visible()
            expect(page.locator("#catalog-rows tr")).to_have_count(30)
            page.locator("#finance button").click()
            expect(page.locator("#financial-result")).to_contain_text("14.47")
            page.locator("#pipeline button").click()
            expect(page.locator("#pipeline-result")).to_contain_text("Conciliación: Coincide")
            page.locator("#growth-plan button").click()
            expect(page.locator("#growth-plan-result")).to_contain_text("25 s")
            page.locator("#growth-campaign button").click()
            expect(page.locator("#growth-campaign-result")).to_contain_text("Evaluar escalamiento con CEO")
            page.locator("#evidence-form input[name=reference]").fill("DEMO-2026")
            page.locator("#evidence-form button").click()
            expect(page.locator("#evidence-rows")).to_contain_text("DEMO-2026")
            page.get_by_role("button", name="Aceptar ensayo", exact=True).click()
            expect(page.locator("#evidence-rows")).to_contain_text("Aceptado (ensayo)")
            page.locator("#durable-refresh").click()
            expect(page.locator("#durable-status")).to_contain_text("Ensayo activo")
            page.locator("#durable-form input[name=reference]").fill("DEMO-100")
            page.locator("#durable-form button").click()
            expect(page.locator("#durable-message")).to_contain_text("Pedido de ensayo registrado")
            expect(page.locator("#durable-rows tr")).to_have_count(1)
            page.locator("#durable-form button").click()
            expect(page.locator("#durable-message")).to_contain_text("sin duplicar")
            expect(page.locator("#durable-rows tr")).to_have_count(1)
            page.locator("#durable-pause").click()
            expect(page.locator("#durable-status")).to_contain_text("Ensayo pausado")
            expect(page.locator("#durable-form button")).to_be_disabled()
            page.locator("#durable-resume").click()
            expect(page.locator("#durable-status")).to_contain_text("Ensayo activo")
            page.get_by_role("button", name="Ver DEMO-100", exact=True).click()
            expect(page.locator("#durable-detail")).to_contain_text("101.00")
            print("PASS durable demo order UI: create, duplicate, pause, resume, detail")
            page.locator("#tasks-refresh").click()
            expect(page.locator("#tasks-status")).to_contain_text("Cola disponible")
            page.locator("#tasks-form input[name=reference]").fill("DEMO-200")
            page.locator("#tasks-form select[name=intent]").select_option("settlement_difference")
            page.locator("#tasks-form button").click()
            expect(page.locator("#tasks-rows")).to_contain_text("En cola")
            page.locator("#tasks-tick").click()
            expect(page.locator("#tasks-rows")).to_contain_text("Pendiente de revisión CEO")
            page.get_by_role("button", name="Revisar DEMO-200", exact=True).click()
            expect(page.locator("#tasks-rows")).to_contain_text("Revisado (ensayo)")
            print("PASS task queue UI: enqueue, manual tick, CEO review")
            page.locator("#logout").click()
            expect(page.locator("#workspace")).to_be_hidden()
            expect(page.locator("#login")).to_be_visible()
            assert not errors, errors
            print("PASS authenticated lab: login, catalog, finance, COD, marketing, evidence review, logout")
            browser.close()
    finally:
        server.terminate()
        try:
            server.wait(timeout=10)
        except subprocess.TimeoutExpired:
            server.kill()
            server.wait()
