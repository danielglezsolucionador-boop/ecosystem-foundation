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
