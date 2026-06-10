# CEO Pending Definitions Model

Fecha: 2026-06-09

## Propósito

Este modelo define cómo CEREBRO y los departamentos del ecosistema deben operar cuando falta una definición del CEO.

El objetivo es mantener movimiento sin inventar datos, sin crear compromisos externos y sin convertir una suposición en estado real.

## Principio operativo

Si falta un dato del CEO:

- crear o actualizar una entrada en `CEO_PENDING_DEFINITIONS_REGISTER.md`;
- marcar el estado como `pending_ceo`, `unknown`, `needs_discovery`, `needs_audit` o `prepared_until_defined`;
- continuar solo en modo preparado cuando sea seguro;
- escalar al CEO si el dato afecta dinero, cuentas, credenciales, publicación externa, riesgo legal o reputación.

## Cuándo crear una entrada

CEREBRO debe crear una entrada cuando:

- una misión depende de una decisión del CEO no confirmada;
- una oportunidad económica requiere información comercial no validada;
- una publicación depende de cuentas oficiales no confirmadas;
- una pieza de PLUMA o LENTE depende de nicho, canal, tono o identidad no definidos;
- una brecha técnica necesita definir si FORJA puede trabajar o solo preparar;
- Product Readiness no tiene evidencia suficiente sobre DCFT o SENTINELA;
- NUBE, SENTINELA o AUDITORÍA detectan riesgo por falta de gobierno de credenciales;
- Revenue OS no puede distinguir hipótesis, estimación o venta real.

## Reglas por tipo de dato faltante

### Dinero

Si el dato afecta dinero real, inversión, campaña pagada, proveedor, compra, contratación o herramienta con costo:

- estado: `pending_ceo`;
- ejecución real: bloqueada;
- modo permitido: preparado;
- acción: pedir definición CEO con ROI, riesgo y alternativa.

### Publicación externa

Si el dato afecta publicación, cuenta externa, canal, identidad pública, marca o calendario real:

- estado: `pending_ceo` o `needs_discovery`;
- ejecución real: bloqueada hasta confirmar cuenta conectada o autorización;
- modo permitido: preparar borrador, calendario y piezas sin publicar.

### Cuentas o credenciales

Si el dato afecta credenciales sensibles, API keys, passwords, tokens, cuentas externas o acceso administrativo:

- estado: `pending_ceo`;
- ejecución real: bloqueada;
- modo permitido: documentación de gobierno sin secretos;
- acción: usar vault o variables seguras, nunca chat ni documentos.

### Documentación interna

Si el dato solo afecta documentación interna o modelo conceptual:

- estado: `prepared_until_defined`;
- ejecución real: no aplica;
- modo permitido: preparar alternativas marcadas como hipótesis.

### Producto protegido

Si el dato afecta DCFT, SENTINELA, SUNAT, Local Agent, cuentas externas, APIs externas reales o runtime productivo:

- estado: `needs_audit`, `pending_ceo` o `blocked`;
- ejecución real: bloqueada;
- modo permitido: auditoría, readiness o preparación documental.

## Responsabilidades por departamento

### CEREBRO

- Detecta dependencia pendiente.
- Prioriza impacto.
- Registra la definición faltante.
- Decide si puede continuar en modo preparado.
- Escala al CEO cuando hay dinero, credenciales, publicación externa o riesgo alto.

### AUDITORÍA

- Revisa que no se declare real lo que está preparado.
- Bloquea claims sin evidencia.
- Marca `needs_audit` cuando falte validación.

### MARKETING

- Puede preparar campañas, ofertas y paquetes comerciales.
- No puede declarar cuentas, ventas, métricas o campañas pagadas reales sin evidencia.

### PLUMA

- Puede proponer textos, guiones, libros y líneas editoriales.
- No puede cerrar una línea editorial final sin definición estratégica.

### LENTE

- Puede preparar formatos, estilos, visuales y escenarios de canal.
- No puede declarar nichos o canales finales sin definición CEO.

### MARCA PERSONAL

- Puede preparar estrategia.
- No puede mezclar cuentas personales actuales y cuentas nuevas sin decisión CEO.

### E-COMMERCE y SNIFF AMAZON

- Pueden registrar hipótesis y oportunidades.
- No pueden duplicar nombre oficial ni declarar métricas, compras o ventas reales sin evidencia.

### DCFT y SENTINELA

- Deben mantenerse preparados, auditables y actualizados.
- No tienen meta de venta propia.
- MARKETING vende cuando exista readiness suficiente.
- No se declaran listos si el estado real está `unknown` o `needs_audit`.

### FORJA

- Puede recibir tareas preparadas.
- No debe marcar implementado si no hay evidencia de ejecución.

### NUBE

- Puede registrar riesgos, costos, URLs y preparación operativa.
- No despliega ni toca cuentas externas sin flujo autorizado.

## Estados de salida

Cuando una definición pendiente afecta una misión, la misión debe usar uno de estos estados:

- `prepared_until_defined`
- `waiting_ceo_definition`
- `needs_discovery`
- `needs_audit`
- `blocked_by_missing_definition`

No usar:

- `approved`
- `completed`
- `published`
- `connected`
- `revenue_confirmed`

si falta evidencia o decisión CEO.

## Integración con modelos existentes

Los modelos de CEREBRO, Revenue OS, Publishing & Growth y Product Readiness deben referenciar este registro para evitar:

- inventar cuentas oficiales;
- inventar nichos;
- inventar ventas;
- inventar métricas;
- inventar estado de DCFT o SENTINELA;
- inventar credenciales, conexiones o runtime real.

## Regla anti-alucinación

Una ausencia de definición no es un permiso para asumir.

Cuando falte información:

- registrar;
- preparar si es seguro;
- bloquear si hay riesgo;
- pedir CEO si afecta dinero, reputación, credenciales, publicación externa o productos protegidos.
