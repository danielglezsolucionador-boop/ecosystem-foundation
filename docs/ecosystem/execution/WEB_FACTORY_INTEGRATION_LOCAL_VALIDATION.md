# WEB_FACTORY Integration Local Validation

Fecha: 2026-06-06

## Resultado

WEB_FACTORY queda PASS local como discovery profile del bloque 2 del ecosistema.

No se hizo deploy Vercel para WEB_FACTORY durante la preparacion local. La app queda visible y controlada en `ecosystem-foundation` sin conexion runtime externa.

## Alcance

- App: `web_factory`
- Estado de discovery: `prepared_for_discovery`
- Contrato: `web_factory.discovery.v1`
- Integration Bus service: `web_factory`
- Evento interno: `platform.web_factory.discovery.completed`
- Consumer: `web-factory-discovery-consumer`
- Conexion runtime externa: deshabilitada
- Credenciales externas: no requeridas

## Discovery Tecnico

No se detecto un repositorio standalone de Web Factory. La integracion se modela como snapshot interno sobre capacidades de produccion web, despliegue, Control Center e Integration Bus ya presentes en `ecosystem-foundation`.

Evidencia versionada:

- `docs/ecosystem/03_ECOSYSTEM_DEPLOYMENT_ORDER.md`
- `docs/ecosystem/04_ECOSYSTEM_CONTROL_CENTER.md`
- `docs/ecosystem/05_ECOSYSTEM_EXECUTION_PLAN.md`
- `docs/ecosystem/06_ECOSYSTEM_INTEGRATION_MAP.md`
- `apps/web/control-center/index.html`
- `apps/web/control-center/assets/app.js`
- `apps/api/app/services/app_registry.py`
- `apps/api/app/services/integration_bus.py`

Resultado endpoint local:

- `GET /api/v1/integrations/apps/web_factory` -> 200
- `GET /api/v1/integrations/apps/web_factory/discovery` -> 200
- `health_status=local_evidence_snapshot_found`
- `missing_evidence_files=[]`
- `external_connection_enabled=false`

## Governance Gate

Validado por test automatizado:

- `GET /api/v1/governance/integration-gates` muestra `web_factory` como app no protegida.
- `POST /api/v1/governance/integration-gates/web_factory/request-discovery` -> `pending_approval`
- `POST /api/v1/governance/integration-gates/web_factory/approve-discovery` -> `approved_for_discovery`
- La aprobacion no ejecuta conexion real ni cambia el estado a `connected`.

## Contratos, Eventos y Bus

Contratos:

- `web_factory.discovery.v1` registrado en contratos estaticos.
- `web_factory.discovery.v1` sembrado como contrato dinamico controlado.
- `GET /api/v1/contracts?app_id=web_factory` validado por tests.

Integration Bus:

- Servicio `web_factory` agregado con `status=prepared_for_discovery`.
- Ruta interna de discovery WEB_FACTORY validada por tests.
- No hay conexiones externas.

Eventos:

- `platform.web_factory.discovery.completed` agregado al catalogo.
- `web-factory-discovery-consumer` registrado.
- Publicacion del evento validada por tests.

Control Center:

- WEB_FACTORY conserva `status=planned` y pasa a `touch_policy=integration_prepared_no_runtime_connection`.
- Control Center muestra WEB_FACTORY desde el registry sin tocar UI.

## Validaciones

- Suite focal registry/integrations/events/bus/contracts/control-center/governance/observability -> PASS, 139 tests
- `python -m pytest apps/api/tests` -> PASS, 233 tests
- `python -m compileall apps/api api scripts -q` -> PASS
- `python scripts/validate_v1.py` -> PASS, 233 tests
- Secret scan -> PASS
- `python scripts/dev_validate.py --allow-sqlite` -> PASS
- Validacion directa Control Center/Governance/Integration Bus/Contracts/Audit/Observability -> PASS

## Decision

WEB_FACTORY queda integrado localmente como discovery controlado del bloque 2.
