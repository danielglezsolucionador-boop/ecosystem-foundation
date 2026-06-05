# Ecosystem Foundation

Repositorio oficial de la fundacion tecnica del ecosistema.

Estado actual:

- documentacion ejecutiva versionada en `docs/ecosystem/`;
- estructura base del proyecto creada;
- backend Python/FastAPI base creado en `apps/api/`;
- healthcheck local disponible;
- configuracion por entorno sin secrets reales;
- Plataforma V1 local operativa;
- preparacion Vercel/Postgres versionada.

Fuera de alcance en esta fase:

- deploy;
- infraestructura cloud real;
- cambios en FORJA;
- cambios en CEREBRO;
- integracion con proveedores IA;
- storage productivo;
- base de datos productiva.

## Estructura

```text
apps/
  api/        Backend base del ecosistema.
  web/        Futuro Control Center web.
docs/
  ecosystem/  Fuente de verdad documental.
infra/
  local/      Configuracion local futura.
packages/
  contracts/  Contratos compartidos futuros.
```

## Requisitos Locales

- Python 3.11 o superior.
- FastAPI, Uvicorn, Pytest y HTTPX disponibles en el entorno local.

Las dependencias esperadas estan declaradas en:

```text
apps/api/pyproject.toml
requirements.txt
```

## Configuracion Local

Template seguro:

```text
apps/api/config/environment.example
```

Variables soportadas:

```text
ECOSYSTEM_API_ENVIRONMENT=local
ECOSYSTEM_API_SERVICE_NAME=ecosystem-foundation-api
ECOSYSTEM_API_VERSION=0.1.0
ECOSYSTEM_API_COMMIT=local
ECOSYSTEM_API_CORS_ORIGINS=http://localhost:5173
ECOSYSTEM_API_DEBUG=false
ECOSYSTEM_API_DATABASE_URL=sqlite:///./var/ecosystem_foundation.db
CONTROL_CENTER_ADMIN_EMAIL=
CONTROL_CENTER_ADMIN_PASSWORD=
CONTROL_CENTER_ADMIN_NAME=
```

No guardar secrets reales en el repositorio.

Para Vercel/Postgres, configurar en Vercel:

```text
DATABASE_URL=postgresql://...
ECOSYSTEM_API_ENVIRONMENT=staging
ECOSYSTEM_API_SERVICE_NAME=ecosystem-foundation-api
ECOSYSTEM_API_VERSION=0.1.0
ECOSYSTEM_API_COMMIT=<git commit sha>
ECOSYSTEM_API_DEBUG=false
CONTROL_CENTER_ADMIN_EMAIL=<primer CEO>
CONTROL_CENTER_ADMIN_PASSWORD=<password seguro solo en Vercel>
CONTROL_CENTER_ADMIN_NAME=<nombre visible>
```

El usuario CEO inicial del Control Center solo se crea si las tres variables
`CONTROL_CENTER_ADMIN_EMAIL`, `CONTROL_CENTER_ADMIN_PASSWORD` y
`CONTROL_CENTER_ADMIN_NAME` existen en el entorno. Si falta una, el backend no
crea usuarios automaticamente y no hay password por defecto.

## Ejecutar Backend Local

Desde la raiz del repositorio:

```powershell
cd apps/api
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Endpoints locales:

```text
GET http://127.0.0.1:8000/
GET http://127.0.0.1:8000/health
GET http://127.0.0.1:8000/readiness
GET http://127.0.0.1:8000/runtime/status
GET http://127.0.0.1:8000/version
```

Control Center local:

```text
GET http://127.0.0.1:8000/control-center
POST http://127.0.0.1:8000/api/v1/auth/login
GET http://127.0.0.1:8000/api/v1/auth/me
POST http://127.0.0.1:8000/api/v1/auth/logout
```

## Probar

Desde la raiz del repositorio:

```powershell
python -m compileall apps/api -q
cd apps/api
python -m pytest -q
```

Validacion fuerte desde la raiz:

```powershell
python scripts/validate_v1.py
```

## Contrato de Salud

El contrato operativo esta documentado en:

```text
docs/ecosystem/execution/operations/HEALTHCHECK_CONTRACT.md
```

Estado actual de dependencias:

- database: `connected`
- storage: `database_backed`
- provider: `not_required`
- memory: `database_backed`

Esto es intencional: la primera version ejecutable no conecta todavia aplicaciones externas, pero si prepara almacenamiento local/cloud.

## Seguridad

Reglas vigentes:

- no subir `.env`;
- no subir secrets;
- no imprimir tokens en logs;
- no crear usuarios admin por defecto;
- no hacer deploy desde esta fase;
- no tocar FORJA;
- no tocar CEREBRO.

## Siguiente Trabajo Recomendado

Siguiente paso recomendado:

1. Configurar `DATABASE_URL` en Vercel.
2. Ejecutar primer deployment staging desde el commit/tag estable.
3. Validar `/health`, `/readiness`, `/runtime/status`, `/api/v1/platform/status`.
4. Mantener FORJA y CEREBRO fuera de alcance hasta contratos externos aprobados.
