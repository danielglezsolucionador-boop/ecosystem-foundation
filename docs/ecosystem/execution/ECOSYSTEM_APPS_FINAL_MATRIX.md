# ECOSYSTEM Apps Final Matrix V1

Estado: matriz maestra documental
Fecha: 2026-06-06

## Reglas de matriz

- No usar "listo" de forma generica.
- No mezclar SNIFF AMAZON con COMERCIO AUTONOMO.
- No declarar runtime externo real si `external_connection_enabled=false`.
- "Datos reales" significa dato backend/plataforma o produccion externa validada, no conexion desde el ecosystem.

| APP | ROL | ESTADO REAL | CABINA CORAZON | CABINA TECNICA | CABINA HUMANA | RELACION CON CEREBRO | RELACION CON FORJA | RELACION CON AUDITORIA | RELACION CON NUBE | RELACION CON SENTINELA | DATOS REALES | MOCK/PREPARADO | PROXIMO PASO | NO TOCAR |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| CEREBRO | Director estrategico | `discovery_prepared` | Decide y ordena | Profile/contract sin runtime | Hablar con CEREBRO | Es origen de prioridad | Pide tareas futuras aprobadas | Recibe observaciones | Recibe estado cloud futuro | Recibe riesgos | Discovery documentado | Preparado | Probar 12 preguntas | Runtime productivo |
| FORJA | Directora de construccion | `production_pass` externo / `discovery_prepared` interno | Construye | Profile/contract sin runtime | Enviar tarea controlada | Recibe decision aprobada | Es ejecutora | Entrega evidencia | Puede requerir deploy futuro | Recibe bloqueos | Produccion externa validada previamente | Discovery interno | Tareas solo con CEO | Productivo y Local Agent |
| DCFT / Doctor Contable Financiero Tributario | Producto vendible tributario | `protected_no_touch` | Producto comercial prioritario | Externo protegido | Pendiente integracion controlada | Reportara estado futuro | Puede recibir construccion futura | Requiere auditoria fuerte | Requiere cloud/vault | Requiere seguridad | Produccion externa validada previamente | Protegido | Vault/deploy/piloto/aprobacion | SUNAT real, Clave SOL, productivo |
| SENTINELA / CENTINELA | Seguridad defensiva | `pending_review` | Protege | Registry-only planned | Pendiente revision CEO | Reporta riesgos | Bloquea tareas peligrosas | Complementa auditoria | Revisa secretos/cloud futuro | Es responsable seguridad | Registry | Pendiente | Discovery defensivo | Acciones ofensivas/productivo |
| AUDITORIA | Juez de calidad/costos/aprobacion | `discovery_prepared` e interno operativo | Audita | Audit backend real + profile | Ver auditorias | Reporta observaciones | Valida entregables | Es auditor | Audita costos/cloud futuro | Recibe incidentes | Audit interno real | App standalone preparada | Definir app/repo si aplica | Construccion/deploy |
| NUBE | Torre de control cloud | `documented_only` / `planned` | Controla cloud | No registrada | Revisar NUBE | Reporta estado cloud | Da condiciones de deploy | Entrega evidencia costos | Es responsable cloud | Coordina secretos | Herramienta local existe | Documentada | Auditoria local | NUBE local, secretos, variables |
| HERMES | Comunicacion/automatizacion | `discovery_prepared` | Comunica | Profile/contract sin runtime | Verificar estado | Entrega mensajes preparados | Puede apoyar notificaciones | Auditable | Puede avisar deploy futuro | Debe respetar permisos | Discovery documentado | Preparado | Confirmar runtime real | Bots/mensajes reales |
| PLUMA | Contenido y escritura | `discovery_prepared` | Genera contenido | Profile/contract sin runtime | Ver ficha | Recibe narrativa | Puede producir borradores | Requiere revision | Puede publicar futuro con NUBE | Revisa datos sensibles | Discovery documentado | Preparado | Validar repo/runtime | Publicar sin aprobacion |
| LENTE | Observacion/analisis visual y senales | `discovery_prepared` | Analiza visuales/senales | Profile/contract sin runtime | Ver ficha | Entrega analisis | Da insumos a tareas | Audita evidencia visual | Puede requerir assets cloud | Detecta riesgos de datos | Discovery documentado | Preparado | Confirmar runtime | Fuentes externas sin permiso |
| WEB FACTORY / Creador de Webs | Produccion web | `discovery_prepared` | Crea webs | Profile/contract sin runtime | Ver ficha | Recibe prioridades web | FORJA podria construir | Auditoria revisa calidad | NUBE controla deploy/dominio | Sentinela revisa seguridad | Discovery interno | Preparado | Definir runtime/repo | Deploy/dominio real |
| MARKETING / Growth Lab | Crecimiento y campanas | `discovery_prepared` | Activa mercado | Profile/contract sin runtime | Ver ficha | Recibe estrategia | FORJA puede preparar activos | Auditoria revisa costos | NUBE revisa herramientas | Sentinela revisa datos | Discovery interno | Preparado | Definir aprobaciones | Publicar/gastar/enviar |
| MARCA PERSONAL | Marca CEO | `discovery_prepared` | Voz del CEO | Profile/contract sin runtime | Ver ficha | Recibe criterio CEO | FORJA puede producir piezas | Auditoria revisa tono | NUBE no aplica salvo assets | Sentinela protege identidad | Discovery interno | Preparado | Validar guia marca | Publicar identidad |
| CREADOR DE APIS | Fabrica de APIs | `documented_only` | Crea APIs | No registrado; futuro bus | Pendiente | CEREBRO define necesidad | FORJA construye API futura | Auditoria valida contrato | NUBE despliega futuro | Sentinela revisa auth/secrets | No conectado | Documentado | Registrar como planned | Rutas reales del bus |
| BUSCADOR DE TENDENCIAS | Radar general | `discovery_prepared` | Detecta tendencias | Profile/contract sin runtime | Ver ficha | Entrega oportunidades | FORJA convierte hallazgo | Auditoria valida fuentes | NUBE no aplica inicial | Sentinela revisa fuentes | Discovery interno | Preparado | Validar fuentes | APIs/scraping externos |
| SNIFF AMAZON | Radar Amazon especializado | `documented_only` | Detecta oportunidades Amazon | No registrado | Pendiente | Entrega oportunidades Amazon | FORJA prepara pruebas futuras | Auditoria valida riesgo | NUBE no aplica inicial | Sentinela revisa scraping/datos | No conectado | Documentado | Crear discovery separado | Mezclar con Comercio Autonomo |
| COMERCIO AUTONOMO | E-commerce/dropshipping/comercio propio | `discovery_prepared` | Genera comercio | Profile/contract sin runtime | Ver ficha | Recibe estrategia comercial | FORJA construye flujos | Auditoria revisa costos/legal | NUBE controla deploy/pagos futuro | Sentinela revisa datos/pagos | Discovery interno | Preparado | Definir alcance comercial | Ventas/pagos reales |

## Cierre

La matriz contiene todas las apps obligatorias y separa SNIFF AMAZON de COMERCIO AUTONOMO.
