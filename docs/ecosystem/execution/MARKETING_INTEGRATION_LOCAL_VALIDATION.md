# MARKETING Integration Local Validation

Fecha: 2026-06-06

## Resultado

MARKETING queda PASS local como discovery profile del bloque 2 del ecosistema.

No se hizo deploy Vercel para MARKETING durante la preparacion local. La app queda visible y controlada en `ecosystem-foundation` sin conexion runtime externa.

## Alcance

- App: `marketing`
- Estado de discovery: `prepared_for_discovery`
- Contrato: `marketing.discovery.v1`
- Integration Bus service: `marketing`
- Evento interno: `platform.marketing.discovery.completed`
- Consumer: `marketing-discovery-consumer`
- Conexion runtime externa: deshabilitada
- Credenciales externas: no requeridas

## Discovery Tecnico

No se detecto un repositorio standalone de Marketing. La integracion se modela como snapshot interno sobre capacidades de eventos, observabilidad, crecimiento y Control Center ya presentes en `ecosystem-foundation`.

Evidencia versionada:

- `docs/ecosystem/04_ECOSYSTEM_CONTROL_CENTER.md`
- `docs/ecosystem/05_ECOSYSTEM_EXECUTION_PLAN.md`
- `docs/ecosystem/06_ECOSYSTEM_INTEGRATION_MAP.md`
- `docs/ecosystem/execution/events/EVENTS_BLOCK4_INTERNAL_EVENTS.md`
- `docs/ecosystem/execution/observability/OBSERVABILITY_BLOCK8_CENTRALIZED_OBSERVABILITY.md`
- `apps/api/app/services/events.py`
- `apps/api/app/services/observability.py`
- `apps/api/app/services/integration_bus.py`

Resultado endpoint local:

- `GET /api/v1/integrations/apps/marketing` -> 200
- `GET /api/v1/integrations/apps/marketing/discovery` -> 200
- `health_status=local_evidence_snapshot_found`
- `missing_evidence_files=[]`
- `external_connection_enabled=false`

## Governance Gate

Validado por test automatizado:

- `GET /api/v1/governance/integration-gates` muestra `marketing` como app no protegida.
- `POST /api/v1/governance/integration-gates/marketing/request-discovery` -> `pending_approval`
- `POST /api/v1/governance/integration-gates/marketing/approve-discovery` -> `approved_for_discovery`
- La aprobacion no ejecuta conexion real ni cambia el estado a `connected`.

## Contratos, Eventos y Bus

Contratos:

- `marketing.discovery.v1` registrado en contratos estaticos.
- `marketing.discovery.v1` sembrado como contrato dinamico controlado.
- `GET /api/v1/contracts?app_id=marketing` validado por tests.

Integration Bus:

- Servicio `marketing` agregado con `status=prepared_for_discovery`.
- Ruta interna de discovery MARKETING validada por tests.
- No hay conexiones externas.

Eventos:

- `platform.marketing.discovery.completed` agregado al catalogo.
- `marketing-discovery-consumer` registrado.
- Publicacion del evento validada por tests.

Control Center:

- MARKETING conserva `status=planned` y pasa a `touch_policy=integration_prepared_no_runtime_connection`.
- Control Center muestra MARKETING desde el registry sin tocar UI.

## Validaciones

- Suite focal registry/integrations/events/bus/contracts/control-center/governance/observability -> PASS, 139 tests
- `python -m pytest apps/api/tests` -> PASS, 233 tests
- `python -m compileall apps/api api scripts -q` -> PASS
- `python scripts/validate_v1.py` -> PASS, 233 tests
- Secret scan -> PASS
- `python scripts/dev_validate.py --allow-sqlite` -> PASS
- Validacion directa Control Center/Governance/Integration Bus/Contracts/Audit/Observability -> PASS

## Decision

MARKETING queda integrado localmente como discovery controlado del bloque 2.
