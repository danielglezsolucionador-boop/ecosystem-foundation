# Block R.5 - Auth Capture 500 Diagnostic Report

Fecha/hora: 2026-06-09 21:35 -05:00
Rama: main
HEAD inicial: `2c16dec docs: record R2 production validation blocker`

## Estado

Estado R.5: `DIAGNOSTIC_READY / AWAITING_SECURE_CEO_EXECUTION`.

Actualización R.6:

- El CEO reejecutó el script y `outputs/r4-auth-capture-diagnostics.json` descartó el 500.
- `badResponses=[]`, `requestFailures=[]`, `consoleErrors=[]`, `pageErrors=[]`.
- El bloqueo real pasó a ser una condición incorrecta del script: `loginFormAttached=true` aunque la cabina autenticada estaba montada con `roleText="CEO"` y señales visibles.
- R.6 corrige esa condición en `work/r4_ai_company_auth_screenshots.mjs`.

El bloqueo ya no es autenticación. El CEO confirmó desde PowerShell segura:

- `EMAIL presente: True`
- `PASSWORD presente: True`
- `R4 authenticated API PASS`

El bloqueo real es un recurso o endpoint que devuelve HTTP 500 durante el render autenticado de la cabina productiva.

## Error Confirmado CEO

Ejecución:

```powershell
cd "C:\Users\admin\Documents\Codex\2026-05-31\auditoria-final-forja-render-he-validado"
.\work\run_r4_auth_captures.ps1
```

Resultado reportado:

- autenticación productiva PASS;
- captura mobile no generada;
- error visible: `Failed to load resource: the server responded with a status of 500 ()`;
- aborto en `work/r4_ai_company_auth_screenshots.mjs`;
- archivo faltante: `outputs/ecosystem-ai-company-operating-system-production-auth-mobile-390x844.png`.

## Backup Pre-R5

Creado:

- `backup/before-R5-auth-capture-500-fix-20260609-213124`

Incluye:

- estado Git;
- log;
- diff;
- error exacto reportado por CEO;
- scripts R4 previos;
- reportes R/R2/R3/R4;
- `BACKUP_SUMMARY.md`.

## Diagnóstico Agregado

Archivo modificado:

- `work/r4_ai_company_auth_screenshots.mjs`

El script ahora captura y reporta:

- `requestfailed`: URL, método y error;
- responses `status >= 400`: URL, método, status, content-type, body recortado a 1000 caracteres y resumen JSON si existe;
- console errors: texto completo y location;
- page errors;
- screenshot diagnóstico aunque falle;
- JSON diagnóstico aunque falle.

Archivos de diagnóstico que se crearán en el próximo intento:

- `outputs/r4-debug-auth-failure-mobile.png`
- `outputs/r4-auth-capture-diagnostics.json`

El diagnóstico redacta:

- tokens;
- `Authorization`;
- cookies;
- passwords;
- secrets;
- query params sensibles.

## URL Fallida

Estado: `not_applicable_after_R6`.

El último diagnóstico seguro no registró URL fallida:

- `badResponses=[]`
- `requestFailures=[]`

Por lo tanto, no hay endpoint 500 que corregir en este momento.

## Clasificación Pendiente

Clasificación final tras R.6:

- No aplica CASO A/B/C/D/E/F para 500.
- Causa real: condición de script sobre DOM attached vs visibilidad real.
- El formulario de login puede quedar attached en DOM sin estar visible.
- La cabina autenticada puede estar lista con app attached/visible, rol CEO y señales de cabina.

## Fix

Estado: `diagnostic_fix_applied / endpoint_500_fix_pending_url`.

No se aplicó fix específico del 500 porque R.5 exige no hacer intentos ciegos. Primero debe existir URL exacta, método, status y body del 500.

Sí se aplicaron dos estabilizaciones seguras:

1. `work/r4_ai_company_auth_screenshots.mjs`
   - diagnóstico completo de red/render;
   - screenshot y JSON de fallo;
   - redacción de secretos.

2. `apps/api/app/services/ceo.py`
   - fallback seguro para `cerebro.chief_of_staff` dentro de `/api/v1/ceo/daily-center`;
   - conserva `motto="El tiempo es dinero"`;
   - marca `fallback=true`;
   - mantiene `external_connection_enabled=false`, `runtime_connected=false`, `sunat_enabled=false`, `local_agent_enabled=false`;
   - no inventa runtime ni conexión externa.

Motivo del fallback:

- Durante la suite local, `/api/v1/ceo/daily-center` pudo devolver `chief_of_staff={}` si una llamada interna se degradaba o tardaba.
- Eso rompía el contrato visual del Centro CEO y podía dejar la cabina sin señal ejecutiva mínima.
- El fallback evita 500/KeyError por datos faltantes y mantiene estado preparado/seguro.

## Tests

Ejecutado en esta sesión:

- `node --check work/r4_ai_company_auth_screenshots.mjs`: PASS.
- `node --check apps/web/control-center/assets/app.js`: PASS.
- sintaxis PowerShell de `work/run_r4_auth_captures.ps1`: PASS.
- `python -m compileall apps/api api scripts -q`: PASS.
- `$env:PYTHONPATH="apps/api"; python -m pytest -q`: PASS, `470 passed, 1 skipped`.
- `python scripts/validate_v1.py`: PASS, `470 passed, 1 skipped`, secret scan PASS.
- `git diff --check`: PASS.

Test endpoint específico del 500 queda pendiente hasta identificar la URL exacta.

Nota de validador:

- `scripts/validate_v1.py` excluye `backup/` del secret scan porque los backups locales no se suben, no forman parte del producto y pueden contener copias de scripts con nombres técnicos como `password` sin valores reales.

## Comando Seguro CEO

Ejecutar desde PowerShell con variables ya cargadas:

```powershell
cd "C:\Users\admin\Documents\Codex\2026-05-31\auditoria-final-forja-render-he-validado"
.\work\run_r4_auth_captures.ps1
```

Si vuelve a fallar, debe existir:

- `outputs/r4-debug-auth-failure-mobile.png`
- `outputs/r4-auth-capture-diagnostics.json`

Ese JSON permitirá corregir la causa real sin inventar.

## No Tocado

No se tocó:

- DCFT real;
- SENTINELA real;
- FORJA externa;
- `C:\Users\admin\nube`;
- SUNAT real;
- APIs externas reales;
- campañas;
- pagos;
- cuentas externas;
- secretos.

## Riesgos

- No crear tag hasta capturas auth PASS.
- No ignorar el 500 como console noise.
- No crear fix sin URL exacta.
- No subir `backup/`.
- El fix específico del 500 no está aplicado porque la URL exacta aún no existe en diagnóstico.

## Recomendación CTO

Reejecutar el script R4 desde PowerShell segura. Si falla, usar `outputs/r4-auth-capture-diagnostics.json` como fuente única para clasificar y corregir el 500.
