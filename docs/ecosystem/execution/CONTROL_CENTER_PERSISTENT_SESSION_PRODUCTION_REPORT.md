# Control Center Persistent Session Production Report

Fecha local: 2026-06-08

## Estado

Mejora `Recordar sesion en este dispositivo` preparada para cierre productivo del Control Center.

## Implementado

- Checkbox visible en el login: `Recordar sesion en este dispositivo`.
- Payload de login agrega `remember_me`.
- Restauracion automatica al abrir `/control-center` mediante `/api/v1/auth/me`.
- Estado visual de sesion restaurada o sesion invalida.
- Logout limpia almacenamiento persistente y de pestana.
- Backend registra metadata de auditoria del login persistente.

## Funcionamiento

Sesion recordada:

- `remember_me=true`.
- Token Bearer guardado en `localStorage`.
- Duracion backend: 30 dias.
- Al volver al Control Center, el frontend valida el token con `/api/v1/auth/me`.

Sesion normal:

- `remember_me=false`.
- Token Bearer guardado en `sessionStorage`.
- Duracion backend: 12 horas.
- Al cerrar pestana/navegador, la sesion no queda persistida como recordada.

## Seguridad

- No se guarda contrasena en `localStorage`.
- No se guarda contrasena en `sessionStorage`.
- No se hardcodea usuario ni contrasena en frontend.
- No se imprimen credenciales.
- No se imprime token Bearer.
- Token invalido fuerza login.
- Sin sesion mantiene 401 en endpoints protegidos.
- Logout borra `localStorage` y `sessionStorage` para la clave de sesion.

## Validaciones locales pre-push

- `node --check apps/web/control-center/assets/app.js`: PASS.
- `python -m compileall apps/api api scripts -q`: PASS.
- `PYTHONPATH=apps/api pytest -q`: PASS, 302 tests.
- `python scripts/validate_v1.py`: PASS, incluye 302 tests y secret scan.
- `git diff --check`: PASS.
- Secret scan del diff: PASS.
- Chequeo frontend:
  - `remember_me=true`: PASS.
  - `localStorage` solo guarda token: PASS.
  - `sessionStorage` solo guarda token: PASS.
  - no password en storage: PASS.
  - logout limpia ambos storages: PASS.

## Capturas locales base

- `outputs/control-center-remember-session-mobile-390x844.png`.
- `outputs/control-center-remember-session-desktop-1280x720.png`.

## Riesgos

- `localStorage` mantiene sesion por mas tiempo; debe usarse solo en dispositivo confiable.
- Si el navegador esta comprometido, cualquier token persistente aumenta exposicion.
- La restauracion siempre depende de `/api/v1/auth/me`; si backend rechaza el token, se muestra login.

## Recomendacion de uso

Usar `Recordar sesion en este dispositivo` solo en equipo propio y confiable. En equipo compartido, dejar desmarcado y cerrar sesion al terminar.

## No tocado

- DCFT real.
- SENTINELA real.
- ARSENAL real.
- FORJA productiva externa.
- NUBE local externa.
- Local Agent.
- SUNAT real.
- APIs externas reales.
- Rutas nuevas del bus.
- Backups en Git.
