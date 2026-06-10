# Block R.8 - Control Center Endpoint Hardening Report

Fecha/hora: 2026-06-09 23:32 -05:00
Rama: main
HEAD inicial: `1c1d3f7 docs: clarify R7 audit script scope`

## Estado

Estado R.8: `FIX_DEPLOYED_PUBLIC_PASS / AUTH_AUDIT_PENDING`.

## Problema

La captura autenticada productiva dejo de fallar en Revenue Sprint, pero aparecio otro 500:

- `GET /api/v1/cerebro/chief-of-staff/status`
- Status: `500`

Conclusion tecnica: la cabina no necesitaba otro parche endpoint por endpoint; necesitaba blindaje contra datos faltantes, payloads legacy, `payload_json` nulo/string/dict y diferencias PostgreSQL/SQLite.

## Regla Aplicada

Endpoints de cabina autenticados deben mantener:

- 401 si no hay autenticacion valida;
- 403 si falta permiso;
- 404 si la ruta o recurso puntual no existe;
- 200 con fallback seguro si el dato interno opcional falta, esta vacio, es legacy o esta incompleto.

## Endpoints Inventariados

Inventario desde `apps/web/control-center/assets/app.js`, scripts de captura y auditoria:

- `/api/v1/auth/me`
- `/api/v1/control-center`
- `/api/v1/control-center/apps`
- `/api/v1/governance/auth-boundary?role_id=ceo`
- `/api/v1/cerebro/status`
- `/api/v1/cerebro/chief-of-staff/status`
- `/api/v1/cerebro/goals`
- `/api/v1/cerebro/missions`
- `/api/v1/cerebro/alerts`
- `/api/v1/cerebro/revenue`
- `/api/v1/cerebro/approval-requests`
- `/api/v1/cerebro/checkpoints/morning`
- `/api/v1/cerebro/checkpoints/midday`
- `/api/v1/cerebro/checkpoints/evening`
- `/api/v1/departments`
- `/api/v1/departments/audits`
- `/api/v1/revenue/status`
- `/api/v1/revenue/goals`
- `/api/v1/revenue/opportunities`
- `/api/v1/revenue/approval-requests`
- `/api/v1/revenue/department-contribution`
- `/api/v1/revenue/daily-report`
- `/api/v1/revenue/sprint/status`
- `/api/v1/revenue/sprint/routes`
- `/api/v1/revenue/sprint/missions`
- `/api/v1/revenue/sprint/daily`
- `/api/v1/revenue/sprint/risks`
- `/api/v1/revenue/sprint/approval-needed`
- `/api/v1/arsenal/status`
- `/api/v1/arsenal/catalog`
- `/api/v1/arsenal/categories`
- `/api/v1/arsenal/risks`
- `/api/v1/arsenal/readiness`
- `/api/v1/missions`
- `/api/v1/missions/active`
- `/api/v1/missions/reports/daily`
- `/api/v1/workday/status`
- `/api/v1/workday/morning`
- `/api/v1/workday/midday`
- `/api/v1/workday/evening`
- `/api/v1/workday/alerts`
- `/api/v1/workday/priority-changes`
- `/api/v1/workday/report`
- `/api/v1/upgrades/status`
- `/api/v1/upgrades/packages`
- `/api/v1/publishing/status`
- `/api/v1/publishing/channels`
- `/api/v1/publishing/calendar`
- `/api/v1/publishing/content`
- `/api/v1/publishing/growth`
- `/api/v1/product-readiness/status`
- `/api/v1/product-readiness/dcft`
- `/api/v1/product-readiness/sentinela`
- `/api/v1/product-readiness/gaps`
- `/api/v1/product-readiness/marketing-package`
- `/api/v1/ceo/daily-center`
- `/api/v1/ceo/morning`
- `/api/v1/ceo/evening`
- `/api/v1/ceo/decisions`
- `/api/v1/integration-bus/status`
- `/api/v1/integration-bus/routes`
- `/api/v1/integration-bus/prepared-routes`
- `/api/v1/contracts`
- `/api/v1/contracts/status`
- `/api/v1/auditoria/status`
- `/api/v1/auditoria/reviews`
- `/api/v1/auditoria/queue`
- `/api/v1/nube/status`
- `/api/v1/nube/projects`
- `/api/v1/nube/deployments`
- `/api/v1/nube/health-checks`
- `/api/v1/nube/risks`
- `/api/v1/nube/costs`
- `/api/v1/governance`
- `/api/v1/governance/reports`
- `/api/v1/governance/decisions`
- `/api/v1/governance/approvals`
- `/api/v1/governance/integration-gates`
- `/api/v1/governance/policies`
- `/api/v1/governance/risks`
- `/api/v1/governance/audit`
- `/api/v1/audit`
- `/api/v1/observability/status`

