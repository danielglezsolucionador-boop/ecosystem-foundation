# AUDITORIA OPERATIONAL MODEL

Fecha local: 2026-06-08

## Proposito

AUDITORIA queda definida como juez operativo interno del ecosistema dentro de `ecosystem-foundation`.

No es app standalone externa. No ejecuta codigo productivo. No conecta runtimes externos. No toca DCFT real, SENTINELA real, ARSENAL real, FORJA productiva externa, NUBE local externa, Local Agent, SUNAT real ni APIs externas.

## Rol

AUDITORIA actua como:

- Juez de calidad.
- Juez de costos.
- Juez de cumplimiento.
- Juez de seguridad.
- Juez de preparacion comercial.
- Bloqueador cuando algo no cumple el estandar CEO.
- Revisor de cabina humana, cabina tecnica y cabina corazon.

AUDITORIA no actua como:

- Ejecutor de codigo.
- Runtime externo.
- Duenio de estrategia.
- Aprobador para desbloquear productos protegidos.
- Sustituto de decision CEO.

## Estados

- `pending_review`: revision creada y en cola.
- `in_review`: revision tomada por AUDITORIA.
- `approved`: cumple para el alcance interno evaluado.
- `observed`: puede continuar solo si atiende observaciones.
- `rejected`: no cumple el estandar solicitado.
- `blocked`: debe detenerse.
- `requires_ceo_decision`: requiere decision explicita del CEO.

## Objetos Auditables

- `cerebro_task`: tareas creadas por CEREBRO.
- `bus_route`: rutas internas del bus.
- `ceo_decision`: decisiones CEO.
- `report`: reportes.
- `cabin`: cabina humana, tecnica o corazon.
- `department`: departamentos internos.
- `protected_product`: DCFT, SENTINELA, ARSENAL u otro protegido.
- `deploy`: preparacion de deploy.
- `risk`: riesgos.

## Criterios

- `visual_quality`: calidad visual.
- `functional_quality`: calidad funcional.
- `security`: seguridad.
- `costs`: costos.
- `human_clarity`: claridad humana.
- `ceo_standard`: cumplimiento del estandar CEO.
- `technical_readiness`: preparacion tecnica.
- `operational_risk`: riesgo operativo.
- `commercial_risk`: riesgo comercial.
- `legal_tax_risk`: riesgo legal/tributario cuando aplique.

## Integracion Con CEREBRO

CEREBRO puede enviar una tarea a AUDITORIA por el bus interno usando la ruta preparada `cerebro_to_auditoria_future`.

Resultado esperado:

- Se crea una review operativa real.
- Se registra audit trail.
- Se registra evento de bus `audit_review_created`.
- No se ejecuta runtime externo.
- No se conecta app standalone.

## Integracion Con Bus Interno

El bus registra:

- `audit_review_created`.
- `audit_decision_recorded`.
- `audit_blocked`.
- `audit_approved`.

Todos los registros mantienen:

- `external_connection_enabled=false`.
- `runtime_connected=false`.
- Sin Local Agent.
- Sin SUNAT.
- Sin APIs externas.

## Governance

Governance exige AUDITORIA aprobada antes de aprobar una conexion futura con `approve-connection`.

La aprobacion de discovery sigue siendo preparacion interna y no abre runtime real.

Si la app o ruta esta protegida, AUDITORIA no puede desbloquearla:

- DCFT sigue protected_no_touch.
- SENTINELA sigue pending_review/protected.
- ARSENAL sigue planned/pending_integration.

## Reglas Anti-Alucinacion

- No decir que una ruta fue ejecutada externamente si solo fue preparada.
- No decir que AUDITORIA aprobo un producto protegido para conexion real.
- No decir que DCFT, SENTINELA o ARSENAL quedaron vivos.
- No decir que FORJA externa o NUBE local fueron tocadas.
- No decir que SUNAT, Local Agent o APIs externas fueron activadas.
- Escalar al CEO cuando una decision excede el alcance interno.
