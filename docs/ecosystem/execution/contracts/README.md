# Ecosystem Contracts

Estado: `BLOCK_6_CONTRACTS_IMPLEMENTED`

## Objetivo

Definir como se comunican las aplicaciones mediante contratos versionados y
auditables antes de cualquier conexion real.

## Endpoints

- `GET /api/v1/contracts`
- `POST /api/v1/contracts`
- `GET /api/v1/contracts/{contract_id}`
- `PUT /api/v1/contracts/{contract_id}`
- `POST /api/v1/contracts/{contract_id}/validate`
- `GET /api/v1/contracts/{contract_id}/versions`
- `POST /api/v1/contracts/{contract_id}/compatibility-check`
- `GET /api/v1/contracts/audit`
- `GET /api/v1/contracts/status`

## Reglas

- Contratos por `app_id` registrado.
- Payloads se validan contra schema local.
- Cambios incompatibles se detectan.
- Cada creacion/edicion genera version.
- Cada validacion genera auditoria.
- No se conectan aplicaciones reales.
