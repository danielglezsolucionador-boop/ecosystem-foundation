# ECOSYSTEM COMPANY OPERATING MODEL

Estado: modelo operativo maestro documentado.
Alcance: Empresa IA completa, con corrección explícita de departamentos, jerarquía, flujos y cabina.
Fase siguiente sugerida: `ECOSYSTEM_COMPANY_CABIN_REDESIGN`.

## 1. Regla de Corrección Aplicada

Este documento reemplaza la idea de crear o documentar una app nueva llamada `INVESTIGADOR` o `RADAR IA`.

La función de investigación, detección de señales, análisis de oportunidades, observación de tendencias y radar estratégico pertenece a:

`BUSCADOR DE TENDENCIAS`

Por tanto:

- No se crea una app nueva `INVESTIGADOR`.
- No se crea una app nueva `RADAR IA`.
- No se duplica el rol de investigación estratégica.
- El radar de mercado queda integrado dentro de `BUSCADOR DE TENDENCIAS`.

## 2. Modelo de Dirección

La Empresa IA funciona con una dirección ejecutiva clara:

- `CEO`: autoridad final, define prioridades, aprueba decisiones, desbloquea riesgos y puede hablar con cualquier departamento o app directamente.
- `CEREBRO`: Jefe de Gabinete IA / Chief of Staff. Recibe señales de apps y departamentos, ordena prioridades, prepara decisiones, resume riesgos y presenta al CEO lo que requiere criterio humano.

Flujo por defecto:

`Apps / Departamentos -> CEREBRO -> CEO`

Excepción permitida:

`CEO -> cualquier app o departamento`

El CEO no queda encerrado en el flujo jerárquico. La jerarquía ordena la operación diaria, pero no limita la autoridad ejecutiva.

## 3. Departamentos Corregidos

### DIRECCIÓN

- `CEO`
- `CEREBRO`

Responsabilidad: gobierno ejecutivo, prioridades, decisiones, revisión diaria, desbloqueo de riesgos y coherencia estratégica.

### CONSTRUCCIÓN

- `FORJA`
- `HERMES`
- `CREADOR DE APIS Y SKILLS`
- `WEB FACTORY`

Responsabilidad: construir, empaquetar, convertir ideas en activos técnicos, mantener piezas ligeras de operación y preparar capacidades reutilizables.

`HERMES` vive aquí como soporte ligero de construcción y operación. No dirige la empresa ni reemplaza a CEREBRO.

`CREADOR DE APIS` queda corregido como:

`CREADOR DE APIS Y SKILLS`

Su responsabilidad incluye APIs internas, APIs vendibles, skills internas, skills vendibles, empaquetado técnico y preparación de activos reutilizables.

### INTELIGENCIA

- `BUSCADOR DE TENDENCIAS`

Responsabilidad: investigación de mercado, radar de señales, oportunidades de IA, oportunidades de video, cambios regulatorios, tendencias de contenido, señales comerciales y alertas estratégicas.

Este departamento absorbe completamente el rol antes planteado como `INVESTIGADOR` o `RADAR IA`.

### PRODUCTOS COMERCIALES

- `DCFT`
- `SENTINELA`
- `SNIFF AMAZON`
- `COMERCIO AUTÓNOMO`
- `APIs vendibles`
- `Skills vendibles`
- `Apps vendibles`

Responsabilidad: activos que pueden convertirse en producto, oferta comercial, servicio, licencia, herramienta vendible o unidad de negocio.

`SNIFF AMAZON` pertenece aquí como producto comercial. No pertenece al departamento de Inteligencia, aunque pueda consumir señales del `BUSCADOR DE TENDENCIAS`.

`COMERCIO AUTÓNOMO` permanece separado de `SNIFF AMAZON`. Pueden colaborar, pero no se fusionan.

### CONTENIDO Y CRECIMIENTO

- `PLUMA`
- `LENTE`
- `MARKETING`
- `MARCA PERSONAL`

Responsabilidad: contenido, narrativa, crecimiento, distribución, presencia pública, material educativo, campañas y posicionamiento.

### OPERACIÓN

- `NUBE`

Responsabilidad: operación local, infraestructura controlada, disponibilidad, empaquetado operativo y soporte de ejecución no productivo cuando corresponda.

### CONTROL Y SEGURIDAD

- `AUDITORÍA`
- `SENTINELA`

Responsabilidad: revisión, seguridad, riesgos, validación, vigilancia defensiva, pruebas, controles y protección del ecosistema.

