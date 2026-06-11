# CEO Pending Definitions Register

Fecha: 2026-06-09

## Propósito

Este documento registra decisiones, definiciones o datos que el CEO todavía no ha confirmado.

Sirve para evitar alucinaciones dentro del ecosistema.

Cuando CEREBRO, AUDITORÍA, FORJA, MARKETING, PLUMA, LENTE u otro departamento no tenga información suficiente, debe registrar la duda aquí o en el modelo equivalente, en vez de inventar.

## Regla de oro

"No inventar información del CEO. Si falta una definición, registrarla y continuar solo en modo preparado cuando sea seguro."

## Estados permitidos

- `pending_ceo`
- `answered`
- `discovered`
- `blocked`
- `unknown`
- `partial`
- `needs_audit`
- `needs_discovery`
- `prepared_until_defined`
- `needs_strategy`

## Campos obligatorios por definición

Cada definición debe tener:

- `id`
- `tema`
- `pregunta`
- `contexto`
- `opciones_posibles`
- `estado`
- `impacto`
- `bloque_afectado`
- `departamento_afectado`
- `respuesta_ceo`
- `fecha_creacion`
- `fecha_actualizacion`
- `siguiente_accion`
- `riesgo_si_se_inventa`
- `puede_continuar_en_modo_prepared`

## Definiciones iniciales

### 1. REDES_OFICIALES_EXISTENTES

- id: `REDES_OFICIALES_EXISTENTES`
- tema: Redes oficiales existentes.
- pregunta: ¿Qué redes oficiales existen realmente hoy para el ecosistema, marca personal, marketing, e-commerce, LENTE y otros canales?
- contexto: Publishing & Growth necesita diferenciar cuentas existentes, cuentas conectadas y cuentas solo preparadas.
- opciones_posibles: cuentas existentes confirmadas; cuentas no existentes; cuentas por descubrir; cuentas por crear.
- estado: `pending_ceo`
- impacto: Bloque P Publishing & Growth Engine.
- bloque_afectado: Bloque P.
- departamento_afectado: CEREBRO, MARKETING, MARCA PERSONAL, LENTE, E-COMMERCE.
- respuesta_ceo: pendiente.
- fecha_creacion: 2026-06-09.
- fecha_actualizacion: 2026-06-09.
- siguiente_accion: CEO debe confirmar redes oficiales existentes o autorizar discovery documental.
- riesgo_si_se_inventa: Publicar o preparar contenido para cuentas inexistentes o equivocadas.
- puede_continuar_en_modo_prepared: sí.

### 2. CUENTAS_NUEVAS_A_CREAR

- id: `CUENTAS_NUEVAS_A_CREAR`
- tema: Cuentas externas nuevas.
- pregunta: ¿Qué cuentas externas oficiales nuevas deben crearse y cuáles deben esperar?
- contexto: Crear cuentas externas afecta identidad pública y gobierno de credenciales.
- opciones_posibles: crear ahora; preparar nombre; esperar; bloquear.
- estado: `pending_ceo`
- impacto: Publishing, Marketing, Marca Personal, LENTE, E-commerce.
- bloque_afectado: Bloque P, Revenue OS.
- departamento_afectado: MARKETING, MARCA PERSONAL, LENTE, E-COMMERCE, CEREBRO.
- respuesta_ceo: pendiente.
- fecha_creacion: 2026-06-09.
- fecha_actualizacion: 2026-06-09.
- siguiente_accion: CEO debe aprobar cualquier cuenta externa nueva antes de creación real.
- riesgo_si_se_inventa: Crear identidad pública incorrecta o duplicada.
- puede_continuar_en_modo_prepared: sí.

### 3. MARCA_PERSONAL_CUENTAS_ACTUALES_O_NUEVAS

- id: `MARCA_PERSONAL_CUENTAS_ACTUALES_O_NUEVAS`
- tema: Cuentas de marca personal.
- pregunta: ¿La marca personal del CEO usará cuentas actuales o cuentas nuevas?
- contexto: La estrategia de autoridad del CEO puede mezclar o separar audiencia actual y marca nueva.
- opciones_posibles: usar cuentas actuales; crear cuentas nuevas; estrategia híbrida; esperar.
- estado: `pending_ceo`
- impacto: Marca Personal, Marketing, Publishing.
- bloque_afectado: Bloque H, Bloque P, Revenue OS.
- departamento_afectado: MARCA PERSONAL, MARKETING, PLUMA, LENTE.
- respuesta_ceo: pendiente.
- fecha_creacion: 2026-06-09.
- fecha_actualizacion: 2026-06-09.
- siguiente_accion: CEO debe definir estrategia de cuentas antes de publicación real.
- riesgo_si_se_inventa: Mezclar audiencia personal actual con estrategia nueva sin decisión CEO.
- puede_continuar_en_modo_prepared: sí.