## Blindaje Chief of Staff

`/api/v1/cerebro/chief-of-staff/status` ahora:

- responde 200 aunque haya payloads corruptos o incompletos en goals, missions, alerts o approval requests;
- incluye `mode`, `fallback`, `count`, `requires_ceo_action`, `message`;
- conserva motto `El tiempo es dinero`;
- conserva politica de autonomia sin runtime externo;
- mantiene `external_connection_enabled=false`, `runtime_connected=false`, `sunat_enabled=false`, `local_agent_enabled=false`;
- no inventa metas, ingresos, aprobaciones ni acciones reales.

## Helpers Globales

Se agrego `app.core.safe_data` con:

- `safe_payload(row)`;
- `safe_payload_json(value)`;
- `safe_json_value(value)`;
- `safe_list(value)`;
- `safe_dict(value)`;
- `safe_count(value)`;
- `safe_iso_datetime(value)`;
- `safe_endpoint_response(default_payload, error_context)`.

Tambien se amplio `get_row_value(row, key, index=None, default=None)` para tolerar:

- PostgreSQL `dict_row`;
- SQLite `Row`;
- fallback por indice legacy;
- campos ausentes.

## Servicios Blindados

Servicios ajustados:

- `cerebro`;
- `revenue`;
- `publishing`;
- `product_readiness`;
- `missions`;
- `workday`;
- `upgrades`;
- `departments`;
- `arsenal`;
- `governance`;
- `nube` interno del ecosistema;
- `audit`;
- `contracts`;
- `observability`;
- `integration_bus`;
- `events`;
- `memory`;
- `security`;
- `auth` audit metadata.

## Auditoria Auth

`work/run_total_ecosystem_authenticated_audit.ps1` fue actualizado localmente para cubrir la superficie ampliada de cabina, incluyendo:

- Revenue Sprint routes/missions/daily/risks/approval-needed;
- Workday midday/alerts/priority-changes/report;
- Publishing calendar/growth;
- Product Readiness gaps/marketing-package;
- Arsenal categories/risks;
- Governance reports/decisions/approvals/gates/policies/risks/audit;
- CEO morning/evening/decisions.

Nota: `work/` esta ignorado por Git; el script queda actualizado en la maquina local para ejecucion del CEO, pero no se incluye en commit.

## Tests

Nuevo test:

- `apps/api/tests/test_control_center_endpoint_stability.py`

Cobertura:

- endpoints de cabina con auth responden 200;
- sin auth siguen respondiendo 401;
- Chief of Staff no devuelve 500 por payloads legacy/corruptos;
- Revenue Sprint approval-needed no devuelve 500;
- Publishing/Product Readiness no inventan pagos, cuentas ni metas propias;
- no se declaran ingresos reales.

Resultados locales:

- test focal R.8: PASS, `5 passed`;
- suite completa: PASS, `479 passed, 1 skipped`.

## No Tocado

No se toco:

- DCFT real;
- SENTINELA real;
- FORJA externa;
- `C:\Users\admin\nube`;
- SUNAT real;
- pagos;
- campanas;
- cuentas externas;
- secretos;
- tag final.

## Pendiente

- Validaciones finales completas: PASS.
- Commit: `60b2948 fix: harden control center production endpoints`.
- Push a `origin/main`: PASS.
- Deploy automatico Vercel: PASS.
- `/version`: commit `60b2948`.
- `/runtime/status`: commit `60b2948`, PostgreSQL conectado, SQLite false, persistent true.
- `/control-center`: HTTP 200.
- Rutas protegidas sin auth: 401 en `chief-of-staff/status`, `revenue/sprint/approval-needed` y `control-center`.
- CEO debe ejecutar `.\work\run_total_ecosystem_authenticated_audit.ps1`.
- Luego CEO debe ejecutar `.\work\run_r4_auth_captures.ps1`.
- Tag `v1-ai-company-operating-system` solo con auditoria auth ampliada PASS y `R4_AUTH_CAPTURES_PASS`.
