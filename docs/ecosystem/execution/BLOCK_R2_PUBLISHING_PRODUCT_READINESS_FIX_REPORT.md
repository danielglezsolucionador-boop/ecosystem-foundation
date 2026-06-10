# Block R.2 - Publishing + Product Readiness Production Fix Report

Fecha/hora: 2026-06-09 20:00 -05:00
Rama: main
HEAD base: 4a83141 feat: consolidate AI company operating system
Commit fix: 55e1974 fix: stabilize publishing and product readiness production endpoints

## Actualización R.3

El CEO confirmó desde PowerShell segura que `.\work\run_total_ecosystem_authenticated_audit.ps1` finalizó con:

- `AUTHENTICATED_TOTAL_AUDIT_PASS`

Con esa evidencia, R.2 queda validado en producción autenticada:

- Publishing: PASS.
- Product Readiness: PASS.
- Rutas P/Q corregidas: PASS.
- No se imprimieron credenciales.
- No se imprimieron tokens.
- No se imprimió `Authorization`.

La sesión actual de Codex no contiene las variables seguras de autenticación y no puede regenerar capturas autenticadas finales sin que el CEO reejecute el flujo seguro.

## Estado

R.2 corrige localmente los errores 500 detectados en producción autenticada durante el cierre R.1 del AI Company Operating System.

Endpoints reportados con 500:

- `/api/v1/publishing/status`
- `/api/v1/publishing/channels`
- `/api/v1/publishing/content`
- `/api/v1/product-readiness/status`
- `/api/v1/product-readiness/dcft`
- `/api/v1/product-readiness/sentinela`

## Causa

La causa técnica encontrada fue compatibilidad SQLite/PostgreSQL:

- Los servicios `publishing` y `product_readiness` leían `payload_json` con `row[0]`.
- Localmente SQLite tolera ese acceso.
- Producción usa `psycopg.rows.dict_row`, por lo que la fila se comporta como diccionario y `row[0]` puede romper con 500.

También se reforzó tolerancia ante payloads legacy o corruptos para que los endpoints públicos autenticados devuelvan fallback seguro en vez de bloquear el cierre productivo.

## Fix Publishing

Cambios aplicados:

- `apps/api/app/services/publishing.py` usa `get_row_value(row, "payload_json")`.
- Se agregó lectura segura de payload JSON.
- `/status`, `/channels` y `/content` pueden devolver fallback preparado si no hay datos válidos.
- Canales sin cuenta conectada quedan `account_status="not_connected"`.
- Contenido sin publicación real queda `publication_mode="prepared"` y `publication_status="prepared"`.
- Métricas reales no se inventan.
- Paid campaigns siguen requiriendo aprobación CEO.
- Cuenta externa nueva sigue requiriendo aprobación CEO.

## Fix Product Readiness

Cambios aplicados:

- `apps/api/app/services/product_readiness.py` usa `get_row_value(row, "payload_json")`.
- Se agregó lectura segura de payload JSON.
- Si falta o falla un payload de producto, se reconstruye fallback seguro para DCFT/SENTINELA.
- DCFT mantiene `sales_owner="MARKETING"` y `has_own_sales_goal=false`.
- SENTINELA mantiene `sales_owner="MARKETING"` y `has_own_sales_goal=false`.
- No se declara App Store/Play Store ready.
- No se inventan claims legales ni claims de seguridad.
- SENTINELA no se define como "producto B2B futuro".

## Tests

Se actualizaron tests en:

- `apps/api/tests/test_ai_company_operating_system.py`

Cobertura R.2 agregada:

- Los seis endpoints que fallaban responden HTTP 200 con auth.
- Publishing conserva cuentas no conectadas como prepared/not_connected.
- Product Readiness conserva MARKETING como owner de venta.
- DCFT/SENTINELA no tienen meta propia.
- App Store/Play Store no se declara publicado.
- Lectores de payload aceptan filas tipo PostgreSQL dict-row.

Ejecución focalizada:

- `$env:PYTHONPATH="apps/api"; pytest -q apps/api/tests/test_ai_company_operating_system.py apps/api/tests/test_publishing_growth_engine.py apps/api/tests/test_product_readiness_dcft_sentinela.py`
- Resultado: PASS, 29 passed.

## Producción Pública

Resultado después de commit/push/deploy:

- `/version`: PASS, commit `55e1974`.
- `/runtime/status`: PASS.
- `/control-center`: PASS.

## Producción Autenticada

Estado: `BLOCKED_AUTH`.

La sesión actual de Codex no tiene variables seguras:

- `CONTROL_CENTER_ADMIN_EMAIL`: ausente.
- `CONTROL_CENTER_ADMIN_PASSWORD`: ausente.

No se pidieron credenciales por chat, no se imprimieron credenciales, no se imprimieron tokens y no se imprimió Authorization.

Comando seguro pendiente para CEO desde PowerShell con variables cargadas:

- `.\work\run_total_ecosystem_authenticated_audit.ps1`

Debe confirmar:

- publishing/status PASS
- publishing/channels PASS
- publishing/content PASS
- product-readiness/status PASS
- product-readiness/dcft PASS
- product-readiness/sentinela PASS
- y conservar PASS del resto de rutas R.1.

## No Tocado

No se tocó:

- DCFT real.
- SENTINELA real.
- FORJA externa.
- `C:\Users\admin\nube`.
- SUNAT real.
- Local Agent.
- APIs externas reales.
- campañas pagadas.
- cuentas externas.
- pagos.
- secretos.

## Riesgos

- R.2 queda local hasta commit/push/deploy.
- Producción autenticada debe revalidarse con variables seguras.
- Si existen payloads antiguos incompatibles en PostgreSQL, ahora se omiten o reconstruyen con fallback preparado; no se declaran capacidades reales.

## Recomendación CTO

Hacer commit fix, push, esperar deploy y reejecutar auditoría productiva autenticada completa antes de crear `v1-ai-company-operating-system`.
