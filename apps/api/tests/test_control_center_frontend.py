from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_control_center_frontend_is_served() -> None:
    response = client.get("/control-center")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Control Center" in response.text
    assert "/control-center/assets/favicon.svg" in response.text
    assert "/control-center/assets/app.js" in response.text
    assert "login-form" in response.text
    assert "active-user-role" in response.text
    assert "logout" in response.text
    assert "ECOSISTEMA IA" in response.text
    assert "Centro de Dirección Empresarial" in response.text
    assert "Decisión CEO" in response.text
    assert "Semáforo principal" in response.text
    assert "Mapa rapido" in response.text
    assert "Panel derecho de decisiones CEO" in response.text
    assert "Acciones ejecutivas del CEO" in response.text
    assert "Lo que el CEO debe entender primero" in response.text
    assert "Control humano de decisiones e integraciones" in response.text
    assert "Decision Center" in response.text
    assert "Approval Center" in response.text
    assert "Integration Gates" in response.text
    assert "Policy Center" in response.text
    assert "Risk Center" in response.text
    assert "Governance Audit" in response.text
    assert "Governance Reports" in response.text
    assert "Reunión con CEREBRO" in response.text
    assert "Reunión de Mañana" in response.text
    assert "Reunión de Tarde" in response.text
    assert "CEREBRO operativo interno" in response.text
    assert "CEREBRO ya coordina internamente" in response.text
    assert "Flujos de Empresa IA" in response.text
    assert "Simulación departamental" in response.text


def test_control_center_assets_are_served() -> None:
    css_response = client.get("/control-center/assets/styles.css")
    js_response = client.get("/control-center/assets/app.js")
    favicon_response = client.get("/favicon.ico")

    assert css_response.status_code == 200
    assert "text/css" in css_response.headers["content-type"]
    assert js_response.status_code == 200
    assert "javascript" in js_response.headers["content-type"]
    assert favicon_response.status_code == 200
    assert "image/svg+xml" in favicon_response.headers["content-type"]
    assert "/api/v1/control-center" in js_response.text
    assert "/api/v1/governance/auth-boundary" in js_response.text
    assert "/api/v1/auth/login" in js_response.text
    assert "Authorization" in js_response.text
    assert "executePendingAction" in js_response.text
    assert "escalate_approval" in js_response.text
    assert "companyDepartments" in js_response.text
    assert "dailyMeetingModels" in js_response.text
    assert "/api/v1/cerebro/status" in js_response.text
    assert "/api/v1/cerebro/brief/morning" in js_response.text
    assert "/api/v1/cerebro/brief/evening" in js_response.text
    assert "/api/v1/cerebro/decisions" in js_response.text
    assert "/api/v1/cerebro/tasks" in js_response.text
    assert "cerebro-operational-grid" in js_response.text
    assert "Bus interno" in js_response.text
    assert "rutas internas activas" in js_response.text
    assert "departmentalSimulationFlows" in js_response.text
    assert "Oportunidad IA / Video" in js_response.text
    assert "Ciberseguridad para SENTINELA" in js_response.text
    assert "Regulación DCFT" in js_response.text
    assert "API / Skill vendible" in js_response.text
    assert "Producto Amazon / Comercio" in js_response.text
    assert "Simulación departamental" in js_response.text
    assert "Sin ejecución externa" in js_response.text
    assert "CEO, esto requiere tu decisión." in js_response.text
    assert "CEO, este es el cierre del día." in js_response.text
    assert "Esto puede generar ingresos" in js_response.text
    assert "Esto está protegido y no se toca" in js_response.text
    assert "Esto debe auditarse antes de avanzar" in js_response.text
    assert "Esto puede pasar a FORJA" in js_response.text
    assert "Esto debe esperar aprobación" in js_response.text or "debe esperar aprobación" in js_response.text
    assert "datos reales" in js_response.text.lower()
    assert "datos preparados" in js_response.text.lower()
    assert "Empresa IA" in js_response.text
    assert "CREADOR DE APIS Y SKILLS" in js_response.text
    assert "BUSCADOR DE TENDENCIAS" in js_response.text
    assert "ARSENAL" in js_response.text
    assert "SNIFF AMAZON" in js_response.text
    assert "DIRECCIÓN" in js_response.text
    assert "CONSTRUCCIÓN" in js_response.text
    assert "INTELIGENCIA" in js_response.text
    assert "PRODUCTOS COMERCIALES" in js_response.text
    assert "CONTENIDO Y CRECIMIENTO" in js_response.text
    assert "OPERACIÓN" in js_response.text
    assert "CONTROL Y SEGURIDAD" in js_response.text
    assert "ALMACEN ESTRATÉGICO" in js_response.text
    assert "planned / pending_integration" in js_response.text
    assert "Inventario de APIs, modelos, skills, conectores" in js_response.text
    assert "COMERCIO AUTONOMO" in js_response.text
    assert "INVESTIGADOR" not in js_response.text
    assert "RADAR IA" not in js_response.text
    assert "forbidden" in css_response.text
    assert "mobile-brand-chip" in css_response.text
    assert "department-card" in css_response.text


def test_control_center_cerebro_copy_stays_truthful_and_protected() -> None:
    js_response = client.get("/control-center/assets/app.js")

    assert js_response.status_code == 200
    text = js_response.text
    normalized = text.lower()

    assert "Chief of Staff / Jefe de Gabinete IA" in text
    assert "Mano derecha del CEO" in text
    assert "Operativo interno; sin apps protegidas ni runtimes externos." in text
    assert "CEREBRO coordina dentro del backend/control center. Sin runtime externo." in text
    assert "Preparado, sin conexión real" in text
    assert "Todas las conexiones externas siguen apagadas" in text
    assert "DCFT sigue protegido" in text
    assert "sin SUNAT real" in text
    assert "Runtime local verificado" in text
    assert "Deploy conectado" not in text
    assert "DCFT protegido/no-touch: no integrado, no SUNAT real" in text
    assert "SENTINELA no productivo" in text
    assert "ARSENAL no runtime" in text
    assert "sin ruta interna activa hacia ARSENAL" in text
    assert "sin Local Agent" in text
    assert "sin SUNAT" in text

    forbidden_claims = [
        "dcft esta integrado",
        "sentinela esta activo en produccion",
        "forja real esta conectada",
        "nube esta conectada",
        "arsenal ya funciona como runtime",
        "hay rutas externas del bus",
        "hay apps externas conectadas",
        "se toco produccion",
        "se activo sunat",
        "local agent esta activo",
        "cerebro ejecuto codigo",
    ]
    for claim in forbidden_claims:
        assert claim not in normalized
