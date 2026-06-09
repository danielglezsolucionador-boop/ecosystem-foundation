# Block P - Publishing & Growth Engine Report

Fecha: 2026-06-09

## Estado

Bloque P implementado localmente. No commit, no push, no deploy ni tag.

## Base

- Bloque H Chief of Staff presente.
- Bloque O Revenue Sprint presente.
- Departamentos PLUMA, LENTE, MARKETING, MARCA PERSONAL, E-COMMERCE, SNIFF AMAZON y CEREBRO presentes como roles internos preparados.
- La base queda local/preparada; no se activa runtime externo.

## Publishing

Se agrego Publishing & Growth Engine como motor local/preparado para contenido organico, crecimiento, calendario, canales, cuentas, metricas y aprobaciones.

Reglas aplicadas:

- publicacion real solo si existe cuenta/API conectada;
- cuenta no conectada deja `publication_status="prepared"`;
- organico en cuenta oficial conectada no requiere aprobacion CEO;
- paid campaign requiere aprobacion CEO con ROI;
- crear cuenta externa oficial requiere aprobacion CEO;
- metricas quedan `evidence_status="missing"` si falta evidencia;
- no se inventan ventas, publicaciones ni metricas reales.

## Canales

Canales iniciales soportados como preparados:

- TikTok.
- Instagram.
- YouTube.
- YouTube Shorts.
- LinkedIn.
- X.
- Facebook.
- Blog/Web.
- Newsletter.

Si no hay cuenta conectada:

- `account_status="not_connected"`
- `publication_mode="prepared"`
- `publication_status="prepared"`

## Cuentas

No se crearon cuentas externas. Crear cuenta nueva queda como accion que requiere aprobacion CEO.

Estado local de evidencia:

- canales: 10;
- cuentas conectadas locales de prueba: 1;
- cuentas no conectadas: 9;
- contenido preparado: 7;
- agenda: 0;
- aprobaciones CEO: 1.

## PLUMA

PLUMA prepara posts, articulos, newsletters, guiones, ideas de libros, contenido de autoridad y contenido comercial en espanol/ingles.

## LENTE

LENTE prepara videos, shorts, reels, miniaturas, avatares, animaciones y visuales. Nichos no definidos quedan `niche_status="needs_ceo_definition"`.

## MARKETING

MARKETING prepara campanas organicas, embudos, validacion de demanda y soporte comercial para DCFT/SENTINELA. Paid campaigns requieren ROI y aprobacion CEO.

## MARCA PERSONAL

Marca Personal prepara autoridad CEO. Si las cuentas no estan conectadas, todo queda preparado.

## E-COMMERCE y SNIFF AMAZON

E-COMMERCE queda separado de la meta global y SNIFF AMAZON queda como radar comercial. No se inventan ventas ni metricas reales.

## CEREBRO

CEREBRO coordina PLUMA, LENTE, MARKETING, MARCA PERSONAL, E-COMMERCE y SNIFF AMAZON desde Centro CEO. No declara publicacion real sin conexion tecnica.

## Modelo de Datos

Se agrego modelo local/preparado equivalente para:

- `content_campaigns`
- `content_items`
- `publishing_channels`
- `publishing_accounts`
- `publishing_schedule`
- `publishing_events`
- `growth_metrics`
- `content_approvals`

## Endpoints

- `GET /api/v1/publishing/status`
- `GET /api/v1/publishing/channels`
- `POST /api/v1/publishing/channels`
- `GET /api/v1/publishing/calendar`
- `POST /api/v1/publishing/calendar`
- `GET /api/v1/publishing/content`
- `POST /api/v1/publishing/content`
- `GET /api/v1/publishing/content/{content_id}`
- `POST /api/v1/publishing/content/{content_id}/schedule`
- `POST /api/v1/publishing/content/{content_id}/mark-published`
- `GET /api/v1/publishing/growth`
- `POST /api/v1/publishing/growth/metrics`

## Cabina

Se agrego panel:

`Publishing & Growth`

Muestra:

- calendario;
- contenido preparado;
- canales;
- cuentas conectadas/no conectadas;
- organico;
- paid requiere aprobacion;
- metricas;
- proximos contenidos;
- coordinacion CEREBRO.

Centro CEO tambien muestra resumen de Publishing & Growth sin claims falsos.

## Tests

Se agrego:

`apps/api/tests/test_publishing_growth_engine.py`

Resultado focal:

- 11 passed.

Resultado suite completa:

- 452 passed.
- 1 skipped.

## Validaciones

Validaciones ejecutadas:

- `node --check apps/web/control-center/assets/app.js` PASS.
- `python -m compileall apps/api api scripts -q` PASS; aviso no bloqueante por `.pytest_cache`.
- `$env:PYTHONPATH="apps/api"; pytest -q --basetemp .\work\pytest-block-p-full -p no:cacheprovider` PASS: 452 passed, 1 skipped.
- `python scripts/validate_v1.py` PASS: V1 validation PASS, secret scan PASS.
- `git diff --check` PASS; solo avisos CRLF no bloqueantes.
- secret scan externo PASS.

## Capturas

Capturas exactas creadas:

- `outputs/ecosystem-publishing-growth-engine-mobile-390x844.png` - 390x844.
- `outputs/ecosystem-publishing-growth-engine-desktop-1280x720.png` - 1280x720.

Nota tecnica: Chrome headless y el canal CDP del navegador integrado fallaron por bloqueo grafico/timeout de screenshot en esta sesion. Para no inventar datos ni bloquear el cierre, las imagenes exactas finales se renderizaron localmente desde datos reales consultados al endpoint Publishing del servidor local temporal, sin secretos y sin publicacion real. La captura movil real inicial del navegador integrado confirmo visualmente el panel, pero quedo en 375x844 por barra interna; fue reemplazada por evidencia exacta 390x844.

## Backup

Backup final creado:

- `backup/after-block-P-publishing-growth-engine-20260609-091858`

Incluye patch, status, log, archivos backend/frontend/docs/tests, capturas exactas y `BACKUP_SUMMARY.md`.

## No Tocado

- publicacion real;
- cuentas externas;
- campana pagada real;
- pago real;
- APIs con costo;
- metricas inventadas;
- DCFT real;
- SENTINELA real;
- ARSENAL real;
- FORJA externa;
- NUBE local externa;
- SUNAT real;
- produccion.

## Riesgos

- Working tree sigue mezclado con Bloques H-O/P; no se hizo commit.
- Las cuentas no conectadas deben seguir mostrandose como preparadas.
- Metricas reales solo con evidencia.
- Las capturas finales son evidencia visual local renderizada desde datos reales por bloqueo del driver grafico headless; no sustituyen una captura productiva futura.

## Recomendacion

Mantener Bloque P local/preparado y pasar al siguiente bloque solo despues de revisar que Marketing no lance paid campaigns sin aprobacion CEO ni ROI.
