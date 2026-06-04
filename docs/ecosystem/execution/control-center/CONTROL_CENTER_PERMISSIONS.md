# Control Center Permissions

Estado: `SECURITY_BLOCK_2_IMPLEMENTED`

## 1. Roles

Roles logicos iniciales:

- `CEO`
- `ADMIN`
- `OPERATOR`
- `AUDITOR`
- `SERVICE`

## 2. Matriz

| Accion | CEO | ADMIN | OPERATOR | AUDITOR | SERVICE |
|---|---:|---:|---:|---:|---:|
| Ver estado global | SI | SI | SI | SI | SI |
| Ver apps activas | SI | SI | SI | SI | SI |
| Ver bloqueos | SI | SI | SI | SI | SI |
| Ver auditoria | SI | SI | SI | SI | NO |
| Crear tarea interna futura | SI | SI | SI | NO | NO |
| Aprobar accion critica | SI | NO | NO | NO | NO |
| Cambiar permisos | SI | NO | NO | NO | NO |
| Exportar reportes futuros | SI | SI | SI | SI | NO |
| Ver secrets | NO | NO | NO | NO | NO |

## 3. Reglas

- Ningun rol puede ver secrets.
- Acciones criticas requieren auditoria.
- Permisos se validan en backend mediante `/api/v1/security/validate-access`.
- El frontend nunca debe ser la unica barrera.

## 4. Acciones Criticas

- deploy;
- push automatico;
- eliminacion de datos;
- rotacion de secrets;
- cambios de permisos;
- ejecucion de agentes con escritura;
- transmision de datos sensibles.
