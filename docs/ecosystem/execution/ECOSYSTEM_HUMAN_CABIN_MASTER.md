# ECOSYSTEM Human Cabin Master V1

Estado: diseno documental, no implementacion
Fecha: 2026-06-06

## Sensacion esperada

La cabina humana debe sentirse como:

```text
Centro de Dirección de la empresa IA.
```

No debe sentirse como:

- lista de tabs;
- dashboard técnico;
- consola de programador;
- pagina larga sin decisión;
- tablero saturado;
- inventario sin alma.

## Inspiracion operaciónal

Se toma lo aprendido de DCFT:

- entrada clara;
- estado global visible;
- semáforo;
- alerta principal;
- próxima accion;
- botones compactos;
- drawers/paneles colapsados;
- mobile-first;
- lenguaje humano;
- nada técnico innecesario en Home;
- decisión en menos de 10 segundos.

No se copia DCFT literalmente. DCFT es doctor empresarial. El ecosistema es centro de dirección de la empresa IA.

## Home propuesta

### 1. Header

```text
ECOSISTEMA IA
Centro de Dirección Empresarial
```

Texto de apoyo:

```text
Dirección, construcción, auditoría, seguridad, nube y productos IA bajo control humano.
```

### 2. Estado global

Estados permitidos:

- Operativo.
- En construcción.
- Atención.
- Bloqueado.

Nunca usar "todo listo" si hay apps en discovery, pending_review o protected_no_touch.

### 3. Semáforo principal

| Semáforo | Verde | Ambar | Rojo | Gris |
| --- | --- | --- | --- | --- |
| Operación | Backbone responde | Hay endpoints pendientes | Runtime caido | No configurado |
| Construcción | FORJA aprobada para tarea | FORJA estable pero sin tarea CEO | Tarea bloqueada | No configurado |
| Seguridad | SENTINELA/Audit sin riesgo | Requiere revisión | Secreto/riesgo crítico | Pendiente |
| Cloud/Costos | NUBE auditada | NUBE documental | Variable/deploy en riesgo | No registrada |

### 4. Próxima decisión CEO

Debe responder:

- que decisión falta;
- por que importa;
- que pasa si se aprueba;
- que no se tocara.

Ejemplo:

```text
Próxima decisión: revisar cabina con CEREBRO antes de push/deploy.
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
- SENTINELA: pendiente, no integrar sin revisión.
- NUBE local: no tocar sin auditoría.

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
- Ejecutar auditoría.
- Revisar NUBE.
- Ver riesgos.
- Ver pendientes.
- Ver apps.

Regla: si el boton no ejecuta una accion real, debe decir "ver", "preparar" o "solicitar", no "ejecutar".

## Panel CEREBRO

Debe decir:

- Que sabe: estado, prioridades, riesgos, pendientes.
- Que puede recomendar: siguiente paso, decisión CEO, que no tocar.
- Que no puede hacer: ejecutar codigo, abrir agentes, conectar runtimes.

## Panel FORJA

Debe decir:

- Que puede construir: apps, documentos, entregables, pruebas.
- Que necesita: aprobación CEO, alcance, heartbeat si hay Local Agent.
- Que no puede hacer: tomar tareas reales sin aprobación.

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

Estado actual: documental/preparada, no registrada. No tocar NUBE local sin auditoría.

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
2. Semáforo compacto.
3. Próxima accion.
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
- Centro: dirección y apps prioritarias.
- Panel derecho: decisiones CEO, riesgos, pendientes.
- Drawers: detalle técnico, auditoría, cloud, contratos.

## Lenguaje

Usar:

- "Preparado para discovery".
- "Protegido".
- "Pendiente de aprobación".
- "Conexión externa apagada".
- "Próxima decisión".

Evitar:

- "mock" visible al CEO salvo en vista técnica.
- "routes=0" en Home.
- "payload", "endpoint", "schema" en Home.
- "operativo" para apps sin runtime.

## Cierre

La cabina humana debe convertir complejidad técnica en decisión ejecutiva sin mentir sobre conexiones reales.
