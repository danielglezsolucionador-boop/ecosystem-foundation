# Ecosystem Local Rupture Audit Report

Fecha local: 2026-06-08 01:49:26 -05:00

Frente: ECOSISTEMA IA / AUDITORIA LOCAL FUERTE / CABINA EMPRESA IA

## Estado final

- Auditoria local fuerte ejecutada.
- Cabina local autenticada validada.
- Ruptura visual mobile/desktop validada.
- Seguridad local validada.
- Consistencia real/preparado/protegido validada.
- Correccion local aplicada y revalidada.
- No push.
- No deploy.
- No produccion.
- No Vercel.
- No runtimes externos.
- No rutas reales del bus.

## Inspeccion inicial

Rama:

- `main`

Estado del working tree:

- Habia cambios trackeados previos en cabina, API y tests.
- Habia multiples documentos nuevos de ecosistema.
- Habia carpeta `backup/` de paquetes previos.
- El working tree estaba mezclado, por lo que no se considero seguro hacer commit local.

Servidor local:

- URL: `http://127.0.0.1:8000/control-center`
- Estado inicial: HTTP 200.
- El servidor fue reiniciado localmente para cargar la correccion de governance.
- PID despues de reinicio: `3256`.

## Pruebas ejecutadas

### Cabina local

- Login local CEO por API: PASS.
- Sesion local CEO en cabina: PASS.
- Cabina autenticada visible: PASS.
- CEREBRO visible: PASS.
- Reunion con CEREBRO visible: PASS.
- Departamentos visibles en DOM: PASS.
- Arsenal visible: PASS.
- Bottom nav mobile visible: PASS.
- Navegacion bottom nav: PASS.

### Ruptura visual

Viewports probados:

- Mobile exacto `390x844`: PASS.
- Ancho menor `320x844`: PASS.
- Desktop exacto `1280x720`: PASS.

Resultados:

- Sin overflow horizontal.
- Sin textos importantes cortados.
- Sin loading persistente.
- Sin scrolls internos excesivos.
- Sin botones ilegibles.
- Sin cards gigantes.
- Sin informacion critica oculta.
- Console errors: 0.

Capturas:

- `outputs/ecosystem-audit-mobile-390x844.png`.
- `outputs/ecosystem-audit-desktop-1280x720.png`.

Nota:

- El motor de captura del navegador integrado fallo con timeout en `Page.captureScreenshot`.
- Se uso fallback local con Chrome del sistema y Playwright ya disponible en `work/node_modules`.
- No se instalo nada.
- No se uso red externa.

### Seguridad local

Resultados API:

- Sin sesion en `/api/v1/control-center`: 401 PASS.
- Token invalido en `/api/v1/control-center`: 401 PASS.
- Login local CEO: 200 PASS.
- `/api/v1/auth/me` con sesion local: rol `CEO` PASS.
- `/api/v1/control-center` con sesion local: 200 PASS.
- Sin auth en `/api/v1/governance/auth-boundary`: 401 PASS.
- Auth valida en `/api/v1/governance/auth-boundary`: 200 PASS.
- Intento discovery DCFT protegido: 400 PASS.
- Intento connection DCFT protegido: 400 PASS.
- Gate DCFT: `blocked`, `protected=true` PASS.
- No se imprimieron tokens.
- No se imprimieron credenciales.
- No se activaron conexiones externas.

### Consistencia

Validado:

- DCFT no integrado: PASS.
- DCFT `protected_no_touch` / protegido: PASS.
- SENTINELA no productivo, pendiente/revision: PASS.
- FORJA real no conectada: PASS.
- FORJA visible/preparada: PASS.
- NUBE documental/no tocada: PASS.
- Arsenal `planned / pending_integration`: PASS.
- Buscador de Tendencias como radar oficial: PASS.
- No `INVESTIGADOR`: PASS.
- No `RADAR IA`: PASS.
- Sniff Amazon separado de Comercio Autonomo: PASS.
- Hermes en Construccion: PASS.
- Creador de APIs y Skills correcto: PASS.
- Datos reales vs preparados visibles: PASS.

## Fallos encontrados

### F1 - Discovery sobre app protegida respondia 200

Ruptura:

- `POST /api/v1/governance/integration-gates/doctor_contable_financiero_tributario/request-discovery`
- Estado antes: respondia 200 aunque el gate permanecia `blocked`.

Riesgo:

- La respuesta 200 podia leerse como avance permitido sobre DCFT protegido.

Correccion:

- `request_gate_discovery` ahora audita el intento y devuelve `400` con `protected_app_discovery_blocked` cuando el gate esta protegido.
- Se agrego test de regresion para bloquear discovery y connection de apps protegidas.

Archivos:

- `apps/api/app/services/governance.py`.
- `apps/api/tests/test_governance.py`.

Resultado despues:

- Discovery DCFT protegido: 400.
- Connection DCFT protegido: 400.
- Gate DCFT sigue `blocked` y `protected=true`.

## Validaciones tecnicas

- `node --check apps/web/control-center/assets/app.js`: PASS.
- `python -m compileall apps/api api scripts -q`: PASS.
- `$env:PYTHONPATH="apps/api"; python -m pytest -q`: PASS, 258 tests.
- `python scripts/validate_v1.py`: PASS, 258 tests y `secret scan PASS`.
- `git diff --check`: PASS, solo avisos CRLF.
- Secret scan manual sin imprimir secretos: PASS, `NO_MATCHES`.

## Archivos y artefactos

Archivos modificados por correccion/auditoria:

- `apps/api/app/services/governance.py`.
- `apps/api/tests/test_governance.py`.
- `docs/ecosystem/execution/ECOSYSTEM_LOCAL_RUPTURE_AUDIT_REPORT.md`.

Artefactos generados:

- `outputs/ecosystem-audit-mobile-390x844.png`.
- `outputs/ecosystem-audit-desktop-1280x720.png`.
- `outputs/ecosystem-audit-browser-results.json`.

## No tocado

- DCFT real.
- FORJA productiva.
- SENTINELA productiva.
- NUBE local.
- Local Agent.
- SUNAT real.
- Produccion.
- Vercel.
- Runtimes externos.
- Rutas reales del bus.
- Secretos.

## Riesgos pendientes

- El working tree sigue mezclado con cambios previos de ecosistema.
- No es seguro hacer commit local atomico sin separar paquetes.
- La cabina local esta validada, pero sigue siendo local.
- Arsenal sigue planned/pending, sin runtime real.
- SENTINELA y NUBE siguen pendientes/documentales desde este frente.

## Backup final

- Creado despues de auditoria PASS.
- Ruta: `backup/after-ecosystem-local-rupture-audit-pass-20260608-020124`.
- Estrategia: carpeta backup + patch local.
- Commit local: no realizado por working tree mezclado.
- Tests y servicios Python se preservaron como `.py.bak` dentro del backup para no interferir con pytest.

## Recomendacion

Crear backup final por carpeta/patch, no commit local, porque el working tree contiene cambios mezclados. Despues, el CEO puede decidir si se separa en commits por paquete o si se sigue con una revision de consolidacion documental.
