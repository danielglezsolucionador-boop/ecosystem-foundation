# ECOSYSTEM Codex Execution Plan V1

Estado: plan preparado, no ejecutado
Fecha: 2026-06-06

## Regla

Este plan no autoriza ejecucion. Solo prepara fases futuras para Codex.

## Fase 1 - Revision autenticada CEO del Control Center

- Objetivo: validar cabina con sesion CEO real.
- Archivos probables: ninguno o reporte.
- Validacion: login, `/api/v1/auth/me`, rutas protegidas, mobile/desktop.
- Riesgos: credenciales en chat.
- No tocar: produccion mutable, secretos.
- Cierre: CEO ve cabina y endpoints protegidos PASS.

## Fase 2 - Cabina humana premium del ecosistema

- Objetivo: ajustar Home como centro de direccion.
- Archivos probables: `apps/web/control-center/*`, tests, reporte.
- Validacion: console 0, overflow NO, login no roto.
- Riesgos: declarar operativo lo preparado.
- No tocar: backend/auth salvo necesidad aprobada.
- Cierre: CEO entiende estado en 10 segundos.

## Fase 3 - Inventario completo de apps

- Objetivo: consolidar registry, discovery, documented_only.
- Archivos probables: docs y data registry si se aprueba.
- Validacion: matriz completa.
- Riesgos: mezclar Sniff Amazon y Comercio Autonomo.
- No tocar: runtimes externos.
- Cierre: todas las apps obligatorias con estado.

## Fase 4 - Registrar NUBE como planned/documented_only

- Objetivo: reflejar NUBE sin tocar herramienta local.
- Archivos probables: registry/docs si se aprueba.
- Validacion: NUBE visible como planned/documented_only.
- Riesgos: tocar secretos o deploys.
- No tocar: `C:\Users\admin\nube`, variables cloud.
- Cierre: NUBE documentada, no conectada.

## Fase 5 - Completar SENTINELA como pending_review

- Objetivo: definir seguridad defensiva sin integracion real.
- Archivos probables: registry/contracts/docs si se aprueba.
- Validacion: pending_review, no ofensivo.
- Riesgos: seguridad ofensiva por error.
- No tocar: productivo, escaneos externos.
- Cierre: SENTINELA no conectado y pendiente CEO.

## Fase 6 - Mantener DCFT como protected_no_touch

- Objetivo: sostener bloqueo hasta cierre de criterios.
- Archivos probables: docs/governance si se aprueba.
- Validacion: DCFT no conectado.
- Riesgos: SUNAT real o credenciales.
- No tocar: DCFT productivo, SUNAT, Clave SOL.
- Cierre: protected_no_touch visible.

## Fase 7 - Probar CEREBRO con 12 preguntas

- Objetivo: validar respuesta ejecutiva.
- Archivos probables: reporte de validacion.
- Validacion: respuestas cortas, sin alucinacion.
- Riesgos: CEREBRO declare conexiones falsas.
- No tocar: runtime CEREBRO.
- Cierre: preguntas PASS o observaciones.

## Fase 8 - Definir rutas futuras del bus sin activarlas

- Objetivo: disenar eventos/contratos futuros.
- Archivos probables: docs/contracts.
- Validacion: routes siguen 0 si no hay aprobacion.
- Riesgos: crear rutas reales.
- No tocar: Integration Bus runtime real.
- Cierre: rutas documentadas, no activas.

## Fase 9 - Preparar commit local

- Objetivo: agrupar cambios aprobados.
- Archivos probables: docs, tests, UI.
- Validacion: compileall, pytest, validate_v1, secret scan.
- Riesgos: incluir secretos/untracked externos.
- No tocar: apps protegidas.
- Cierre: git diff revisado.

## Fase 10 - Push/deploy solo con autorizacion CEO/CTO

- Objetivo: publicar cambios aprobados.
- Archivos probables: commit/tag/reporte.
- Validacion: produccion publica y autenticada.
- Riesgos: deploy innecesario, cuota, auth.
- No tocar: DCFT/FORJA/SENTINELA/NUBE local.
- Cierre: push/deploy PASS o blocker registrado.

## Cierre

Codex debe ejecutar una fase solo cuando el CEO/CTO la autorice.
