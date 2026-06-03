# Report and Deliverable Formats

Estado: `BASE_DEFINED`

## 1. Reporte Tecnico

```yaml
report:
  id: uuid
  title: string
  app_id: string
  phase: string
  status: PASS|PARTIAL|FAIL|BLOCKED
  created_at: ISO-8601
  summary: string
  evidence:
    - string
  risks:
    - string
  next_action: string
```

## 2. Entregable

```yaml
deliverable:
  id: uuid
  title: string
  app_id: string
  type: document|report|artifact|export
  file_id: string
  sensitivity: public|internal|confidential|restricted
  created_by: string
  created_at: ISO-8601
  status: draft|validated|approved|archived
```

## 3. Reglas

- Todo entregable debe tener owner.
- Todo entregable debe tener sensibilidad.
- Todo archivo persistente debe tener `file_id`.
- No incluir secrets.
- Reportes de auditoria deben incluir evidencia.

