# ECOSYSTEM COMPANY CABIN REDESIGN

Estado: propuesta de diseño mobile-first.
Alcance: cabina humana de la Empresa IA organizada por departamentos.
Base: `ECOSYSTEM_COMPANY_OPERATING_MODEL.md`.
Implementación: no incluida.

## 1. Principio Central

La cabina ya no debe sentirse como una lista de apps.

Debe sentirse como:

`EMPRESA IA OPERANDO POR DEPARTAMENTOS`

Vista desde el celular del CEO.

La primera experiencia debe responder en menos de 10 segundos:

1. ¿Qué debo decidir hoy?
2. ¿Qué me dice CEREBRO?
3. ¿Cómo está mi Empresa IA?
4. ¿Qué oportunidades aparecieron?
5. ¿Qué riesgos hay?
6. ¿Qué departamento necesita atención?
7. ¿Qué puede generar ingresos?
8. ¿Qué está protegido / no-touch?

La cabina debe priorizar claridad ejecutiva, no densidad técnica.

## 2. Enfoque Mobile-First

El diseño nace en móvil y luego se amplía a desktop.

La primera pantalla móvil debe tener máximo:

1. Reunión con CEREBRO.
2. Estado de Empresa IA.
3. Decisiones CEO.
4. Oportunidades.
5. Riesgos.
6. Departamentos.

Reglas de la primera pantalla:

- No mostrar todo.
- No llenar con cards largas.
- No usar texto técnico pesado.
- No repetir `ECOSISTEMA IA` como rótulo constante.
- No saturar con botones.
- No convertir el inicio en una tabla de monitoreo.
- No poner listas largas de apps como contenido principal.

La home móvil debe funcionar como una mesa ejecutiva de bolsillo: breve, decisiva y orientada a acción.

## 3. Home Móvil Ideal

### Sección 1 - Header Compacto

Objetivo: ubicar al CEO en la Empresa IA sin ocupar espacio crítico.

Debe incluir:

- Globo dorado del ecosistema.
- Texto corto: `Empresa IA`.
- Estado: `Local / revisión CEO`.
- Acceso a perfil o sesión.

Composición recomendada:

- Altura baja.
- Un solo renglón principal.
- Estado visible, pero secundario.
- Perfil como icono o acceso discreto.

No debe incluir:

- Texto explicativo largo.
- Repetición de marca.
- Menús densos.
- Estado técnico detallado.

### Sección 2 - Reunión con CEREBRO

Este debe ser el bloque más importante de la home.

Debe sentirse como una reunión ejecutiva, no como una tarjeta de chatbot.

Microcopy sugerido:

`Buenos días, CEO. Tengo tu resumen.`

Debe mostrar:

- Decisiones pendientes.
- Oportunidades nuevas.
- Riesgos activos.
- Tareas en construcción.
- Botón principal: `Hablar con CEREBRO` o `Abrir reunión`.

Ejemplo visual:

```text
Reunión con CEREBRO
3 decisiones
2 oportunidades
1 riesgo
[Abrir reunión]
```

Reglas:

- CEREBRO es el Chief of Staff / Jefe de Gabinete IA.
- CEREBRO prepara; el CEO decide.
- El bloque debe tener más peso visual que cualquier lista de apps.
- El CTA principal debe ser único y claro.

### Sección 3 - Estado Empresa IA

Objetivo: dar salud ejecutiva en una mirada.

Debe mostrar 4 indicadores:

- Dirección.
- Construcción.
- Seguridad.
- Ingresos / Productos.

Estados permitidos:

- Verde: estable / sin bloqueo crítico.
- Amarillo: requiere atención.
- Rojo: requiere decisión o riesgo activo.

Reglas:

- Solo usar verde, amarillo y rojo para estado.
- No usar más colores para semáforo.
- No mostrar métricas técnicas si no ayudan al CEO.
- Cada indicador debe tener una frase corta de contexto.

