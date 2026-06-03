# Healthcheck Contract

Estado: `FOUNDATION_TEMPLATE`

## 1. Objetivo

Definir el contrato minimo de salud operacional para aplicaciones del ecosistema.

## 2. Endpoints Recomendados

| Endpoint | Uso | Publico |
|---|---|---:|
| `/health` | Estado basico del servicio | SI |
| `/readiness` | Dependencias listas | Controlado |
| `/runtime/status` | Estado operativo detallado | Controlado |
| `/version` | Version y commit | Controlado |

## 3. `/health`

Respuesta minima:

```json
{
  "status": "ok",
  "service": "app-name",
  "timestamp": "ISO-8601"
}
```

## 4. `/runtime/status`

Respuesta minima:

```json
{
  "status": "operational|degraded|blocked",
  "service": "app-name",
  "environment": "local|staging|production",
  "version": "string",
  "commit": "string",
  "database": "connected|not_required|error",
  "storage": "connected|not_required|error",
  "provider": "ready|not_required|error",
  "memory": "connected|not_required|error",
  "updated_at": "ISO-8601"
}
```

## 5. Reglas

- `health` no debe filtrar secrets.
- `runtime/status` no debe exponer URLs con credenciales.
- Dependencias criticas deben indicar estado.
- Debe existir timestamp.
- Debe existir version o commit cuando sea posible.

## 6. Auditoria

- [x] Contrato no crea codigo.
- [x] No asume stack.
- [x] Compatible con Control Center.

