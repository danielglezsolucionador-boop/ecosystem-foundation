# ECOSYSTEM Agent Relationship Map

Fecha: 2026-06-06
Repositorio: `ecosystem-foundation`
Estado: configuracion operativa documental

## Proposito

Este mapa define la relacion operativa entre las apps/agentes del ecosistema para que la cabina humana pueda responder de forma simple:

- quien decide;
- quien construye;
- quien audita;
- quien protege;
- quien controla nube;
- quien opera comunicacion o automatizacion;
- que puede pedir el CEO;
- que no se debe ejecutar sin aprobacion humana.

Este documento no activa conexiones reales, no crea tareas automaticas, no abre Local Agent y no toca apps productivas.

## Principio rector

El ecosistema opera con separacion de responsabilidades:

1. El CEO decide.
2. CEREBRO ordena y recomienda.
3. Governance registra la decision y exige aprobacion cuando aplica.
4. FORJA construye solo si hay tarea aprobada.
5. AUDITORIA revisa calidad, costos, riesgos y evidencia.
6. SENTINELA protege.
7. NUBE controla infraestructura cloud.
8. DCFT permanece como producto vendible protegido hasta aprobacion de piloto.
9. HERMES apoya comunicacion, automatizacion y memoria operativa cuando su estado real este confirmado.

## Roles operativos

### CEREBRO

Rol: Director estrategico / mano derecha CEO.

Responsabilidades:

- Decide prioridades junto al CEO.
- Resume estado del ecosistema.
- Pide ejecucion a FORJA o Codex cuando hay aprobacion.
- Coordina agentes y evita abrir frentes innecesarios.
- Responde al CEO con estado, riesgo, proximo paso y que no tocar.

Limites:

- No ejecuta codigo directamente.
- No modifica apps productivas.
- No dispara Local Agent.
- No declara conexiones reales si solo hay discovery o documentacion.

Estado actual:

- Discovery profile preparado en `ecosystem-foundation`.
- Sin runtime externo conectado desde esta cabina.
- `external_connection_enabled=false`.

### FORJA

Rol: Directora de construccion.

Responsabilidades:

- Convierte decisiones aprobadas en tareas.
- Produce entregables, apps, documentos, pruebas y reportes.
- Puede coordinar Local Agent solo con aprobacion CEO.
- Debe respetar memoria, permisos, rutas de entregables y criterio de no tocar apps protegidas.

Limites:

- No ejecuta tareas reales sin aprobacion CEO.
- No abre Local Agent por defecto.
- No consume cola productiva sin heartbeat y aprobacion.
- No toca DCFT, SENTINELA, CEREBRO productivo ni otras apps sin alcance aprobado.

Estado actual:

- Produccion FORJA recuperada y congelada estable segun evidencia previa.
- Backup estable creado segun reporte externo del bloque FORJA.
- En `ecosystem-foundation`: discovery profile preparado, sin runtime conectado.
- Local Agent requiere heartbeat; si la PC esta apagada, FORJA puede aparecer offline.

### AUDITORIA

Rol: juez de calidad, costos y aprobacion.

Responsabilidades:

- Audita calidad humana, tecnica y de negocio.
- Revisa contratos, costos, riesgos, permisos, evidencias y cambios.
- Puede bloquear avance si la app no cumple cabina humana, tecnica o corazon del producto.
- Registra trazabilidad y evidencia.

Limites:

- No construye.
- No ejecuta tareas.
- No desbloquea integraciones sin evidencia y rol autorizado.

Estado actual:

- Auditoria interna del backbone operativa.
- App Auditor preparada como discovery profile.
- Pendiente repo/app independiente si el CEO decide convertirla en producto o runtime separado.

### NUBE

Rol: torre de control cloud.

Responsabilidades:

- Controla URLs, deploys, proveedores, costos, backups, variables y dominios.
- Debe vigilar Vercel, Render, PostgreSQL, dominios y estado de produccion.
- Debe registrar decisiones cloud con evidencia.

Limites:

- No debe tocar secretos sin autorizacion.
- No debe redeployar ni cambiar variables sin aprobacion.
- No debe modificar proveedores cloud por iniciativa propia.

Estado actual:

- Documental/preparada.
- Herramienta local detectada en `C:\Users\admin\nube`.
- No registrada todavia como app integrada en `ecosystem-foundation`.
- No tocar hasta auditoria local de NUBE.

### SENTINELA

Rol: seguridad defensiva del ecosistema.

Responsabilidades:

- Protege agentes, permisos, datos, apps e incidentes.
- Detecta riesgos, anomalias, secretos expuestos, permisos peligrosos y acciones no autorizadas.
- Debe bloquear o escalar cuando una accion supera el alcance aprobado.

Limites:

- No hace hacking ofensivo.
- No escanea objetivos externos sin autorizacion explicita.
- No activa monitoreo invasivo.
- No toca produccion sin alcance aprobado.

Estado actual:

