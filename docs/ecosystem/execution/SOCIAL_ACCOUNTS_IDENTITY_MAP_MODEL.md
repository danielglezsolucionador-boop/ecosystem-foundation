# Social Accounts & Identity Map Model

Fecha: 2026-06-10
Fase: S.2
Baseline: `v1-ai-company-operating-system` / `d29455a` mas cambios locales validados de S.1.

## Proposito

S.2 crea el mapa oficial preparado de identidades, marcas, cuentas y canales sociales que el ecosistema necesitara para operar en el mundo real.

Este modelo no crea cuentas, no conecta redes, no publica contenido, no guarda credenciales y no habilita APIs externas.

## Identidad del ecosistema

La identidad matriz es `Ecosistema IA`. Puede preparar presencia en Blog/Web, Newsletter, LinkedIn, X y canales sociales, pero todo queda en estado `unknown`, `existing_unconfirmed`, `proposed_new` o `prepared` hasta que exista evidencia o decision CEO.

Reglas:

- Si existe una cuenta pero no hay evidencia, estado `existing_unconfirmed`.
- Si se propone crear una cuenta, estado `proposed_new` y requiere CEO.
- Si solo se prepara contenido o estructura local, estado `prepared`.
- Si falta definicion, estado `unknown` o `needs_ceo_definition`.

## Marca personal CEO

La marca personal requiere confirmacion directa del CEO antes de definir handles, canales oficiales, podcast o perfiles publicos.

PLUMA, LENTE y MARKETING pueden preparar contenido, guiones y calendario, pero no publicar real.

## Marcas de productos

Productos representados:

- DCFT.
- SENTINELA.
- APIs/Skills.
- E-Commerce.
- SNIFF AMAZON / CHIEF AMAZON.

Reglas:

- MARKETING puede preparar posicionamiento.
- Web Factory puede preparar landings locales.
- PLUMA y LENTE pueden preparar piezas.
- DCFT y SENTINELA no se tocan como runtime real desde S.2.
- No se hacen claims legales, tributarios o de seguridad sin evidencia.

## Marcas de canales

Canales contemplados:

- TikTok.
- Instagram.
- YouTube.
- YouTube Shorts.
- LinkedIn.
- X.
- Facebook.
- Blog/Web.
- Newsletter.
- Podcast.

Cada canal debe separar cuenta actual, cuenta propuesta, evidencia, owner interno, riesgo y accion recomendada.

## Estados permitidos

- `unknown`
- `existing_unconfirmed`
- `confirmed_existing`
- `proposed_new`
- `prepared`
- `needs_ceo_definition`
- `needs_credentials`
- `needs_account_creation`
- `blocked`

## Reglas de aprobacion

Requiere CEO:

- crear cuenta externa nueva;
- declarar cuenta oficial;
- usar marca personal CEO;
- conectar credenciales;
- publicar real en cuenta no confirmada;
- resolver identidad publica sensible;
- crear Newsletter/Podcast/canal externo;
- definir producto/canal DCFT o SENTINELA.

No requiere CEO:

- preparar documento;
- preparar calendario;
- preparar piezas PLUMA/LENTE;
- preparar landing local;
- mantener estado `prepared` sin publicar.

## Riesgos de identidad publica

Riesgos principales:

- publicar en cuenta equivocada;
- crear marca duplicada;
- exponer credenciales;
- declarar cuenta oficial sin evidencia;
- lanzar producto con claims no validados;
- publicar contenido de seguridad, tributacion o finanzas sin fuente;
- confundir `prepared` con `published`.

## Relacion con departamentos

CEREBRO:
coordina el mapa, prioriza definiciones y escala al CEO.

MARKETING:
propone canales, posicionamiento y paquetes comerciales.

PLUMA:
prepara textos, articulos, newsletters, guiones y autoridad.

LENTE:
prepara videos, shorts, reels, visuales, miniaturas y podcast/avatar.

Revenue OS:
relaciona canales con oportunidad de ingresos, sin inventar ventas ni metricas.

AUDITORIA:
verifica que no existan claims falsos, credenciales o publicacion real.

## Reglas anti-alucinacion

- Sin evidencia, estado `unknown`.
- No declarar `confirmed_existing` sin fuente.
- No declarar `published` desde S.2.
- No declarar seguidores, ventas, metricas o conversiones.
- No guardar passwords, tokens, API keys ni sesiones.
- No usar `prepared` como sinonimo de cuenta conectada.
