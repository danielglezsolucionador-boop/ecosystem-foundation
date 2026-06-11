# Real World Execution Queue Model

Fecha: 2026-06-10
Fase: S.8
Baseline: `v1-ai-company-operating-system` / `d29455a`, con cambios locales S.1/S.2/S.5 presentes.

## Proposito

S.8 crea una cola local para ordenar futuras acciones reales sin ejecutarlas.

La cola separa:

- acciones preparadas;
- acciones internas;
- acciones que requieren CEO;
- acciones que requieren dinero;
- acciones que requieren credenciales;
- acciones bloqueadas;
- acciones listas para ejecucion manual interna.

## Regla de seguridad

La cola no ejecuta acciones reales.

Prohibido en S.8:

- conectar cuentas;
- pagar;
- publicar;
- lanzar campanas;
- crear cuentas externas;
- conectar APIs externas;
- guardar secretos;
- confirmar ejecucion manual o API.

## Estados

- `prepared`: registro preparado/documental.
- `ready_internal`: puede avanzar como trabajo interno sin dinero, credenciales ni cuenta externa.
- `waiting_ceo`: espera decision CEO.
- `waiting_credentials`: espera credenciales por canal seguro.
- `waiting_paid_approval`: espera aprobacion de dinero/ROI.
- `waiting_account_creation`: espera creacion de cuenta externa aprobada.
- `waiting_legal_review`: espera revision legal/riesgo.
- `blocked`: bloqueado por riesgo, falta de vault, falta de evidencia o decision CEO.
- `executed_manual_confirmed`: estado soportado por modelo, no asignado por S.8.
- `executed_api_confirmed`: estado soportado por modelo, no asignado por S.8.

## Prioridad

La prioridad ordena la cola:

- `critical`: bloquea seguridad, credenciales o runtime externo.
- `high`: impacta ingresos, producto o riesgo legal.
- `medium`: coordina departamentos o backlog comercial.
- `low`: seguimiento o opcion futura.

## Riesgos

- `low`: accion documental/interna.
- `medium`: depende de evidencia.
- `high`: puede afectar marca, gasto o producto.
- `sensitive`: involucra credenciales, dinero, cuenta externa, SUNAT, API o seguridad.

## Aprobaciones

Requiere CEO si la accion implica:

- dinero;
- credenciales;
- cuenta externa;
- revision legal;
- riesgo sensible;
- estado waiting/bloqueado;
- cualquier ejecucion fuera del sistema local.

## Owner interno

Cada item tiene owner interno:

- CEREBRO prioriza y coordina.
- MARKETING prepara ROI o campana.
- WEB FACTORY prepara landing o dominio.
- PLUMA prepara contenido.
- AUDITORIA revisa riesgo/evidencia.
- REVENUE OS vincula impacto economico.
- SNIFF AMAZON / CHIEF AMAZON mantiene radar Amazon.

## Impacto economico

El impacto economico es descriptivo y no confirma ingresos.

Reglas:

- no inventar ventas;
- no inventar margen;
- no inventar ROI;
- si falta evidencia, usar `missing` o `unknown`;
- e-commerce USD 10,000 permanece separado de meta global USD 6,000.

## Evidencia

Cada accion debe indicar evidencia:

- `internal_docs` si deriva de documentos internos;
- `policy` si deriva de regla de seguridad;
- `missing` si falta evidencia real;
- referencia a bloque o reporte si existe.

## Relacion con misiones CEREBRO

CEREBRO puede:

- crear acciones;
- priorizar;
- bloquear;
- pedir aprobacion;
- vincular con Revenue;
- vincular con Workday;
- vincular con Mission Execution Loop.

CEREBRO no puede:

- ejecutar pagos;
- crear cuentas;
- publicar real;
- conectar APIs;
- guardar credenciales;
- confirmar ejecucion real sin evidencia externa autorizada.

## Cierre de item

Un item no se cierra como ejecutado en S.8.

Estados `executed_manual_confirmed` y `executed_api_confirmed` requieren un bloque posterior con:

- autorizacion CEO;
- evidencia verificable;
- auditoria;
- ausencia de secretos;
- reporte.
