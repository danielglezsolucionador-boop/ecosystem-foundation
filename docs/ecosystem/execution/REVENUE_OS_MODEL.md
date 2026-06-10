# Revenue OS Model

Fecha: 2026-06-09

## Proposito

Revenue OS permite que CEREBRO gestione la meta economica del ecosistema sin inventar ingresos reales y sin ejecutar pagos, campanas pagadas, cuentas externas ni pasarelas.

Estado base:

- actual_revenue=0
- actual_revenue_status=no_real_revenue_reported
- payment_connected=false
- external_connection_enabled=false
- runtime_connected=false
- sunat_enabled=false

## Metas

Meta global Ecosistema IA:

- USD 6,000 mensuales.
- Incluye oportunidades de contenido, marketing, APIs, skills, Web Factory, DCFT/SENTINELA vendidos por Marketing cuando esten listos, marca personal y productos internos.
- No incluye e-commerce.

Meta E-COMMERCE:

- USD 10,000 mensuales.
- Separada de la meta global.
- Incluye e-commerce y Sniff Amazon.

## Ingresos

Ingresos reales:

- Solo se consideran reales cuando exista evidencia externa validada.
- En este bloque no hay conexion de pagos ni cuentas externas.
- Por defecto: actual_revenue=0.

Ingresos estimados:

- Viven como pipeline.
- Deben estar marcados como estimados.
- No pueden mostrarse como venta real, cobro real ni ingreso confirmado.

## Oportunidad

Toda oportunidad debe incluir:

- titulo
- origen
- departamento
- producto relacionado
- inversion
- ingreso esperado
- utilidad neta
- probabilidad
- riesgo
- tiempo de retorno
- contribucion a meta global USD 6,000
- contribucion a meta e-commerce USD 10,000 si aplica
- requiere aprobacion
- estado

Estados permitidos:

- prepared
- evaluated
- needs_more_data
- waiting_ceo_approval
- approval_requested
- rejected

## Matriz Economica

Toda solicitud de dinero debe incluir:

- inversion
- ingreso esperado
- utilidad neta esperada
- probabilidad
- tiempo de retorno
- riesgo
- contribucion a meta mensual
- recomendacion

Si falta informacion:

- status=needs_more_data
- roi_percent=null
- no se inventa ROI
- no se pide ejecucion real

Ejemplo:

- Inversion: USD 100.
- Ingreso esperado: USD 600.
- Utilidad neta: USD 500.
- Contribucion meta USD 6,000: 8.33%.
- Recomendacion: aprobar solo con decision CEO.

## Aprobacion CEO

CEREBRO debe pedir aprobacion si:

- inversion > 0
- campana pagada
- API con costo
- herramienta con costo
- compra de inventario
- contratacion
- cuenta externa con costo

CEREBRO no debe pedir aprobacion para:

- organico
- analisis
- mision interna
- Local Agent preparado sin runtime real
- tarea FORJA preparada
- deploy controlado segun politica
- publicacion organica en cuenta ya configurada

## Departamentos

Contribucion directa:

- PLUMA: autoridad, libros, contenido comercial, trafico.
- LENTE: canales, videos, assets y monetizacion audiovisual.
- MARKETING: leads, demanda, ventas y embudos.
- MARCA PERSONAL: autoridad, audiencia, alianzas y confianza.
- BUSCADOR DE TENDENCIAS: oportunidades monetizables.
- CREADOR APIs/SKILLS: productos tecnicos vendibles.
- WEB FACTORY: landings y paginas para vender.
- E-COMMERCE: meta propia USD 10,000 mensual.
- SNIFF AMAZON: oportunidades Amazon y marketplace.

Productos preparados:

- DCFT: vendido por Marketing cuando este actualizado; no SUNAT real.
- SENTINELA: vendido por Marketing cuando este actualizado; no runtime real.

Contribucion indirecta:

- AUDITORIA: calidad, evidencia y control de no inventar ingresos.
- NUBE: operacion, costos, URLs y despliegues preparados.
- HERMES: automatizacion ligera.
- FORJA: ejecucion preparada cuando la politica lo permite.

## Integracion CEREBRO

CEREBRO puede:

- ver estado Revenue OS;
- registrar oportunidad;
- evaluar oportunidad;
- pedir aprobacion con ROI cuando hay dinero;
- reportar avance diario;
- separar e-commerce de la meta global;
- presionar departamentos con tareas internas preparadas.

CEREBRO no puede:

- ejecutar pago real;
- conectar pasarela;
- crear cuenta externa oficial;
- activar SUNAT;
- declarar venta real sin evidencia;
- conectar APIs externas con costo desde este bloque.

## Definiciones pendientes CEO

Revenue OS debe usar `CEO_PENDING_DEFINITIONS_REGISTER.md` cuando una ruta de ingreso dependa de cuentas, nichos, productos, métricas, pricing o evidencias no confirmadas.

Si falta definición del CEO, la oportunidad puede seguir como hipótesis o pipeline preparado, pero no como ingreso real, venta real, campaña real ni cuenta oficial conectada.
