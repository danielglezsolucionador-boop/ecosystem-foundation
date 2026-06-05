# Hermes Integration Production Validation

Fecha: 2026-06-05

## Resultado

Hermes queda PASS productivo para el hito de discovery controlado.

Alcance validado:

- Produccion: `https://ecosystem-foundation.vercel.app`
- Version productiva final: `commit=e60c7d4`
- Estado Hermes: `prepared_for_discovery`
- Contrato: `hermes.discovery.v1`
- Runtime externo Hermes: no conectado
- Credenciales externas: no requeridas
- Conexion externa: `external_connection_enabled=false`

## Preflight Git

- Repo: `ecosystem-foundation`
- Rama: `main`
- Estado Git antes de validar: limpio
- `origin/main` contiene:
  - `b532e24 feat: integrate hermes discovery profile`
  - `3c930e4 docs: record hermes production deploy blocker`

## Validacion Local

Validacion inicial antes de deploy:

- `python -m compileall apps api scripts` -> PASS
- `python -m pytest apps/api/tests` -> PASS, 199 tests
- `python scripts/validate_v1.py` -> PASS
- Secret scan -> PASS

Durante la validacion productiva se detecto que Vercel no puede leer rutas locales del repo Hermes. Se agrego soporte para snapshot versionado de evidencia local, sin habilitar runtime externo.

Commit correctivo:

- `e60c7d4 fix: support hermes production discovery evidence`

Validacion local posterior:

- `python -m compileall apps api scripts` -> PASS
- `python -m pytest apps/api/tests` -> PASS, 200 tests
- `python scripts/validate_v1.py` -> PASS
- Secret scan -> PASS
- `python scripts/dev_validate.py --allow-sqlite` -> PASS

## Deploys Vercel

Deploy 1:

- URL: `https://ecosystem-foundation-gln0kg97o.vercel.app`
- Alias: `https://ecosystem-foundation.vercel.app`
- Resultado: Ready
- Commit servido: `caa4c27`
- Hallazgo: Hermes estaba desplegado, pero `/api/v1/integrations/apps/hermes/discovery` reportaba `blocked_missing_repository_evidence` porque Vercel no tiene acceso al path local de Hermes.

Deploy 2:

- URL: `https://ecosystem-foundation-2topywxwx.vercel.app`
- Alias: `https://ecosystem-foundation.vercel.app`
- Resultado: Ready
- Commit servido: `e60c7d4`
- Resultado Hermes: PASS productivo para discovery controlado.

## Produccion Validada

Endpoints base:

- `GET /health` -> 200, `status=ok`
- `GET /readiness` -> 200, `status=ready`, `postgres=true`, `sqlite=false`, `persistent=true`
- `GET /runtime/status` -> 200, `status=operational`, `commit=e60c7d4`
- `GET /version` -> 200, `commit=e60c7d4`

Hermes:

- `GET /api/v1/apps` -> 200, Hermes presente
- `GET /api/v1/apps/hermes` -> 200, `touch_policy=integration_prepared_no_runtime_connection`
- `GET /api/v1/integrations/apps/hermes` -> 200, `integration_status=prepared_for_discovery`
- `GET /api/v1/integrations/apps/hermes/discovery` -> 200
  - `integration_status=prepared_for_discovery`
  - `contract_id=hermes.discovery.v1`
  - `evidence_source=versioned_local_discovery_snapshot`
  - `evidence_repository_commit=fd150cf`
  - `missing_evidence_files=[]`
  - `health_status=local_evidence_snapshot_found`
  - `external_connection_enabled=false`

Contracts:

- `GET /api/v1/contracts?app_id=hermes` -> 200, `hermes.discovery.v1`
- `GET /api/v1/integrations/contracts/hermes.discovery.v1` -> 200, `status=prepared_for_discovery`

Integration Bus:

- `GET /api/v1/integration-bus` -> 200
- `GET /api/v1/integration-bus/services` -> 200, servicio `hermes` presente
- `GET /api/v1/integration-bus/status` -> 200, `external_connections_enabled=false`

Events:

- `GET /api/v1/events/catalog` -> 200
- `GET /api/v1/events/consumers` -> 200
- Evento Hermes registrado: `platform.hermes.discovery.completed`
- Consumer Hermes registrado: `hermes-discovery-consumer`

Control Center, Governance, Audit y Observability:

- `GET /control-center` -> 200
- Control Center carga login ejecutivo en produccion
- Browser console errors en Control Center: 0
- `GET /api/v1/control-center` sin sesion -> 401 esperado
- `GET /api/v1/governance` sin sesion -> 401 esperado
- `GET /api/v1/audit/integration` sin sesion -> 401 esperado
- `GET /api/v1/observability/status` sin sesion -> 401 esperado

Nota: no se usaron credenciales productivas durante esta validacion. La visibilidad autenticada completa se cubrio localmente con `scripts/dev_validate.py --allow-sqlite`, que valida auth, Control Center, Control Center apps, Governance gates y Observability.

## Ruptura Productiva Segura

Sin escribir datos en produccion:

- `GET /api/v1/integrations/apps/ghost/discovery` -> 404 esperado
- `GET /api/v1/integrations/contracts/ghost.v1` -> 404 esperado
- `GET /api/v1/events/missing-event` -> 404 esperado
- APIs protegidas sin sesion -> 401 esperado

Resultado: fail-closed PASS.

## Observaciones

- `/runtime/status` responde desde el alias productivo, pero el campo `environment` sigue mostrando `staging`. No bloquea Hermes, pero conviene reconciliar la variable de entorno del proyecto Vercel en un bloque de configuracion posterior.
- Hermes queda en discovery controlado, no en conexion runtime. Cualquier conexion real futura requiere aprobacion humana y credenciales fuera del repo.

## Decision

Hermes queda validado en produccion como primera integracion progresiva del ecosistema.

Se puede avanzar a Auditor respetando el orden aprobado.

