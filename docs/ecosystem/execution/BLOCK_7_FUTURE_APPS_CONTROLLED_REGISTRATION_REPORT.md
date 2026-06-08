# Block 7 - Future Apps Controlled Registration Report

Fecha/hora local: 2026-06-08 07:38:58 -05:00

## Estado General

Bloque 7 ejecutado localmente para registrar y verificar DCFT, SENTINELA y ARSENAL como componentes visibles, preparados o protegidos dentro del ecosistema. No se habilitó ningún runtime real, conexión externa, ruta real del bus, SUNAT, Local Agent, producción, push ni deploy.

## DCFT

- Nombre visible: Doctor Contable Financiero Tributario.
- Rol interno: contador financiero tributario de la empresa.
- Alcance futuro: contabilidad, finanzas, tributación, auditoría contable y auditoría financiera.
- Rol comercial: primer producto comercial vendible prioritario previsto.
- Estado controlado: `protected_no_touch`.
- Conexión externa: `external_connection_enabled=false`.
- Runtime real: `runtime_connected=false`.
- SUNAT real: `sunat_enabled=false`.
- Secretos/credenciales: `secrets_required=false`.
- Aprobación CEO: `requires_ceo_approval=true`.
- Governance: ejecución real bloqueada; gate protegido.

## SENTINELA

- Nombre visible: SENTINELA.
- Rol interno: seguridad y protección del ecosistema.
- Alcance futuro: vigilancia de agentes, permisos, datos, prompts, incidentes y riesgos.
- Rol comercial: futuro producto B2B de seguridad y protección.
- Estado controlado: `pending_review_protected`.
- Conexión externa: `external_connection_enabled=false`.
- Runtime real: `runtime_connected=false`.
- SUNAT real: `sunat_enabled=false`.
- Secretos/credenciales: `secrets_required=false`.
- Aprobación CEO: `requires_ceo_approval=true`.
- Governance: ejecución real bloqueada; gate protegido.

## ARSENAL

- Nombre visible: ARSENAL.
- Rol interno: almacén estratégico de APIs, skills, modelos, conectores, herramientas y capacidades.
- Estado controlado: `planned_pending_integration`.
- Conexión externa: `external_connection_enabled=false`.
- Runtime real: `runtime_connected=false`.
- Secretos requeridos: `secrets_required=false`.
- Cabina humana completa: `human_cabin_complete=false`.
- Aprobación CEO: `requires_ceo_approval=true`.
- Governance: sin conexión real; permanece como componente planificado sin runtime.

## Qué Se Registró

- Se amplió el App Registry a 14 apps incluyendo ARSENAL.
- Se agregaron banderas de control a las apps registradas: conexión externa, runtime, SUNAT, secretos, aprobación CEO, bloqueo governance y estado controlado.
- Se expusieron esas banderas en el Control Center API.
- Se actualizó la cabina local para explicar que DCFT y SENTINELA están representados, protegidos y no conectados, y que ARSENAL está planificado sin runtime.
- Se actualizó Governance para proteger SENTINELA igual que DCFT y mantener alias seguro `sentinela -> centinela`.

## Qué Quedó Bloqueado

- DCFT real.
- SENTINELA real.
- ARSENAL como runtime real.
- SUNAT real.
- Credenciales y secretos.
- Rutas reales del bus.
- Runtimes externos.
- Producción, push, deploy y commit.

## Cabina

La cabina local muestra:

- DCFT: representado, no conectado, `protected_no_touch`, sin SUNAT real, credenciales ni runtime.
- SENTINELA: representado, no conectado, `pending_review / protected`, sin runtime productivo.
- ARSENAL: `planned / pending_integration`, planificado, no conectado, sin cabina humana completa, runtime, secretos ni APIs reales.
- La próxima decisión CEO indica que los tres están visibles como representados o planificados y que ninguno está conectado.

## Governance

- DCFT permanece protegido y bloqueado.
- SENTINELA queda protegido y bloqueado.
- ARSENAL queda no protegido pero no conectado, sin runtime y con ejecución real bloqueada por la política general de no conexiones externas.
- No se ejecuta conexión real aunque una fase futura aprobara discovery o connection.

## Contracts

No se crearon contratos productivos ni rutas reales. El cambio es documental/controlado por App Registry, Control Center y Governance local.

## Validaciones

- `node --check apps/web/control-center/assets/app.js`: PASS.
- `python -m compileall apps/api api scripts -q`: PASS.
- `$env:PYTHONPATH="apps/api"; pytest -q`: PASS, 259 passed.
- `python scripts/validate_v1.py`: PASS, incluye compileall, pytest, import API y secret scan.
- `git diff --check`: PASS.
- Secret scan adicional case-insensitive para `sk-*`: PASS.

## Seguridad

Durante la validación se detectó un patrón `sk-*` en un backup previo no tracked: `backup/before-final-product-auth-tag-20260608-065019/final-working-tree.patch`. Fue redactado sin imprimir valores. Después de la redacción, el secret scan oficial y el adicional quedaron PASS.

## Riesgos

- `backup/` ya existía como carpeta no tracked antes de este bloque; se preserva sin commit.
- ARSENAL aún no tiene cabina humana completa ni contrato de integración. Esto es intencional para este bloque.
- SENTINELA está visible y protegido, pero no revisado como producto real.

## No Tocado

- DCFT real productivo.
- SENTINELA real productivo.
- FORJA productiva.
- NUBE local.
- Local Agent.
- SUNAT real.
- Producción pública.
- Vercel.
- Runtimes externos.
- Rutas reales del bus.

## Siguiente Bloque Recomendado

Bloque 8: revisión CEO de App Registry + Governance Gates para decidir si ARSENAL requiere modelo documental propio o si primero debe avanzarse con un contrato de integración preparado, sin runtime real.
