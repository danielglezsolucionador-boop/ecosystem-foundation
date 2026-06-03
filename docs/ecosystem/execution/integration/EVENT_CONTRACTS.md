# Event Contracts

Estado: `BASE_DEFINED`

## 1. Objetivo

Definir eventos internos base para integraciones asincronicas.

## 2. Evento Base

```json
{
  "event_id": "uuid",
  "event_type": "app.resource.changed",
  "version": "1.0",
  "source_app": "app-name",
  "workspace_id": "workspace-id",
  "created_at": "ISO-8601",
  "payload": {}
}
```

## 3. Eventos Iniciales

| Evento | Uso |
|---|---|
| `app.status.changed` | Cambio de health/runtime |
| `deliverable.created` | Nuevo entregable |
| `memory.entry.created` | Nueva entrada de memoria |
| `task.created` | Nueva tarea |
| `task.completed` | Tarea completada |
| `approval.requested` | Aprobacion humana requerida |
| `backup.failed` | Backup fallido |

## 4. Reglas

- No secrets en eventos.
- Payload minimo necesario.
- Version obligatorio.
- Idempotencia para eventos criticos.
- Auditoria para acciones criticas.