Ejemplo:

```text
Dirección      Verde     agenda clara
Construcción   Amarillo  2 bloqueos
Seguridad      Verde     sin alerta crítica
Ingresos       Amarillo  3 oportunidades
```

### Sección 4 - Próxima Decisión CEO

Objetivo: poner una decisión concreta frente al CEO.

Debe incluir:

- Decisión.
- Por qué importa.
- Acción principal.

Formato recomendado:

```text
Próxima decisión CEO
Priorizar producto comercial de APIs vendibles.
Importa porque puede abrir una línea de ingresos reusable.
[Revisar decisión]
```

Reglas:

- Una decisión visible.
- No convertir la sección en backlog.
- Si no hay decisión urgente, mostrar `Sin decisión crítica ahora`.
- Siempre explicar por qué importa en lenguaje ejecutivo.

### Sección 5 - Departamentos

Objetivo: que el CEO vea áreas de empresa, no apps sueltas.

Mostrar departamentos como accesos premium:

- Dirección.
- Construcción.
- Inteligencia.
- Productos Comerciales.
- Contenido y Crecimiento.
- Operación.
- Control y Seguridad.
- Arsenal.

Cada departamento debe tener:

- Icono.
- Color tenue propio.
- Estado.
- Número de asuntos.
- Botón o gesto de `Ver más`.

Reglas:

- La app puede aparecer dentro del departamento, no como protagonista inicial.
- Mostrar máximo una línea de función por departamento.
- Evitar cards interminables.
- Priorizar estado, asuntos y acción.

### Sección 6 - Bottom Nav

Máximo 5 opciones:

- Inicio.
- Cerebro.
- Departamentos.
- Riesgos.
- Perfil.

Reglas:

- No usar navegación confusa tipo `Gobierno / Sistema` si no aporta al CEO.
- No esconder `CEREBRO`.
- No poner más de 5 opciones.
- La navegación debe poder usarse con una mano.

## 4. Jerarquía Visual Móvil

Orden recomendado de atención:

1. Reunión con CEREBRO.
2. Próxima decisión CEO.
3. Estado Empresa IA.
4. Oportunidades y riesgos resumidos.
5. Departamentos.
6. Accesos secundarios.

Lo que debe verse primero:

- Qué necesita el CEO.
- Qué recomienda CEREBRO.
- Qué está sano, en alerta o bloqueado.

Lo que debe ocultarse o aplazarse:

- Listados completos de apps.
- Tablas grandes.
- Configuraciones.
- Métricas internas.
- Rutas técnicas.
- Estados de runtime.
- Detalles de bus.
- Integraciones.
- Historial completo.

## 5. Diseño Desktop

Desktop debe ampliar lo móvil, no inventar otra aplicación.

La lógica sigue siendo:

`CEREBRO prepara -> CEO decide -> Departamentos ejecutan`

### Layout Recomendado

#### Izquierda

Panel de navegación ejecutiva:

- Globo dorado.
- Sesión CEO.
- Inicio.
- CEREBRO.
- Departamentos.
- Riesgos.
- Decisiones.
- Perfil.

Reglas:

- Navegación simple.
- No saturar con todas las apps.
- Mantener departamentos como estructura principal.

#### Centro

Centro ejecutivo:

- Reunión con CEREBRO.
- Estado de Empresa IA.
- Próxima decisión CEO.
- Oportunidades.
- Riesgos.

Reglas:

- El centro debe conservar el foco de la home móvil.
- Las oportunidades y riesgos deben estar resumidos.
- Las decisiones deben poder escanearse rápido.

#### Derecha

Panel de mando rápido:

- Hablar con CEREBRO.
- Pedir trabajo a FORJA.
- Ver Auditoría.
- Ver NUBE.
- Ver SENTINELA.
- Ver DCFT protegido.
- Ver Arsenal.
- Ver oportunidades.

Reglas:

