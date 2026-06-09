# DCFT + SENTINELA Product Readiness Model

Fecha: 2026-06-09

## Proposito

Definir como el ecosistema evalua y prepara readiness de DCFT y SENTINELA para que MARKETING pueda venderlos cuando corresponda, sin tocar productos reales, datos sensibles, SUNAT, tiendas, campanas pagadas ni integraciones externas.

## Regla Comercial

- DCFT no tiene meta de venta propia.
- SENTINELA no tiene meta de venta propia.
- MARKETING es owner de venta.
- DCFT y SENTINELA deben mantenerse actualizados, fuertes y comercialmente preparados.
- Readiness no significa venta, publicacion, activacion ni aprobacion final.

## Readiness Tecnico

Evalua:

- funcionalidades existentes con evidencia;
- runtime real o no runtime;
- dependencias tecnicas;
- integraciones permitidas;
- brechas;
- estado FORJA;
- estado AUDITORIA.

Si falta evidencia:

- `technical_status="unknown"`
- `evidence_status="missing"`
- `readiness_status="requires_validation"`

## Readiness Comercial

Evalua:

- propuesta de valor;
- publico objetivo;
- objeciones;
- argumentos;
- landing;
- onboarding;
- pricing;
- soporte;
- piezas PLUMA;
- piezas LENTE;
- paquete para MARKETING.

MARKETING puede preparar materiales, pero no debe declarar producto listo sin evidencia.

## Readiness Legal / Riesgo

DCFT:

- requiere fuentes oficiales tributarias/contables/financieras;
- no se prometen resultados SUNAT;
- no se declaran claims legales sin fuente;
- no se toca SUNAT real desde este bloque.

SENTINELA:

- requiere evidencia de capacidades defensivas;
- no se promete proteccion total;
- no se declara deteccion/respuesta real sin pruebas;
- no se activa runtime real.

## App Store / Play Store

Estado permitido:

- `unknown`
- `requires_validation`

Prohibido:

- crear cuenta App Store/Play Store;
- publicar app;
- declarar app publicada;
- usar datos sensibles reales.

## Actualizacion

DCFT debe revisar fuentes tributarias, financieras y contables antes de claims.

SENTINELA debe revisar fuentes de amenazas, riesgos e incidentes antes de claims.

Si no hay fuente:

- `status="unknown"`
- `claim_status="requires_validation"`

## Marketing Package

Cada paquete debe incluir:

- propuesta de valor;
- publico objetivo;
- objeciones;
- argumentos;
- piezas necesarias;
- landing requerida;
- contenido PLUMA;
- contenido LENTE;
- riesgos;
- brechas;
- estado listo/no listo.

Reglas:

- no inventar claims legales;
- no inventar claims de seguridad;
- no inventar ventas;
- paid campaign requiere aprobacion CEO;
- crear cuenta externa requiere aprobacion CEO.

## FORJA

FORJA puede recibir brechas como tareas preparadas.

Si no hay evidencia:

- `forge_status="prepared"`
- `technical_status="pending_execution"`

Prohibido declarar:

- implementado;
- conectado;
- publicado;
- listo para venta.

## AUDITORIA

AUDITORIA debe revisar:

- evidencia tecnica;
- evidencia legal;
- evidencia de seguridad;
- landing;
- onboarding;
- pricing;
- soporte;
- tiendas;
- claims de marketing.

## DCFT Readiness

Estado inicial:

- producto protegido;
- no SUNAT real;
- no credenciales;
- no runtime externo;
- no venta automatica;
- MARKETING owner de venta;
- evidencia tecnica/legal pendiente.

Brechas iniciales:

- fuentes tributarias oficiales;
- evidencia tecnica del producto real;
- landing/onboarding;
- pricing;
- App Store / Play Store.

## SENTINELA Readiness

Definicion:

Sistema/producto de seguridad que debe estar actualizado y preparado para comercializacion cuando MARKETING lo empuje.

Estado inicial:

- no runtime real;
- no conexion productiva;
- no activacion;
- MARKETING owner de venta;
- evidencia de seguridad pendiente.

Brechas iniciales:

- capacidades defensivas con evidencia;
- fuentes de amenazas;
- landing/onboarding;
- pricing;
- App Store / Play Store.

## Reglas Anti-Alucinacion

- Si falta informacion: `status="unknown"`.
- Si falta evidencia: `evidence_status="missing"`.
- Si el claim requiere fuente: `claim_status="requires_validation"`.
- No declarar cumplimiento legal.
- No declarar proteccion completa.
- No declarar ventas reales.
- No declarar tienda publicada.
- No activar SUNAT.
- No tocar productos reales.