### 4. LENTE_CANALES_FINALES

- id: `LENTE_CANALES_FINALES`
- tema: Canales finales de LENTE.
- pregunta: ¿Cuál será la lista final de canales de LENTE?
- contexto: El CEO indicó que LENTE tendrá varios canales de YouTube/TikTok por nicho, con avatares, animación, podcast con avatares, canales infantiles, cristianos, IA, tendencias y otros posibles.
- opciones_posibles: canales por nicho; canales por formato; canales por idioma; lista mixta; pendiente.
- estado: `pending_ceo`
- impacto: LENTE, Publishing, Revenue OS.
- bloque_afectado: Bloque P, Bloque O.
- departamento_afectado: LENTE, MARKETING, PLUMA, CEREBRO.
- respuesta_ceo: pendiente.
- fecha_creacion: 2026-06-09.
- fecha_actualizacion: 2026-06-09.
- siguiente_accion: No cerrar lista final todavía; preparar solo escenarios.
- riesgo_si_se_inventa: Crear calendario o identidad de canal con nichos no aprobados.
- puede_continuar_en_modo_prepared: sí.

### 5. LENTE_NICHOS_PRIORITARIOS

- id: `LENTE_NICHOS_PRIORITARIOS`
- tema: Nichos prioritarios de LENTE.
- pregunta: ¿Cuáles son los nichos prioritarios iniciales de LENTE?
- contexto: Buscador de Tendencias puede aportar señales, pero no cerrar nichos finales.
- opciones_posibles: infantil; cristiano; IA; tendencias; podcast avatar; otro nicho validado; pendiente discovery.
- estado: `pending_ceo / needs_discovery`
- impacto: LENTE, Buscador de Tendencias, Marketing.
- bloque_afectado: Bloque P, Bloque O.
- departamento_afectado: LENTE, BUSCADOR DE TENDENCIAS, MARKETING.
- respuesta_ceo: pendiente.
- fecha_creacion: 2026-06-09.
- fecha_actualizacion: 2026-06-09.
- siguiente_accion: Buscador de Tendencias puede proponer nichos, pero no declararlos finales sin decisión CEO.
- riesgo_si_se_inventa: Dirigir contenido, diseño y calendario a nichos no definidos.
- puede_continuar_en_modo_prepared: sí.

### 6. DCFT_ESTADO_REAL

- id: `DCFT_ESTADO_REAL`
- tema: Estado real de DCFT.
- pregunta: ¿Cuál es el estado real actual de DCFT?
- contexto: Product Readiness y Marketing necesitan evidencia antes de preparar venta.
- opciones_posibles: operativo local; preparado; bloqueado por proveedor; requiere auditoría; unknown.
- estado: `needs_audit`
- impacto: Product Readiness, Marketing, Revenue OS.
- bloque_afectado: Bloque Q, Revenue OS.
- departamento_afectado: DCFT, MARKETING, AUDITORÍA, CEREBRO.
- respuesta_ceo: pendiente.
- fecha_creacion: 2026-06-09.
- fecha_actualizacion: 2026-06-09.
- siguiente_accion: Auditar DCFT con evidencia sin tocar SUNAT real ni declarar producción.
- riesgo_si_se_inventa: Vender o prometer capacidades no verificadas.
- puede_continuar_en_modo_prepared: sí.

### 7. SENTINELA_ESTADO_REAL

- id: `SENTINELA_ESTADO_REAL`
- tema: Estado real de SENTINELA.
- pregunta: ¿Cuál es el estado real actual de SENTINELA?
- contexto: SENTINELA debe mantenerse actualizado y preparado, pero no debe inventarse estado productivo.
- opciones_posibles: operativo local; preparado; pending_review; blocked; unknown.
- estado: `needs_audit`
- impacto: Product Readiness, Marketing, Security.
- bloque_afectado: Bloque Q.
- departamento_afectado: SENTINELA, MARKETING, AUDITORÍA, CEREBRO.
- respuesta_ceo: pendiente.
- fecha_creacion: 2026-06-09.
- fecha_actualizacion: 2026-06-09.
- siguiente_accion: Auditar capacidades reales y brechas con evidencia.
- riesgo_si_se_inventa: Declarar capacidades defensivas, detección o protección sin pruebas.
- puede_continuar_en_modo_prepared: sí.