`SENTINELA` tiene doble lectura:

- Producto comercial en `PRODUCTOS COMERCIALES`.
- Capacidad de control en `CONTROL Y SEGURIDAD`.

### ALMACÉN ESTRATÉGICO

- `ARSENAL`

Responsabilidad: inventario estratégico de assets, prompts, APIs, skills, documentos, piezas reutilizables, materiales técnicos, módulos, paquetes comerciales y componentes listos para ensamblar.

`ARSENAL` es una app pendiente. Estado recomendado:

`planned / pending_integration`

No debe tratarse como sistema productivo existente.

## 4. Roles Operativos Principales

### CEREBRO

Rol: Jefe de Gabinete IA / Chief of Staff.

Funciones:

- Recibir información de departamentos.
- Consolidar señales.
- Preparar agenda diaria.
- Separar decisiones de ejecución automática.
- Traducir riesgos técnicos a decisiones ejecutivas.
- Presentar al CEO un tablero claro de estado, oportunidades, bloqueos y próximos movimientos.

### BUSCADOR DE TENDENCIAS

Rol: radar estratégico oficial.

Funciones:

- Detectar oportunidades de IA.
- Detectar oportunidades de video.
- Detectar señales de ciberseguridad útiles para `SENTINELA`.
- Detectar cambios regulatorios relevantes para `DCFT`.
- Detectar temas para `PLUMA`, `LENTE`, `MARKETING` y `MARCA PERSONAL`.
- Detectar productos, APIs, skills o apps con potencial comercial.

No es una app nueva de investigación. Es la app responsable del radar.

### ARSENAL

Rol: almacén estratégico pendiente.

Funciones esperadas:

- Guardar assets reutilizables.
- Organizar prompts, skills, APIs, módulos y documentos.
- Separar piezas internas de piezas vendibles.
- Preparar inventario para construcción y comercialización.
- Servir como memoria material de activos listos para uso.
- Registrar APIs OpenAI, APIs Anthropic, APIs open source y APIs chinas/baratas/gratis como opciones futuras.
- Registrar modelos de video, texto y voz sin activar proveedores.
- Registrar skills, conectores, APIs propias, APIs vendibles y apps vendibles.
- Comparar costos, limites, calidad, riesgos y mejor uso recomendado.

Estado:

`planned / pending_integration`

Restricción:

- No se integra todavía.
- No se asume producción.
- No se conecta a sistemas reales.
- No tiene runtime real.
- No guarda secretos.
- No conecta APIs reales.
- No requiere cabina humana inicial.
- Sí requerirá cabina corazón, cabina técnica y operación interna cuando sea diseñado.

### HERMES

Rol: soporte ligero de construcción y operación.

Ubicación: `CONSTRUCCIÓN`.

Funciones:

- Apoyar tareas internas.
- Ayudar en preparación de piezas.
- Coordinar pequeños trabajos técnicos.
- Servir como asistente operativo de construcción.

No reemplaza a `CEREBRO`.

### CREADOR DE APIS Y SKILLS

Rol: fábrica de capacidades reutilizables.

Funciones:

- Crear APIs internas.
- Crear APIs vendibles.
- Crear skills internas.
- Crear skills vendibles.
- Documentar contratos.
- Preparar empaquetado comercial cuando aplique.

### SNIFF AMAZON

Rol: producto comercial.

Ubicación: `PRODUCTOS COMERCIALES`.

Funciones:

- Analizar oportunidades comerciales ligadas a Amazon.
- Detectar productos, señales o patrones vendibles.
- Alimentar decisiones de producto.

No pertenece a Inteligencia. Puede recibir señales del `BUSCADOR DE TENDENCIAS`, pero su naturaleza es comercial.

## 5. Reunión Diaria CEO + CEREBRO

### Reunión de Mañana

Objetivo: decidir el foco del día.

Entrada:

- Estado de departamentos.
- Oportunidades nuevas.
- Riesgos activos.
- Bloqueos.
- Tareas que requieren decisión CEO.

Salida:

- Prioridades del día.
- Decisiones CEO.
- Riesgos aceptados, mitigados o bloqueados.
- Acciones asignadas a departamentos.

Formato recomendado:

1. Estado Empresa IA.
2. Decisiones pendientes.
3. Oportunidades.
4. Riesgos.
5. Acciones por departamento.

### Reunión de Tarde

Objetivo: cerrar el día y preparar continuidad.

Entrada:

- Avances del día.
- Cambios detectados.
- Riesgos nuevos.
- Decisiones no resueltas.
- Próximas oportunidades.

