# Logging Conventions

Estado: `FOUNDATION_TEMPLATE`

## 1. Objetivo

Definir convenciones de logs para aplicaciones, workers, agentes e integraciones del ecosistema.

## 2. Formato

```json
{
  "timestamp": "ISO-8601",
  "level": "debug|info|warn|error",
  "service": "app-name",
  "environment": "local|staging|production",
  "request_id": "uuid",
  "correlation_id": "uuid",
  "user_id": "optional",
  "workspace_id": "optional",
  "event": "event.name",
  "message": "summary"
}
```

## 3. Niveles

- `debug`: solo local o troubleshooting controlado.
- `info`: eventos normales.
- `warn`: comportamiento inesperado recuperable.
- `error`: fallo que requiere atencion.

## 4. Prohibido

- API keys.
- Passwords.
- Tokens completos.
- Secrets.
- Credenciales externas.
- Documentos sensibles completos.
- Datos financieros o tributarios sin mascara.

## 5. Eventos Recomendados

- `app.start`
- `app.stop`
- `request.received`
- `request.completed`
- `auth.login`
- `auth.denied`
- `storage.write`
- `storage.error`
- `backup.completed`
- `backup.failed`
- `integration.event.published`
- `integration.event.failed`

## 6. Auditoria

- [x] Compatible con observabilidad.
- [x] Compatible con Control Center.
- [x] No contiene secrets.

