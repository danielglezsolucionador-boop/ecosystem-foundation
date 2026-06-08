# ECOSYSTEM Governance Rules V1

Estado: reglas maestras documentales
Fecha: 2026-06-06

## CEREBRO puede decidir

- Prioridades recomendadas.
- Siguiente paso minimo.
- Riesgo principal.
- Que no tocar.
- Si una propuesta debe ir a AUDITORIA, NUBE, SENTINELA o FORJA.

## CEREBRO no puede decidir

- Push/deploy.
- Tareas reales.
- Local Agent.
- SUNAT real.
- Conexion runtime.
- Uso de secretos.
- Cambios productivos.

## FORJA puede ejecutar

- Documentos.
- Entregables.
- Apps o cambios locales aprobados.
- Pruebas locales.
- Tareas reales solo con aprobacion CEO y alcance claro.

## FORJA no puede ejecutar

- Tareas reales sin CEO.
- Local Agent sin CEO.
- Productivo sin auditoria.
- DCFT/FORJA/CEREBRO/SENTINELA productivos fuera de alcance.
- Acciones con secretos no autorizados.

## AUDITORIA bloquea

- Falta de evidencia.
- Costos no revisados.
- Cabina humana confusa.
- Tests fallando.
- Secretos expuestos.
- Conexiones no aprobadas.
- Diferencia entre estado declarado y estado real.

## SENTINELA bloquea

- Riesgos de seguridad.
- Uso de credenciales reales en chat/codigo/reportes.
- Acciones ofensivas.
- Permisos excesivos.
- Exposicion de datos sensibles.
- Local Agent sin aprobacion.

## NUBE controla

- URLs.
- Deploys.
- Proveedores.
- Costos.
- Backups.
- Variables.
- Dominios.
- Health cloud.

NUBE no toca secretos sin autorizacion.

## Requiere aprobacion CEO

- Tareas reales FORJA.
- Local Agent.
- SUNAT real.
- Integrar DCFT.
- Conectar runtime externo.
- Publicar contenido o campanas reales.
- Activar comercio, pagos o ventas.

## Requiere aprobacion CTO

- Rutas reales del Integration Bus.
- Contratos runtime.
- Cambios backend compartidos.
- Secret management.
- Deploys productivos.
- Integraciones con proveedores externos.

## Apps no-touch

- DCFT productivo.
- FORJA productivo.
- CEREBRO productivo.
- SENTINELA productivo.
- NUBE local hasta auditoria.

## Apps que pueden documentarse

- NUBE.
- SENTINELA.
- CREADOR DE APIS.
- SNIFF AMAZON.
- DCFT como protected_no_touch.
- Apps discovery existentes.

## Apps que pueden conectarse despues

Solo despues de contrato, auditoria, observability, secrets, pruebas y aprobacion:

- CEREBRO.
- FORJA.
- HERMES.
- PLUMA.
- LENTE.
- WEB FACTORY.
- MARKETING.
- MARCA PERSONAL.
- BUSCADOR DE TENDENCIAS.
- SNIFF AMAZON.
- COMERCIO AUTONOMO.
- CREADOR DE APIS.
- NUBE.
- SENTINELA.
- DCFT.

## Reglas duras

- No produccion sin auditoria.
- No tareas reales FORJA sin CEO.
- No Local Agent sin CEO.
- No SUNAT real sin CEO.
- No runtime externo sin aprobacion.
- No variables/secrets sin NUBE/SENTINELA.
- No app pasa a "operativa" solo por tener tab.
- No Sniff Amazon mezclado con Comercio Autonomo.
- No push/deploy sin autorizacion CEO/CTO.

## Cierre

Estas reglas gobiernan el paso de documentacion a ejecucion real.