### 8. ECOMMERCE_NOMBRE_OFICIAL_CODIGO

- id: `ECOMMERCE_NOMBRE_OFICIAL_CODIGO`
- tema: Nombre oficial de E-COMMERCE en código.
- pregunta: ¿Cuál es el nombre oficial en código para E-COMMERCE?
- contexto: Hay posibles equivalencias como comercio autónomo, e-commerce u otro nombre.
- opciones_posibles: E-COMMERCE; COMERCIO_AUTONOMO; Comercio Autónomo; otro alias confirmado.
- estado: `needs_discovery`
- impacto: Revenue OS, E-commerce, Publishing.
- bloque_afectado: Bloque O, Bloque P.
- departamento_afectado: E-COMMERCE, SNIFF AMAZON, CEREBRO.
- respuesta_ceo: pendiente.
- fecha_creacion: 2026-06-09.
- fecha_actualizacion: 2026-06-09.
- siguiente_accion: Inventariar nombres reales en código y reportar equivalencias.
- riesgo_si_se_inventa: Duplicar departamento, métricas o rutas operativas.
- puede_continuar_en_modo_prepared: sí.

### 9. SNIFF_AMAZON_O_CHIEF_AMAZON_NOMBRE_FINAL

- id: `SNIFF_AMAZON_O_CHIEF_AMAZON_NOMBRE_FINAL`
- tema: Nombre final de Amazon.
- pregunta: ¿El nombre final será SNIFF AMAZON, CHIEF AMAZON u otro?
- contexto: El ecosistema debe evitar duplicar departamento o mezclar rol con producto.
- opciones_posibles: SNIFF AMAZON; CHIEF AMAZON; Comercio Autónomo Amazon; otro.
- estado: `pending_ceo`
- impacto: SNIFF AMAZON, E-commerce, Revenue OS.
- bloque_afectado: Bloque O, Bloque P.
- departamento_afectado: SNIFF AMAZON, E-COMMERCE, CEREBRO.
- respuesta_ceo: pendiente.
- fecha_creacion: 2026-06-09.
- fecha_actualizacion: 2026-06-09.
- siguiente_accion: CEO debe confirmar nombre canónico antes de nuevas rutas o UI.
- riesgo_si_se_inventa: Duplicar departamento y romper trazabilidad de ingresos.
- puede_continuar_en_modo_prepared: sí.

### 10. REDES_ORGANICAS_PUBLICACION_REAL

- id: `REDES_ORGANICAS_PUBLICACION_REAL`
- tema: Redes orgánicas habilitadas para publicación real.
- pregunta: ¿Qué redes oficiales ya están configuradas para publicación orgánica sin aprobación?
- contexto: La política permite publicación orgánica sin aprobación solo si la red oficial ya está configurada.
- opciones_posibles: lista de redes conectadas; ninguna; pending discovery; requiere CEO.
- estado: `pending_ceo`
- impacto: Publishing & Growth Engine.
- bloque_afectado: Bloque P.
- departamento_afectado: CEREBRO, MARKETING, PLUMA, LENTE, MARCA PERSONAL.
- respuesta_ceo: pendiente.
- fecha_creacion: 2026-06-09.
- fecha_actualizacion: 2026-06-09.
- siguiente_accion: Validar evidencia de cuenta configurada antes de publicación real.
- riesgo_si_se_inventa: Publicar en canal incorrecto o declarar publicación real sin conexión.
- puede_continuar_en_modo_prepared: sí.

### 11. CUENTAS_CON_CREDENCIALES_SENSIBLES

- id: `CUENTAS_CON_CREDENCIALES_SENSIBLES`
- tema: Cuentas con credenciales sensibles.
- pregunta: ¿Qué cuentas externas tienen credenciales sensibles y cómo se gobernarán?
- contexto: Las credenciales no deben guardarse en documentación ni imprimirse en reportes.
- opciones_posibles: vault; variables seguras; pendiente CEO; bloqueado.
- estado: `pending_ceo`
- impacto: Seguridad, NUBE, CEREBRO.
- bloque_afectado: Seguridad, NUBE, Publishing, Revenue OS.
- departamento_afectado: SENTINELA, NUBE, CEREBRO, MARKETING.
- respuesta_ceo: pendiente.
- fecha_creacion: 2026-06-09.
- fecha_actualizacion: 2026-06-09.
- siguiente_accion: Definir gobierno de credenciales sin registrar secretos en este documento.
- riesgo_si_se_inventa: Exposición de secretos o falsa sensación de conexión segura.
- puede_continuar_en_modo_prepared: no.

