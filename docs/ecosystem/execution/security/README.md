# Security Foundation

Estado: `BLOCK_2_SECURITY_FOUNDATION_IMPLEMENTED`

## Objetivo

Crear la base interna de identidad, roles, permisos y validacion de acceso para
la Plataforma del Ecosistema.

## Alcance

- User Registry local reservado.
- Role Registry.
- Permission Registry.
- Policy Registry.
- Access Control Engine.
- Service Identity.
- API Key Placeholder seguro.
- Session Model preparado.
- Permission Audit persistente.
- Access Validation.

## Endpoints

- `GET /api/v1/security`
- `GET /api/v1/security/users`
- `GET /api/v1/security/roles`
- `GET /api/v1/security/roles/{role_id}`
- `GET /api/v1/security/permissions`
- `GET /api/v1/security/policies`
- `GET /api/v1/security/service-identities`
- `GET /api/v1/security/api-key-placeholders`
- `GET /api/v1/security/session-model`
- `POST /api/v1/security/validate-access`
- `GET /api/v1/security/audit`

## Reglas

- No hay login real todavia.
- No se emiten sesiones reales todavia.
- No se almacenan API keys reales.
- Ningun rol puede ver secrets.
- Ningun rol puede tocar aplicaciones externas.
- Todo intento de validacion de acceso queda auditado.
