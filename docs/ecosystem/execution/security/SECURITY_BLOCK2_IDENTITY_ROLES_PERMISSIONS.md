# Security Block 2: Identity, Roles and Permissions

Estado: `IMPLEMENTED_LOCAL`

## 1. Objetivo

Crear la base de seguridad interna de la Plataforma del Ecosistema antes de
conectar aplicaciones reales.

## 2. Modulos Implementados

- User Registry.
- Role Registry.
- Permission Registry.
- Policy Registry.
- Access Control Engine.
- Service Identity.
- API Key Placeholder seguro.
- Session Model.
- Permission Audit.
- Access Validation.

## 3. Roles Oficiales

| Rol | Scope | Apps externas | Secrets |
| --- | --- | --- | --- |
| `CEO` | executive_control | NO | NO |
| `ADMIN` | local_platform_admin | NO | NO |
| `OPERATOR` | local_operations | NO | NO |
| `AUDITOR` | audit_read_only | NO | NO |
| `SERVICE` | internal_service_identity | NO | NO |

## 4. Permisos Minimos

- `read:control_center`
- `write:control_center`
- `read:apps`
- `write:apps`
- `read:memory`
- `write:memory`
- `read:events`
- `write:events`
- `read:audit`
- `write:audit`
- `read:observability`
- `write:observability`
- `manage:system`

Permisos adicionales de seguridad:

- `read:permissions`
- `write:permissions`

## 5. Endpoints

| Endpoint | Proposito |
| --- | --- |
| `GET /api/v1/security` | Vista consolidada de seguridad. |
| `GET /api/v1/security/users` | Principales humanos reservados. |
| `GET /api/v1/security/roles` | Role Registry. |
| `GET /api/v1/security/roles/{role_id}` | Detalle de rol o 404 controlado. |
| `GET /api/v1/security/permissions` | Permission Registry. |
| `GET /api/v1/security/policies` | Policy Registry. |
| `GET /api/v1/security/service-identities` | Identidades de servicio. |
| `GET /api/v1/security/api-key-placeholders` | Placeholders sin secreto real. |
| `GET /api/v1/security/session-model` | Modelo de sesion futuro. |
| `POST /api/v1/security/validate-access` | Validacion de acceso con auditoria. |
| `GET /api/v1/security/audit` | Historial de validaciones. |

## 6. Persistencia

Tabla creada bajo la capa database existente:

- `security_access_audit_events`

Se usa para registrar:

- rol evaluado;
- permiso evaluado;
- recurso;
- resultado;
- razon;
- timestamp.

No guarda secrets.

## 7. Politicas

- `no_secret_exposure`
- `external_app_isolation`
- `critical_action_human_approval`
- `audit_all_access_validation`

## 8. Riesgos

- Login real no implementado todavia.
- Sesiones reales no emitidas todavia.
- API keys reales requieren secret manager futuro.
- Cambios a roles deben mantenerse en backend, no solo frontend.

## 9. Dependencias

- Database layer local.
- Pydantic schemas.
- FastAPI.
- Matrices JSON controladas en repositorio.
- Audit persistence.

## 10. Auditoria Interna

Validaciones ejecutadas:

- `python -m compileall apps/api/app -q`
- `python -m pytest apps/api/tests -q`

Resultado inicial:

- compileall: `PASS`
- pytest: `75 passed`

## 11. Checklist

- [x] Roles minimos implementados.
- [x] Permisos minimos implementados.
- [x] Politicas implementadas.
- [x] Validacion positiva.
- [x] Validacion negativa.
- [x] Bloqueo de recurso externo.
- [x] Auditoria por intento de acceso.
- [x] API key placeholders sin material secreto.
- [x] Session model preparado sin emitir sesiones.
- [x] Compatibilidad `/api/v1/permissions`.

## 12. Recomendaciones

Siguiente bloque recomendado:

`BLOCK_3_SHARED_ECOSYSTEM_MEMORY`

Antes de avanzar:

1. Crear rama de backup.
2. Registrar recovery point.
3. Ejecutar pruebas completas.
