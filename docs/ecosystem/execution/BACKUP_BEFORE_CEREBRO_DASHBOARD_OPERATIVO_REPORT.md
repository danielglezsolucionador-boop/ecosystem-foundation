# Backup Before Cerebro Dashboard Operativo

Fecha: 2026-06-16 21:37:34 -05:00 (America/Lima)
Repositorio: ecosystem-foundation
Rama: main
Commit actual confirmado al iniciar respaldo: c200846781303077c430ee73864b2d7900d1e9cc
Tag de respaldo: backup-before-cerebro-dashboard-operativo

## Estado de produccion respaldado

- La cabina abre directo sin login.
- El ecosistema completo es visible.
- FORJA / CEREBRO / CENTINELA / PLUMA / LENTE / AUDITORIA / MARKETING / TENDENCIAS estan visibles.
- El acceso discreto a BUNKER mediante "Daniel" abajo se mantiene como decision del CEO.
- No se mejora estetica en esta mision.
- No se modifica CEREBRO en esta mision; se respalda el estado operativo actual y se agrega evidencia documental.

## Pruebas disponibles

- Suite general: `python -m pytest`.
- Configuracion activa: `pytest.ini` con `testpaths = apps/api/tests` y `pythonpath = apps/api`.
- Pruebas relevantes disponibles: `apps/api/tests/test_auth_control_center.py`, `apps/api/tests/test_cerebro_sombra_inbox.py`, `apps/api/tests/test_control_center_frontend.py`.
- `pytest.ini` excluye `backup`, `outputs` y `work` de la recoleccion de pruebas.

## Control de despliegue

- `.vercelignore` mantiene excluidos `.env`, `.env.*`, `backup/`, `outputs/`, `work/` y `work_*.pdf`.
- No se suben secretos.
- Escaneo de patrones comunes de secretos en archivos candidatos: sin coincidencias.

## Limites respetados

- `apps/sombra/`: no tocado.
- `backup/`: no tocado.
- Hetzner: no tocado.
- Cabina: sin rediseño.

Nota: "BÚNKER se mantiene como acceso discreto mediante Daniel".
