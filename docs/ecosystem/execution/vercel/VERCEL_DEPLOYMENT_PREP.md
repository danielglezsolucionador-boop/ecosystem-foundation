# Ecosystem Foundation Vercel Deployment Prep

Estado: preparado, no desplegado desde esta fase.

## Proyecto

- GitHub: `https://github.com/danielglezsolucionador-boop/ecosystem-foundation`
- Vercel: `https://vercel.com/danielglezsolucionador-boops-projects/ecosystem-foundation`

## Entry Point

Vercel usa:

```text
api/index.py
```

Ese archivo expone la app FastAPI desde:

```text
apps/api/app/main.py
```

## Configuracion Versionada

```text
requirements.txt
vercel.json
api/index.py
apps/api/config/environment.example
```

## Variables Requeridas En Vercel

Obligatorias para staging/cloud:

```text
DATABASE_URL=<postgres connection string>
ECOSYSTEM_API_ENVIRONMENT=staging
ECOSYSTEM_API_SERVICE_NAME=ecosystem-foundation-api
ECOSYSTEM_API_VERSION=0.1.0
ECOSYSTEM_API_COMMIT=<git commit sha>
ECOSYSTEM_API_DEBUG=false
```

Opcional:

```text
ECOSYSTEM_API_CORS_ORIGINS=https://<frontend-domain>
```

## Base De Datos

Local:

```text
ECOSYSTEM_API_DATABASE_URL=sqlite:///./var/ecosystem_foundation.db
```

Cloud:

```text
DATABASE_URL=postgresql://...
```

El runtime detecta:

- `sqlite:///` para local.
- `postgresql://` o `postgres://` para Vercel/Postgres.

## Validacion Antes De Deploy

Desde la raiz del repo:

```powershell
python scripts/validate_v1.py
```

Debe pasar:

- `compileall`
- `pytest`
- import serverless `api.index`
- secret scan local

## Rollback

Antes de despliegue real:

1. Confirmar tag estable `v1-local-foundation`.
2. Confirmar ultimo commit verde.
3. Configurar `DATABASE_URL` en Vercel.
4. Usar redeploy de Vercel apuntando al commit estable.
5. Si falla readiness, volver al deployment anterior desde Vercel Dashboard.

## Restricciones

- No tocar FORJA.
- No tocar CEREBRO.
- No conectar apps externas todavia.
- No subir secrets.
- No crear infraestructura real desde el repo.
