# ECOSYSTEM App Contracts

Fecha: 2026-06-06
Repositorio: `ecosystem-foundation`
Estado: contratos operativos documentales

## Regla de lectura

Un contrato en este documento no significa conexion real.

Estados usados:

- `connected_real`: conexion runtime real validada.
- `prepared_for_discovery`: discovery profile/contrato/evidencia preparados, sin runtime externo.
- `registry_only`: app reservada en registry.
- `external_protected`: app externa protegida, no conectada.
- `not_registered`: no registrada todavia en el backbone.

En esta version, ninguna app externa esta marcada como `connected_real` desde `ecosystem-foundation`.

## Contratos por app

### CEREBRO

| Campo | Valor |
| --- | --- |
| Nombre | CEREBRO |
| Rol | Director estrategico / mano derecha CEO |
| Estado | `prepared_for_discovery` |
| URL frontend | Pendiente de validar en este contrato; no consumida desde `ecosystem-foundation` |
| URL backend | Pendiente de validar en este contrato; no consumida desde `ecosystem-foundation` |
| Repo | `centro-de-direccion-app` segun discovery profile |
| Datos reales/mock | Discovery real documentado; runtime no conectado |
| Dependencias | CEO, Governance, Audit, FORJA futura, memoria operativa |
| Permisos | Puede recomendar; no ejecuta codigo |
| Riesgos | Confundir conversacion real con discovery documental |
| Acciones permitidas | Resumir estado, recomendar prioridad, pedir aprobacion |
| Acciones prohibidas | Ejecutar tareas, tocar codigo, abrir agentes o conectar runtime sin aprobacion |
| Proximo paso | Validar respuestas de prueba y decidir si se conecta runtime futuro |

### FORJA

| Campo | Valor |
| --- | --- |
| Nombre | FORJA |
| Rol | Directora de construccion |
| Estado | `prepared_for_discovery`; produccion externa congelada estable por evidencia previa |
| URL frontend | `https://forja-frontend.onrender.com` segun validaciones previas |
| URL backend | `https://forja-core.onrender.com` segun validaciones previas |
| Repo | `forja-core` segun discovery profile |
| Datos reales/mock | Produccion externa real; ecosystem solo discovery sin runtime conectado |
| Dependencias | CEO approval, CEREBRO, Governance, Audit, Local Agent, entregables |
| Permisos | Puede ejecutar tareas solo si CEO aprueba |
| Riesgos | Ejecutar tareas reales sin aprobacion o sin heartbeat |
| Acciones permitidas | Preparar tareas, documentar entregables, validar estado |
| Acciones prohibidas | Abrir Local Agent, tomar tareas reales o consumir cola productiva sin aprobacion |
| Proximo paso | Revisar con CEO antes de cualquier tarea real controlada |

### AUDITORIA

| Campo | Valor |
| --- | --- |
| Nombre | AUDITORIA / Auditor |
| Rol | Juez de calidad, costos y aprobacion |
| Estado | `prepared_for_discovery`; audit interno operativo |
| URL frontend | Control Center de `ecosystem-foundation` |
| URL backend | API de `ecosystem-foundation` |
| Repo | `ecosystem-foundation-internal-audit` segun discovery profile |
| Datos reales/mock | Audit interno real; app standalone pendiente |
| Dependencias | Contracts, Governance, Observability, Security |
| Permisos | Puede auditar, bloquear o escalar con evidencia |
| Riesgos | Tomar decisiones ejecutivas en vez de auditar |
| Acciones permitidas | Revisar calidad, costos, evidencias, permisos y riesgos |
| Acciones prohibidas | Construir, desplegar o conectar apps por si misma |
| Proximo paso | Decidir si se crea repo/app independiente de Auditoria |

### NUBE

| Campo | Valor |
| --- | --- |
| Nombre | NUBE |
| Rol | Torre de control cloud |
| Estado | `not_registered`; herramienta local documental/preparada |
| URL frontend | No registrada |
| URL backend | No registrado |
| Repo | Herramienta local en `C:\Users\admin\nube` |
| Datos reales/mock | No auditado en esta fase |
| Dependencias | Vercel, Render, Postgres, dominios, backups, variables |
| Permisos | Solo lectura/documental hasta auditoria CEO |
| Riesgos | Tocar secretos, variables, costos o deploys sin aprobacion |
| Acciones permitidas | Documentar estado cloud y preparar auditoria |
| Acciones prohibidas | Cambiar variables, secretos, proveedores, deploys o dominios |
| Proximo paso | Auditoria local de NUBE sin tocar secretos |

### SENTINELA