Salida:

- Resumen ejecutivo.
- Decisiones para el día siguiente.
- Alertas para CEO.
- Ajuste de prioridades.

Formato recomendado:

1. Qué avanzó.
2. Qué quedó bloqueado.
3. Qué cambió.
4. Qué debe decidir el CEO.
5. Qué se revisa mañana.

## 6. Flujos Operativos Definidos

### Flujo de Oportunidad IA / Video

1. `BUSCADOR DE TENDENCIAS` detecta señal de IA o video.
2. `CEREBRO` evalúa relevancia estratégica.
3. `PLUMA`, `LENTE`, `MARKETING` o `MARCA PERSONAL` preparan ángulo de contenido si aplica.
4. `FORJA`, `WEB FACTORY` o `CREADOR DE APIS Y SKILLS` evalúan posibilidad técnica si aplica.
5. `CEREBRO` presenta recomendación al `CEO`.
6. `CEO` decide avanzar, pausar o descartar.

### Flujo de Ciberseguridad para SENTINELA

1. `BUSCADOR DE TENDENCIAS` detecta señal de ciberseguridad.
2. `CEREBRO` clasifica urgencia.
3. `SENTINELA` evalúa relevancia defensiva o comercial.
4. `AUDITORÍA` revisa riesgo y controles.
5. `CEREBRO` consolida recomendación.
6. `CEO` decide si se transforma en mejora, alerta, producto o investigación.

### Flujo Regulatorio para DCFT

1. `BUSCADOR DE TENDENCIAS` detecta cambio regulatorio o señal normativa.
2. `CEREBRO` filtra impacto.
3. `DCFT` recibe la señal como insumo protegido.
4. `AUDITORÍA` revisa riesgo de interpretación.
5. `CEREBRO` prepara resumen ejecutivo.
6. `CEO` decide si se estudia, se documenta o se agenda para revisión.

Restricción:

`DCFT` no se toca desde este documento. No se modifica código, flujo productivo ni integraciones.

### Flujo de Creación de API / Skill Vendible

1. `BUSCADOR DE TENDENCIAS`, `CEO`, `CEREBRO` o un producto comercial detectan necesidad.
2. `CEREBRO` define prioridad y alcance.
3. `CREADOR DE APIS Y SKILLS` diseña capacidad.
4. `FORJA` o `WEB FACTORY` apoyan construcción si aplica.
5. `AUDITORÍA` revisa control, seguridad y límites.
6. `ARSENAL`, cuando exista, almacena la pieza empaquetada.
7. `CEREBRO` presenta estado al `CEO`.
8. `CEO` decide uso interno, venta, pausa o descarte.

### Flujo de Contenido / Marca

1. `BUSCADOR DE TENDENCIAS` detecta tema, señal o narrativa posible.
2. `CEREBRO` decide si encaja con la estrategia.
3. `PLUMA` prepara texto.
4. `LENTE` prepara visuales o criterio audiovisual.
5. `MARKETING` define distribución.
6. `MARCA PERSONAL` adapta tono y presencia.
7. `CEREBRO` consolida.
8. `CEO` aprueba, ajusta o descarta.

### Flujo de Producto Comercial

1. Señal nace desde `BUSCADOR DE TENDENCIAS`, `SNIFF AMAZON`, `COMERCIO AUTÓNOMO`, `DCFT`, `SENTINELA` o el `CEO`.
2. `CEREBRO` evalúa potencial.
3. Departamento propietario define hipótesis comercial.
4. `CONSTRUCCIÓN` evalúa factibilidad.
5. `CONTROL Y SEGURIDAD` revisa riesgos.
6. `ARSENAL`, cuando exista, organiza assets reutilizables.
7. `CEREBRO` presenta caso ejecutivo.
8. `CEO` decide si se convierte en producto, experimento, backlog o descarte.

## 7. Cabina Mobile-First

La cabina de Empresa IA debe diseñarse primero para móvil.

La primera pantalla móvil solo debe mostrar:

- `Reunión con CEREBRO`
- `Estado Empresa IA`
- `Decisiones CEO`
- `Oportunidades`
- `Riesgos`
- `Departamentos`

Regla de diseño:

La pantalla inicial móvil debe servir al CEO en pocos segundos. No debe estar saturada por paneles, explicaciones largas, tablas densas ni módulos secundarios.

Prioridad visual:

1. Qué necesita decidir el CEO.
2. Qué está pasando en la empresa.
3. Qué oportunidad apareció.
4. Qué riesgo exige atención.
5. Qué departamento requiere foco.

