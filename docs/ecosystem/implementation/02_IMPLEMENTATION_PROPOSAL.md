# 02 - Implementation Proposal

Estado: `PROPOSAL_READY`

Fecha: 2026-06-03

Fuente:

- [01_REPOSITORY_DISCOVERY_REPORT.md](./01_REPOSITORY_DISCOVERY_REPORT.md)
- [../01_INFRASTRUCTURE_FOUNDATION.md](../01_INFRASTRUCTURE_FOUNDATION.md)
- [../04_ECOSYSTEM_CONTROL_CENTER.md](../04_ECOSYSTEM_CONTROL_CENTER.md)
- [../06_ECOSYSTEM_INTEGRATION_MAP.md](../06_ECOSYSTEM_INTEGRATION_MAP.md)
- [../execution/app-registry/APP_REGISTRY_V1.md](../execution/app-registry/APP_REGISTRY_V1.md)

## 1. Objetivo

Proponer la primera version ejecutable de la plataforma `ecosystem-foundation` a partir del descubrimiento real del repositorio.

Esta propuesta no crea codigo, no crea infraestructura y no hace deploy.

## 2. Principio de Decision

El repositorio no tiene stack existente. Por eso el stack recomendado debe cumplir:

- bajo costo inicial;
- desarrollo local simple;
- contratos claros;
- buen soporte para APIs, agentes, memoria y automatizacion;
- frontend administrativo claro;
- base de datos relacional desde el inicio;
- migraciones versionadas;
- pruebas automatizables;
- cloud-agnostic.

## 3. Stack Recomendado

Recomendacion:

| Capa | Stack recomendado | Motivo |
|---|---|---|
| Backend | Python + FastAPI | APIs rapidas, documentacion OpenAPI, buen encaje con agentes, memoria, auditorias y workers |
| Frontend | React + TypeScript + Vite | Control Center liviano, rapido, sin complejidad SSR inicial |
| Base de datos | PostgreSQL | Relacional, robusta, multi-tenant, migraciones y auditoria |
| ORM/Migraciones | SQLAlchemy + Alembic | Madurez, control de schema, compatibilidad FastAPI |
| Validacion/Schemas | Pydantic | Contratos tipados, validacion de request/response |
| Tests backend | Pytest | Simple y compatible con FastAPI |
| Tests frontend | Vitest + Testing Library | Validacion rapida de componentes |
| Lint/Formato backend | Ruff | Rapido, simple |
| Lint/Formato frontend | ESLint + Prettier | Estandar TypeScript |
| Eventos iniciales | Tabla `event_outbox` en PostgreSQL | Evita introducir broker antes de necesitarlo |
| Queue futura | Redis/worker posterior | Solo cuando haya jobs reales |
| Storage inicial | File metadata en DB + storage adapter | Permite local primero y objeto cloud despues |
| Observabilidad inicial | JSON logs + request_id | Suficiente para primera version local |

## 4. Backend Recomendado

Backend inicial: `apps/api`

Responsabilidades V1:

- `/health`;
- `/runtime/status`;
- App Registry API;
- Memory API;
- Deliverables API;
- Audit API;
- Auth foundation sin defaults inseguros;
- workspace foundation;
- permisos backend;
- OpenAPI automatico;
- logs con `request_id`;
- configuracion por entorno sin secrets en repo.

Endpoints iniciales:

```text
GET  /health
GET  /runtime/status
GET  /api/v1/apps
POST /api/v1/apps
GET  /api/v1/apps/{app_id}
GET  /api/v1/memory
POST /api/v1/memory
GET  /api/v1/deliverables
POST /api/v1/deliverables
GET  /api/v1/audit/events
```

No incluir en V1:

- deploy;
- integracion real con FORJA;
- integracion real con CEREBRO;
- proveedores IA;
- agentes locales;
- acciones destructivas;
- broker externo.

## 5. Frontend Recomendado

Frontend inicial: `apps/web`

Experiencia V1:

- Control Center documental-operativo;
- estado global;
- apps registradas;
- health/runtime por app cuando exista fuente;
- memoria;
- entregables;
- bloqueos;
- auditoria;
- pantalla de configuracion de manifests;
- vista mobile simple.

No incluir en V1:

- redisenos de FORJA;
- redisenos de CEREBRO;
- dashboards falsos;
- datos productivos inventados;
- acciones de deploy.

## 6. Base de Datos Recomendada

Base: PostgreSQL.

Tablas iniciales:

```text
users
workspaces
workspace_memberships
roles
permissions
apps
app_environments
app_dependencies
memory_entries
deliverables
audit_events
event_outbox
```

Reglas:

- migraciones Alembic desde el primer commit de codigo;
- ningun dato sensible en seeds;
- admin inicial solo por variables de entorno obligatorias;
- fail-safe si faltan secrets requeridos;
- timestamps en todas las entidades operativas.

## 7. Estructura de Carpetas Recomendada

```text
apps/
  api/
    app/
      main.py
      api/
      core/
      db/
      models/
      schemas/
      services/
      tests/
    alembic/
    pyproject.toml
  web/
    src/
      app/
      components/
      features/
      lib/
      tests/
    package.json
packages/
  contracts/
    openapi/
    json-schema/
  docs-tools/
infra/
  local/
  future-cloud/
docs/
  ecosystem/
```

Nota:

Esta estructura todavia no debe crearse hasta aprobar la fase de implementacion ejecutable.

## 8. Estrategia de Integracion

Orden recomendado:

1. Crear backend local con `/health` y `/runtime/status`.
2. Crear DB local y migraciones.
3. Implementar App Registry como primera entidad real.
4. Implementar Memory, Deliverables y Audit con contratos existentes.
5. Crear frontend Control Center consumiendo solo API local.
6. Agregar tests y smoke local.
7. Registrar primera app real por manifest, sin tocar su repo.
8. Integrar apps externas solo por API/manifest aprobado.

## 9. Primer Hito Ejecutable Propuesto

Nombre:

`EXECUTABLE_PLATFORM_SCAFFOLD_V1`

Criterio de salida:

- repo mantiene `docs/ecosystem/`;
- `apps/api` creado;
- `apps/web` creado;
- backend arranca local;
- frontend arranca local;
- `/health` responde;
- `/runtime/status` responde;
- DB local conecta;
- migracion inicial PASS;
- tests minimos PASS;
- no secrets en git;
- no deploy;
- no FORJA;
- no CEREBRO.

## 10. Riesgos

| Riesgo | Impacto | Mitigacion |
|---|---:|---|
| Construir demasiado en V1 | Alto | Limitar V1 a Core API + Control Center basico |
| Elegir stack sin evidencia | Medio | Stack elegido despues de discovery y por requisitos documentados |
| Duplicar FORJA/CEREBRO | Alto | No tocar apps externas en V1 |
| Incluir secrets | Critico | `.env` ignorado y templates sin valores |
| Introducir broker prematuro | Medio | Usar `event_outbox` en PostgreSQL inicialmente |

## 11. Decision Recomendada

Avanzar a `EXECUTABLE_PLATFORM_SCAFFOLD_V1` con:

- Python + FastAPI para backend;
- React + TypeScript + Vite para frontend;
- PostgreSQL para persistencia;
- Alembic para migraciones;
- App Registry como primera entidad funcional;
- Control Center como primera UI;
- sin deploy;
- sin infraestructura real;
- sin tocar FORJA ni CEREBRO.
