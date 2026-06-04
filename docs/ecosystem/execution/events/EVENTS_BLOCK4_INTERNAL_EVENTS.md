# Events Block 4: Internal Events

Estado: `IMPLEMENTED_LOCAL`

## 1. Objetivo

Crear la base de comunicacion interna de la Plataforma del Ecosistema con
eventos persistentes, validacion de payload, historial auditable, replay
controlado y dead letter preparado.

## 2. Modulos Implementados

- Event Registry.
- Event Catalog.
- Event Publisher.
- Event Consumer Registry.
- Event History.
- Event Replay.
- Event Validation.
- Event Metadata.
- Event Audit.
- Event Status.

## 3. Estados

- `created`
- `published`
- `consumed`
- `failed`
- `replayed`
- `dead_letter`

## 4. Endpoints

| Endpoint | Proposito |
| --- | --- |
| `GET /api/v1/events` | Lista eventos con filtros. |
| `POST /api/v1/events` | Publica evento interno. |
| `GET /api/v1/events/{event_id}` | Lee evento por id. |
| `POST /api/v1/events/{event_id}/replay` | Replay controlado. |
| `GET /api/v1/events/catalog` | Catalogo de eventos permitidos. |
| `GET /api/v1/events/consumers` | Consumidores internos registrados. |
| `GET /api/v1/events/audit` | Auditoria de eventos. |
| `GET /api/v1/events/dead-letter` | Eventos en dead letter. |
| `GET /api/v1/events/status` | Estado operacional de eventos. |

## 5. Catalogo Inicial

- `platform.memory.created`
- `platform.memory.updated`
- `platform.security.access_validated`
- `platform.control_center.read`
- `platform.audit.completed`

## 6. Persistencia

Tablas:

- `internal_events`
- `internal_event_audit`

La capa de database existente permite SQLite local y PostgreSQL mediante
`DATABASE_URL` para staging/production.

## 7. Validacion

Cada evento debe:

- tener tipo registrado en catalogo;
- cumplir campos obligatorios del payload;
- incluir source y subject;
- persistirse con metadata;
- crear auditoria.

## 8. Replay

El replay:

- no modifica el evento original;
- crea un nuevo evento `replayed`;
- incrementa `replay_count`;
- agrega metadata con `original_event_id`;
- registra auditoria.

## 9. Dead Letter

Dead letter queda preparado de forma local:

- eventos pueden enrutarse a `dead_letter`;
- se consultan por endpoint dedicado;
- no hay cola externa conectada.

## 10. Riesgos

- No existe broker real todavia.
- No hay consumidores ejecutando acciones reales.
- La produccion debe usar PostgreSQL.
- Los eventos no deben activar FORJA, CEREBRO o DCFT hasta aprobar contratos.

## 11. Dependencias

- Database layer.
- Pydantic schemas.
- FastAPI router.
- Catalogo JSON controlado.
- Consumer Registry local.

## 12. Auditoria Interna

Validaciones ejecutadas:

- `python -m compileall apps/api/app -q`
- `python -m pytest apps/api/tests -q`

Resultado inicial:

- compileall: `PASS`
- pytest: `97 passed`

## 13. Checklist

- [x] Event Registry.
- [x] Event Catalog.
- [x] Publisher.
- [x] Consumer Registry.
- [x] History.
- [x] Replay.
- [x] Payload validation.
- [x] Metadata.
- [x] Audit.
- [x] Status.
- [x] Dead letter.
- [x] No external queue connected.

## 14. Recomendaciones

Siguiente bloque recomendado:

`BLOCK_5_INTEGRATION_BUS`

Antes de avanzar:

1. Crear rama de backup.
2. Registrar recovery point.
3. Ejecutar pruebas completas.