| Campo | Valor |
| --- | --- |
| Nombre | SENTINELA / CENTINELA |
| Rol | Seguridad defensiva del ecosistema |
| Estado | `registry_only` como `centinela` |
| URL frontend | No conectada |
| URL backend | No conectado |
| Repo | Pendiente de confirmar |
| Datos reales/mock | Registry planned; sin discovery profile |
| Dependencias | Security, Governance, Audit, Observability |
| Permisos | Defensivo, no ofensivo |
| Riesgos | Escaneo ofensivo, tocar productivo o bloquear sin evidencia |
| Acciones permitidas | Preparar reglas defensivas, checklist y revision CEO |
| Acciones prohibidas | Hacking ofensivo, monitoreo invasivo, cambios productivos sin alcance |
| Proximo paso | Revision CEO local, decision sobre untracked y aprobacion push/deploy |

### DCFT

| Campo | Valor |
| --- | --- |
| Nombre | DCFT / Doctor Contable Financiero Tributario |
| Rol | Producto vendible contable, financiero y tributario |
| Estado | `external_protected` |
| URL frontend | `https://dcft-frontend.vercel.app` segun validaciones previas |
| URL backend | `https://dcft.vercel.app` segun validaciones previas |
| Repo | Externo al backbone; no tocar en este contrato |
| Datos reales/mock | Producto real externo; ecosystem no conectado |
| Dependencias | Vault SUNAT auxiliar, Postgres, CEO approval, piloto controlado |
| Permisos | Solo integracion controlada cuando CEO apruebe |
| Riesgos | SUNAT real, secretos, Clave SOL principal, datos sensibles |
| Acciones permitidas | Documentar pendiente, validar bloqueos, preparar criterios |
| Acciones prohibidas | Activar SUNAT real, usar credenciales reales, tocar produccion sin bloque aprobado |
| Proximo paso | Cerrar vault, deploy controlado, piloto 1 estudiante + 2 empresas y aprobacion CEO |

### HERMES

| Campo | Valor |
| --- | --- |
| Nombre | HERMES |
| Rol | Comunicacion, automatizacion, bots, notificaciones o backend operativo |
| Estado | `prepared_for_discovery` |
| URL frontend | No conectada desde `ecosystem-foundation` |
| URL backend | No conectado desde `ecosystem-foundation` |
| Repo | `hermes-knowledge-core` segun discovery profile |
| Datos reales/mock | Discovery real documentado; runtime no conectado |
| Dependencias | Memoria, eventos, notificaciones futuras, Governance |
| Permisos | Preparar comunicacion; no enviar mensajes reales sin aprobacion |
| Riesgos | Automatizaciones reales no aprobadas |
| Acciones permitidas | Mantener memoria y estado documental |
| Acciones prohibidas | Enviar bots, correos, mensajes o automatizaciones reales sin aprobacion |
| Proximo paso | Confirmar estado real antes de integracion runtime |

### PLUMA

| Campo | Valor |
| --- | --- |
| Nombre | PLUMA |
| Rol | Contenido y escritura |
| Estado | `prepared_for_discovery` |
| URL frontend | No conectada desde `ecosystem-foundation` |
| URL backend | No conectado desde `ecosystem-foundation` |
| Repo | `pluma` segun discovery profile |
| Datos reales/mock | Discovery documentado; runtime no conectado |
| Dependencias | CEREBRO, FORJA futura, Auditoria |
| Permisos | Preparar contenido bajo aprobacion |
| Riesgos | Publicar contenido no aprobado |
| Acciones permitidas | Discovery, documentacion, plan de contenido |
| Acciones prohibidas | Publicar o automatizar salidas reales sin aprobacion |
| Proximo paso | Confirmar repo limpio y runtime antes de conexion |

### LENTE

| Campo | Valor |
| --- | --- |
| Nombre | LENTE |
| Rol | Observacion y analisis |
| Estado | `prepared_for_discovery` |
| URL frontend | No conectada desde `ecosystem-foundation` |
| URL backend | No conectado desde `ecosystem-foundation` |
| Repo | `lente` segun discovery profile |
| Datos reales/mock | Discovery documentado; runtime no conectado |
| Dependencias | Marketing, Marca Personal, CEREBRO |
| Permisos | Analizar y preparar reportes |
| Riesgos | Confundir analisis preparado con datos vivos |
| Acciones permitidas | Discovery, reportes y validacion local |
| Acciones prohibidas | Conectar fuentes externas sin aprobacion |
| Proximo paso | Confirmar estado real del runtime |

### WEB FACTORY

