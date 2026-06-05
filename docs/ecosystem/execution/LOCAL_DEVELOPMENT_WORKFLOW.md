# Local Development Workflow

Fecha: 2026-06-04

## Objetivo

Este flujo permite desarrollar el ECOSISTEMA primero en local, con GitHub como respaldo y Vercel solo para hitos grandes.

Nuevo flujo operativo:

1. Local
2. Pruebas fuertes
3. Commit
4. Push
5. Backup
6. Continuar local

Solo en hitos grandes:

1. Local estable
2. GitHub
3. Vercel
4. Validacion produccion
5. Tag

## Alcance Local

El repositorio puede levantar y validar:

- backend FastAPI
- Control Center
- PostgreSQL local
- Auth
- Governance
- App Registry
- Hermes discovery local
- Integration Bus
- Contracts
- Memory
- Audit
- Observability
- pruebas
- secret scan

No conecta aplicaciones externas reales.

## Archivos De Soporte

- `.env.local.example`
- `docker-compose.yml`
- `scripts/dev_start.py`
- `scripts/dev_validate.py`
- `scripts/dev_reset_db.py`
- `scripts/dev_seed.py`
- `scripts/dev_test_all.py`

## 1. Preparar Variables Locales

Copiar la plantilla:

```powershell
Copy-Item .env.local.example .env.local
```

La plantilla usa PostgreSQL local por defecto:

```text
ECOSYSTEM_API_DATABASE_URL=postgresql://ecosystem_local:ecosystem_local@127.0.0.1:55432/ecosystem_foundation_local?connect_timeout=3
```

El usuario CEO local de ejemplo es no sensible y solo para desarrollo:

```text
CONTROL_CENTER_ADMIN_EMAIL=ceo.local@example.com
CONTROL_CENTER_ADMIN_PASSWORD=example-local-control-center-password
CONTROL_CENTER_ADMIN_NAME=Local CEO
```

No subir `.env.local`.

## 2. Levantar PostgreSQL Local

Preferencia oficial: Docker Compose.

```powershell
docker compose up -d postgres
```

Validar estado:

```powershell
docker compose ps
```

La base local queda en:

```text
host: 127.0.0.1
port: 55432
database: ecosystem_foundation_local
user: ecosystem_local
password: ecosystem_local
```

El password es local no sensible. No usarlo en staging o production.

Si Docker no esta instalado, instalar Docker Desktop o levantar PostgreSQL local manualmente con esos mismos datos. Evitar el puerto 5432 si ya esta ocupado por otra app.

## 3. Sembrar Base Local

```powershell
python scripts/dev_seed.py
```

El seed inicializa:

- metadata de plataforma
- Auth y CEO local
- Audit
- Memory
- Events
- Integration Bus
- Contracts
- Governance
- Security audit
- Observability

## 4. Ejecutar Backend Local

```powershell
python scripts/dev_start.py
```

Opcional con reload:

```powershell
python scripts/dev_start.py --reload
```

Fallback SQLite solo para emergencia local:

```powershell
python scripts/dev_start.py --allow-sqlite
```

URL backend:

```text
http://127.0.0.1:8000
```

## 5. Abrir Cabina Humana

Control Center local:

```text
http://127.0.0.1:8000/control-center
```

Login local:

```text
Email: ceo.local@example.com
Password: example-local-control-center-password
```

## 6. Endpoints Locales Clave

Publicos:

```text
GET /
GET /health
GET /readiness
GET /runtime/status
GET /version
GET /api/v1/apps
GET /api/v1/apps/hermes
GET /api/v1/integrations/apps/hermes/discovery
GET /api/v1/integration-bus
GET /api/v1/contracts?app_id=hermes
```

Protegidos:

```text
POST /api/v1/auth/login
GET /api/v1/auth/me
GET /api/v1/control-center
GET /api/v1/governance/integration-gates
GET /api/v1/observability/status
```

## 7. Validacion Local

Validacion de runtime local con PostgreSQL:

```powershell
python scripts/dev_validate.py
```

Suite completa:

```powershell
python scripts/dev_test_all.py
```

Fallback SQLite solo si PostgreSQL local no esta disponible:

```powershell
python scripts/dev_validate.py --allow-sqlite
python scripts/dev_test_all.py --allow-sqlite
```

El fallback SQLite no reemplaza el objetivo local completo con PostgreSQL.

## 8. Reset Seguro De Base Local

El reset es destructivo y exige confirmacion explicita:

```powershell
python scripts/dev_reset_db.py --yes
python scripts/dev_seed.py
```

Guardas de seguridad:

- solo acepta entorno `local`
- solo acepta host local
- solo acepta nombre/user con marcador local
- no toca URLs remotas
- no toca Vercel

## 9. Integraciones Locales

Orden ECO-037:

1. Hermes
2. Auditor
3. Pluma
4. Lente
5. Web Factory
6. Marketing
7. Marca Personal
8. Comercio Autonomo
9. Buscador de Tendencias
10. Doctor Contable Financiero Tributario
11. FORJA
12. CENTINELA
13. CEREBRO

Regla local:

- primero discovery
- luego contrato
- luego adapter
- luego Integration Bus
- luego Control Center
- luego tests
- luego commit/push

No conectar runtime real hasta tener contrato y aprobacion humana.

## 10. Cuando Hacer Push

Hacer push despues de:

- tests locales PASS
- secret scan PASS
- documentacion actualizada
- no haber tocado FORJA/CEREBRO/DCFT
- git diff revisado

## 11. Cuando Hacer Deploy Vercel

No usar Vercel para cada tarea.

Usar Vercel solo cuando:

- varias fases locales esten estables
- `python scripts/dev_test_all.py` este en PASS con PostgreSQL local
- exista reporte de hito
- el cambio sea suficientemente grande para validacion cloud

Despues de deploy:

- validar produccion
- crear tag si aplica

## 12. Compatibilidad Vercel

La app conserva:

- `vercel.json`
- `api/index.py`
- `DATABASE_URL` como variable cloud
- `ECOSYSTEM_API_DATABASE_URL` como variable prioritaria cuando exista

No se requieren secrets locales para desarrollar.
