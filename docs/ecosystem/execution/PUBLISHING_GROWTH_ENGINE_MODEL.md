# Publishing & Growth Engine Model

Fecha: 2026-06-09

## Propósito

Preparar el motor operativo de contenido orgánico, crecimiento y publicación coordinada entre PLUMA, LENTE, MARKETING, MARCA PERSONAL, E-COMMERCE, SNIFF AMAZON y CEREBRO.

Este modelo no publica real si no existe conexión técnica de cuenta/API. Si la cuenta no está conectada, el estado efectivo es:

- `account_status="not_connected"`
- `publication_mode="prepared"`
- `publication_status="prepared"`

## Reglas

- Publicación orgánica en cuenta oficial ya conectada no requiere aprobación CEO.
- Campaña pagada requiere aprobación CEO con ROI.
- Crear cuenta externa oficial nueva requiere aprobación CEO.
- Conectar APIs con costo requiere aprobación CEO.
- No se inventan métricas, alcance, ventas, views ni conversiones.
- Si falta evidencia, `evidence_status="missing"`.
- Si el nicho de LENTE no está definido, `niche_status="needs_ceo_definition"`.

## Canales Iniciales

- TikTok.
- Instagram.
- YouTube.
- YouTube Shorts.
- LinkedIn.
- X.
- Facebook.
- Blog/Web.
- Newsletter.

Todos empiezan como preparados si no hay cuenta conectada.

## Modelo De Datos

Tablas locales preparadas:

- `content_campaigns`
- `content_items`
- `publishing_channels`
- `publishing_accounts`
- `publishing_schedule`
- `publishing_events`
- `growth_metrics`
- `content_approvals`

Cada pieza registra:

- título;
- formato;
- departamento owner;
- canal;
- estado de cuenta;
- idioma;
- nicho;
- estado;
- fecha programada;
- modo de publicación;
- aprobación requerida;
- vínculo con Revenue OS;
- métricas con evidencia.

## PLUMA

PLUMA prepara:

- posts;
- artículos;
- newsletters;
- guiones;
- ideas de libros;
- contenido de autoridad;
- contenido comercial;
- español e inglés.

## LENTE

LENTE prepara:

- videos;
- shorts;
- reels;
- miniaturas;
- avatares;
- animaciones;
- podcast avatar;
- canales por nicho.

Si el nicho final no está definido, queda `needs_ceo_definition`. No se fijan nichos finales sin decisión CEO.

## MARKETING

MARKETING prepara:

- campañas orgánicas;
- embudos;
- validación de demanda;
- soporte DCFT/SENTINELA;
- propuestas pagadas con ROI.

Paid campaigns quedan bloqueadas hasta aprobación CEO.

## MARCA PERSONAL

Marca Personal prepara autoridad CEO en:

- TikTok;
- Instagram;
- LinkedIn;
- X;
- YouTube.

Si falta cuenta conectada, queda preparado y no publicado.

## E-COMMERCE Y SNIFF AMAZON

E-COMMERCE mantiene su ruta separada. SNIFF AMAZON puede producir señales para contenido y oportunidades, pero no compra, no publica venta real, no registra inventario y no inventa métricas.

## CEREBRO

CEREBRO puede:

- crear plan de contenido;
- pedir piezas a PLUMA;
- pedir visuales a LENTE;
- pedir campaña orgánica a MARKETING;
- preparar publicación si no hay conexión;
- escalar aprobación si hay campaña pagada o cuenta nueva.

CEREBRO no puede:

- crear cuentas externas reales;
- lanzar campañas pagadas;
- publicar real sin conexión;
- inventar métricas;
- declarar ventas.

## Relación Con Revenue OS

Publishing & Growth alimenta Revenue OS y Revenue Sprint con evidencia orgánica. No declara ingresos reales. Solo puede proponer inversión si existe señal y ROI preparado para revisión CEO.

## Criterios De Cierre

- Canales preparados.
- Contenido preparado.
- Reglas de aprobación activas.
- Centro CEO muestra Publishing.
- Cabina muestra cuentas conectadas/no conectadas.
- Tests PASS.
- No push, no deploy, no publicación real.
