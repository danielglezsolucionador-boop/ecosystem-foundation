# Block R.6 - Final Auth Capture Script Fix Report

Fecha/hora: 2026-06-09 22:05 -05:00
Rama: main
HEAD inicial: `2c16dec docs: record R2 production validation blocker`

## Estado

Estado R.6: `SCRIPT_FIXED / AWAITING_SECURE_CAPTURE_EXECUTION`.

El bloqueo real ya no es autenticación ni 500.

Evidencia desde `outputs/r4-auth-capture-diagnostics.json`:

- `badResponses`: `[]`
- `requestFailures`: `[]`
- `consoleErrors`: `[]`
- `pageErrors`: `[]`
- `loginFormAttached`: `true`
- `appAttached`: `true`
- `roleText`: `CEO`
- señales visibles: `Empresa IA`, `CEREBRO`, `Revenue`, `AUDITORÍA`

Conclusión:

- La cabina autenticada sí cargó señales reales.
- El script fallaba por tratar `loginFormAttached` como error aunque el login no estuviera visible y la app autenticada estuviera montada.

## Backup Pre-R6

Creado:

- `backup/before-R6-final-auth-capture-script-fix-20260609-220030`

Incluye:

- estado Git;
- log;
- diff;
- `outputs/r4-auth-capture-diagnostics.json`;
- `outputs/r4-debug-auth-failure-mobile.png`;
- `work/r4_ai_company_auth_screenshots.mjs`;
- `BACKUP_SUMMARY.md`.

## Fix Script

Archivo modificado:

- `work/r4_ai_company_auth_screenshots.mjs`

Cambios:

- Ya no falla por `loginFormAttached`.
- Calcula `loginFormVisible` real.
- Calcula `appVisible` real.
- Calcula `hasCabinSignals`.
- Calcula `authenticatedCabinReady`.
- Falla por login solo cuando:
  - `loginFormVisible === true`;
  - `appVisible !== true`;
  - `hasCabinSignals !== true`.
- Si la cabina está lista, guarda captura final aunque el formulario exista oculto en el DOM.
- Mantiene diagnóstico JSON y screenshot de fallo si algo falla.

## Fix Mojibake

Búsqueda ejecutada en:

- `apps/web`
- `docs/ecosystem/execution`
- `apps/api/app/data`
- `work`, excluyendo tests/detectores intencionales y temporales pytest.

Resultado:

- No se encontró mojibake real en fuentes visibles.
- `outputs/r4-auth-capture-diagnostics.json` está correctamente codificado: `AUDITORÍA` en disco.
- El mojibake observado provenía de render de consola, no del archivo fuente.

Detector reforzado:

- `Ãƒ`
- `Ã‚`
- `Ã¢`
- `ï¿½`
- `Ã`
- `Â`
- `â`

## Tests

Test agregado:

- `work/r4_ai_company_auth_screenshots.test.mjs`

Cobertura:

- login attached pero app visible no falla;
- login visible y app no visible sí falla;
- mojibake con `Ãƒ`/`Ã` sí falla;
- app attached con CEO/CEREBRO/Revenue/AUDITORÍA pasa.

Resultado:

- `node --test work/r4_ai_company_auth_screenshots.test.mjs`: PASS, 4 tests.
- `node --check work/r4_ai_company_auth_screenshots.mjs`: PASS.
- `node --check apps/web/control-center/assets/app.js`: PASS.
- `python -m compileall apps/api api scripts -q`: PASS.
- `$env:PYTHONPATH="apps/api"; python -m pytest -q`: PASS, `470 passed, 1 skipped`.
- `python scripts/validate_v1.py`: PASS, `470 passed, 1 skipped`, secret scan PASS.
- `git diff --check`: PASS.

## Pendiente Para Cierre

Codex no tiene `CONTROL_CENTER_ADMIN_EMAIL` ni `CONTROL_CENTER_ADMIN_PASSWORD` en esta sesión.

El CEO debe ejecutar desde PowerShell segura:

```powershell
cd "C:\Users\admin\Documents\Codex\2026-05-31\auditoria-final-forja-render-he-validado"
.\work\run_r4_auth_captures.ps1
```

Criterio de cierre:

- `R4_AUTH_CAPTURES_PASS`
- existe `outputs/ecosystem-ai-company-operating-system-production-auth-mobile-390x844.png`
- existe `outputs/ecosystem-ai-company-operating-system-production-auth-desktop-1280x720.png`
- cabina visible;
- no login visible bloqueante;
- no mojibake;
- no 500;
- console errors críticos 0.

## No Tocado

No se tocó:

- DCFT real;
- SENTINELA real;
- FORJA externa;
- `C:\Users\admin\nube`;
- SUNAT real;
- pagos;
- campañas;
- cuentas externas;
- secretos.

## Recomendación CTO

Ejecutar capturas R4 nuevamente desde PowerShell segura. Si devuelve `R4_AUTH_CAPTURES_PASS`, proceder con commit final, push, deploy y tag `v1-ai-company-operating-system`.
