# Centralized Audit

Estado: `BLOCK_7_CENTRALIZED_AUDIT_IMPLEMENTED`

## Objetivo

Crear auditoria transversal para la Plataforma del Ecosistema.

## Severidades

- `info`
- `low`
- `medium`
- `high`
- `critical`

## Endpoints

- `GET /api/v1/audit`
- `POST /api/v1/audit/events`
- `GET /api/v1/audit/events/{event_id}`
- `GET /api/v1/audit/reports`
- `POST /api/v1/audit/reports/generate`
- `GET /api/v1/audit/security`
- `GET /api/v1/audit/configuration`
- `GET /api/v1/audit/integration`
- `GET /api/v1/audit/runtime`
- `GET /api/v1/audit/errors`

Alias compatible:

- `POST /api/v1/audit/run`

## Reglas

- No se leen secrets.
- No se imprimen secrets.
- Los eventos son persistentes.
- Los reportes son persistentes.
- Las categorias son filtrables.
- `external_connections_enabled=false`.
