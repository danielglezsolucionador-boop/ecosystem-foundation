# Shared Ecosystem Memory

Estado: `BLOCK_3_SHARED_MEMORY_IMPLEMENTED`

## Objetivo

Crear una memoria compartida local, persistente, versionada y auditable para la
Plataforma del Ecosistema.

## Tipos Soportados

- `global`
- `application`
- `service`
- `context`
- `execution`
- `decision`
- `knowledge`

## Endpoints

- `GET /api/v1/memory`
- `POST /api/v1/memory`
- `GET /api/v1/memory/{memory_id}`
- `PUT /api/v1/memory/{memory_id}`
- `GET /api/v1/memory/{memory_id}/versions`
- `GET /api/v1/memory/apps/{app_id}`
- `GET /api/v1/memory/audit`
- `GET /api/v1/memory/status`

Aliases compatibles:

- `GET /api/v1/memory/entries`
- `POST /api/v1/memory/entries`

## Reglas

- Toda creacion genera version `1`.
- Toda actualizacion incrementa version.
- Toda creacion o actualizacion genera auditoria.
- No se conecta memoria real de FORJA.
- No se conecta memoria real de CEREBRO.
- No se conecta memoria real de DCFT.
- `external_sources_connected=false`.
