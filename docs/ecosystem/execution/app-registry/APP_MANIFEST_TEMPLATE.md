# App Manifest Template

Estado: `TEMPLATE_DEFINED`

Fuente:

- [APP_REGISTRY_V1.md](./APP_REGISTRY_V1.md)
- [../operations/HEALTHCHECK_CONTRACT.md](../operations/HEALTHCHECK_CONTRACT.md)
- [../config/ENVIRONMENT_VARIABLES_TEMPLATE.md](../config/ENVIRONMENT_VARIABLES_TEMPLATE.md)
- [../security/SECURITY_BASELINE_CHECKLIST.md](../security/SECURITY_BASELINE_CHECKLIST.md)

## 1. Objetivo

Definir la plantilla obligatoria para registrar cualquier aplicacion dentro del App Registry del ecosistema.

No incluir secrets reales en este archivo ni en manifests derivados.

## 2. Manifest

```yaml
manifest_version: "1.0"

app:
  app_id: ""
  name: ""
  owner: ""
  business_purpose: ""
  criticality: "low|medium|high|critical"

repository:
  provider: ""
  url: ""
  branch: ""
  commit: ""
  evidence:
    - ""

environments:
  local:
    status: "planned|active|inactive|unknown"
    frontend_url: null
    backend_url: null
    health_url: null
    runtime_status_url: null
  staging:
    status: "planned|active|inactive|unknown"
    frontend_url: null
    backend_url: null
    health_url: null
    runtime_status_url: null
  production:
    status: "planned|active|inactive|unknown"
    frontend_url: null
    backend_url: null
    health_url: null
    runtime_status_url: null

runtime:
  health_contract: "required"
  runtime_status_contract: "required"
  startup_command: ""
  build_command: ""
  test_command: ""
  smoke_test_command: ""

data:
  database: null
  storage: null
  memory: null
  file_storage: null
  persistent_data: false
  backup_required: false
  restore_required: false

providers:
  ai_provider: null
  email_provider: null
  payment_provider: null
  external_services: []

security:
  auth_required: false
  roles_required: []
  secrets_required: []
  secrets_in_repo: false
  public_env_vars: []
  sensitive_scopes: []

integration:
  internal_api_contracts: []
  event_contracts: []
  deliverables_source: "api|manual|none"
  memory_source: "api|manual|none"
  control_center_visibility: "executive|operational|hidden"

operations:
  logs: "required"
  monitoring: "required"
  backup: "required_if_persistent"
  rollback: "required"
  runbook: ""

risks:
  level: "low|medium|high|critical"
  open_risks: []
  blockers: []

validation:
  classification: "candidate|ready|active|degraded|blocked|retired"
  last_checked_at: null
  checked_by: ""
  evidence: []
```

## 3. Reglas

- `app_id` debe ser estable, corto y en minusculas.
- `owner` no puede quedar vacio para pasar a `ready`.
- `health_url` y `runtime_status_url` son obligatorios para `active`.
- `secrets_in_repo` debe ser `false`.
- `backup_required` debe ser `true` si `persistent_data` es `true`.
- `evidence` debe incluir archivos, comandos o validaciones verificables.
- No se permiten contrasenas, tokens, API keys ni valores de secrets.

## 4. Checklist de Aprobacion

- [ ] Manifest completo.
- [ ] Owner definido.
- [ ] Repositorio identificado.
- [ ] Entornos declarados.
- [ ] Health declarado.
- [ ] Runtime/status declarado.
- [ ] Persistencia declarada.
- [ ] Backups definidos si aplica.
- [ ] Rollback documentado.
- [ ] Secrets fuera del repo.
- [ ] Riesgos documentados.
- [ ] Evidencia versionada.

## 5. Siguiente Uso

Copiar esta estructura a un manifest especifico por aplicacion dentro de `docs/ecosystem/execution/app-registry/apps/` cuando exista autorizacion para registrar esa app.