- Acciones cortas.
- No abrir integraciones reales desde esta fase.
- No convertirlo en panel técnico.
- Las acciones pueden ser conceptuales hasta futura implementación.

## 6. Departamentos Correctos

Usar exactamente estos departamentos.

### 1. DIRECCIÓN

Apps:

- CEO.
- CEREBRO.

Color sugerido:

- Dorado.

Función:

- Decisiones, prioridades, coordinación y gobierno ejecutivo.

Lectura para CEO:

- Aquí se define qué importa, qué se decide y qué se desbloquea.

### 2. CONSTRUCCIÓN

Apps:

- FORJA.
- HERMES.
- CREADOR DE APIS Y SKILLS.
- WEB FACTORY.

Color sugerido:

- Ámbar / naranja industrial tenue.

Función:

- Construir entregables, APIs, skills, webs, automatizaciones y soporte técnico.

Lectura para CEO:

- Aquí se convierte una decisión en entregable.

### 3. INTELIGENCIA

Apps:

- BUSCADOR DE TENDENCIAS.

Color sugerido:

- Violeta / azul profundo tenue.

Función:

- Detectar señales, novedades, oportunidades, amenazas y tendencias.

Lectura para CEO:

- Aquí aparece lo que el mercado, la IA o el entorno están mostrando.

Regla:

- No existe app nueva `INVESTIGADOR`.
- No existe app nueva `RADAR IA`.
- El radar oficial es `BUSCADOR DE TENDENCIAS`.

### 4. PRODUCTOS COMERCIALES

Apps:

- DCFT.
- SENTINELA.
- SNIFF AMAZON.
- COMERCIO AUTÓNOMO.
- APIs vendibles.
- Skills vendibles.
- Apps vendibles.

Color sugerido:

- Verde negocio / esmeralda tenue.

Función:

- Generar ingresos.

Lectura para CEO:

- Aquí vive lo que puede convertirse en producto, venta, licencia, servicio o unidad comercial.

Reglas:

- `SNIFF AMAZON` pertenece aquí.
- `SNIFF AMAZON` no pertenece a Inteligencia.
- `COMERCIO AUTÓNOMO` se mantiene separado de `SNIFF AMAZON`.
- `DCFT` se muestra como protegido / no-touch.

### 5. CONTENIDO Y CRECIMIENTO

Apps:

- PLUMA.
- LENTE.
- MARKETING.
- MARCA PERSONAL.

Color sugerido:

- Azul / cian creativo tenue.

Función:

- Contenido, marca, campañas, video, crecimiento y presencia pública.

Lectura para CEO:

- Aquí se transforma una señal en narrativa, publicación, campaña o crecimiento.

### 6. OPERACIÓN

Apps:

- NUBE.

Color sugerido:

- Azul nube / acero tenue.

Función:

- URLs, deploys, costos, variables, backups, dominios y health checks.

Lectura para CEO:

- Aquí se vigila el soporte operativo sin exponer ruido técnico innecesario.

Regla:

- `NUBE` queda sola en Operación.
- No tocar NUBE local desde esta fase.

### 7. CONTROL Y SEGURIDAD

Apps:

- AUDITORÍA.
- SENTINELA.

Color sugerido:

- Verde militar / rojo alerta controlado.

Función:

- Calidad, riesgos, revisión, seguridad, protección y control.

Lectura para CEO:

- Aquí se ve qué está protegido, qué requiere revisión y qué riesgo no debe ignorarse.

### 8. ALMACÉN ESTRATÉGICO

Apps:

- ARSENAL.

Color sugerido:

- Cobre / dorado oscuro.

Función:

- Almacenar APIs, skills, modelos, conectores, herramientas y capacidades.

Lectura para CEO:

- Aquí vive el inventario estratégico de piezas reutilizables de la Empresa IA.

Estado:

- `planned / pending_integration`.

## 7. Arsenal