| Campo | Valor |
| --- | --- |
| Nombre | WEB FACTORY |
| Rol | Produccion web |
| Estado | `prepared_for_discovery` |
| URL frontend | No conectada desde `ecosystem-foundation` |
| URL backend | No conectado desde `ecosystem-foundation` |
| Repo | Discovery interno de `ecosystem-foundation` |
| Datos reales/mock | Discovery interno; runtime no detectado |
| Dependencias | FORJA, Auditoria, NUBE futura |
| Permisos | Preparar fabrica web bajo governance |
| Riesgos | Crear/deployar sitios sin aprobacion |
| Acciones permitidas | Planificar y documentar produccion web |
| Acciones prohibidas | Deploy real o dominio real sin aprobacion |
| Proximo paso | Definir runtime o repo dedicado |

### MARKETING

| Campo | Valor |
| --- | --- |
| Nombre | MARKETING |
| Rol | Crecimiento y campanas |
| Estado | `prepared_for_discovery` |
| URL frontend | No conectada desde `ecosystem-foundation` |
| URL backend | No conectado desde `ecosystem-foundation` |
| Repo | Discovery interno de `ecosystem-foundation` |
| Datos reales/mock | Discovery interno; runtime no conectado |
| Dependencias | LENTE, PLUMA, Marca Personal, CEREBRO |
| Permisos | Preparar campanas, no ejecutar pauta real |
| Riesgos | Activar gasto o comunicaciones no aprobadas |
| Acciones permitidas | Estrategia y planificacion |
| Acciones prohibidas | Publicar, gastar, enviar o automatizar sin aprobacion |
| Proximo paso | Definir fuentes y aprobaciones |

### MARCA PERSONAL

| Campo | Valor |
| --- | --- |
| Nombre | MARCA PERSONAL |
| Rol | Marca del CEO |
| Estado | `prepared_for_discovery` |
| URL frontend | No conectada desde `ecosystem-foundation` |
| URL backend | No conectado desde `ecosystem-foundation` |
| Repo | Discovery interno de `ecosystem-foundation` |
| Datos reales/mock | Discovery interno; runtime no conectado |
| Dependencias | CEREBRO, PLUMA, LENTE, Marketing |
| Permisos | Preparar narrativa y plan |
| Riesgos | Publicar voz del CEO sin aprobacion |
| Acciones permitidas | Documentar estrategia y piezas borrador |
| Acciones prohibidas | Publicar contenido o usar identidad sin aprobacion |
| Proximo paso | Validar guia de marca y workflow |

### COMERCIO AUTONOMO

| Campo | Valor |
| --- | --- |
| Nombre | COMERCIO AUTONOMO |
| Rol | Operacion comercial futura |
| Estado | `prepared_for_discovery` |
| URL frontend | No conectada desde `ecosystem-foundation` |
| URL backend | No conectado desde `ecosystem-foundation` |
| Repo | Discovery interno de `ecosystem-foundation` |
| Datos reales/mock | Discovery interno; runtime no conectado |
| Dependencias | DCFT futuro, Marketing, NUBE, Auditoria |
| Permisos | Discovery comercial sin APIs externas |
| Riesgos | Ejecutar ventas, pagos o flujos reales sin aprobacion |
| Acciones permitidas | Mapear flujo comercial y riesgos |
| Acciones prohibidas | Cobrar, vender, conectar pasarelas o enviar mensajes reales |
| Proximo paso | Definir alcance comercial aprobado |

### BUSCADOR DE TENDENCIAS

| Campo | Valor |
| --- | --- |
| Nombre | BUSCADOR DE TENDENCIAS |
| Rol | Radar de oportunidades |
| Estado | `prepared_for_discovery` |
| URL frontend | No conectada desde `ecosystem-foundation` |
| URL backend | No conectado desde `ecosystem-foundation` |
| Repo | Discovery interno de `ecosystem-foundation` |
| Datos reales/mock | Discovery interno; runtime no conectado |
| Dependencias | LENTE, Marketing, CEREBRO |
| Permisos | Discovery sin proveedores externos reales |
| Riesgos | Usar APIs, scraping o fuentes externas sin aprobacion |
| Acciones permitidas | Documentar criterios y preparar perfiles |
| Acciones prohibidas | Consultar proveedores externos reales sin aprobacion |
| Proximo paso | Validar fuente y permisos antes de conectar |

## Acciones globales prohibidas sin aprobacion CEO

- Push o deploy.
- Tareas reales.
- Local Agent.
- SUNAT real.
- Uso de credenciales reales.
- Cambio de secretos, dominios o variables cloud.
- Conexion runtime externa.
- Automatizaciones de comunicacion, bots, pagos o publicaciones.

## Cierre

Estos contratos ordenan responsabilidades y limites. No modifican App Registry, Integration Bus, Governance, Auth, backend ni apps productivas.
