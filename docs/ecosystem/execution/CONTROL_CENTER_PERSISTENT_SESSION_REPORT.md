# CONTROL CENTER - Persistent Session Report

Fecha: 2026-06-08

## Estado

Se implementó la opción visual y funcional `Recordar sesión en este dispositivo` para el login del Control Center.

El objetivo es evitar que el CEO tenga que escribir credenciales cada vez que abre la cabina, manteniendo el modelo actual de autenticación con sesiones Bearer y sin crear backdoors.

## Qué Se Implementó

- Campo `remember_me` opcional en `POST /api/v1/auth/login`.
- Sesión normal con duración de 12 horas.
- Sesión recordada con duración de 30 días.
- Auditoría del login con metadata:
  - `remember_me`.
  - `session_ttl_hours`.
- Checkbox premium/mobile-first en el login:
  - `Recordar sesión en este dispositivo`.
  - Copy visible: `Activa una sesión extendida sin guardar tu contraseña.`
- Restauración automática al cargar `/control-center`:
  - El frontend busca una sesión guardada.
  - Llama a `/api/v1/auth/me`.
  - Si responde PASS, entra directo a la cabina.
  - Si responde 401 o la sesión expiró, borra la sesión local y muestra login.

## Dónde Se Guarda La Sesión

- Si `Recordar sesión` está marcado:
  - El token Bearer se guarda en `localStorage`.
  - El backend emite expiración de 30 días.
- Si `Recordar sesión` no está marcado:
  - El token Bearer se guarda en `sessionStorage`.
  - El backend emite expiración de 12 horas.
- Logout borra ambos almacenamientos:
  - `localStorage`.
  - `sessionStorage`.

## Por Qué No Se Guarda Contraseña

- La contraseña solo se usa en el request de login.
- No se guarda contraseña en `localStorage`.
- No se guarda contraseña en `sessionStorage`.
- No se imprime contraseña en consola, reportes ni tests.
- No se hardcodea usuario ni contraseña en el frontend.

## Seguridad

Se mantiene el modelo actual:

- Token Bearer con prefijo de sesión del Control Center.
- Token guardado hasheado en backend.
- `/api/v1/auth/me` como fuente de verdad para restaurar sesión.
- Token inválido fuerza login.
- Sesión expirada fuerza login.
- Sin sesión sigue devolviendo 401.
- Rutas protegidas siguen protegidas.
- Logout revoca sesión en backend y limpia storage del navegador.

No se agregaron endpoints públicos para saltar login.
No se crearon usuarios públicos.
No se crearon rutas nuevas del bus.

## Frontend

Archivos actualizados:

- `apps/web/control-center/index.html`.
- `apps/web/control-center/assets/styles.css`.
- `apps/web/control-center/assets/app.js`.

Cambios:

- Checkbox visual de recordar sesión.
- Estado de restauración: `Validando sesión guardada en este dispositivo.`
- Mensaje de éxito: `Sesión restaurada en este dispositivo.`
- Etiqueta visible `Contraseña`.
- Login mobile validado sin overflow horizontal.

## Backend

Archivos actualizados:

- `apps/api/app/schemas/auth.py`.
- `apps/api/app/services/auth.py`.

Cambios:

- `LoginRequest.remember_me`.
- TTL normal: 12 horas.
- TTL recordado: 30 días.
- Audit event con metadata segura del tipo de sesión.

## Tests

Archivos actualizados:

- `apps/api/tests/test_auth_control_center.py`.
- `apps/api/tests/test_control_center_frontend.py`.

Cobertura agregada:

- Login normal sigue funcionando.
- Login con `remember_me=true` funciona.
- Sesión recordada permite `/api/v1/auth/me`.
- Sesión recordada tiene expiración mayor que sesión normal.
- Logout revoca sesión recordada.
- Token inválido/sin sesión siguen bloqueados por pruebas existentes.
- Frontend no guarda contraseña en `localStorage`.
- Frontend no guarda contraseña en `sessionStorage`.
- UI expone `Recordar sesión en este dispositivo`.

## Capturas

Capturas locales generadas:

- `outputs/control-center-remember-session-mobile-390x844.png`.
- `outputs/control-center-remember-session-desktop-1280x720.png`.

Resultado visual:

- Mobile 390x844: PASS.
- Desktop 1280x720: PASS.
- Console errors: 0.
- Overflow horizontal: NO.
- Login visible: PASS.
- Checkbox visible: PASS.
- Copy de no guardar contraseña visible: PASS.

## Validaciones

- `node --check apps/web/control-center/assets/app.js`: PASS.
- `python -m compileall apps/api api scripts -q`: PASS.
- `$env:PYTHONPATH="apps/api"; pytest -q`: PASS, 302 passed.
- `python scripts/validate_v1.py`: PASS.
- `git diff --check`: PASS.
- Secret scan: PASS.

## Riesgos

- Una sesión recordada mantiene un token Bearer en el navegador por más tiempo. Es útil para el CEO, pero requiere dispositivo confiable.
- Si el dispositivo se comparte o se pierde, el CEO debe cerrar sesión o revocar la sesión desde el Control Center.
- No sustituye políticas futuras de identidad fuerte, MFA o proveedor SSO.

## No Tocado

- DCFT real.
- SENTINELA real.
- ARSENAL real.
- FORJA productiva externa.
- NUBE local externa.
- Local Agent.
- SUNAT real.
- APIs externas reales.
- Rutas nuevas del bus.
- Producción.

## Recomendación

Mantener este bloque local hasta revisión CEO. Si se autoriza subirlo, realizar cierre productivo separado con validación pública y autenticada.
