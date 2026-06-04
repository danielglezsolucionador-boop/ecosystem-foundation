# Internal Events

Estado: `BLOCK_4_INTERNAL_EVENTS_IMPLEMENTED`

## Objetivo

Crear la base de comunicacion interna del Ecosistema sin conectar colas externas
ni aplicaciones reales.

## Estados

- `created`
- `published`
- `consumed`
- `failed`
- `replayed`
- `dead_letter`

## Endpoints

- `GET /api/v1/events`
- `POST /api/v1/events`
- `GET /api/v1/events/{event_id}`
- `POST /api/v1/events/{event_id}/replay`
- `GET /api/v1/events/catalog`
- `GET /api/v1/events/consumers`
- `GET /api/v1/events/audit`
- `GET /api/v1/events/dead-letter`
- `GET /api/v1/events/status`

## Reglas

- Los eventos se persisten localmente.
- El catalogo valida tipos y payload requerido.
- El replay crea un nuevo evento `replayed`.
- Dead letter esta preparado sin cola externa.
- `external_queue_connected=false`.
- No se conecta FORJA, CEREBRO ni DCFT.
