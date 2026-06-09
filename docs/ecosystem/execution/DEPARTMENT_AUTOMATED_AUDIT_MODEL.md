# Department Automated Audit Model

Fecha: 2026-06-09

## Propósito

Bloque I permite que CEREBRO ordene auditorías automáticas por departamento y que AUDITORÍA genere diagnóstico, brechas, funciones faltantes, riesgos, prioridad, impacto económico, plan de corrección, posible tarea para FORJA y reporte para CEREBRO/CEO.

El sistema no inventa capacidades. Si no hay fuente, cabina o evidencia, el resultado debe decir `missing` o `unknown`.

## Inventario

Departamentos soportados:

- CEREBRO;
- AUDITORÍA;
- NUBE;
- FORJA;
- HERMES;
- PLUMA;
- LENTE;
- MARKETING;
- MARCA PERSONAL;
- BUSCADOR DE TENDENCIAS;
- WEB FACTORY;
- CREADOR DE APIs/SKILLS;
- E-COMMERCE;
- SNIFF AMAZON / CHIEF AMAZON;
- DCFT;
- SENTINELA;
- ARSENAL.

Los alias se normalizan sin duplicar registros.

## Estado de cabinas

Cada departamento se evalúa con:

- `heart_cabin`: `complete`, `partial`, `missing`, `unknown`;
- `technical_cabin`: `complete`, `partial`, `missing`, `unknown`;
- `human_cabin`: `complete`, `partial`, `missing`, `unknown`.

Regla:

- si existe una fuente exacta y suficiente, puede ser `complete`;
- si existe evidencia parcial, es `partial`;
- si se buscó y no existe, es `missing`;
- si no hay suficiente información para decidir, es `unknown`.

## Estado operativo

Estados:

- `ready`;
- `partial`;
- `needs_forge`;
- `needs_audit`;
- `blocked`;
- `governed`;
- `unknown`.

## Criterios de auditoría

AUDITORÍA evalúa:

- propósito claro;
- metas;
- funciones esperadas;
- relación con ingresos;
- relación con CEREBRO;
- relación con AUDITORÍA;
- relación con FORJA;
- relación con NUBE;
- riesgos;
- datos faltantes;
- readiness comercial;
- readiness técnico;
- readiness humano.

## Resultado de auditoría

Cada auditoría guarda:

- departamento;
- fuente revisada;
- cabina corazón;
- cabina técnica;
- cabina humana;
- brechas;
- tareas sugeridas;
- prioridad;
- impacto económico;
- riesgo;
- estado;
- recomendación;
- fecha/hora;
- audit trail.

Flags permanentes:

- `external_connection_enabled=false`;
- `runtime_connected=false`;
- `sunat_enabled=false`.

## Flujo CEREBRO / AUDITORÍA / FORJA

1. CEO da instrucción a CEREBRO.
2. CEREBRO crea misión de auditoría.
3. CEREBRO envía a AUDITORÍA.
4. AUDITORÍA revisa fuentes, cabinas y metas.
5. AUDITORÍA genera brechas.
6. Si hay faltantes implementables, se prepara tarea para FORJA.
7. FORJA queda con tarea preparada, sin ejecución externa real.
8. AUDITORÍA puede marcar revisión posterior.
9. CEREBRO reporta al CEO.

## Primeras auditorías soportadas

### PLUMA

Revisa:

- libros;
- bestseller como meta larga;
- artículos;
- posts;
- newsletters;
- guiones;
- contenido comercial;
- español/inglés;
- apoyo a marca personal y marketing.

### LENTE

Revisa:

- YouTube;
- TikTok;
- avatares;
- animación;
- podcasts con avatares;
- canales por nicho;
- meta de 5 canales con 100K+ suscriptores.

### MARKETING

Revisa:

- orgánico;
- campañas pagadas con ROI;
- embudos;
- leads;
- capacidad de vender ofertas cuando CEO lo decida.

Pagos y campañas pagadas requieren aprobación CEO.

### MARCA PERSONAL

Revisa:

- metas de seguidores;
- TikTok;
- Instagram;
- LinkedIn;
- X;
- YouTube.

### E-COMMERCE

Revisa meta separada USD 10,000 mensual.

### SNIFF AMAZON / CHIEF AMAZON

Revisa oportunidades Amazon/marketplace sin contactar Amazon ni proveedores reales.

### DCFT

Revisa actualización y readiness.

Reglas:

- no SUNAT real;
- no runtime real;
- no meta de venta propia en esta auditoría.

### SENTINELA

Revisa actualización defensiva de seguridad.

Reglas:

- no runtime productivo;
- sin etiqueta comercial propia;
- no meta de venta propia.

## Reglas anti-invención

- No declarar cabina completa sin fuente.
- No declarar FORJA implementado si solo se creó tarea preparada.
- No declarar DCFT real.
- No declarar SENTINELA real.
- No activar SUNAT.
- No activar APIs externas.
- No crear cuentas externas.
- No ejecutar pagos reales.
- No exponer secretos.
