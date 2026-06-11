# Real World Connection Readiness Model

Fecha: 2026-06-10
Baseline: `v1-ai-company-operating-system`
Commit base: `d29455a`

## Proposito

Esta fase prepara el mapa de conexiones reales del ecosistema sin ejecutar acciones externas, sin crear cuentas, sin hacer pagos, sin publicar contenido real y sin guardar secretos.

CEREBRO puede preparar, auditar, proponer, priorizar y convertir brechas en misiones internas. CEREBRO no puede ejecutar dinero real, campanas pagadas, cuentas externas nuevas, APIs con costo, credenciales sensibles, SUNAT real ni publicacion real en cuentas no confirmadas sin aprobacion CEO.

## Tipos de conexion

- `social_account`
- `publishing_account`
- `analytics_account`
- `payment_provider`
- `marketplace`
- `app_store`
- `cloud_provider`
- `external_api`
- `marketing_platform`
- `ecommerce_platform`
- `security_feed`
- `tax/regulatory_source`
- `content_tool`
- `ai_tool`
- `email_tool`
- `crm_tool`

## Estados permitidos

- `unknown`: no hay evidencia suficiente.
- `not_connected`: se sabe que no esta conectado.
- `prepared`: puede continuar como preparacion local/documental.
- `needs_ceo_definition`: falta definicion del CEO.
- `needs_credentials`: requiere credenciales por canal seguro.
- `needs_paid_approval`: requiere aprobacion por dinero real.
- `needs_account_creation`: crear cuenta externa requiere CEO.
- `needs_legal_review`: requiere revision legal, tributaria o de terminos.
- `connected_manual`: conexion manual confirmada con evidencia.
- `connected_api`: conexion API confirmada con evidencia.
- `blocked`: bloqueado por riesgo, falta de evidencia o decision.
- `deprecated`: no se recomienda usar.

## Niveles de riesgo

- `low`: preparacion documental o local sin datos sensibles.
- `medium`: requiere definicion o evidencia, pero no toca dinero o secreto.
- `high`: puede afectar marca, datos, terminos, cuenta externa o operacion.
- `sensitive`: credenciales, pagos, datos sensibles, seguridad, tienda o regulatorio.

## Reglas de aprobacion CEO

Requiere CEO:

- dinero real;
- pagos;
- campana pagada;
- cuenta externa nueva;
- credenciales;
- herramienta/API con costo;
- conexion legal/tributaria;
- publicacion real en cuenta no confirmada;
- acceso a datos sensibles.

No requiere CEO:

- inventario;
- propuesta;
- documentacion;
- simulacion;
- preparacion de conexion;
- contenido organico preparado;
- auditoria;
- mision interna;
- tarea FORJA interna;
- fallback `prepared` o `unknown`.

## Reglas anti-alucinacion

- No declarar `connected_*` sin evidencia.
- No declarar cuenta existente si el CEO no la confirmo.
- No declarar publicacion real si la cuenta no esta confirmada y conectada.
- No declarar venta, ingreso, lead, conversion o ROI real sin evidencia.
- No guardar passwords, tokens, API keys, client secrets, Clave SOL ni credenciales en docs, frontend, logs o reportes.
- Si falta informacion, usar `unknown`, `needs_ceo_definition` o `prepared`.

## Acciones internas permitidas

- `mark-prepared`: deja la conexion como preparacion interna sin ejecutar fuera.
- `request-ceo-definition`: escala definicion al CEO.
- `request-approval`: registra que una accion externa necesita aprobacion.
- `status`: resume conteos para CEREBRO y Centro CEO.
- `approval-needed`: lista conexiones que no deben avanzar solas.
- `risks`: lista conexiones `high` o `sensitive`.

## Acciones prohibidas en S.1

- conectar cuenta externa real;
- crear cuenta externa;
- cobrar;
- lanzar campana pagada;
- publicar en redes;
- activar SUNAT real;
- activar App Store o Play Store;
- conectar API externa con costo;
- tocar DCFT real;
- tocar SENTINELA real;
- tocar FORJA externa;
- tocar `C:\Users\admin\nube`.

## Integracion con CEREBRO

CEREBRO debe leer:

- conexiones inventariadas;
- conexiones `prepared`;
- conexiones `unknown`;
- conexiones que requieren CEO;
- conexiones que requieren dinero;
- conexiones que requieren credenciales;
- conexiones sensibles;
- bloqueos que impiden Publishing, Marketing, Revenue, E-commerce, DCFT, SENTINELA, Web Factory o APIs/Skills.

CEREBRO debe responder con lenguaje ejecutivo: preparar, auditar, pedir definicion, pedir aprobacion o mantener bloqueado. No debe decir que ejecuto una conexion real.

## Integracion con Centro CEO

Centro CEO debe mostrar:

- total de conexiones;
- `connected`;
- `prepared`;
- `unknown`;
- `needs CEO`;
- `needs credentials`;
- `needs paid approval`;
- riesgos altos/sensibles;
- siguiente accion recomendada.

## Criterio de cierre S.1

S.1 queda valido si:

- existe registro inicial;
- endpoints protegidos responden;
- Centro CEO puede leer resumen;
- cabina muestra panel ligero;
- tests confirman que no hay secretos ni ejecucion externa;
- capturas locales no muestran overflow ni mojibake nuevo;
- no hubo commit, push, deploy ni tag.
