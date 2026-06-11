# Real World Connections Register

Fecha: 2026-06-10
Baseline: `v1-ai-company-operating-system`
Commit base: `d29455a`

Regla: este registro no confirma cuentas conectadas. Si no hay evidencia, el estado queda `unknown`, `prepared`, `needs_ceo_definition`, `needs_credentials`, `needs_paid_approval`, `needs_account_creation` o `needs_legal_review`.

| id | area | conexion | estado actual | evidencia | requiere CEO | requiere credenciales | requiere dinero | riesgo | accion recomendada | bloque relacionado | owner interno | puede continuar prepared | notas |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| marca_personal_tiktok | Marca Personal | TikTok | unknown | missing | si | no | no | medium | Confirmar cuenta oficial antes de publicar. | S.1 | MARCA PERSONAL | si | No publicar real. |
| marca_personal_instagram | Marca Personal | Instagram | unknown | missing | si | no | no | medium | Confirmar cuenta oficial. | S.1 | MARCA PERSONAL | si | Preparar contenido solo como borrador. |
| marca_personal_linkedin | Marca Personal | LinkedIn | unknown | missing | si | no | no | medium | Definir cuenta actual o nueva. | S.1 | MARCA PERSONAL | si | Cuenta nueva requiere CEO. |
| marca_personal_x | Marca Personal | X | unknown | missing | si | no | no | medium | Confirmar handle oficial. | S.1 | MARCA PERSONAL | si | No publicar real. |
| marca_personal_youtube | Marca Personal | YouTube | unknown | missing | si | no | no | medium | Confirmar canal oficial. | S.1 | MARCA PERSONAL | si | Preparar guiones. |
| lente_youtube_channels | LENTE | YouTube canales | needs_ceo_definition | missing | si | no | no | medium | Definir canales y nichos. | S.1 | LENTE | si | No cerrar lista final. |
| lente_tiktok_channels | LENTE | TikTok canales | needs_ceo_definition | missing | si | no | no | medium | Definir canales oficiales por nicho. | S.1 | LENTE | si | No crear cuentas. |
| lente_reels_shorts | LENTE | Reels/Shorts | prepared | local_model | no | no | no | low | Preparar piezas sin publicar real. | S.1 | LENTE | si | Solo assets. |
| lente_podcast_avatar | LENTE | podcast/avatar | needs_ceo_definition | missing | si | no | no | medium | Definir identidad visual y canal. | S.1 | LENTE | si | Preparar escenarios. |
| lente_animation | LENTE | animacion | prepared | local_model | no | no | no | low | Preparar assets sin cuenta externa. | S.1 | LENTE | si | Sin publicacion real. |
| lente_childrens_channels | LENTE | canales infantiles | needs_ceo_definition | missing | si | no | no | high | Revisar riesgo de contenido infantil. | S.1 | LENTE | si | Requiere definicion. |
| lente_christian_channels | LENTE | canales cristianos | needs_ceo_definition | missing | si | no | no | medium | Definir si el nicho aplica. | S.1 | LENTE | si | No inventar nicho final. |
| lente_ai_trends_channels | LENTE | canales IA/tendencias | needs_ceo_definition | missing | si | no | no | medium | Definir lista final. | S.1 | LENTE | si | Depende de CEO. |
| publishing_facebook | Publishing & Growth | Facebook | unknown | missing | si | no | no | medium | Confirmar cuenta oficial. | S.1 | MARKETING | si | Sin publicacion real. |
| publishing_instagram | Publishing & Growth | Instagram | unknown | missing | si | no | no | medium | Mantener `publication_status=prepared`. | S.1 | MARKETING | si | No inventar cuenta. |
| publishing_tiktok | Publishing & Growth | TikTok | unknown | missing | si | no | no | medium | Confirmar cuenta antes de publicar. | S.1 | MARKETING | si | No publicar real. |
| publishing_youtube | Publishing & Growth | YouTube | unknown | missing | si | no | no | medium | Confirmar canal o preparar borradores. | S.1 | MARKETING | si | No subir videos. |
| publishing_linkedin | Publishing & Growth | LinkedIn | unknown | missing | si | no | no | medium | Confirmar cuenta oficial. | S.1 | MARKETING | si | Organico solo si cuenta confirmada. |
| publishing_x | Publishing & Growth | X | unknown | missing | si | no | no | medium | Confirmar cuenta oficial. | S.1 | MARKETING | si | No publicar real. |
| publishing_blog_web | Publishing & Growth | Blog/Web | prepared | local_model | no | no | no | low | Preparar contenido y landing. | S.1 | WEB FACTORY | si | No publicar dominio no confirmado. |
| publishing_newsletter | Publishing & Growth | Newsletter | needs_credentials | missing | si | si | no | sensitive | Definir herramienta y credenciales seguras. | S.1 | MARKETING | no | No guardar secretos. |
| marketing_meta_ads | Marketing | Meta Ads | needs_paid_approval | missing | si | si | si | sensitive | Preparar ROI; no lanzar campana. | S.1 | MARKETING | si | Dinero real bloqueado. |
| marketing_google_ads | Marketing | Google Ads | needs_paid_approval | missing | si | si | si | sensitive | Preparar presupuesto y ROI. | S.1 | MARKETING | si | No activar. |
| marketing_tiktok_ads | Marketing | TikTok Ads | needs_paid_approval | missing | si | si | si | sensitive | Propuesta pagada con ROI. | S.1 | MARKETING | si | No gastar. |
| marketing_linkedin_ads | Marketing | LinkedIn Ads | needs_paid_approval | missing | si | si | si | sensitive | Evaluar solo si ROI justifica. | S.1 | MARKETING | si | No lanzar. |
| marketing_email | Marketing | email marketing | needs_credentials | missing | si | si | no | sensitive | Elegir herramienta y vault. | S.1 | MARKETING | no | No secretos. |
| marketing_crm | Marketing | CRM | needs_ceo_definition | missing | si | si | no | high | Definir CRM sin crear cuenta. | S.1 | MARKETING | si | Cuenta externa requiere CEO. |
| revenue_payment_gateway | Revenue OS | pasarela de pago | needs_paid_approval | missing | si | si | si | sensitive | Definir proveedor y credenciales. | S.1 | REVENUE OS | si | No cobrar. |
| revenue_invoicing | Revenue OS | facturacion | needs_legal_review | missing | si | no | no | sensitive | Revisar legal/tributario. | S.1 | DCFT | si | No SUNAT real. |
| revenue_tracking | Revenue OS | tracking de ingresos | prepared | local_model | no | no | no | low | Preparar tablero sin inventar ventas. | S.1 | REVENUE OS | si | Datos reales quedan en 0 si no hay evidencia. |
| revenue_roi | Revenue OS | ROI | prepared | local_model | no | no | no | low | Modelar hipotesis con evidencia faltante. | S.1 | REVENUE OS | si | No declarar ROI real. |
| revenue_conversion_metrics | Revenue OS | metricas de conversion | unknown | missing | no | no | no | medium | Esperar herramienta o evidencia. | S.1 | MARKETING | si | No inventar conversion. |
| ecommerce_store | E-commerce | tienda propia | needs_ceo_definition | missing | si | si | no | high | Definir plataforma/nombre. | S.1 | E-COMMERCE | si | No crear tienda. |
| ecommerce_marketplace | E-commerce | marketplace | needs_account_creation | missing | si | si | no | sensitive | Crear cuenta externa requiere CEO. | S.1 | E-COMMERCE | si | No abrir cuenta. |
| ecommerce_payments | E-commerce | pagos | needs_paid_approval | missing | si | si | si | sensitive | No conectar pagos sin aprobacion. | S.1 | E-COMMERCE | si | No cobrar. |
| ecommerce_inventory | E-commerce | inventario | unknown | missing | no | no | si | high | No comprar inventario. | S.1 | E-COMMERCE | si | Documentar fuentes. |
| ecommerce_logistics | E-commerce | logistica | unknown | missing | no | no | si | high | Preparar mapa logistico sin contratar. | S.1 | E-COMMERCE | si | No contratar. |
| ecommerce_analytics | E-commerce | analitica | prepared | local_model | no | no | no | low | Preparar metricas sin inventar datos. | S.1 | E-COMMERCE | si | Sin cuenta real. |
| amazon_seller | SNIFF AMAZON / CHIEF AMAZON | Amazon Seller | needs_account_creation | missing | si | si | no | sensitive | Cuenta Amazon requiere CEO. | S.1 | SNIFF AMAZON | si | No crear cuenta. |
| amazon_product_research | SNIFF AMAZON / CHIEF AMAZON | Amazon Product Research | prepared | local_model | no | no | no | medium | Preparar criterios sin herramienta paga. | S.1 | SNIFF AMAZON | si | Sin compra. |
| amazon_buy_box_tracking | SNIFF AMAZON / CHIEF AMAZON | Buy Box tracking | unknown | missing | si | no | si | high | Confirmar herramienta y costo. | S.1 | SNIFF AMAZON | si | No conectar API. |
| amazon_scraping_monitoring | SNIFF AMAZON / CHIEF AMAZON | scraping/monitoring permitido | needs_legal_review | missing | si | no | no | high | Revisar terminos antes de automatizar. | S.1 | SNIFF AMAZON | si | No scraping real. |
| amazon_external_tools | SNIFF AMAZON / CHIEF AMAZON | herramientas externas | needs_paid_approval | missing | si | si | si | sensitive | No activar herramientas con costo. | S.1 | SNIFF AMAZON | si | Requiere ROI. |
| dcft_tax_sources | DCFT | fuentes tributarias | needs_legal_review | missing | si | no | no | sensitive | Validar fuente oficial sin SUNAT real. | S.1 | DCFT | si | DCFT real no tocado. |
| dcft_accounting_sources | DCFT | fuentes contables | needs_legal_review | missing | si | no | no | high | Revisar fuentes antes de claims. | S.1 | DCFT | si | No claims legales. |
| dcft_normative_updates | DCFT | actualizacion normativa | needs_legal_review | missing | si | no | no | sensitive | No afirmar actualizacion legal sin fuente. | S.1 | DCFT | si | No SUNAT real. |
| dcft_landing | DCFT | landing | prepared | local_model | no | no | no | low | Preparar landing sin publicar. | S.1 | WEB FACTORY | si | No venta automatica. |
| dcft_pricing | DCFT | pricing | needs_ceo_definition | missing | si | no | no | medium | CEO/Marketing confirman precio. | S.1 | MARKETING | si | No inventar precio final. |
| dcft_support | DCFT | soporte | needs_ceo_definition | missing | si | no | no | medium | Definir soporte y canales. | S.1 | DCFT | si | No cuenta externa. |
| dcft_distribution | DCFT | distribucion | needs_ceo_definition | missing | si | no | no | medium | Definir canal comercial. | S.1 | MARKETING | si | No publicar real. |
| sentinela_security_sources | SENTINELA | fuentes de ciberseguridad | needs_legal_review | missing | si | no | no | sensitive | Validar fuentes y permisos. | S.1 | SENTINELA | si | SENTINELA real no tocado. |
| sentinela_threat_feeds | SENTINELA | threat feeds | needs_credentials | missing | si | si | no | sensitive | No conectar feed real. | S.1 | SENTINELA | no | No secretos. |
| sentinela_landing | SENTINELA | landing | prepared | local_model | no | no | no | low | Preparar landing sin claims no validados. | S.1 | WEB FACTORY | si | No publicar real. |
| sentinela_pricing | SENTINELA | pricing | needs_ceo_definition | missing | si | no | no | medium | Marketing define precio. | S.1 | MARKETING | si | SENTINELA no vende solo. |
| sentinela_support | SENTINELA | soporte | needs_ceo_definition | missing | si | no | no | medium | Definir soporte sin abrir cuentas. | S.1 | SENTINELA | si | No cuentas externas. |
| sentinela_distribution | SENTINELA | distribucion | needs_ceo_definition | missing | si | no | no | medium | Definir canal comercial. | S.1 | MARKETING | si | No claims de seguridad. |
| web_factory_domains | Web Factory | dominios | needs_paid_approval | missing | si | no | si | high | Compra dominio requiere CEO. | S.1 | WEB FACTORY | si | No comprar. |
| web_factory_hosting | Web Factory | hosting | needs_paid_approval | missing | si | si | si | sensitive | Hosting con costo requiere aprobacion. | S.1 | WEB FACTORY | si | No conectar provider. |
| web_factory_landing_pages | Web Factory | landing pages | prepared | local_model | no | no | no | low | Preparar landing local sin publicar. | S.1 | WEB FACTORY | si | Solo local/documental. |
| web_factory_forms | Web Factory | formularios | needs_credentials | missing | si | si | no | sensitive | Definir destino de datos. | S.1 | WEB FACTORY | no | No capturar datos reales. |
| web_factory_analytics | Web Factory | analytics | needs_credentials | missing | si | si | no | high | Preparar medicion sin cuenta real. | S.1 | WEB FACTORY | si | No tracking real. |
| apis_internal | APIs/Skills | APIs internas | prepared | local_model | no | no | no | low | Mantener internas sin costo ni secretos. | S.1 | CREADOR APIs/SKILLS | si | Sin externa. |
| apis_sellable | APIs/Skills | APIs vendibles | prepared | local_model | no | no | no | medium | Preparar documentacion y pricing. | S.1 | CREADOR APIs/SKILLS | si | No vender real. |
| apis_external_tools | APIs/Skills | herramientas externas | needs_paid_approval | missing | si | si | si | sensitive | API con costo requiere CEO y vault. | S.1 | CREADOR APIs/SKILLS | si | No conectar. |
| apis_documentation | APIs/Skills | documentacion | prepared | local_model | no | no | no | low | Documentar sin secretos. | S.1 | CREADOR APIs/SKILLS | si | Permitido. |
| apis_pricing | APIs/Skills | pricing | needs_ceo_definition | missing | si | no | no | medium | Definir precios antes de venta. | S.1 | MARKETING | si | No precio final inventado. |
| app_store_google_play | App Stores | Google Play | needs_account_creation | missing | si | si | si | sensitive | Crear cuenta o publicar app requiere CEO. | S.1 | NUBE | si | No Play Store real. |
| app_store_apple | App Stores | Apple App Store | needs_account_creation | missing | si | si | si | sensitive | Cuenta Apple y publicacion requieren CEO. | S.1 | NUBE | si | No App Store real. |

## Resumen operativo

- Conexiones reales confirmadas: 0.
- Conexiones API reales confirmadas: 0.
- Secretos registrados: 0.
- Pagos o campanas activas: 0.
- SUNAT real: apagado.
- App Store / Play Store real: apagado.
- Estado maximo permitido sin evidencia: `prepared` o `unknown`.
