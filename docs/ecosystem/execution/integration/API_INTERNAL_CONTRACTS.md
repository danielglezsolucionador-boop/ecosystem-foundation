# API Internal Contracts

Estado: `BASE_DEFINED`

## 1. Objetivo

Definir contratos base para APIs internas del ecosistema.

## 2. Reglas

- Versionado obligatorio.
- Auth obligatorio.
- Permisos por scope.
- No exponer secrets.
- Errores normalizados.
- Request ID obligatorio.

## 3. App Status Contract

```yaml
name: app-status
version: v1
method: GET
path: /api/internal/v1/apps/{app_id}/status
auth: required
scope: ecosystem.status.read
response:
  app_id: string
  health: string
  runtime: string
  updated_at: string
```

## 4. Deliverables Contract

```yaml
name: deliverables-register
version: v1
method: POST
path: /api/internal/v1/deliverables
auth: required
scope: ecosystem.deliverables.write
request:
  title: string
  app_id: string
  file_id: string
  sensitivity: string
response:
  deliverable_id: string
  status: registered
```

## 5. Memory Contract

```yaml
name: memory-entry
version: v1
method: POST
path: /api/internal/v1/memory
auth: required
scope: ecosystem.memory.write
request:
  type: string
  source: string
  content: object
response:
  memory_id: string
  status: stored
```

