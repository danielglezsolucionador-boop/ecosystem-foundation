# Integration Bus

Estado: `BLOCK_5_INTEGRATION_BUS_IMPLEMENTED`

## Objetivo

Permitir rutas internas y dispatch simulado de mensajes sin acoplar ni tocar
aplicaciones externas.

## Endpoints

- `GET /api/v1/integration-bus`
- `GET /api/v1/integration-bus/routes`
- `POST /api/v1/integration-bus/routes`
- `GET /api/v1/integration-bus/services`
- `POST /api/v1/integration-bus/dispatch`
- `GET /api/v1/integration-bus/dependencies`
- `GET /api/v1/integration-bus/audit`
- `GET /api/v1/integration-bus/status`

## Reglas

- Solo servicios internos locales.
- No se conectan FORJA, CEREBRO ni DCFT.
- Cada ruta registrada genera auditoria.
- Cada dispatch genera auditoria.
- El dispatch publica eventos internos.
- Dead letter routing esta preparado.
- `external_connections_enabled=false`.
