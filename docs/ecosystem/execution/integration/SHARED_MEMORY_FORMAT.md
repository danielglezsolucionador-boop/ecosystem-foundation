# Shared Memory Format

Estado: `BASE_DEFINED`

## 1. Objetivo

Definir formato base para memoria compartida del ecosistema.

## 2. Entrada de Memoria

```json
{
  "memory_id": "uuid",
  "type": "decision|priority|blocker|deliverable|status|audit",
  "source": "app-or-human",
  "app_id": "optional",
  "workspace_id": "optional",
  "content": {},
  "sensitivity": "public|internal|confidential|restricted",
  "created_at": "ISO-8601",
  "version": "1.0"
}
```

## 3. Reglas

- Toda entrada debe tener fuente.
- Toda entrada debe tener timestamp.
- Toda entrada debe tener sensibilidad.
- No almacenar secrets.
- Datos sensibles deben minimizarse.
- Cambios criticos deben auditarse.

## 4. Tipos Iniciales

| Tipo | Uso |
|---|---|
| `decision` | Decisiones ejecutivas |
| `priority` | Prioridades activas |
| `blocker` | Bloqueos |
| `deliverable` | Entregables |
| `status` | Estado de apps |
| `audit` | Eventos relevantes |

