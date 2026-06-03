# Control Center Permissions

Estado: `BASE_DEFINED`

## 1. Roles

Roles logicos iniciales:

- `CEO`
- `OPERATOR`
- `AUDITOR`
- `VIEWER`

## 2. Matriz

| Accion | CEO | OPERATOR | AUDITOR | VIEWER |
|---|---:|---:|---:|---:|
| Ver estado global | SI | SI | SI | SI |
| Ver apps activas | SI | SI | SI | SI |
| Ver bloqueos | SI | SI | SI | SI |
| Ver auditoria | SI | NO | SI | NO |
| Crear tarea | SI | SI | NO | NO |
| Aprobar accion critica | SI | NO | NO | NO |
| Cambiar permisos | SI | NO | NO | NO |
| Exportar reportes | SI | SI | SI | NO |
| Ver secrets | NO | NO | NO | NO |

## 3. Reglas

- Ningun rol puede ver secrets.
- Acciones criticas requieren auditoria.
- Permisos deben validarse en backend futuro.
- El frontend nunca debe ser la unica barrera.

## 4. Acciones Criticas

- deploy;
- push automatico;
- eliminacion de datos;
- rotacion de secrets;
- cambios de permisos;
- ejecucion de agentes con escritura;
- transmision de datos sensibles.

