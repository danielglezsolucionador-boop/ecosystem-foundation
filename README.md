# Ecosystem Foundation

Repositorio oficial de la fundacion tecnica del ecosistema.

Estado actual:

- documentacion ejecutiva versionada en `docs/ecosystem/`;
- estructura base del proyecto creada;
- backend Python/FastAPI base creado en `apps/api/`;
- healthcheck local disponible;
- configuracion por entorno sin secrets reales.

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
```

No guardar secrets reales en el repositorio.

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

## Probar

Desde la raiz del repositorio:

```powershell
python -m compileall apps/api -q
cd apps/api
python -m pytest -q
```

Resultado esperado actual:

```text
6 passed
```

## Contrato de Salud

El contrato operativo esta documentado en:

```text
docs/ecosystem/execution/operations/HEALTHCHECK_CONTRACT.md
```

Estado actual de dependencias:

- database: `not_required`
- storage: `not_required`
- provider: `not_required`
- memory: `not_required`

Esto es intencional: la primera version ejecutable no conecta todavia dependencias externas.

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

Continuar con `ECO-031` ampliando el scaffold ejecutable hacia:

1. App Registry API local;
2. modelos y persistencia local;
3. migraciones;
4. frontend Control Center;
5. smoke tests end-to-end locales.