`ARSENAL` debe documentarse como una app pendiente.

Definición:

- Almacén estratégico de APIs, skills, modelos, conectores, herramientas, prompts, módulos y capacidades.
- Debe representar APIs OpenAI, APIs Anthropic, APIs open source y APIs chinas/baratas/gratis.
- Debe representar modelos de video, modelos de texto y modelos de voz.
- Debe representar skills, conectores, APIs propias, APIs vendibles y apps vendibles.
- Debe comparar costos, limites, calidad, riesgos y mejor uso recomendado.

Estado:

- `planned / pending_integration`.

Reglas:

- No conectarlo todavía.
- No crear runtime.
- No secretos.
- No integraciones reales.
- No conectar APIs reales.
- No asumir producción.
- No darle prioridad visual sobre CEREBRO.

Cabinas futuras:

- Debe tener cabina corazón.
- Debe tener cabina técnica.
- No necesita cabina humana inicial completa.
- Trabaja por dentro como inventario estratégico.

Potencial comercial:

- Puede ser comercial en el futuro.
- Puede almacenar assets para APIs vendibles, skills vendibles y apps vendibles.
- Puede ayudar a separar piezas internas de piezas empaquetables.

## 8. Colores por App y Departamento

Las apps estratégicas no deben ser todas doradas.

La estética general debe ser:

- Oscura premium.
- Acentos tenues.
- Alto contraste controlado.
- Sin colores chillones.
- Sin estilo infantil.
- Sin saturación visual.

### Acentos por App

| App / Área | Acento recomendado | Uso visual |
| --- | --- | --- |
| CEREBRO | dorado | dirección ejecutiva, foco principal |
| FORJA | ámbar industrial | construcción, taller, producción |
| AUDITORÍA | azul/gris judicial o dorado balanza | revisión, criterio, control |
| NUBE | azul cloud | operación, infraestructura, disponibilidad |
| SENTINELA | verde militar / operativo | vigilancia, defensa, seguridad |
| DCFT | vino / borgoña protegido | producto regulatorio protegido |
| PLUMA | blanco / perla editorial | escritura, claridad, contenido |
| LENTE | violeta / cian visual | audiovisual, mirada, edición |
| MARKETING | magenta / rojo crecimiento tenue | campañas, distribución, tracción |
| MARCA PERSONAL | oro suave | presencia pública, reputación |
| BUSCADOR DE TENDENCIAS | violeta / azul señal | radar, señales, investigación |
| SNIFF AMAZON | naranja comercial | mercado, producto, comercio |
| COMERCIO AUTÓNOMO | verde comercio | ventas, automatización comercial |
| ARSENAL | cobre / dorado oscuro | almacenamiento estratégico |
| CREADOR DE APIS Y SKILLS | azul eléctrico controlado | capacidades, APIs, skills |
| WEB FACTORY | teal / azul web | interfaces, sitios, frontends |
| HERMES | plata / dorado mensajero | apoyo ligero, coordinación técnica |

### Semáforo de Estado

El semáforo ejecutivo usa solo:

- Verde.
- Amarillo.
- Rojo.

Los acentos por app no deben confundirse con el estado operativo.

## 9. Pantallas Propuestas

### 1. Inicio CEO

Propósito:

- Vista inmediata de la Empresa IA.

Contenido:

- Header compacto.
- Reunión con CEREBRO.
- Estado Empresa IA.
- Próxima decisión CEO.
- Oportunidades y riesgos resumidos.
- Departamentos.

### 2. Reunión con CEREBRO

Propósito:

- Agenda ejecutiva del día.

Contenido:

- Resumen de mañana.
- Resumen de tarde.
- Decisiones pendientes.
- Recomendaciones de CEREBRO.
- Preguntas para el CEO.
- Acciones sugeridas.

### 3. Departamentos

Propósito:

- Ver la Empresa IA por áreas, no por lista de apps.

Contenido:

