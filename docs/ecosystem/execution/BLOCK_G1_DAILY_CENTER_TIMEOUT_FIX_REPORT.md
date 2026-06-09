# BLOCK G.1 - CEO Daily Center Timeout Fix Report

Fecha/hora local: 2026-06-08 23:00:00 -05:00

## Estado

Fix local implementado y validado.

El cierre G quedó bloqueado previamente por timeout en:

- `GET /api/v1/ceo/daily-center`

También se corrigió el riesgo de que Playwright imprimiera `Authorization` o `Bearer` en el call log si una llamada autenticada fallaba por timeout.

## Diagnóstico

`/api/v1/ceo/daily-center` consolidaba mañana, tarde y resumen ejecutivo con consultas repetidas a governance, CEREBRO, BUS, AUDITORÍA y NUBE.

Localmente era aceptable, pero en producción podía amplificar latencia de base de datos o cold start porque el endpoint recalculaba varias veces los mismos estados internos.

No se detectaron llamadas a APIs externas, SUNAT, Local Agent, DCFT real, SENTINELA real, ARSENAL real, FORJA externa ni `C:\Users\admin\nube`.

## Fix Daily Center

- Se agregó snapshot interno único para el Centro CEO.
- Se limitaron lecturas de AUDITORÍA usadas por el resumen.
- Se agregaron timeouts internos por submódulo.
- Se agregaron fallbacks seguros por submódulo.
- Si un submódulo falla o tarda, el endpoint responde HTTP 200 con `mode="degraded"`, `degraded=true` y warnings.
- Se mantienen `external_connection_enabled=false`, `runtime_connected=false`, `sunat_enabled=false` y `local_agent_enabled=false`.
- DCFT, SENTINELA y ARSENAL siguen protegidos/bloqueados.

## Fix Token Redaction

`work/command_core_production_auth_close.mjs` ahora:

- usa `redactSensitive`;
- usa `safeApiGet`;
- usa `safeLogError`;
- no imprime stacktrace;
- no imprime credenciales;
- no imprime tokens;
- no imprime `Authorization`;
- si daily-center falla, reporta `BLOCKED DAILY CENTER` sin filtrar secretos.

## Validaciones Locales

- `node --check apps/web/control-center/assets/app.js`: PASS.
- `node --check work/command_core_production_auth_close.mjs`: PASS.
- `python -m compileall apps/api api scripts -q`: PASS.
- `$env:PYTHONPATH="apps/api"; pytest -q`: PASS, 341 tests.
- `python scripts/validate_v1.py`: PASS, 341 tests y secret scan PASS.
- `git diff --check`: PASS.

## Performance Local

Endpoint autenticado local:

- `GET /api/v1/ceo/daily-center`

Mediciones en `127.0.0.1:8021`:

- 504 ms.
- 560 ms.
- 684 ms.
- 765 ms.
- 638 ms.

Resultado: menor a 1 segundo en las cinco corridas locales.

## No Tocado

- DCFT real.
- SENTINELA real.
- ARSENAL real.
- FORJA productiva externa.
- NUBE local externa.
- `C:\Users\admin\nube`.
- SUNAT real.
- APIs externas reales.
- Local Agent.

## Riesgos

La producción autenticada final todavía requiere ejecutar el script desde una PowerShell con `CONTROL_CENTER_ADMIN_EMAIL` y `CONTROL_CENTER_ADMIN_PASSWORD` presentes.

## Siguiente Paso

Commit fix, push, deploy, reejecutar cierre productivo autenticado, capturas productivas, reporte final, tag `v1-ecosystem-command-core` y backup final PASS.
