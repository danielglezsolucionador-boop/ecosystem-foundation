# Mission Execution Loop - Modelo Operativo Local

Fecha: 2026-06-09

## Propósito

Mission Execution Loop convierte una orden del CEO en una misión interna trazable:

CEO -> CEREBRO -> MISIÓN -> DEPARTAMENTOS -> AUDITORÍA -> FORJA -> AUDITORÍA -> REPORTE CEO.

El loop existe para que CEREBRO avance trabajo interno sin quedarse esperando aprobaciones que no hacen falta. También evita que CEREBRO prometa ejecución real cuando una acción está protegida o requiere dinero, credenciales, proveedor externo o riesgo alto.

## Fuente Operativa

La fuente de misión sigue siendo CEREBRO. El Bloque L reutiliza `cerebro_missions` y añade metadata operativa:

- `assignments`
- `events`
- `audit_reviews`
- `forge_requests`
- `revenue_links`
- `reports`

No se crea una app externa nueva. No se conecta runtime externo.

## Estados

- `created`
- `planned`
- `assigned`
- `in_progress`
- `waiting_department`
- `waiting_audit`
- `waiting_forge`
- `waiting_external_approval`
- `waiting_ceo_approval`
- `needs_clarification`
- `completed`
- `blocked`
- `rejected`
- `failed`

## Autonomía De CEREBRO

CEREBRO puede avanzar sin aprobación CEO cuando la acción es interna y no implica gasto real ni integración externa:

- crear misión interna;
- cambiar prioridad diaria;
- pedir auditoría interna;
- enviar tarea preparada a FORJA interna;
- preparar producto;
- preparar publicación orgánica en cuenta oficial ya configurada;
- preparar checklist de Local Agent sin activarlo;
- preparar deploy controlado con backup, tests y auditoría.

## Decisión CEO Obligatoria

CEREBRO debe detenerse y escalar al CEO cuando aparezca:

- dinero real;
- pago;
- campaña pagada;
- API o herramienta con costo;
- contratación;
- cuenta oficial externa nueva;
- credenciales sensibles;
- riesgo legal, tributario o reputacional alto;
- SUNAT real;
- producto protegido.

En este bloque, DCFT, SENTINELA, ARSENAL, SUNAT y Local Agent permanecen sin ejecución real.

## Flujo

1. CEO crea una orden.
2. CEREBRO registra la misión.
3. CEREBRO infiere departamentos si la orden los menciona.
4. CEREBRO planifica pasos.
5. CEREBRO asigna departamentos.
6. CEREBRO despacha instrucciones internas.
7. AUDITORÍA revisa cuando se solicita.
8. FORJA recibe solicitud preparada si falta construcción.
9. Revenue OS registra enlace si la misión tiene impacto comercial.
10. CEREBRO completa o bloquea y reporta al CEO.

## Endpoints

- `GET /api/v1/missions`
- `POST /api/v1/missions`
- `GET /api/v1/missions/{mission_id}`
- `POST /api/v1/missions/{mission_id}/plan`
- `POST /api/v1/missions/{mission_id}/dispatch`
- `POST /api/v1/missions/{mission_id}/assign`
- `POST /api/v1/missions/{mission_id}/request-audit`
- `POST /api/v1/missions/{mission_id}/send-to-forja`
- `POST /api/v1/missions/{mission_id}/update`
- `POST /api/v1/missions/{mission_id}/complete`
- `POST /api/v1/missions/{mission_id}/block`
- `GET /api/v1/missions/{mission_id}/timeline`
- `GET /api/v1/missions/active`
- `GET /api/v1/missions/reports/daily`

## Reglas Anti-Alucinación

- Si falta objetivo, CEREBRO marca `needs_clarification`.
- Si falta ROI, el impacto queda `unknown`.
- Si hay dinero real, queda `waiting_ceo_approval`.
- Si hay SUNAT real, queda detenido para CEO y otro frente.
- Si se envía a FORJA, queda `prepared_no_external_forja_execution`.
- No se declara venta real.
- No se declara runtime externo.
- No se declara SUNAT activo.
- No se guardan secretos.

## UI

La cabina muestra `Mission Execution Loop` con:

- misiones activas;
- misión prioritaria;
- departamentos;
- pasos;
- auditoría;
- FORJA preparada;
- impacto económico;
- límites de autonomía.

La vista es local, mobile-first y documental/operativa.
