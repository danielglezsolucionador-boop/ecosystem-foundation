# Memory Block 3: Shared Ecosystem Memory

Estado: `IMPLEMENTED_LOCAL`

## 1. Objetivo

Crear una memoria persistente, versionada y auditable para la Plataforma del
Ecosistema, sin conectar fuentes reales de aplicaciones externas.

## 2. Modulos Implementados

- Global Memory.
- Application Memory.
- Service Memory.
- Context Memory.
- Execution Memory.
- Decision Memory.
- Knowledge Records.
- Memory Versioning.
- Memory Retention.
- Memory Audit.

## 3. Tipos

- `global`
- `application`
- `service`
- `context`
- `execution`
- `decision`
- `knowledge`

## 4. Estados

- `active`
- `draft`
- `archived`
- `superseded`

## 5. Endpoints

| Endpoint | Proposito |
| --- | --- |
| `GET /api/v1/memory` | Lista memoria con filtros por app, tipo y estado. |
| `POST /api/v1/memory` | Crea memoria versionada. |
| `GET /api/v1/memory/{memory_id}` | Lee un registro. |
| `PUT /api/v1/memory/{memory_id}` | Actualiza un registro e incrementa version. |
| `GET /api/v1/memory/{memory_id}/versions` | Lista versiones del registro. |
| `GET /api/v1/memory/apps/{app_id}` | Lista memoria asociada a una app. |
| `GET /api/v1/memory/audit` | Lista auditoria de memoria. |
| `GET /api/v1/memory/status` | Estado operacional de memoria. |

Aliases compatibles:

- `GET /api/v1/memory/entries`
- `POST /api/v1/memory/entries`

## 6. Persistencia

Tablas:

- `ecosystem_memory_records`
- `ecosystem_memory_versions`
- `ecosystem_memory_audit_events`

La capa de database existente permite:

- SQLite local controlado.
- PostgreSQL mediante `DATABASE_URL` para staging/production.

## 7. Versionado

Reglas:

- Creacion: version `1`.
- Actualizacion: version `n + 1`.
- Cada version guarda snapshot completo.
- `change_reason` queda como accion de version.

## 8. Auditoria

Cada creacion o actualizacion registra:

- `memory_id`
- accion
- version
- estado de auditoria
- fecha

No se guardan secrets.

## 9. Busqueda

Filtros implementados:

- `app_id`
- `type`
- `status`

## 10. Riesgos

- La memoria productiva debe correr sobre PostgreSQL.
- No existe UI de gestion de memoria todavia.
- No se han conectado memorias reales de aplicaciones externas por politica.
- La retencion esta modelada como metadata operativa, no como job automatico.

## 11. Dependencias

- Database layer.
- Pydantic schemas.
- FastAPI router.
- App Registry solo como referencia nominal, no como conexion externa.

## 12. Auditoria Interna

Validaciones ejecutadas:

- `python -m compileall apps/api/app -q`
- `python -m pytest apps/api/tests -q`

Resultado inicial:

- compileall: `PASS`
- pytest: `82 passed`

## 13. Checklist

- [x] Persistencia.
- [x] Versionado obligatorio.
- [x] Auditoria obligatoria.
- [x] Tipos minimos.
- [x] Estados.
- [x] Busqueda por app.
- [x] Busqueda por tipo.
- [x] Busqueda por estado.
- [x] 404 controlado.
- [x] Payload invalido 422.
- [x] No conectar FORJA.
- [x] No conectar CEREBRO.
- [x] No conectar DCFT.

## 14. Recomendaciones

Siguiente bloque recomendado:

`BLOCK_4_INTERNAL_EVENTS`

Antes de avanzar:

1. Crear rama de backup.
2. Registrar recovery point.
3. Ejecutar pruebas completas.
