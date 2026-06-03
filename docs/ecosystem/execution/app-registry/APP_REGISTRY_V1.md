# App Registry V1

Estado: `REGISTRY_INITIALIZED`

Fuente:

- [../../03_ECOSYSTEM_DEPLOYMENT_ORDER.md](../../03_ECOSYSTEM_DEPLOYMENT_ORDER.md)
- [../../04_ECOSYSTEM_CONTROL_CENTER.md](../../04_ECOSYSTEM_CONTROL_CENTER.md)
- [../../06_ECOSYSTEM_INTEGRATION_MAP.md](../../06_ECOSYSTEM_INTEGRATION_MAP.md)
- [../08_ECOSYSTEM_CRITICAL_PATH.md](../08_ECOSYSTEM_CRITICAL_PATH.md)

## 1. Objetivo

Crear el registro inicial de aplicaciones del ecosistema para habilitar Control Center, integraciones futuras, health checks, runtime/status, memoria, entregables, bloqueos y auditoria.

Este documento no modifica aplicaciones, no crea infraestructura real, no hace deploy y no consulta servicios productivos.

## 2. Alcance de Esta Version

Incluye:

- modelo oficial de registro por aplicacion;
- estado inicial del inventario dentro del repositorio `ecosystem-foundation`;
- reglas de entrada para registrar aplicaciones reales;
- campos obligatorios para Control Center;
- criterios de validacion antes de marcar una app como activa.

No incluye:

- cambios en FORJA;
- cambios en CEREBRO;
- validaciones live;
- creacion de recursos cloud;
- integracion real con bases de datos;
- secretos;
- URLs no verificadas desde este repositorio.

## 3. Estado Actual del Inventario

| Categoria | Cantidad | Estado |
|---|---:|---|
| Aplicaciones certificadas en este registry | 0 | Pendiente |
| Aplicaciones con manifest aprobado | 0 | Pendiente |
| Referencias externas detectadas en documentos | 2 | No registradas como activas |
| Apps con health validado desde este repo | 0 | No ejecutado |
| Apps con runtime/status validado desde este repo | 0 | No ejecutado |

Razon:

El repositorio `ecosystem-foundation` contiene documentacion base del ecosistema, pero no contiene codigo de aplicaciones ni manifests aprobados por aplicacion. Por regla, no se inventan rutas, owners, health URLs, commits ni estados productivos.

## 4. Referencias Externas Detectadas

Estas referencias aparecen en la documentacion actual como aplicaciones externas que no deben tocarse sin aprobacion.

| app_id | Nombre | Tipo | Estado en Registry | Motivo |
|---|---|---|---|---|
| `forja` | FORJA | Aplicacion externa | `REFERENCED_NOT_REGISTERED` | Requiere manifest aprobado o permiso explicito para inspeccion |
| `cerebro` | CEREBRO | Aplicacion externa | `REFERENCED_NOT_REGISTERED` | Requiere manifest aprobado o permiso explicito para inspeccion |

Estas aplicaciones no se marcan como activas porque este repositorio no contiene evidencia versionada suficiente de owner, rutas, health, runtime/status, dependencias, estado productivo y riesgos.

## 5. Registro Oficial Inicial

No hay aplicaciones certificadas todavia.

```json
{
  "registry_version": "1.0",
  "generated_from": "docs/ecosystem",
  "status": "initialized",
  "certified_apps": [],
  "referenced_external_apps": [
    {
      "app_id": "forja",
      "name": "FORJA",
      "status": "REFERENCED_NOT_REGISTERED",
      "requires": "approved_app_manifest"
    },
    {
      "app_id": "cerebro",
      "name": "CEREBRO",
      "status": "REFERENCED_NOT_REGISTERED",
      "requires": "approved_app_manifest"
    }
  ]
}
```

## 6. Modelo Obligatorio por Aplicacion

Cada aplicacion debe registrarse con:

```yaml
app_id: string
name: string
owner: string
business_purpose: string
repository:
  provider: string
  url: string
  branch: string
  commit: string
environments:
  local:
    status: planned|active|inactive|unknown
    frontend_url: string|null
    backend_url: string|null
    health_url: string|null
    runtime_status_url: string|null
  staging:
    status: planned|active|inactive|unknown
    frontend_url: string|null
    backend_url: string|null
    health_url: string|null
    runtime_status_url: string|null
  production:
    status: planned|active|inactive|unknown
    frontend_url: string|null
    backend_url: string|null
    health_url: string|null
    runtime_status_url: string|null
dependencies:
  database: string|null
  storage: string|null
  ai_provider: string|null
  queue: string|null
  external_services: []
operational_contracts:
  health: required
  runtime_status: required
  logs: required
  backups: required_if_persistent
  rollback: required
control_center:
  visibility: executive|operational|hidden
  status_source: registry|runtime|manual
  deliverables_source: api|manual|none
  memory_source: api|manual|none
risk:
  level: low|medium|high|critical
  open_risks: []
validation:
  last_checked_at: ISO-8601|null
  checked_by: string|null
  evidence: []
  classification: candidate|ready|active|degraded|blocked|retired
```

## 7. Criterios Para Registrar una App Como Activa

Una app solo puede pasar a `active` si existe evidencia versionada de:

- owner definido;
- repositorio y branch correctos;
- commit live o commit local verificable;
- entorno declarado;
- `/health` definido;
- `/runtime/status` definido;
- secrets fuera del repositorio;
- storage persistente si guarda datos;
- backup y rollback documentados si persiste datos;
- dependencias declaradas;
- riesgos abiertos documentados;
- fecha de ultima validacion;
- fuente de evidencia.

## 8. Estados Permitidos

| Estado | Uso |
|---|---|
| `candidate` | App conocida, sin evidencia completa |
| `ready` | Manifest completo, pendiente de validacion live |
| `active` | App validada y operativa |
| `degraded` | App activa con falla parcial |
| `blocked` | App no operativa o sin requisito critico |
| `retired` | App retirada |
| `referenced_not_registered` | Mencionada en documentos, no incorporada |

## 9. Relacion con Control Center

El Control Center solo debe consumir apps con:

- `classification` diferente de `referenced_not_registered`;
- timestamp de validacion;
- fuente de estado declarada;
- health/runtime disponibles o estado manual marcado como tal.

No debe mostrar datos como reales si provienen de referencias no verificadas.

## 10. Riesgos

| Riesgo | Impacto | Mitigacion |
|---|---:|---|
| Inventar apps sin evidencia | Alto | Requiere manifest aprobado |
| Mostrar estado productivo falso | Alto | Timestamp y fuente obligatorios |
| Tocar FORJA/CEREBRO sin autorizacion | Critico | Mantenerlos como referencias externas |
| Registrar URLs no verificadas | Medio | Campo `evidence` obligatorio |
| Control Center con datos incompletos | Alto | No consumir apps sin classification valida |

## 11. Auditoria Interna

- [x] Usa `docs/ecosystem/` como fuente.
- [x] No modifica FORJA.
- [x] No modifica CEREBRO.
- [x] No hace deploy.
- [x] No crea infraestructura real.
- [x] No inventa URLs productivas.
- [x] Define modelo de app.
- [x] Define estados.
- [x] Define criterios de activacion.
- [x] Es compatible con Control Center.

## 12. Siguiente Tarea

Crear el primer manifest aprobado por aplicacion usando [APP_MANIFEST_TEMPLATE.md](./APP_MANIFEST_TEMPLATE.md), empezando por la primera app que el CEO autorice registrar sin tocar su codigo.
