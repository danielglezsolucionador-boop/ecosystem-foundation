# Control Center Premium Block 1

Estado: `IMPLEMENTED_LOCAL`

## 1. Objetivo

Construir la primera columna vertebral premium del ecosistema con un Control
Center local, estructurado y auditable.

El bloque no conecta FORJA, CEREBRO, DCFT ni ninguna aplicacion externa.

## 2. Alcance Implementado

- overview ejecutivo;
- estado de aplicaciones;
- estado de servicios;
- estado de dependencias;
- runtime status;
- metricas de plataforma;
- resumen operacional;
- resumen ejecutivo;
- alertas;
- readiness;
- audit trail local del Control Center.

## 3. Endpoints

| Endpoint | Proposito |
| --- | --- |
| `GET /api/v1/control-center` | Respuesta consolidada completa. |
| `GET /api/v1/control-center/overview` | Vista ejecutiva y operacional resumida. |
| `GET /api/v1/control-center/status` | Runtime, apps, servicios y dependencias. |
| `GET /api/v1/control-center/apps` | Estado por aplicacion desde App Registry. |
| `GET /api/v1/control-center/services` | Servicios internos de la plataforma. |
| `GET /api/v1/control-center/dependencies` | Dependencias de runtime, database y gobernanza. |
| `GET /api/v1/control-center/metrics` | Metricas operativas estructuradas. |
| `GET /api/v1/control-center/alerts` | Alertas activas con severidad. |
| `GET /api/v1/control-center/readiness` | Preparacion para siguientes fases. |

## 4. Estados

Estados permitidos:

- `healthy`
- `degraded`
- `blocked`
- `unknown`

El estado `blocked` se usa de forma deliberada para contratos de integracion
externa pendientes. No representa fallo del runtime local.

## 5. Fuentes de Datos

- `apps/api/app/data/apps_registry.json`
- `apps/api/app/services/app_registry.py`
- `apps/api/app/services/storage.py`
- `apps/api/app/core/database.py`
- `apps/api/app/core/config.py`
- `apps/api/app/core/metadata.py`

## 6. Reglas de Seguridad

- `external_connections_enabled=false`
- FORJA no se toca.
- CEREBRO no se toca.
- DCFT no se toca.
- No se imprimen secrets.
- No se conectan runtimes externos.
- `DATABASE_URL` solo se reporta por fuente, nunca por valor.

## 7. Persistencia

El Control Center registra lecturas consolidadas en:

- tabla: `control_center_audit_events`
- schema marker: `control_center_schema_version`

La persistencia usa la configuracion existente:

- local: SQLite controlado del repositorio;
- staging/production: `DATABASE_URL` con PostgreSQL cuando este configurado.

## 8. Riesgos

- La produccion debe usar PostgreSQL para persistencia cloud real.
- Las aplicaciones externas siguen como referencias controladas, no como
  integraciones runtime.
- Los contratos de integracion deben aprobarse antes de habilitar conexiones
  reales.

## 9. Dependencias

- App Registry local.
- Database layer.
- Pydantic schemas.
- FastAPI router.
- TestClient para validacion local.

## 10. Auditoria Interna

Validaciones ejecutadas:

- `python -m compileall apps/api/app -q`
- `python -m pytest apps/api/tests -q`

Resultado:

- compileall: `PASS`
- pytest: `61 passed`

## 11. Checklist

- [x] Pydantic models.
- [x] Service layer.
- [x] REST endpoints.
- [x] Controlled errors via FastAPI 404.
- [x] Positive endpoint tests.
- [x] Negative endpoint tests.
- [x] App Registry consolidation.
- [x] Runtime/database consolidation.
- [x] CEO view.
- [x] Operational view.
- [x] External app isolation.
- [x] Audit persistence.

## 12. Recomendaciones

Siguiente bloque recomendado:

`BLOCK_2_IDENTITY_ROLES_PERMISSIONS`

Antes de avanzar:

1. Crear rama de backup.
2. Registrar punto de recuperacion.
3. Ejecutar ciclo de pruebas completo.
