# Block 8 - Prepared Bus Routes Report

Fecha/hora local: 2026-06-08 07:52:00 -05:00

## Estado General

Bloque 8 ejecutado localmente para definir rutas futuras del Integration Bus entre CEREBRO y departamentos/productos del ecosistema. Las rutas quedaron como catálogo preparado y bloqueado de solo lectura. No se activó ninguna ruta real, no se ejecutó runtime externo, no se conectó DCFT, SENTINELA, FORJA real, NUBE local, Local Agent, SUNAT ni producción.

## Bus Actual

- Servicios actuales registrados en `integration_bus_services.json`: 20.
- Rutas preparadas nuevas en `integration_bus_prepared_routes.json`: 16.
- `external_connections_enabled=false`.
- Las rutas activas siguen viviendo en la tabla local `integration_bus_routes` y no fueron usadas como mecanismo para estas rutas futuras.
- Las rutas preparadas se exponen como `prepared_routes` en el overview del bus y por `GET /api/v1/integration-bus/prepared-routes`.

## Rutas Definidas

| Ruta | Estado | Uso futuro |
| --- | --- | --- |
| CEREBRO -> FORJA | `prepared_blocked` | construcción, actualización, reparación, creación de producto |
| CEREBRO -> HERMES | `prepared_blocked` | automatizaciones simples, bots, notificaciones, apoyo operativo |
| CEREBRO -> CREADOR DE APIS Y SKILLS | `prepared_blocked` | APIs internas/vendibles, skills, conectores |
| CEREBRO -> WEB FACTORY | `prepared_blocked` | landings, webs, páginas comerciales |
| CEREBRO -> BUSCADOR DE TENDENCIAS | `prepared_blocked` | investigación diaria, señales de mercado, tendencias IA, ciberseguridad, tributación, oportunidades |
| CEREBRO -> PLUMA | `prepared_blocked` | artículos, posts, newsletters, guiones, textos comerciales |
| CEREBRO -> LENTE | `prepared_blocked` | videos, imágenes, visuales, assets creativos |
| CEREBRO -> MARKETING | `prepared_blocked` | campañas, embudos, adquisición, ventas |
| CEREBRO -> MARCA PERSONAL | `prepared_blocked` | contenidos CEO, LinkedIn, autoridad personal |
| CEREBRO -> AUDITORÍA | `prepared_blocked` | calidad, costos, aprobación/bloqueo, auditoría de cabinas |
| CEREBRO -> NUBE | `prepared_blocked` | URLs, deploys, costos, variables, backups, dominios, health checks |
| CEREBRO -> SENTINELA | `protected_blocked` | riesgos, seguridad, protección, incidentes |
| CEREBRO -> DCFT | `protected_no_touch_blocked` | contabilidad, finanzas, tributación, auditoría contable/financiera, producto comercial prioritario |
| CEREBRO -> ARSENAL | `planned_blocked` | APIs, skills, modelos, costos, recomendación de capacidades |
| CEREBRO -> SNIFF AMAZON | `prepared_blocked` | oportunidades Amazon, Buy Box, productos ganadores |
| CEREBRO -> COMERCIO AUTÓNOMO | `prepared_blocked` | e-commerce, venta, operación comercial |

## Por Qué Están Bloqueadas

Todas las rutas tienen:

- `requires_ceo_approval=true`.
- `external_connection_enabled=false`.
- `runtime_connected=false`.
- `blocked_reason` explícito.

DCFT y SENTINELA quedan además protegidos por governance. ARSENAL queda planificado sin runtime ni secretos. NUBE local se mantiene como referencia documental y no se toca.

## Qué Falta Para Activarlas

- Aprobación explícita CEO.
- Contrato técnico por ruta.
- Governance gate por destino.
- Pruebas aisladas sin producción.
- Auditoría de permisos, secretos, costos, rollback y observabilidad.
- Decisión separada para cada runtime real.

## Governance

El Bloque 8 no abre ejecución. Las rutas preparadas no son aceptadas por `POST /api/v1/integration-bus/dispatch`; una ruta preparada como `cerebro_to_dcft_future` devuelve `route_not_found` porque no existe en la tabla de rutas activas.

## Cabina

La cabina local muestra las rutas futuras bloqueadas dentro del panel de Integration Bus, con texto de "Ruta futura bloqueada" y "Sin ejecución real".

## Riesgos

- Confundir rutas preparadas con rutas activas. Mitigación: endpoint separado, estado bloqueado, flags falsos y prueba de no dispatch.
- CEREBRO -> DCFT y CEREBRO -> SENTINELA pueden parecer integraciones reales. Mitigación: estados `protected_no_touch_blocked` y `protected_blocked`.
- NUBE, SNIFF AMAZON y COMERCIO AUTÓNOMO requieren revisión específica antes de cualquier runtime futuro.

## No Tocado

- DCFT real.
- SENTINELA real.
- FORJA productiva.
- NUBE local.
- Local Agent.
- SUNAT real.
- Producción pública.
- Runtimes externos.
- Rutas reales del bus.
- Push, deploy y commit.

## Validaciones

- `node --check apps/web/control-center/assets/app.js`: PASS.
- `python -m compileall apps/api api scripts -q`: PASS.
- `$env:PYTHONPATH="apps/api"; pytest -q`: PASS, 263 passed.
- `python scripts/validate_v1.py`: PASS, incluye compileall, pytest, import API y secret scan.
- `git diff --check`: PASS.
- Secret scan adicional case-insensitive para `sk-*`: PASS.

## Siguiente Bloque Recomendado

Bloque 9: matriz CEO de activación por ruta, priorizando qué destino podría pasar primero a contrato técnico sin runtime real.
