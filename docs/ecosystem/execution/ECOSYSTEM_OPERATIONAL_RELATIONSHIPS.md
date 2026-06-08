# ECOSYSTEM Operational Relationships V1

Estado: mapa operativo documental
Fecha: 2026-06-06

## Regla base

Una relacion en este documento no activa runtime real. Cada flujo indica si es real ahora o futuro.

## Flujos

| Flujo | Envia | Recibe | Puede ordenar | No puede ordenar | Estado | Requiere para activarse |
| --- | --- | --- | --- | --- | --- | --- |
| CEO -> CEREBRO | Objetivo, prioridad, decision | Estado, riesgo, proximo paso | Analisis, recomendacion | Ejecucion directa | Futuro runtime; documental ahora | Sesion CEO y contrato CEREBRO |
| CEREBRO -> FORJA | Tarea aprobada, alcance | Estado de construccion | Preparar tarea futura | Tareas reales sin CEO | Futura | Aprobacion CEO, contrato, Local Agent si aplica |
| FORJA -> AUDITORIA | Entregable, pruebas, evidencia | Observaciones, bloqueo/aprobacion | Revision de calidad | Aprobarse a si misma | Futura | Flujo de tareas aprobado |
| AUDITORIA -> CEREBRO | Riesgo, costo, calidad | Contexto y prioridad | Bloquear/recomendar | Construccion | Interna/futura | Evidencia auditada |
| SENTINELA -> CEREBRO | Riesgo, incidente, permiso | Contexto ejecutivo | Escalar alerta | Ejecutar ofensiva | Futura | Integracion defensiva aprobada |
| SENTINELA -> FORJA | Bloqueo, regla, limite | Tarea propuesta | Bloquear tarea insegura | Construir codigo | Futura | Politicas defensivas |
| NUBE -> CEREBRO | URLs, deploy, costos, backups | Prioridades cloud | Recomendar accion cloud | Cambiar secretos por si sola | Documental/futura | Auditoria NUBE |
| NUBE -> AUDITORIA | Evidencia cloud, costos | Revision | Solicitar auditoria | Aprobar cambios sola | Futura | Registro NUBE |
| HERMES -> CEREBRO | Mensajes/notificaciones preparadas | Prioridad/comando | Preparar comunicacion | Enviar real sin aprobacion | Futura | Runtime Hermes validado |
| PLUMA -> MARKETING | Piezas, copies, borradores | Campana/brief | Proponer contenido | Publicar real | Futura | Aprobacion contenido |
| LENTE -> MARKETING | Analisis, senales, calendario | Objetivos de campana | Recomendar insight | Consultar fuentes externas sin permiso | Futura | Fuentes aprobadas |
| WEB FACTORY -> NUBE | Sitio listo, requerimientos deploy | URL, dominio, estado cloud | Solicitar deploy | Deploy real sin aprobacion | Futura | NUBE auditada, CEO/CTO |
| CREADOR DE APIS -> Integration Bus | Contratos API, endpoints propuestos | Reglas bus | Proponer rutas | Crear rutas reales sin aprobacion | Documental/futura | Contratos y governance |
| BUSCADOR DE TENDENCIAS -> CEREBRO | Oportunidades generales | Foco CEO | Recomendar tendencia | Activar proveedores externos | Discovery/futura | Fuentes aprobadas |
| SNIFF AMAZON -> CEREBRO | Oportunidades Amazon | Criterio comercial | Recomendar oportunidades Amazon | Mezclarse con comercio propio o scraping sin permiso | Documental/futura | Discovery separado y fuentes legales |
| COMERCIO AUTONOMO -> MARKETING / NUBE / AUDITORIA | Flujo comercial, tienda, riesgos | Campanas, cloud, auditoria | Proponer e-commerce | Ventas/pagos reales sin aprobacion | Discovery/futura | Legal, pagos, cloud, auditoria |
| DCFT -> CEREBRO | Estado producto/piloto futuro | Prioridad CEO | Reportar estado futuro | Integrarse ahora | Protegido/futuro | Vault, deploy, piloto, CEO |
| SENTINELA -> Ecosistema | Reglas, alertas, bloqueos | Eventos y permisos | Bloquear riesgo defensivo | Hacking ofensivo | Pending/futura | Revision CEO, alcance defensivo |

## Activacion futura minima

Para activar cualquier relacion runtime:

1. Contrato real.
2. Governance Gate.
3. Auditoria.
4. Observability.
5. Manejo de secretos.
6. Prueba local.
7. Aprobacion CEO/CTO.
8. Plan de rollback.

## Cierre

Las relaciones estan definidas como mapa operativo. No hay rutas reales nuevas del bus.
