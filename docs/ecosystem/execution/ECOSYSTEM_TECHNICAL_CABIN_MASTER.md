# ECOSYSTEM Technical Cabin Master V1

Estado: paquete maestro documental
Fecha: 2026-06-06

## Arquitectura real confirmada

La plataforma `ecosystem-foundation` existe como backbone real con:

- Backend real.
- PostgreSQL persistente en produccion segun validaciones previas.
- Login y sesiones.
- Control Center.
- App Registry.
- Contract Registry.
- Shared Memory DB-backed.
- Integration Bus.
- Roles/Permissions.
- Governance.
- Audit.
- Observability.
- Discovery profiles.

## Separacion de estados

| Estado | Significado |
| --- | --- |
| `real_operational` | Existe y responde como plataforma real |
| `production_pass` | Produccion externa validada por evidencia previa |
| `local_pass` | Validado localmente |
| `discovery_prepared` | Perfil/contrato/evidencia preparado, sin runtime |
| `documented_only` | Documentado, no registrado como runtime |
| `planned` | Planeado o reservado |
| `protected_no_touch` | Protegido, no tocar |
| `blocked` | Bloqueado por politica o falta de evidencia |
| `pending_review` | Requiere revision CEO/CTO |
| `pending_integration` | Falta contrato/runtime/aprobacion |

## Existente real

| Componente | Estado | Nota |
| --- | --- | --- |
| Control Center | `real_operational` | Cabina web protegida por login |
| Backend API | `real_operational` | FastAPI/serverless |
| PostgreSQL | `real_operational` | Persistente en produccion segun validacion previa |
| Login/Auth | `real_operational` | Sesiones Bearer y usuario admin |
| App Registry | `real_operational` | Lista apps y estados |
| Contracts | `real_operational` | Contratos internos/discovery |
| Shared Memory | `real_operational` | DB-backed |
| Integration Bus | `real_operational` | Servicios registrados; routes=0 |
| Governance | `real_operational` | Gates, roles, aprobaciones |
| Audit | `real_operational` | Auditoria central |
| Observability | `real_operational` | Estado/metricas internas |

## Preparado

Apps con discovery/profile preparado, sin runtime externo:

- CEREBRO
- FORJA
- HERMES
- AUDITORIA / Auditor
- PLUMA
- LENTE
- WEB FACTORY
- MARKETING
- MARCA PERSONAL
- COMERCIO AUTONOMO
- BUSCADOR DE TENDENCIAS

## Pendiente

- NUBE: documentada/herramienta local, no registrada.
- CREADOR DE APIS: documentado como capacidad futura.
- SNIFF AMAZON: documentado como app separada de Comercio Autonomo.
- SENTINELA/CENTINELA: registry-only/pending_review.

## Bloqueado / no-touch

- DCFT: `protected_no_touch`.
- SUNAT real: apagado.
- Clave SOL principal: prohibida.
- Local Agent: no abrir sin aprobacion CEO.
- Runtimes externos: deshabilitados.

## Por que Integration Bus tiene routes=0

El bus existe como registro de servicios, contratos y dependencias, pero no tiene rutas reales activas porque:

- no hay runtime externo aprobado;
- `external_connection_enabled=false`;
- ninguna app debe recibir tareas reales todavia;
- faltan contratos de ejecucion reales;
- falta aprobacion CEO/CTO para activar rutas.

Routes=0 es una medida de control, no un fallo.

## Que significa external_connection_enabled=false

Significa que la app puede aparecer en registry, contrato, cabina o discovery, pero:

- no se llama su runtime;
- no se envian tareas reales;
- no se leen datos productivos externos;
- no se activan APIs externas;
- no se importan credenciales;
- no se ejecutan acciones reales.

## Que falta para conectar runtime real

Antes de conectar cualquier runtime externo se requiere:

1. Contrato runtime real.
2. Governance Gate aprobado.
3. Auditoria tecnica y humana.
4. Observability minima.
5. Manejo de secretos con NUBE/SENTINELA.
6. Pruebas locales.
7. Validacion de produccion.
8. Aprobacion CEO/CTO.
9. Plan de rollback.

## Apps que no deben conectarse todavia

- DCFT: protegido hasta vault/deploy/piloto/aprobacion.
- SENTINELA: pendiente revision local.
- NUBE: pendiente auditoria.
- FORJA: no tareas reales sin CEO.
- CEREBRO: no runtime real desde ecosystem hasta contrato.
- HERMES/Marketing/Pluma: no comunicaciones reales sin aprobacion.
- Sniff Amazon: no scraping/APIs externas sin aprobacion.
- Comercio Autonomo: no ventas/pagos reales sin aprobacion.

## Apps solo como discovery/profile/tab

Discovery preparado no es operacion real:

- CEREBRO
- FORJA
- HERMES
- AUDITORIA
- PLUMA
- LENTE
- WEB FACTORY
- MARKETING
- MARCA PERSONAL
- COMERCIO AUTONOMO
- BUSCADOR DE TENDENCIAS

Documentadas/no registradas:

- NUBE
- CREADOR DE APIS
- SNIFF AMAZON

Registry-only:

- SENTINELA/CENTINELA

Protegida:

- DCFT

## Futuras rutas

Rutas futuras del bus, no activas:

- `cerebro.recommendation.created`
- `forja.task.requested`
- `auditoria.review.completed`
- `nube.deploy.status_changed`
- `sentinela.risk.detected`
- `dcft.pilot.status_reported`
- `hermes.notification.prepared`
- `api_creator.contract.proposed`
- `sniff_amazon.opportunity.detected`
- `commerce_autonomo.workflow.proposed`

## Cierre

La cabina tecnica debe mostrar la verdad: backbone real, discovery preparado, rutas futuras apagadas y apps protegidas sin conexion runtime.
