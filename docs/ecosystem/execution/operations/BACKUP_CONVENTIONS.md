# Backup Conventions

Estado: `FOUNDATION_TEMPLATE`

## 1. Objetivo

Definir convenciones base para backups del ecosistema.

## 2. Alcance

Respaldar:

- bases de datos;
- archivos;
- memoria operativa;
- entregables;
- auditoria;
- configuracion no secreta.

## 3. Reglas

- No guardar backups solo en disco efimero.
- No incluir secrets en backups documentales.
- Cifrar backups cuando el proveedor lo permita.
- Separar backup y runtime.
- Registrar exito o fallo.
- Probar restore periodicamente.

## 4. Metadata de Backup

```json
{
  "backup_id": "uuid",
  "source": "database|files|memory|audit",
  "environment": "staging|production",
  "created_at": "ISO-8601",
  "status": "completed|failed",
  "size_bytes": 0,
  "retention_until": "ISO-8601",
  "restore_tested_at": "ISO-8601|null"
}
```

## 5. RPO / RTO

Inicial:

- RPO: 24 horas.
- RTO: 8 horas para servicios criticos.

Objetivo 3 anos:

- RPO menor a 1 hora.
- RTO menor a 1 hora.

## 6. Auditoria

- [x] No crea backups reales.
- [x] No asume proveedor.
- [x] Compatible con Control Center.

