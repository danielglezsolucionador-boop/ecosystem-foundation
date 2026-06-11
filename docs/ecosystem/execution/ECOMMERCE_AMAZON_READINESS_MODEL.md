# E-Commerce + Amazon Readiness Model

Fecha: 2026-06-10
Fase: S.5
Baseline: `v1-ai-company-operating-system` / `d29455a` mas cambios locales S.1/S.2.

## Proposito

S.5 prepara el ecosistema para operar E-COMMERCE y SNIFF AMAZON / CHIEF AMAZON sin ejecutar ventas reales.

No crea tienda real, no conecta pasarelas, no conecta Amazon Seller, no compra inventario, no paga herramientas, no scrapea sitios prohibidos y no inventa productos ganadores, ventas ni margen.

## Meta separada

E-COMMERCE tiene meta separada:

- Meta e-commerce: USD 10,000 mensuales.
- Meta global ecosistema: USD 6,000 mensuales.
- `separated_from_global_goal=true`.

Revenue OS y CEREBRO no deben mezclar ambas metas. Una oportunidad e-commerce no cuenta como pipeline global hasta que exista evidencia y decision comercial.

## SNIFF AMAZON / CHIEF AMAZON

SNIFF AMAZON / CHIEF AMAZON funciona como radar preparado:

- detecta senales;
- propone research;
- identifica riesgos;
- no declara producto ganador;
- no conecta Amazon Seller;
- no compra inventario;
- no usa scraping prohibido;
- no usa herramienta pagada sin CEO y ROI.

## Tienda propia, marketplace y Amazon

Tienda propia:

- puede preparar arquitectura, contenido, analitica manual y flujo conceptual;
- requiere CEO para pasarela de pago, proveedor, inventario o dominio/cuenta con costo.

Marketplace:

- requiere cuenta externa;
- requiere credenciales;
- requiere decision CEO antes de operar.

Amazon:

- Amazon Seller requiere CEO, credenciales y revision;
- herramientas pagadas requieren ROI;
- buy box/tracking requiere fuente permitida;
- hipotesis de categoria no son producto ganador.

## Inversion

Toda inversion real requiere CEO:

- inventario;
- herramienta pagada;
- proveedor;
- pasarela;
- cuenta externa;
- marketplace;
- Amazon Seller.

## Inventario y logistica

Inventario y logistica quedan en research:

- no se compra inventario;
- no se contratan envios;
- no se confirma margen;
- no se declara disponibilidad real.

## Margen

Regla:

- `margin_estimated=unknown_not_estimated` hasta evidencia.
- No se calcula ROI real sin costo, precio, demanda, proveedor y logistica.
- No se inventan ventas ni utilidad.

## Aprobacion CEO

Requiere CEO:

- comprar inventario;
- conectar pagos;
- crear cuenta marketplace;
- conectar Amazon Seller;
- usar herramienta pagada;
- contratar proveedor/logistica;
- lanzar venta real.

No requiere CEO:

- preparar documentos;
- preparar tablero manual;
- preparar contenido organico;
- modelar hipotesis con evidencia faltante;
- dejar estado `prepared`.

## Riesgos

- Confundir radar Amazon con producto ganador.
- Confundir tienda preparada con tienda creada.
- Declarar margen sin proveedor/logistica/precio.
- Conectar pasarela sin autorizacion.
- Comprar inventario antes de validar demanda.
- Usar scraping prohibido o herramientas pagadas sin ROI.

## Reglas anti-alucinacion

- Sin evidencia, estado `unknown`, `idea` o `needs_market_research`.
- No declarar venta real.
- No declarar margen real.
- No declarar inventario comprado.
- No declarar Amazon Seller conectado.
- No declarar producto ganador.
- No declarar pago o pasarela conectada.