## 8. Cabina Desktop

Desktop extiende la experiencia móvil. No la contradice.

Estructura recomendada:

- Panel izquierdo: departamentos, navegación, estado por área.
- Centro ejecutivo: reunión con CEREBRO, estado general, decisiones CEO.
- Panel derecho: acciones rápidas, riesgos, oportunidades y próximos pasos.
- Vista de departamentos: lectura extendida por área.
- Vista de decisiones: cola ejecutiva.
- Vista de oportunidades: señales, priorización y estado.
- Vista de riesgos: severidad, dueño, recomendación y decisión requerida.

Desktop puede mostrar más contexto, pero la lógica central sigue siendo:

`CEREBRO prepara -> CEO decide -> Departamentos ejecutan`

## 9. Reglas de Control

Este documento es de planificación operativa. No autoriza cambios reales.

Queda explícitamente fuera de alcance:

- Commit.
- Push.
- Deploy.
- Producción.
- Cambios en `DCFT`.
- Cambios en `FORJA` real.
- Cambios en `SENTINELA` real.
- Cambios en `NUBE` local.
- Cambios en Local Agent.
- SUNAT real.
- Runtimes.
- Rutas de bus reales.
- Integraciones reales.
- Secretos.
- Credenciales.
- Configuración productiva.

Toda ejecución técnica futura debe pasar por propuesta, plan, validación y decisión CEO.

## 10. Estados Recomendados de Apps

| App / Capacidad | Departamento | Estado recomendado | Nota |
| --- | --- | --- | --- |
| CEO | DIRECCIÓN | activo | Autoridad final |
| CEREBRO | DIRECCIÓN | activo / core | Chief of Staff |
| FORJA | CONSTRUCCIÓN | activo / existente | No tocar desde este documento |
| HERMES | CONSTRUCCIÓN | soporte ligero | Constructor/ops support |
| CREADOR DE APIS Y SKILLS | CONSTRUCCIÓN | definido | Extiende Creador de APIs |
| WEB FACTORY | CONSTRUCCIÓN | definido | Construcción web |
| BUSCADOR DE TENDENCIAS | INTELIGENCIA | radar oficial | Sustituye Investigador/Radar IA |
| DCFT | PRODUCTOS COMERCIALES | protegido | No tocar |
| SENTINELA | PRODUCTOS COMERCIALES / CONTROL | protegido | Producto y control |
| SNIFF AMAZON | PRODUCTOS COMERCIALES | definido | No pertenece a Inteligencia |
| COMERCIO AUTÓNOMO | PRODUCTOS COMERCIALES | definido | Separado de Sniff Amazon |
| PLUMA | CONTENIDO Y CRECIMIENTO | definido | Texto y narrativa |
| LENTE | CONTENIDO Y CRECIMIENTO | definido | Visual/audiovisual |
| MARKETING | CONTENIDO Y CRECIMIENTO | definido | Distribución |
| MARCA PERSONAL | CONTENIDO Y CRECIMIENTO | definido | Presencia pública |
| NUBE | OPERACIÓN | protegido | No tocar |
| AUDITORÍA | CONTROL Y SEGURIDAD | definido | Validación y control |
| ARSENAL | ALMACÉN ESTRATÉGICO | planned / pending_integration | Nueva app pendiente |

## 11. Próximo Paso Recomendado

Crear una propuesta separada:

`ECOSYSTEM_COMPANY_CABIN_REDESIGN`

Esa propuesta debe definir:

- Arquitectura mobile-first.
- Vistas mínimas para CEO.
- Vistas extendidas para desktop.
- Estados por departamento.
- Cola de decisiones CEO.
- Integración futura de `ARSENAL`.
- Relación visual entre `CEREBRO`, departamentos y productos comerciales.

No debe implementar cambios de frontend hasta que exista una propuesta clara y una validación de alcance.

## 12. Cierre Operativo

La Empresa IA queda organizada como un sistema dirigido por el CEO, coordinado por CEREBRO y ejecutado por departamentos especializados.

La corrección central es:

`BUSCADOR DE TENDENCIAS` es el radar oficial.

`ARSENAL` es la nueva app pendiente.

`HERMES` queda en construcción.

`CREADOR DE APIS` evoluciona a `CREADOR DE APIS Y SKILLS`.

`SNIFF AMAZON` queda en productos comerciales.

La cabina debe partir de móvil y expandirse a desktop sin romper la claridad ejecutiva.
