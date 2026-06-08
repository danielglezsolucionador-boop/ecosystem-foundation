# BLOCK 10 - Auditoría fuerte de rutas e integración departamental

Fecha/hora local: 2026-06-08 08:09:30 -05:00

## Estado general

PASS local con corrección aplicada.

El Bloque 10 intentó romper el ecosistema local preparado en los Bloques 7, 8 y 9. El objetivo fue confirmar que DCFT, SENTINELA, ARSENAL, rutas preparadas del bus, FORJA real, NUBE local, Local Agent y SUNAT real no puedan ejecutarse ni conectarse desde la cabina o desde endpoints locales.

No hubo producción, push, deploy ni runtime externo.

## Pruebas ejecutadas

- Inspección de rama y cambios locales.
- Revisión de `apps_registry.json` para DCFT, SENTINELA y ARSENAL.
- Revisión de `integration_bus_prepared_routes.json`.
- Intentos de discovery real sobre DCFT, SENTINELA y ARSENAL.
- Intentos de conexión sobre DCFT, SENTINELA y ARSENAL.
- Intentos de despacho sobre rutas preparadas CEREBRO -> DCFT, SENTINELA, ARSENAL, FORJA y NUBE.
- Evaluación de política para conectar runtime de ARSENAL.
- Pruebas de seguridad local sin sesión y con token inválido.
- Revisión de claims falsos en la cabina.
- Capturas exactas mobile y desktop.
- Validaciones técnicas completas.

## Rupturas y resultado

| Intento | Resultado esperado | Resultado observado |
| --- | --- | --- |
| Discovery real DCFT | Bloqueo seguro | `protected_app_discovery_blocked` |
| Conexión DCFT | Bloqueo seguro | `protected_app_connection_blocked` |
| Ruta CEREBRO -> DCFT | No despachable | `route_not_found` |
| Activación/discovery SENTINELA | Bloqueo seguro | `protected_app_discovery_blocked` |
| Conexión SENTINELA | Bloqueo seguro | `protected_app_connection_blocked` |
| Ruta CEREBRO -> SENTINELA | No despachable | `route_not_found` |
| Discovery ARSENAL | Bloqueo seguro | `planned_app_discovery_blocked` |
| Conexión/runtime ARSENAL | Bloqueo seguro | `planned_app_connection_blocked` |
| Ruta CEREBRO -> ARSENAL | No despachable | `route_not_found` |
| Rutas preparadas del bus | Bloqueadas | Todas mantienen `requires_ceo_approval=true`, `external_connection_enabled=false`, `runtime_connected=false` |
| Sin sesión | 401 | PASS |
| Token inválido | 401 | PASS |

## Correcciones aplicadas

Se corrigió Governance para que ARSENAL quede bloqueado por política de planificación:

- `PLANNED_BLOCKED_APP_IDS = {"arsenal"}`.
- ARSENAL mantiene `protected=false`, pero su gate queda `blocked`.
- Discovery de ARSENAL devuelve `planned_app_discovery_blocked`.
- Conexión/runtime de ARSENAL devuelve `planned_app_connection_blocked`.
- La política de Governance declara que ARSENAL no puede descubrirse, conectarse ni ejecutarse en este bloque.

No se tocó la UI porque las capturas no exigieron cambios visuales.

## Claims falsos bloqueados

La suite de regresión valida que la cabina no afirme:

- DCFT integrado.
- SENTINELA activo en producción.
- FORJA real conectada.
- NUBE conectada.
- ARSENAL funcionando como runtime.
- Rutas reales del bus activas.
- Apps externas conectadas.
- SUNAT activo.
- Activación de Local Agent.
- CEREBRO ejecutando código real.

## Datos reales

- Login local.
- Sesión local.
- Cabina local.
- App Registry local.
- Governance local.
- Integration Bus local.
- Rutas preparadas como datos/documentación local.
- Capturas locales exactas.
- Tests locales.

## Datos preparados

- CEREBRO como coordinador documental/simulado.
- Flujos departamentales simulados.
- FORJA visual/preparada.
- SENTINELA representado y pendiente/protegido.
- ARSENAL planificado.
- Bus con rutas preparadas no despachables.

## Datos protegidos / no touch

- DCFT real: `protected_no_touch`, sin SUNAT real, sin credenciales, sin runtime externo.
- SENTINELA real: `pending_review/protected`, sin runtime real.
- FORJA productiva: no tocada.
- NUBE local: no tocada.
- Local Agent: no activado.
- SUNAT real: no activado.
- Producción: no tocada.

## Visual

Capturas generadas:

- `outputs/ecosystem-block-10-audit-mobile-390x844.png`
- `outputs/ecosystem-block-10-audit-desktop-1280x720.png`

Resultado visual:

- Mobile 390x844: PASS.
- Desktop 1280x720: PASS.
- Console errors: 0.
- Overflow horizontal: NO.
- Loading persistente: NO.
- Textos críticos cortados: NO.
- Claims falsos: NO.
- Bottom nav visible en móvil: SÍ.

## Validaciones

Ejecutadas:

- `node --check work/block_10_visual_audit.mjs`: PASS.
- `node work/block_10_visual_audit.mjs`: PASS.
- `node --check apps/web/control-center/assets/app.js`: PASS.
- `$env:PYTHONPATH="apps/api"; pytest -q apps/api/tests/test_governance.py apps/api/tests/test_block_10_routes_departments_rupture.py`: PASS, 34 passed.
- `python -m compileall apps/api api scripts -q`: PASS.
- `$env:PYTHONPATH="apps/api"; pytest -q`: PASS, 270 passed.
- `python scripts/validate_v1.py`: PASS, incluye compileall, pytest, import API y secret scan PASS.
- `git diff --check`: PASS.

## Riesgos

- El working tree contiene cambios acumulados de bloques anteriores; no se hizo commit para evitar mezclar frentes.
- Las rutas preparadas existen como datos locales y deben mantenerse fuera de cualquier dispatcher real.
- Cualquier futuro runtime de ARSENAL, SENTINELA o DCFT debe exigir aprobación CEO, contrato técnico, pruebas aisladas y nueva auditoría.

## Recomendación

Mantener Bloque 10 como auditoría local de ruptura PASS cuando cierre la validación técnica completa. El siguiente bloque debería revisar contratos preparados y límites de ejecución antes de permitir cualquier integración real futura.
