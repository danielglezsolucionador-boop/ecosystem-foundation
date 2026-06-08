# ECOSYSTEM HUMAN CABIN PREMIUM REPORT

Fecha: 2026-06-06

## 1. Que cambio

Se actualizo la cabina humana del Control Center para que la primera vista lea como Centro de Direccion del Ecosistema IA, no como inventario tecnico.

Cambios frontend-only:

- Header renombrado a ECOSISTEMA IA / Centro de Direccion Empresarial.
- Navegacion humana: Inicio CEO, Gobierno, Operacion, Auditoria, Sistema.
- Semaforo principal: Operacion, Construccion, Seguridad, Finanzas / Cloud.
- Indicador de apps conectadas reales.
- Proxima decision CEO visible en el primer pantallazo.
- Accesos rapidos compactos.
- Cards prioritarias para CEREBRO, FORJA, NUBE, AUDITORIA, SENTINELA, DCFT, HERMES y apps de contenido/crecimiento.
- Bottom nav mobile: Inicio, Apps, Cerebro, Riesgos, Perfil.
- Mapa de apps con fuente del dato: discovery profile, registry, registry externo protegido o no registrada.

No se modifico backend, auth, DCFT, FORJA productivo, CEREBRO productivo ni SENTINELA productivo.

## 2. Que apps aparecen

Aparecen en la cabina:

- CEREBRO
- FORJA
- NUBE
- AUDITORIA
- SENTINELA
- DCFT
- HERMES
- PLUMA
- LENTE
- WEB FACTORY
- MARKETING
- MARCA PERSONAL
- COMERCIO AUTONOMO
- BUSCADOR DE TENDENCIAS

## 3. Apps con datos reales

Datos reales de plataforma:

- Auth/login y sesion Bearer.
- Control Center protegido.
- App Registry.
- Integration profiles.
- Governance.
- Audit.
- Observability.
- Integration Bus.
- Contracts.
- Runtime/status.
- PostgreSQL production cuando backend productivo responde.

Apps externas conectadas reales desde Ecosystem Foundation:

- Ninguna en esta fase.

La cabina muestra `Apps conectadas reales` como conteo separado y no declara conectada una app que solo tiene discovery profile.

## 4. Apps preparadas

Discovery profiles preparados, con `external_connection_enabled=false`:

- HERMES
- AUDITOR
- PLUMA
- LENTE
- WEB FACTORY
- MARKETING
- MARCA PERSONAL
- COMERCIO AUTONOMO
- BUSCADOR DE TENDENCIAS
- FORJA
- CEREBRO

## 5. Apps pendientes

- DCFT: registry externo/protegido; no integrado desde Ecosystem Foundation.
- SENTINELA/CENTINELA: reservado en App Registry; falta discovery profile e integracion.
- NUBE: no registrada todavia en App Registry ni discovery profiles.

## 6. CEREBRO

Queda presentado como Director estrategico / mano derecha CEO.

Estado mostrado:

- Discovery preparado.
- Sin conversacion real conectada desde esta cabina.
- Accion visible: Hablar con CEREBRO, usada como acceso de orientacion dentro de la cabina, no como llamada a runtime externo.

## 7. FORJA

Queda presentada como Directora de construccion.

Estado mostrado:

- Produccion externa congelada y validada por evidencia previa.
- En Ecosystem Foundation solo discovery preparado.
- Runtime externo no conectado.
- Accion visible: Enviar tarea controlada, sin ejecutar tareas reales desde esta cabina.

## 8. NUBE

Queda presentada como Torre de control cloud.

Estado mostrado:

- No registrada todavia en Ecosistema.
- Cloud/DB se separa del rol NUBE: la plataforma puede reportar PostgreSQL vivo, pero NUBE sigue pendiente.

## 9. AUDITORIA

Queda presentada como Juez de calidad, costos y aprobacion.

Estado mostrado:

- Auditoria interna operativa.
- App Auditor preparada como discovery profile.
- Sin runtime externo.

## 10. DCFT

Queda presentada como Doctor contable financiero tributario.

Estado mostrado:

- Piloto SUNAT auxiliar en preparacion controlada.
- Referenciada como externa/protegida.
- No integrada ni conectada desde Ecosystem Foundation.

## 11. SENTINELA

Queda presentada como Seguridad y proteccion del ecosistema.

Estado mostrado:

- Reservada en registry como pendiente.
- Falta discovery profile.
- Falta integration gate completo para integracion futura.

## 12. Mobile

Se preparo layout mobile-first:

- Primer bloque: estado global.
- Semaforo compacto.
- Proxima decision CEO.
- Apps prioritarias.
- Bottom nav fijo con Inicio, Apps, Cerebro, Riesgos, Perfil.

Validacion ejecutada:

- Viewport 390x844 sobre shell de login local.
- Console errors: 0.
- Overflow horizontal: NO.
- Login screen visible: SI.

Limitacion de herramienta:

- El navegador integrado no permitio escribir inputs ni storage para completar login visual autenticado. La sesion autenticada fue validada por API local con Bearer sin imprimir token.

## 13. Desktop

Se mantiene:

- Sidebar izquierda.
- Centro operativo.
- Paneles de decisiones, riesgos, governance, operador, auditor y sistema.

La home ahora prioriza decision ejecutiva y separa dato real de preparado.

Validacion ejecutada:

- Viewport 1280x720 sobre shell de login local.
- Console errors: 0.
- Overflow horizontal: NO.
- Login screen visible: SI.

Validacion autenticada local por API:

- `/api/v1/auth/me`: 200.
- `/api/v1/control-center`: 200.
- `/api/v1/governance`: 200.
- `/api/v1/governance/integration-gates`: 200.
- `/api/v1/audit`: 200.
- `/api/v1/observability/status`: 200.
- `/api/v1/integration-bus/status`: 200.
- `/api/v1/contracts/status`: 200.
- `/api/v1/integrations/apps`: 200, 11 profiles, 0 external connections enabled.

Proteccion sin sesion:

- `/api/v1/auth/me`: 401.
- `/api/v1/control-center`: 401.
- `/api/v1/governance`: 401.
- `/api/v1/audit`: 401.
- `/api/v1/observability/status`: 401.

Tests:

- `node --check apps/web/control-center/assets/app.js`: PASS.
- `python -m compileall apps/api api scripts -q`: PASS.
- `python -m pytest -q` desde `apps/api`: 257 passed.
- `npm run build`: NO APLICA / BLOCKED por ausencia de `package.json` en el repo.
- `npm test`: NO APLICA por ausencia de `package.json`.

## 14. Riesgos

- No hay runtime externo conectado para apps preparadas.
- NUBE no existe todavia en registry.
- SENTINELA solo esta reservada como planned/registry.
- DCFT sigue protegido y fuera de esta integracion.
- La validacion autenticada productiva no se ejecuto en esta tarea porque no se solicitaron credenciales ni autorizacion de produccion.
- La validacion visual autenticada en navegador quedo limitada por la herramienta; los endpoints autenticados si pasaron localmente con token Bearer no impreso.
- Si no existe `package.json`, `npm run build` no aplica al frontend estatico actual.

## 15. Recomendacion

Recomendado para revision CEO local antes de push/deploy.

Siguiente paso recomendado:

1. Levantar backend local.
2. Entrar con sesion local segura.
3. Validar mobile 390x844 y desktop.
4. Confirmar console errors = 0.
5. Confirmar overflow horizontal = NO.
6. Si CEO aprueba, recien entonces preparar commit/push/deploy controlado.