- En registry aparece como `centinela`, estado planned/registry-only.
- Falta discovery profile.
- Pendiente de integracion hasta revision CEO local, decision sobre untracked y aprobacion push/deploy.

### DCFT

Rol: producto vendible / Doctor contable financiero tributario.

Responsabilidades:

- Producto comercial de prioridad alta.
- Atiende diagnostico contable, financiero y tributario.
- Piloto SUNAT auxiliar debe usar solo credenciales auxiliares y modo controlado.

Limites:

- No activar SUNAT real desde el ecosistema.
- No usar Clave SOL principal.
- No integrar al ecosistema sin aprobacion CEO.
- No tocar backend/frontend productivo DCFT fuera de bloque aprobado.

Estado actual:

- App externa protegida en registry.
- Pendiente de integracion al ecosistema hasta cerrar:
  - vault SUNAT auxiliar;
  - deploy controlado;
  - piloto 1 estudiante + 2 empresas;
  - aprobacion CEO.

### HERMES

Rol: comunicacion, automatizacion, bots, notificaciones o backend operativo.

Responsabilidades:

- Puede apoyar memoria, comunicacion, automatizacion interna y notificaciones.
- Debe confirmar estado real antes de pasar de discovery a integracion.

Limites:

- No activar bots ni automatizaciones sin aprobacion.
- No enviar mensajes, correos o notificaciones reales sin autorizacion.
- No declarar runtime conectado si solo existe discovery.

Estado actual:

- Discovery profile preparado.
- Sin conexion runtime real desde `ecosystem-foundation`.
- `external_connection_enabled=false`.

## Otras apps preparadas

| App | Rol operativo | Estado real en ecosystem |
| --- | --- | --- |
| PLUMA | Contenido y escritura | Discovery preparado, sin conexion runtime |
| LENTE | Observacion y analisis | Discovery preparado, sin conexion runtime |
| WEB FACTORY | Produccion web | Discovery preparado, sin conexion runtime |
| MARKETING | Crecimiento y campanas | Discovery preparado, sin conexion runtime |
| MARCA PERSONAL | Marca del CEO | Discovery preparado, sin conexion runtime |
| COMERCIO AUTONOMO | Flujo comercial futuro | Discovery preparado, sin conexion runtime |
| BUSCADOR DE TENDENCIAS | Radar de oportunidades | Discovery preparado, sin conexion runtime |

## Flujo operativo recomendado

```text
CEO
  -> CEREBRO: pide estado, prioridad o decision
  -> Governance: registra aprobacion si la accion es sensible
  -> FORJA/Codex: construye solo con alcance aprobado
  -> AUDITORIA: revisa calidad, costos, evidencia y riesgos
  -> SENTINELA: valida seguridad defensiva
  -> NUBE: controla deploy/cloud/backups/variables
  -> DCFT/HERMES/otras apps: se conectan solo cuando el CEO aprueba el contrato real
```

## Acciones permitidas

- Consultar estado real del ecosistema.
- Ver apps listas, preparadas y pendientes.
- Crear reportes documentales.
- Preparar contratos sin activar conectores.
- Pedir validacion humana antes de cualquier accion sensible.
- Proponer siguiente paso sin abrir frentes nuevos.

## Acciones prohibidas sin aprobacion CEO

- Ejecutar tareas reales.
- Abrir o activar Local Agent.
- Activar SUNAT real.
- Usar credenciales reales en chat, codigo o reportes.
- Hacer push/deploy.
- Tocar DCFT productivo.
- Tocar SENTINELA productivo.
- Tocar FORJA productivo.
- Tocar CEREBRO productivo.
- Cambiar secretos, variables o proveedores cloud.

## Preguntas de validacion para CEREBRO

Las respuestas esperadas deben ser humanas, cortas y utiles.

1. Cerebro, cual es el estado real del ecosistema?
2. Cerebro, que apps estan listas y cuales no?
3. Cerebro, que no debemos tocar ahora?
4. Cerebro, que hace FORJA?
5. Cerebro, que hace AUDITORIA?
6. Cerebro, que hace NUBE?
7. Cerebro, que hace SENTINELA?
8. Cerebro, cual es la prioridad actual del CEO?
9. Cerebro, por que DCFT no debe integrarse todavia?
10. Cerebro, que falta para activar DCFT en el ecosistema?
11. Cerebro, cuando puede FORJA ejecutar tareas reales?
12. Cerebro, dame el proximo paso sin abrir frentes nuevos.

## Respuesta tipo esperada de CEREBRO

Formato recomendado:

```text
Estado: [vivo/preparado/pendiente/bloqueado]
Riesgo: [riesgo principal en una linea]
Proximo paso: [accion minima]
No tocar: [apps o sistemas protegidos]
```

## Cierre

La relacion operativa queda definida como configuracion documental. No hay nuevas conexiones runtime, no hay tareas automaticas y no se modifica ninguna app productiva.
