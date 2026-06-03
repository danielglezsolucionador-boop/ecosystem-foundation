# Environment Variables Template

Estado: `FOUNDATION_TEMPLATE`

## 1. Objetivo

Definir una plantilla segura para declarar variables de entorno por aplicacion sin incluir valores reales.

## 2. Formato Recomendado

```yaml
application:
  name: app-name
  owner: owner-name
  environment: local|staging|production

variables:
  required:
    - name: APP_ENV
      purpose: Runtime environment
      secret: false
      example: staging
    - name: APP_PUBLIC_URL
      purpose: Public application URL
      secret: false
      example: https://example.invalid
    - name: DATABASE_URL
      purpose: Database connection string
      secret: true
      example: DO_NOT_COMMIT_REAL_VALUE
    - name: STORAGE_BACKEND
      purpose: Storage backend selector
      secret: false
      example: object_storage
  optional:
    - name: LOG_LEVEL
      purpose: Logging verbosity
      secret: false
      example: info
```

## 3. Reglas

- No incluir valores reales de secrets.
- No commitear `.env`.
- No imprimir variables secretas en logs.
- Separar variables por entorno.
- Documentar aliases aceptados si existen.
- Toda variable critica debe tener owner.

## 4. Clasificacion

| Tipo | Ejemplo | Puede ir en repo |
|---|---|---:|
| Public config | `APP_PUBLIC_URL` | SI |
| Runtime config | `APP_ENV` | SI |
| Secret | `DATABASE_URL` | NO |
| Token | `API_KEY` | NO |
| Password | `ADMIN_PASSWORD` | NO |

## 5. Auditoria

- [x] No contiene valores reales.
- [x] No asume proveedor definitivo.
- [x] Compatible con local, staging y production.