- Los 8 departamentos correctos.
- Estado de cada departamento.
- Apps internas.
- Asuntos abiertos.
- Riesgo principal.
- Próxima acción.

### 4. Oportunidades

Propósito:

- Mostrar señales con potencial de ingreso, crecimiento o construcción.

Contenido:

- Fuente.
- Departamento sugerido.
- Potencial.
- Urgencia.
- Recomendación de CEREBRO.
- Decisión requerida.

### 5. Riesgos

Propósito:

- Mostrar lo que puede romper, bloquear o exponer la Empresa IA.

Contenido:

- Riesgo.
- Severidad.
- Departamento afectado.
- Estado.
- Recomendación.
- Decisión CEO si aplica.

### 6. Decisiones

Propósito:

- Cola ejecutiva del CEO.

Contenido:

- Decisión.
- Contexto.
- Por qué importa.
- Opciones.
- Recomendación de CEREBRO.
- Estado.

### 7. Productos Comerciales

Propósito:

- Ver lo que puede generar ingresos.

Contenido:

- DCFT.
- SENTINELA.
- SNIFF AMAZON.
- COMERCIO AUTÓNOMO.
- APIs vendibles.
- Skills vendibles.
- Apps vendibles.
- Estado comercial.
- Próximo movimiento.

### 8. Arsenal

Propósito:

- Ver el almacén estratégico futuro.

Contenido:

- Estado `planned / pending_integration`.
- Categorías previstas.
- Capacidades futuras.
- Relación con APIs, skills, modelos y conectores.
- Reglas de no conexión.

### 9. Perfil / Sesión

Propósito:

- Contexto mínimo de sesión CEO.

Contenido:

- Identidad CEO.
- Estado local.
- Preferencias de cabina.
- Cierre de sesión si aplica.

## 10. Cómo Debe Verlo el CEO

La cabina debe hacer sentir:

`Estoy viendo mi Empresa IA, no una lista de aplicaciones.`

Debe priorizar:

- Reunión con CEREBRO.
- Decisiones.
- Oportunidades.
- Riesgos.
- Departamentos.
- Ingresos potenciales.
- Bloqueos.
- Acciones rápidas.

No debe priorizar:

- Lista larga de apps.
- Términos técnicos.
- Tablas grandes.
- Dashboards densos.
- Cards interminables.
- Estados sin explicación.
- Rutas internas.
- Logs o detalles de runtime.

## 11. Criterios de Revisión del Documento

El documento deja definido:

- Cómo se verá en celular.
- Cómo se verá en desktop.
- Qué se ve primero.
- Qué se oculta.
- Qué va en departamentos.
- Qué colores usa cada área.
- Qué se mantiene no-touch.
- Cómo se evita saturación.
- Cómo se evita parecer dashboard técnico.
- Cómo se siente como Empresa IA.

Estado máximo permitido para este documento:

`Listo para revisión CEO`

## 12. Reglas No-Touch

Este documento no autoriza implementación.

No tocar:

- Frontend.
- `app.js`.
- `styles.css`.
- Producción.
- DCFT.
- FORJA real.
- SENTINELA real.
- NUBE local.
- Local Agent.
- SUNAT real.
- Runtimes externos.
- Rutas reales del bus.
- Integraciones reales.
- Secretos.
- Credenciales.

No ejecutar:

- Commit.
- Push.
- Deploy.

## 13. Siguiente Paso Recomendado

El siguiente paso debe ser una revisión CEO del diseño.

Después de esa revisión, y solo si el CEO autoriza explícitamente, se puede preparar un plan quirúrgico de frontend que:

- Respete la estructura mobile-first.
- No rompa desktop.
- No conecte integraciones reales.
- No altere productos protegidos.
- Mantenga `CEREBRO` como centro ejecutivo.
- Mantenga departamentos como unidad principal de navegación.

Hasta entonces, este documento queda como propuesta de diseño.