### 12. CANALES_LENTE_META_100K

- id: `CANALES_LENTE_META_100K`
- tema: Distribución de meta 100K para LENTE.
- pregunta: ¿Cómo se distribuirá la meta de LENTE de al menos 5 canales con 100,000+ suscriptores?
- contexto: La meta requiere estrategia por canal, nicho, idioma y formato.
- opciones_posibles: cinco canales por nicho; cinco por formato; combinación; requiere estrategia.
- estado: `pending_ceo / needs_strategy`
- impacto: LENTE, Revenue OS, Publishing.
- bloque_afectado: Bloque P, Bloque O.
- departamento_afectado: LENTE, MARKETING, CEREBRO.
- respuesta_ceo: pendiente.
- fecha_creacion: 2026-06-09.
- fecha_actualizacion: 2026-06-09.
- siguiente_accion: Preparar escenarios y pedir decisión estratégica.
- riesgo_si_se_inventa: Medir o prometer crecimiento sobre canales no definidos.
- puede_continuar_en_modo_prepared: sí.

### 13. PLUMA_BESTSELLER_PRIMERA_LINEA

- id: `PLUMA_BESTSELLER_PRIMERA_LINEA`
- tema: Primera línea editorial de PLUMA.
- pregunta: ¿Cuál será la primera línea editorial tentativa para buscar un libro bestseller?
- contexto: PLUMA puede proponer líneas editoriales, pero no cerrar sin validación estratégica.
- opciones_posibles: autoridad CEO; negocios IA; espiritual/cristiano; finanzas; educación; otro.
- estado: `needs_discovery`
- impacto: PLUMA, Marca Personal, Revenue OS.
- bloque_afectado: Bloque O, Bloque P.
- departamento_afectado: PLUMA, MARCA PERSONAL, MARKETING.
- respuesta_ceo: pendiente.
- fecha_creacion: 2026-06-09.
- fecha_actualizacion: 2026-06-09.
- siguiente_accion: PLUMA puede proponer, pero no cerrar sin validación estratégica.
- riesgo_si_se_inventa: Crear autoridad o producto editorial en una línea no aprobada.
- puede_continuar_en_modo_prepared: sí.

### 14. APP_LISTA_OFICIAL_16_DEPARTAMENTOS

- id: `APP_LISTA_OFICIAL_16_DEPARTAMENTOS`
- tema: Lista oficial de aplicaciones/departamentos.
- pregunta: ¿Cuál es la lista oficial final de aplicaciones/departamentos del ecosistema?
- contexto: La auditoría automática y las cabinas necesitan una lista canónica.
- opciones_posibles: lista actual; lista corregida; equivalencias; duplicados; unknown.
- estado: `needs_discovery`
- impacto: Bloque I, auditoría automática, cabinas.
- bloque_afectado: Bloque I, Command Core, App Registry.
- departamento_afectado: CEREBRO, AUDITORÍA, FORJA, NUBE, todos los departamentos.
- respuesta_ceo: pendiente.
- fecha_creacion: 2026-06-09.
- fecha_actualizacion: 2026-06-09.
- siguiente_accion: Codex debe inventariar lo existente y reportar duplicados/equivalencias.
- riesgo_si_se_inventa: Crear rutas, reportes o métricas sobre departamentos duplicados o inexistentes.
- puede_continuar_en_modo_prepared: sí.

## Uso operativo

- CEREBRO debe consultar este registro antes de declarar decisiones definitivas del CEO.
- AUDITORÍA debe revisar claims que dependan de una definición pendiente.
- MARKETING, PLUMA y LENTE pueden preparar borradores, pero no publicar ni cerrar identidad externa cuando una definición esté pendiente.
- Revenue OS puede modelar oportunidades, pero no declarar ingresos, cuentas, ventas ni métricas reales sin evidencia.
- Product Readiness puede marcar brechas y estado `unknown`, pero no declarar producto listo si falta evidencia.

## Prohibiciones

