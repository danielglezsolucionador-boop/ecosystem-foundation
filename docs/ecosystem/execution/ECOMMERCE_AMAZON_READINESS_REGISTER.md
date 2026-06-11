# E-Commerce + Amazon Readiness Register

Fecha: 2026-06-10
Fase: S.5

Este registro es local/preparado. No contiene credenciales, cuentas reales, productos ganadores, ventas, margen real ni datos de proveedor.

Estados permitidos: `unknown`, `idea`, `prepared`, `needs_market_research`, `needs_supplier`, `needs_payment_provider`, `needs_account_creation`, `needs_paid_tool`, `blocked`.

| id | linea de negocio | plataforma | producto/categoria | estado | evidencia | inversion necesaria | margen estimado | requiere CEO | requiere cuenta externa | requiere credenciales | requiere proveedor | riesgo | siguiente accion |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ecommerce_storefront_model | E-Commerce | Tienda propia | catalogo por definir | prepared | internal_docs | unknown | unknown_not_estimated | no | no | no | no | low | Preparar arquitectura de tienda sin crear tienda real. |
| ecommerce_payment_provider | E-Commerce | Tienda propia | pagos | needs_payment_provider | missing | unknown | unknown_not_estimated | si | no | si | no | sensitive | Definir proveedor y aprobacion CEO antes de conectar pagos. |
| ecommerce_supplier_map | E-Commerce | Proveedor | proveedores | needs_supplier | missing | unknown_requires_ceo | unknown_not_estimated | si | no | no | si | high | Hacer research de proveedores sin comprar inventario. |
| ecommerce_logistics_map | E-Commerce | Logistica | envios | needs_market_research | missing | unknown | unknown_not_estimated | no | no | no | no | medium | Preparar matriz logistica sin contratar servicios. |
| ecommerce_marketplace_option | E-Commerce | Marketplace | marketplace | needs_account_creation | missing | unknown | unknown_not_estimated | si | si | si | no | sensitive | Crear cuenta marketplace solo con aprobacion CEO. |
| ecommerce_product_shortlist | E-Commerce | Tienda propia | productos candidatos | needs_market_research | missing | unknown | unknown_not_estimated | no | no | no | no | high | Investigar demanda y margen; no declarar productos ganadores. |
| ecommerce_content_engine | E-Commerce | Publishing | contenido organico | prepared | internal_docs | unknown | unknown_not_estimated | no | no | no | no | low | MARKETING/PLUMA/LENTE pueden preparar contenido sin publicar real. |
| ecommerce_analytics_manual | E-Commerce | Analytics manual | metricas | prepared | internal_docs | unknown | unknown_not_estimated | no | no | no | no | low | Preparar tablero manual; ventas reales permanecen en 0 hasta evidencia. |
| amazon_seller_account | SNIFF AMAZON / CHIEF AMAZON | Amazon Seller | cuenta seller | needs_account_creation | missing | unknown | unknown_not_estimated | si | si | si | no | sensitive | Amazon Seller requiere CEO, credenciales y revision antes de crear o conectar. |
| amazon_product_radar | SNIFF AMAZON / CHIEF AMAZON | Radar Amazon | senales de producto | prepared | internal_docs | unknown | unknown_not_estimated | no | no | no | no | low | Preparar criterios de radar sin scraping prohibido ni herramienta paga. |
| amazon_paid_research_tool | SNIFF AMAZON / CHIEF AMAZON | Herramienta externa | research Amazon | needs_paid_tool | missing | unknown_requires_ceo | unknown_not_estimated | si | no | si | no | sensitive | Herramienta con costo requiere ROI y CEO antes de usar. |
| amazon_buy_box_tracking | SNIFF AMAZON / CHIEF AMAZON | Amazon | buy box tracking | needs_market_research | missing | unknown | unknown_not_estimated | si | no | no | no | high | Validar fuente permitida; no scraping prohibido. |
| amazon_category_hypotheses | SNIFF AMAZON / CHIEF AMAZON | Radar Amazon | categorias candidatas | idea | missing | unknown | unknown_not_estimated | no | no | no | no | medium | Formular hipotesis sin declarar producto ganador ni margen. |
| amazon_content_bridge | SNIFF AMAZON / CHIEF AMAZON | Publishing | contenido organico | prepared | internal_docs | unknown | unknown_not_estimated | no | no | no | no | low | Preparar contenido educativo sin afiliados ni venta real. |

## Resumen

E-Commerce:

- oportunidades: 8.
- prepared: 3.
- needs_market_research: 2.
- needs_supplier: 1.
- needs_payment_provider: 1.
- needs_account_creation: 1.
- approval_needed: 3.
- ventas reales: 0.
- margen inventado: false.
- pago conectado: false.
- inventario comprado: false.

Amazon:

- senales/oportunidades: 6.
- prepared: 2.
- idea: 1.
- needs_market_research: 1.
- needs_paid_tool: 1.
- needs_account_creation: 1.
- riesgos: 3.
- Amazon Seller conectado: false.
- productos ganadores declarados: false.
- scraping prohibido: false.

## Regla final

S.5 prepara decisiones y research. No ejecuta comercio real, no valida productos ganadores, no confirma margen y no conecta Amazon.
