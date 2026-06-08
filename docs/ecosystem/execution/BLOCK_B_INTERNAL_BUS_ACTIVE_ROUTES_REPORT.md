# BLOCK B - Internal Bus Active Routes Report

Fecha: 2026-06-08

## Estado General

Bloque B activa rutas reales internas del Integration Bus desde CEREBRO hacia departamentos permitidos dentro de `ecosystem-foundation`.

Estas rutas son reales solo como dispatch interno, persistencia local, evento interno, handler seguro y auditoría. No llaman runtimes externos, no ejecutan apps productivas y no conectan APIs externas.

## Bus Interno

Se extendió el Integration Bus con:

- rutas internas CEREBRO -> departamento;
- dispatch interno seguro;
- handlers locales por destino;
- registro de auditoría;
- estado de ruta;
- bloqueo explícito de destinos protegidos;
- endpoints protegidos por sesión de Control Center y rol.

## Rutas Activas

Rutas internas activas:

- `cerebro_to_forja_future`
- `cerebro_to_hermes_future`
- `cerebro_to_creador_de_apis_y_skills_future`
- `cerebro_to_web_factory_future`
- `cerebro_to_buscador_de_tendencias_future`
- `cerebro_to_pluma_future`
- `cerebro_to_lente_future`
- `cerebro_to_marketing_future`
- `cerebro_to_marca_personal_future`
- `cerebro_to_auditoria_future`
- `cerebro_to_nube_future`
- `cerebro_to_sniff_amazon_future`
- `cerebro_to_comercio_autonomo_future`

Todas mantienen:

- `external_connection_enabled=false`
- `runtime_connected=false`
- sin Local Agent
- sin SUNAT
- sin APIs externas
- sin deploy
- sin publicación externa
- sin compra/venta real

## Rutas Bloqueadas

Rutas bloqueadas:

- `cerebro_to_dcft_future`: DCFT protected_no_touch.
- `cerebro_to_sentinela_future`: SENTINELA pending_review/protected.
- `cerebro_to_arsenal_future`: ARSENAL planned/pending_integration.

El dispatch hacia estas rutas devuelve error controlado `403` con `internal_route_blocked`.

## Handlers Internos

Handlers implementados:

- FORJA -> `task_prepared`
- HERMES -> `automation_prepared`
- CREADOR DE APIS Y SKILLS -> `api_skill_spec_prepared`
- WEB FACTORY -> `landing_brief_prepared`
- BUSCADOR DE TENDENCIAS -> `research_request_prepared`
- PLUMA -> `draft_request_prepared`
- LENTE -> `visual_brief_prepared`
- MARKETING -> `campaign_brief_prepared`
- MARCA PERSONAL -> `personal_brand_brief_prepared`
- AUDITORÍA -> `audit_review_created`
- NUBE -> `cloud_review_prepared`
- SNIFF AMAZON -> `amazon_opportunity_review_prepared`
- COMERCIO AUTÓNOMO -> `commerce_plan_prepared`

Cada handler devuelve respuesta controlada y no ejecuta trabajo externo.

## Endpoints

Endpoints protegidos:

- `GET /api/v1/integration-bus/routes`
- `GET /api/v1/integration-bus/routes/{id}`
- `POST /api/v1/integration-bus/dispatch`
- `POST /api/v1/integration-bus/routes/{id}/state`

Roles:

- Lectura: CEO, ADMIN, OPERATOR, AUDITOR.
- Escritura/dispatch: CEO, ADMIN, OPERATOR.
- AUDITOR puede leer, no despachar.

## CEREBRO

CEREBRO ahora puede crear una tarea interna permitida y despacharla por bus interno seguro.

Flujo:

1. CEO/rol autorizado crea tarea CEREBRO.
2. CEREBRO resuelve destino permitido.
3. CEREBRO despacha por ruta interna.
4. Handler local responde con estado preparado.
5. Bus registra evento interno.
6. Bus registra auditoría.
7. Tarea CEREBRO guarda `route_dispatched=true`, `bus_route_id`, `bus_dispatch_id` y `handler_result`.

Destinos protegidos se mantienen bloqueados y no se despachan.

## Cabina

La cabina muestra en la sección CEREBRO:

- Bus interno.
- 13 rutas internas activas.
- 3 rutas bloqueadas.
- último despacho.
- departamentos permitidos.
- DCFT/SENTINELA/ARSENAL no-touch.
- sin runtime externo.

Validación local tras reiniciar servidor en `127.0.0.1:8000`:

- cabina autenticada visible;
- `13 rutas internas activas`;
- `3 bloqueadas`;
- sin loading persistente;
- sin overflow horizontal.

## Tests

Pruebas agregadas/actualizadas:

- dispatch requiere auth;
- dispatch permitido a FORJA;
- dispatch permitido a HERMES;
- dispatch permitido a CREADOR DE APIS Y SKILLS;
- dispatch permitido a WEB FACTORY;
- dispatch permitido a BUSCADOR DE TENDENCIAS;
- dispatch permitido a PLUMA;
- dispatch permitido a LENTE;
- dispatch permitido a MARKETING;
- dispatch permitido a MARCA PERSONAL;
- dispatch permitido a AUDITORÍA;
- dispatch permitido a NUBE documental sin tocar `C:\Users\admin\nube`;
- dispatch permitido a SNIFF AMAZON sin Amazon real;
- dispatch permitido a COMERCIO AUTÓNOMO sin tienda/venta real;
- DCFT bloqueado;
- SENTINELA bloqueado;
- ARSENAL bloqueado;
- AUDITOR lee pero no despacha;
- estado de ruta protegido no se desbloquea;
- CEREBRO guarda dispatch interno en tareas permitidas;
- no hay conexiones externas ni runtime externo.

## Datos Reales Internos

- Backend local.
- DB local del ecosistema.
- Eventos internos.
- Auditoría interna.
- Control Center autenticado.
- Integration Bus interno.

## Datos No Conectados

- DCFT real.
- SENTINELA real.
- ARSENAL real.
- FORJA productiva externa.
- NUBE local externa.
- Local Agent.
- SUNAT real.
- APIs externas.
- proveedores externos.

## Riesgos

- El término "ruta real" puede confundirse con runtime externo. En este bloque significa solo ruta interna dentro de `ecosystem-foundation`.
- Las rutas permitidas preparan trabajo; no ejecutan publicaciones, deploys, ventas, scraping ni código externo.
- Cualquier conexión externa futura requiere bloque separado, governance y aprobación CEO.

## Validación Técnica

Resultado al crear este reporte:

- Suite enfocada de Bloque B: PASS.
- Suite completa: PASS, 300 passed.
- Verificación local de cabina: PASS.

## No Tocado

- DCFT real.
- SENTINELA real.
- ARSENAL real.
- SUNAT real.
- Local Agent.
- FORJA productiva externa.
- NUBE local externa.
- producción.
- Vercel.
- APIs externas reales.

## Cierre

Estado: rutas reales internas del bus activadas para departamentos permitidos; protegidos bloqueados; sin commit, sin push, sin deploy y sin tag.