- No guardar credenciales en este documento.
- No registrar tokens, contraseñas, claves privadas ni API keys.
- No convertir una pregunta pendiente en decisión final.
- No usar `prepared` como equivalente de ejecución real.
- No declarar aprobado, publicado, vendido, conectado o productivo sin evidencia y autorización correspondiente.
## Actualizacion S.1 - Real World Connection Readiness

Fecha: 2026-06-10

S.1 agrega el registro `REAL_WORLD_CONNECTIONS_REGISTER.md` como inventario operativo de conexiones reales posibles.

Definiciones CEO que quedan explicitamente pendientes:

### S1.1 REDES_OFICIALES_CONFIRMADAS

- id: `S1_REDES_OFICIALES_CONFIRMADAS`
- tema: Redes oficiales existentes y confirmadas.
- pregunta: Que cuentas oficiales existen hoy para Marca Personal, Publishing, Marketing, LENTE y E-commerce?
- contexto: S.1 no puede declarar cuenta conectada ni publicar real sin evidencia.
- estado: `pending_ceo`
- impacto: Publishing & Growth, Marca Personal, LENTE, Marketing.
- siguiente_accion: CEO confirma lista o autoriza discovery documental.
- riesgo_si_se_inventa: Publicacion en cuenta equivocada o claim falso de conexion.
- puede_continuar_en_modo_prepared: si.

### S1.2 CUENTAS_EXTERNAS_NUEVAS

- id: `S1_CUENTAS_EXTERNAS_NUEVAS`
- tema: Cuentas externas nuevas.
- pregunta: Que cuentas nuevas se deben crear y cuales deben quedar bloqueadas?
- contexto: Crear cuenta externa afecta marca, credenciales y gobierno.
- estado: `pending_ceo`
- impacto: LENTE, Marca Personal, E-commerce, App Stores, Marketing.
- siguiente_accion: No crear cuenta real sin aprobacion CEO.
- riesgo_si_se_inventa: Identidad publica duplicada o no autorizada.
- puede_continuar_en_modo_prepared: si.

### S1.3 CREDENCIALES_SENSIBLES

- id: `S1_CREDENCIALES_SENSIBLES`
- tema: Gobierno de credenciales.
- pregunta: Que vault, variables seguras o flujo aprobado se usara para cada proveedor?
- contexto: S.1 no guarda passwords, tokens, API keys, client secrets ni Clave SOL.
- estado: `pending_ceo`
- impacto: SENTINELA, DCFT, NUBE, Revenue OS, Marketing, Web Factory.
- siguiente_accion: Definir canal seguro fuera de documentos y chat.
- riesgo_si_se_inventa: Exposicion de secretos o falsa conexion.
- puede_continuar_en_modo_prepared: no para conexion real; si para inventario.

### S1.4 PUBLICACION_ORGANICA_REAL

- id: `S1_PUBLICACION_ORGANICA_REAL`
- tema: Publicacion organica real.
- pregunta: Que cuentas oficiales ya estan configuradas para publicar organico sin aprobacion adicional?
- contexto: La politica permite organico sin CEO solo si la cuenta oficial ya esta confirmada.
- estado: `pending_ceo`
- impacto: Publishing & Growth, PLUMA, LENTE, Marketing, Marca Personal.
- siguiente_accion: Mantener `publication_status=prepared` hasta evidencia.
- riesgo_si_se_inventa: Publicacion no autorizada o claim falso.
- puede_continuar_en_modo_prepared: si.

### S1.5 DINERO_REAL_Y_COSTOS

- id: `S1_DINERO_REAL_Y_COSTOS`
- tema: Dinero real, pagos, campanas y herramientas con costo.
- pregunta: Que presupuestos, pasarelas, campanas pagadas, tiendas, dominios o herramientas externas puede aprobar el CEO?
- contexto: Todo costo real requiere CEO con ROI, riesgo y evidencia.
- estado: `pending_ceo`
- impacto: Revenue OS, Marketing, Web Factory, E-commerce, APIs/Skills, App Stores.
- siguiente_accion: Preparar ROI y solicitud; no gastar.
- riesgo_si_se_inventa: Gasto no autorizado, cuenta con costo o campana real no aprobada.
- puede_continuar_en_modo_prepared: si.

### S1.6 FUENTES_REGULATORIAS_SEGURIDAD

