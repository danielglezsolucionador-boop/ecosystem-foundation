# Production Auth Environment Setup

Fecha: 2026-06-06

## Objetivo

Habilitar validacion autenticada segura en produccion para `ecosystem-foundation` sin hardcodear credenciales, sin subir passwords reales y sin crear backdoors.

Produccion objetivo:

```text
https://ecosystem-foundation.vercel.app
```

Commit productivo esperado:

```text
9d655d4 feat: integrate block 2 discovery profiles
```

## Diagnostico

El backend ya incluye bootstrap seguro de usuario CEO inicial:

- tabla: `control_center_users`
- sesiones: `control_center_sessions`
- auditoria: `control_center_session_audit`
- hash de password: PBKDF2-SHA256
- rotacion: si cambian las variables `CONTROL_CENTER_ADMIN_*`, el usuario CEO se actualiza de forma controlada
- sin password por defecto
- sin credenciales en repositorio

El error:

```json
{"detail":{"error":"session_required"}}
```

significa que el endpoint protegido no recibio token Bearer valido. Para obtener token primero debe existir un usuario CEO productivo y se debe ejecutar login contra:

```text
POST /api/v1/auth/login
```

## Variables obligatorias en Vercel

Configurar estas variables en el proyecto Vercel `ecosystem-foundation`.

| Variable | Entorno | Uso | Ejemplo seguro |
| --- | --- | --- | --- |
| `CONTROL_CENTER_ADMIN_EMAIL` | Production | Email del usuario CEO inicial que podra iniciar sesion. | `ceo@example.com` |
| `CONTROL_CENTER_ADMIN_PASSWORD` | Production | Password fuerte del usuario CEO inicial. Se guarda hasheado; nunca se debe commitear. | `<generado-en-password-manager-32+chars>` |
| `CONTROL_CENTER_ADMIN_NAME` | Production | Nombre visible del usuario CEO. | `CEO Ecosystem` |

Tambien deben existir las variables operativas ya usadas por produccion:

| Variable | Entorno | Uso | Ejemplo seguro |
| --- | --- | --- | --- |
| `DATABASE_URL` | Production | PostgreSQL productivo persistente. | `<postgresql-url-vercel>` |
| `ECOSYSTEM_API_ENVIRONMENT` | Production | Entorno runtime. | `staging` o `production` |
| `ECOSYSTEM_API_SERVICE_NAME` | Production | Nombre del servicio. | `ecosystem-foundation-api` |
| `ECOSYSTEM_API_VERSION` | Production | Version publica. | `0.1.0` |
| `ECOSYSTEM_API_COMMIT` | Production | Commit productivo esperado. | `9d655d4` |
| `ECOSYSTEM_API_DEBUG` | Production | Debug desactivado. | `false` |

## Procedimiento Vercel

1. Abrir Vercel.
2. Ir a Project `ecosystem-foundation`.
3. Entrar a Settings -> Environment Variables.
4. Crear o actualizar:
   - `CONTROL_CENTER_ADMIN_EMAIL`
   - `CONTROL_CENTER_ADMIN_PASSWORD`
   - `CONTROL_CENTER_ADMIN_NAME`
5. Scope: `Production`.
6. No usar credenciales locales.
7. No guardar el password en archivos, issues, commits ni reportes.
8. Redeployar el commit productivo `9d655d4` o disparar un redeploy de Production para que el runtime lea las variables.

## Como se crea el usuario

El backend ejecuta `ensure_auth_schema()` al recibir login o al resolver una sesion. Ese flujo llama `bootstrap_initial_admin()`.

Resultado esperado despues del redeploy:

1. `POST /api/v1/auth/login` con el email/password productivo devuelve `200`.
2. El token devuelto empieza con `ccs_`.
3. `GET /api/v1/auth/me` con `Authorization: Bearer <token>` devuelve el usuario CEO.
4. Los endpoints protegidos dejan de responder `session_required`.

## Validacion segura desde maquina local

No escribir credenciales en el repo. Usar variables de entorno temporales.

PowerShell:

```powershell
$env:CONTROL_CENTER_ADMIN_EMAIL="ceo@example.com"
$env:CONTROL_CENTER_ADMIN_PASSWORD="<password-productivo-real-no-commitear>"
python scripts/production_block2_validate.py
Remove-Item Env:\CONTROL_CENTER_ADMIN_EMAIL
Remove-Item Env:\CONTROL_CENTER_ADMIN_PASSWORD
```

El validador no imprime el password ni el token.

## Endpoints que debe validar

Publicos:

- `/`
- `/health`
- `/readiness`
- `/runtime/status`
- `/version`
- `/api/v1/apps`
- `/api/v1/integration-bus/status`
- `/api/v1/contracts/status`
- `/api/v1/integrations/apps/{app_id}`
- `/api/v1/integrations/apps/{app_id}/discovery`

Protegidos con Bearer token:

- `/api/v1/auth/me`
- `/api/v1/control-center`
- `/api/v1/control-center/apps`
- `/api/v1/governance`
- `/api/v1/governance/integration-gates`
- `/api/v1/audit`
- `/api/v1/observability/status`

Apps Bloque 2:

- `web_factory`
- `marketing`
- `marca_personal`

Cada app debe seguir con:

```text
integration_status=prepared_for_discovery
external_connection_enabled=false
```

## Criterio para tag

Crear `v1-block-2-web-marketing-brand` solo cuando:

- login productivo PASS
- `/api/v1/auth/me` PASS
- Control Center autenticado PASS
- Governance autenticado PASS
- Audit autenticado PASS
- Observability autenticado PASS
- Web Factory discovery PASS
- Marketing discovery PASS
- Marca Personal discovery PASS
- no hay credenciales expuestas
- tests locales y secret scan PASS

Hasta que esos puntos pasen, el tag queda bloqueado.
