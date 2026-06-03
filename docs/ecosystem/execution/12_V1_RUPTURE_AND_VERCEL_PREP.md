# Platform V1 Rupture Test And Vercel Prep

Fecha: 2026-06-03
Repositorio: `https://github.com/danielglezsolucionador-boop/ecosystem-foundation`
Proyecto Vercel objetivo: `https://vercel.com/danielglezsolucionador-boops-projects/ecosystem-foundation`

## Backup

- Rama: `backup/v1-rupture-prep-20260603-095917`
- Commit: `2d953bb`
- Push backup: PASS

## Estado inicial auditado

- Rama: `main`
- HEAD inicial: `e6836ff`
- Remoto: `origin/main`
- Worktree inicial: limpio
- Stack: Python/FastAPI
- API local: `apps/api/app/main.py`
- Tests iniciales: `34 passed`
- Compileall inicial: PASS
- Secret scan inicial: sin secretos reales

## Prueba de ruptura inicial

Pruebas ejecutadas:

- Endpoints existentes.
- 404 desconocido.
- App id vacio/blank.
- Payload vacio.
- JSON malformado.
- Rol inexistente.
- Contrato inexistente.
- `DATABASE_URL`.
- URL Postgres.

Resultado inicial:

- PASS: 19
- FAIL: 2

Fallos encontrados:

1. `DATABASE_URL` no era aceptado como alias cloud.
2. `postgresql://...` no estaba preparado; la capa DB solo soportaba SQLite.

## Correcciones aplicadas

### Configuracion

- `Settings` ahora acepta:
  - `ECOSYSTEM_API_DATABASE_URL`
  - `DATABASE_URL`
  - fallback SQLite local

### Base de datos

- SQLite local sigue soportado.
- Postgres cloud preparado para:
  - `postgresql://`
  - `postgres://`
- Driver preparado: `psycopg[binary]`.
- Placeholders SQL compatibles:
  - SQLite: `?`
  - Postgres: `%s`
- Schema base `platform_metadata` compartido.

### Runtime

- `/readiness` ahora reporta dependencia real de database.
- `/runtime/status` ahora reporta database y storage reales.
- Control Center deja de declarar que no hay database.

### Vercel

Archivos agregados:

- `requirements.txt`
- `vercel.json`
- `api/index.py`
- `docs/ecosystem/execution/vercel/VERCEL_DEPLOYMENT_PREP.md`

### Tests

Tests nuevos/reforzados:

- Rupture tests.
- Vercel prep tests.
- `DATABASE_URL` alias.
- Postgres backend detection.
- Postgres SQL placeholder.
- Postgres initialization contract con conexion fake.
- Readiness database dependency.

Total final:

- `47 passed`

## Rondas obligatorias

Comando:

```powershell
python scripts/validate_v1.py
```

Cada ronda ejecuta:

- `python -m compileall apps/api api -q`
- `python -m pytest -q`
- import serverless `api.index`
- secret scan local

Resultados:

| Ronda | Resultado | Tests |
|---|---|---|
| 1 | PASS | 47 passed |
| 2 | PASS | 47 passed |
| 3 | PASS | 47 passed |

## Secret scan

Resultado: PASS

No se detectaron secretos reales.

Exclusiones intencionales:

- `.git`
- `.pytest_cache`
- `__pycache__`
- `.venv`
- `venv`
- `node_modules`
- `outputs`
- `work`
- `*.pyc`
- `*.db`
- `*.log`

## Compatibilidad Vercel

Preparado:

- Python serverless entrypoint: `api/index.py`
- Build Vercel: `@vercel/python`
- Routing Vercel: `/(.*)` -> `api/index.py`
- Dependencias cloud: `requirements.txt`
- Postgres: `DATABASE_URL`

No ejecutado:

- No se hizo deploy.
- No se creo infraestructura real.
- No se conectaron apps externas.

## Variables Vercel necesarias

Obligatorias:

```text
DATABASE_URL=<postgres connection string>
ECOSYSTEM_API_ENVIRONMENT=staging
ECOSYSTEM_API_SERVICE_NAME=ecosystem-foundation-api
ECOSYSTEM_API_VERSION=0.1.0
ECOSYSTEM_API_COMMIT=<git commit sha>
ECOSYSTEM_API_DEBUG=false
```

Opcional:

```text
ECOSYSTEM_API_CORS_ORIGINS=https://<frontend-domain>
```

## Validacion de endpoints esperados

Local V1:

- `GET /`
- `GET /health`
- `GET /readiness`
- `GET /runtime/status`
- `GET /version`
- `GET /api/v1/apps`
- `GET /api/v1/apps/{app_id}`
- `GET /api/v1/apps/status/summary`
- `GET /api/v1/control-center/overview`
- `GET /api/v1/permissions/roles`
- `GET /api/v1/permissions/check`
- `GET /api/v1/storage/status`
- `GET /api/v1/memory/status`
- `GET /api/v1/memory/entries`
- `POST /api/v1/memory/entries`
- `POST /api/v1/audit/run`
- `GET /api/v1/audit/reports`
- `GET /api/v1/observability/status`
- `GET /api/v1/integrations/contracts`
- `GET /api/v1/platform/status`

## Estado final

- Platform V1 local: fuerte
- Tests fuertes: PASS
- Vercel config: preparada
- Postgres config: preparada
- Apps externas: no tocadas
- FORJA: no tocada
- CEREBRO: no tocado

## Siguiente paso

1. Crear/configurar Postgres en Vercel.
2. Agregar `DATABASE_URL` y variables operativas.
3. Ejecutar primer deploy staging.
4. Validar `/health`, `/readiness`, `/runtime/status`, `/api/v1/platform/status`.
5. Solo despues considerar frontend Control Center o integracion externa.