- id: `S1_FUENTES_REGULATORIAS_SEGURIDAD`
- tema: Fuentes tributarias, contables y ciberseguridad.
- pregunta: Que fuentes oficiales o feeds se usaran para DCFT y SENTINELA?
- contexto: DCFT y SENTINELA no se tocan como runtime real desde S.1.
- estado: `needs_legal_review`
- impacto: DCFT, SENTINELA, AUDITORIA, Marketing.
- siguiente_accion: Mantener `needs_legal_review` o `needs_credentials` hasta evidencia.
- riesgo_si_se_inventa: Claim legal o de seguridad sin fuente.
- puede_continuar_en_modo_prepared: si.

## Actualizacion S.2 - Social Accounts & Identity Map

Fecha: 2026-06-10

S.2 agrega el registro `SOCIAL_ACCOUNTS_IDENTITY_REGISTER.md` como mapa preparado de identidades, marcas, cuentas y canales.

Definiciones CEO pendientes:

### S2.1 CUENTAS_OFICIALES_EXISTENTES

- id: `S2_CUENTAS_OFICIALES_EXISTENTES`
- tema: Cuentas oficiales existentes.
- pregunta: Que cuentas oficiales existen hoy para Ecosistema IA, Marca Personal CEO, PLUMA, LENTE, MARKETING, Web Factory, E-Commerce, SNIFF AMAZON, DCFT, SENTINELA y APIs/Skills?
- contexto: S.2 no puede declarar `confirmed_existing` sin evidencia.
- estado: `pending_ceo`
- impacto: Social Identity Map, Publishing, Marketing, Marca Personal, Revenue OS.
- siguiente_accion: CEO confirma cuentas existentes o autoriza discovery documental.
- riesgo_si_se_inventa: Publicar o posicionar una identidad en cuenta equivocada.
- puede_continuar_en_modo_prepared: si.

### S2.2 CUENTAS_NUEVAS_PROPUESTAS

- id: `S2_CUENTAS_NUEVAS_PROPUESTAS`
- tema: Cuentas externas nuevas.
- pregunta: Que cuentas nuevas se deben crear y cuales deben quedar bloqueadas?
- contexto: Crear cuenta externa define identidad publica y gobierno de credenciales.
- estado: `pending_ceo`
- impacto: Marca Personal, LENTE, E-Commerce, DCFT, SENTINELA, APIs/Skills.
- siguiente_accion: Mantener `proposed_new` o `needs_account_creation` hasta decision CEO.
- riesgo_si_se_inventa: Duplicar marca, abrir canal no autorizado o generar deuda operativa.
- puede_continuar_en_modo_prepared: si.

### S2.3 HANDLES_Y_NOMBRES_PUBLICOS

- id: `S2_HANDLES_Y_NOMBRES_PUBLICOS`
- tema: Handles, nombres de canal y nombres publicos.
- pregunta: Cuales son los handles oficiales o criterios de nombre para cada marca/canal?
- contexto: PLUMA, LENTE y MARKETING pueden preparar piezas, pero no cerrar identidad externa.
- estado: `pending_ceo`
- impacto: Marca Personal, LENTE, Publishing, Marketing.
- siguiente_accion: Proponer opciones sin reservar ni crear cuentas reales.
- riesgo_si_se_inventa: Perder coherencia de marca o usar nombre no autorizado.
- puede_continuar_en_modo_prepared: si.

### S2.4 CREDENCIALES_SOCIALES

- id: `S2_CREDENCIALES_SOCIALES`
- tema: Gobierno de credenciales sociales.
- pregunta: Que canal seguro se usara para credenciales de redes, newsletter, podcast o herramientas sociales?
- contexto: S.2 no guarda passwords, tokens, API keys ni sesiones.
- estado: `pending_ceo`
- impacto: Publishing, Marketing, SENTINELA, AUDITORIA.
- siguiente_accion: Definir vault/flujo seguro fuera del chat y documentos.
- riesgo_si_se_inventa: Exposicion de credenciales o falsa conexion.
- puede_continuar_en_modo_prepared: no para conexion real; si para inventario.

### S2.5 POLITICA_PUBLICACION_ORGANICA

- id: `S2_POLITICA_PUBLICACION_ORGANICA`
- tema: Politica de publicacion organica.
- pregunta: En que cuentas oficiales confirmadas se puede publicar organico sin aprobacion adicional?
- contexto: S.2 no publica; solo prepara la decision para S.3.
- estado: `pending_ceo`
- impacto: Publishing Prepared, PLUMA, LENTE, MARKETING, Marca Personal.
- siguiente_accion: Mantener publicaciones como prepared si la cuenta no esta confirmada.
- riesgo_si_se_inventa: Publicacion real no autorizada.
- puede_continuar_en_modo_prepared: si.
