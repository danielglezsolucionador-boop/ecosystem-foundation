# Block R.7 - Revenue Sprint Approval Needed Fix Report

Fecha/hora: 2026-06-09 22:35 -05:00
Rama: main
HEAD inicial: `365648e fix: stabilize authenticated release screenshots`

## Estado

Estado R.7: `FIX_DEPLOYED_PUBLIC_PASS / AUTH_CAPTURES_PENDING`.

## Endpoint Fallido

Endpoint exacto reportado por captura autenticada:

- `GET https://ecosystem-foundation.vercel.app/api/v1/revenue/sprint/approval-needed`
- Status: `500`

Diagnóstico del JSON:

- `badResponses`: contiene `approval-needed` con status `500`.
- `requestFailures`: `[]`
- `pageErrors`: `[]`
- cabina visible;
- rol `CEO`;
- señales: `Empresa IA`, `CEREBRO`, `Revenue`, `AUDITORÍA`.

## Causa

Causa técnica encontrada en código:

- `/api/v1/revenue/sprint/approval-needed` devolvía directamente `list[RevenueSprintRoute]`.
- La función dependía de `list_sprint_routes()`, que parseaba todos los payloads de Revenue Sprint de forma estricta.
- Si producción PostgreSQL tenía `payload_json` legacy, nulo, inválido, incompleto o con forma no compatible, el endpoint podía devolver 500.
- No existía fallback seguro para el endpoint visual usado por la cabina.

## Fix

Archivos modificados:

- `apps/api/app/schemas/revenue.py`
- `apps/api/app/api/revenue.py`
- `apps/api/app/services/revenue.py`
- `apps/api/app/services/ceo.py`
- `apps/web/control-center/assets/app.js`
- `work/run_total_ecosystem_authenticated_audit.ps1`

Cambios:

- Se creó `RevenueSprintApprovalNeeded`.
- El endpoint ahora devuelve estructura estable:
  - `status`
  - `mode`
  - `approval_required`
  - `items`
  - `count`
  - `requires_ceo_action`
  - `message`
  - `fallback`
  - flags de no-runtime/no-pagos/no-ingresos reales.
- Si no hay aprobaciones, devuelve `items=[]` y `count=0`.
- Si la carga de rutas falla, devuelve fallback seguro con HTTP 200.
- No inventa aprobaciones, ingresos, ROI ni campañas.
- Frontend acepta objeto nuevo o lista legacy.
- Auditoría autenticada total ahora cubre `/api/v1/revenue/sprint/approval-needed`.
- Centro CEO conserva warning determinístico `nube_status_timeout_fallback` cuando se fuerza degradación local de NUBE, sin tocar `C:\Users\admin\nube`.

## Reglas CEO Preservadas

Requiere CEO:

- dinero real;
- pagos;
- campañas pagadas;
- APIs/herramientas con costo;
- contratación;
- cuentas externas nuevas;
- credenciales sensibles;
- riesgo legal/sensible.

No requiere CEO:

- orgánico preparado;
- Local Agent preparado;
- FORJA interna;
- misiones internas;
- cambios de prioridad;
- auditorías;
- tareas internas.

## Tests

Test focal:

- `$env:PYTHONPATH="apps/api"; python -m pytest -q apps/api/tests/test_revenue_execution_sprint.py`
- Resultado: PASS, `16 passed`.

Cobertura agregada:

- endpoint requiere auth;
- endpoint responde 200 con auth;
- responde estructura estable;
- lista vacía segura si no hay rutas;
- fallback seguro si falla carga de rutas;
- no inventa aprobaciones;
- paid/costo requiere aprobación;
- orgánico/prepared no requiere aprobación;
- parser tolera `payload_json` null, dict, string JSON e inválido.

## Validaciones

Validaciones rápidas:

- `node --check apps/web/control-center/assets/app.js`: PASS.
- `node --check work/r4_ai_company_auth_screenshots.mjs`: PASS.
- `python -m compileall apps/api api scripts -q`: PASS.
- `git diff --check`: PASS.
- `$env:PYTHONPATH="apps/api"; python -m pytest -q`: PASS, `474 passed, 1 skipped`.
- `python scripts/validate_v1.py`: PASS, `474 passed, 1 skipped`, secret scan PASS.

Confirmado post-fix:

- commit funcional: `5572679 fix: stabilize revenue sprint approval-needed endpoint`;
- push a `origin/main`: PASS;
- deploy automático Vercel: PASS;
- `/version`: commit `5572679`;
- `/runtime/status`: commit `5572679`, PostgreSQL conectado, SQLite false, persistent true;
- `/control-center`: HTTP 200.

Pendiente:

- reejecución de capturas auth por CEO;
- tag `v1-ai-company-operating-system` solo si `R4_AUTH_CAPTURES_PASS`.

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

## Siguiente Paso

Pedir al CEO reejecutar desde PowerShell segura:

```powershell
cd "C:\Users\admin\Documents\Codex\2026-05-31\auditoria-final-forja-render-he-validado"
.\work\run_r4_auth_captures.ps1
```
