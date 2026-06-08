# ECOSYSTEM Human Cabin Master V1

Estado: diseno documental, no implementacion
Fecha: 2026-06-06

## Sensacion esperada

La cabina humana debe sentirse como:

```text
Centro de Direccion de la empresa IA.
```

No debe sentirse como:

- lista de tabs;
- dashboard tecnico;
- consola de programador;
- pagina larga sin decision;
- tablero saturado;
- inventario sin alma.

## Inspiracion operacional

Se toma lo aprendido de DCFT:

- entrada clara;
- estado global visible;
- semaforo;
- alerta principal;
- proxima accion;
- botones compactos;
- drawers/paneles colapsados;
- mobile-first;
- lenguaje humano;
- nada tecnico innecesario en Home;
- decision en menos de 10 segundos.

No se copia DCFT literalmente. DCFT es doctor empresarial. El ecosistema es centro de direccion de la empresa IA.

## Home propuesta

### 1. Header

```text
ECOSISTEMA IA
Centro de Direccion Empresarial
```

Texto de apoyo:

```text
Direccion, construccion, auditoria, seguridad, nube y productos IA bajo control humano.
```

### 2. Estado global

Estados permitidos:

- Operativo.
- En construccion.
- Atencion.
- Bloqueado.

Nunca usar "todo listo" si hay apps en discovery, pending_review o protected_no_touch.

### 3. Semaforo principal

| Semaforo | Verde | Ambar | Rojo | Gris |
| --- | --- | --- | --- | --- |
| Operacion | Backbone responde | Hay endpoints pendientes | Runtime caido | No configurado |
| Construccion | FORJA aprobada para tarea | FORJA estable pero sin tarea CEO | Tarea bloqueada | No configurado |
| Seguridad | SENTINELA/Audit sin riesgo | Requiere revision | Secreto/riesgo critico | Pendiente |
| Cloud/Costos | NUBE auditada | NUBE documental | Variable/deploy en riesgo | No registrada |

### 4. Proxima decision CEO

Debe responder:

- que decision falta;
- por que importa;
- que pasa si se aprueba;
- que no se tocara.

Ejemplo:

```text
Proxima decision: revisar cabina con CEREBRO antes de push/deploy.
No tocar: DCFT, SENTINELA, NUBE local ni Local Agent.
```

### 5. Apps prioritarias

Orden recomendado:

1. DCFT
2. CEREBRO
3. FORJA
4. SENTINELA
5. AUDITORIA
6. NUBE

Cada card debe tener:

- rol humano;
- estado real;
- fuente del dato;
- si tiene runtime conectado;
- accion permitida;
- accion prohibida.

### 6. Apps protegidas/no-touch

Mostrar separadas:

- DCFT: `protected_no_touch`.
- FORJA productiva: no tocar; solo discovery interno.
- CEREBRO productivo: no tocar; solo discovery interno.
- SENTINELA: pendiente, no integrar sin revision.
- NUBE local: no tocar sin auditoria.

### 7. Apps preparadas/discovery

Mostrar como "preparadas", no como "operativas":

- HERMES
- PLUMA
- LENTE
- WEB FACTORY
- MARKETING
- MARCA PERSONAL
- COMERCIO AUTONOMO
- BUSCADOR DE TENDENCIAS
- AUDITORIA

### 8. Accesos rapidos

Botones compactos:

- Hablar con CEREBRO.
- Enviar tarea a FORJA.
- Ejecutar auditoria.
- Revisar NUBE.
- Ver riesgos.
- Ver pendientes.
- Ver apps.

Regla: si el boton no ejecuta una accion real, debe decir "ver", "preparar" o "solicitar", no "ejecutar".

## Panel CEREBRO

Debe decir:

- Que sabe: estado, prioridades, riesgos, pendientes.
- Que puede recomendar: siguiente paso, decision CEO, que no tocar.
- Que no puede hacer: ejecutar codigo, abrir agentes, conectar runtimes.

## Panel FORJA

Debe decir:

- Que puede construir: apps, documentos, entregables, pruebas.
- Que necesita: aprobacion CEO, alcance, heartbeat si hay Local Agent.
- Que no puede hacer: tomar tareas reales sin aprobacion.

## Panel AUDITORIA

Debe decir:

- Aprobado.
- Observado.
- Bloqueado.
- Riesgo.
- Evidencia requerida.

## Panel NUBE

Debe decir:

- URLs.
- Deploys.
- Costos.
- Variables.
- Backups.
- Health.

Estado actual: documental/preparada, no registrada. No tocar NUBE local sin auditoria.

## Panel SENTINELA

Debe decir:

- Riesgos.
- Permisos.
- Agentes.
- Datos sensibles.
- Secretos.
- Incidentes.

Estado actual: pending_review, defensiva, no ofensiva.

## Mobile

Primera pantalla mobile:

1. Estado global.
2. Semaforo compacto.
3. Proxima accion.
4. Apps prioritarias.
5. Riesgos.
6. Bottom nav.

Bottom nav sugerido:

- Inicio.
- Apps.
- Cerebro.
- Riesgos.
- Perfil.

## Desktop

Layout sugerido:

- Sidebar izquierda: vistas principales y rol.
- Centro: direccion y apps prioritarias.
- Panel derecho: decisiones CEO, riesgos, pendientes.
- Drawers: detalle tecnico, auditoria, cloud, contratos.

## Lenguaje

Usar:

- "Preparado para discovery".
- "Protegido".
- "Pendiente de aprobacion".
- "Conexion externa apagada".
- "Proxima decision".

Evitar:

- "mock" visible al CEO salvo en vista tecnica.
- "routes=0" en Home.
- "payload", "endpoint", "schema" en Home.
- "operativo" para apps sin runtime.

## Cierre

La cabina humana debe convertir complejidad tecnica en decision ejecutiva sin mentir sobre conexiones reales.
