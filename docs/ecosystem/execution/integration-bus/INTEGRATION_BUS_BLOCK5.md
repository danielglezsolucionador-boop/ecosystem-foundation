# Integration Bus Block 5

Estado: `IMPLEMENTED_LOCAL`

## 1. Objetivo

Crear el sistema que permitira conectar aplicaciones mas adelante sin
acoplarlas directamente y sin tocar FORJA, CEREBRO o DCFT.

## 2. Modulos Implementados

- Integration Bus.
- Routing Engine.
- Service Discovery.
- Dependency Discovery.
- Message Routing.
- Internal Channel Registry.
- Retry Policy.
- Dead Letter Routing.
- Integration Status.
- Integration Audit.

## 3. Endpoints

| Endpoint | Proposito |
| --- | --- |
| `GET /api/v1/integration-bus` | Vista consolidada del bus. |
| `GET /api/v1/integration-bus/routes` | Lista rutas internas. |
| `POST /api/v1/integration-bus/routes` | Registra ruta interna. |
| `GET /api/v1/integration-bus/services` | Service discovery local. |
| `POST /api/v1/integration-bus/dispatch` | Simula dispatch interno. |
| `GET /api/v1/integration-bus/dependencies` | Dependency discovery. |
| `GET /api/v1/integration-bus/audit` | Auditoria del bus. |
| `GET /api/v1/integration-bus/status` | Estado operacional. |

## 4. Servicios Locales

- `app-registry`
- `control-center`
- `security`
- `memory`
- `events`
- `audit`
- `observability`
- `storage`

## 5. Persistencia

Tablas:

- `integration_bus_routes`
- `integration_bus_audit_events`

## 6. Routing

Una ruta define:

- source service;
- target service;
- event type;
- channel;
- retry policy;
- dead letter enabled;
- external connection disabled.

## 7. Dispatch

El dispatch:

- valida la ruta;
- valida el evento contra Event Catalog;
- publica un evento interno;
- registra auditoria;
- puede enrutar a dead letter.

## 8. Retry Policy

El modelo soporta `retry_policy`.

No hay worker de retry real todavia. Esta preparado para la fase de ejecucion
posterior.

## 9. Dead Letter

Dead letter routing se simula mediante Internal Events con status
`dead_letter`.

No hay cola externa conectada.

## 10. Riesgos

- No existe broker externo.
- No hay workers consumidores reales.
- La produccion debe usar PostgreSQL.
- Las apps externas siguen aisladas hasta contratos aprobados.

## 11. Auditoria Interna

Validaciones ejecutadas:

- `python -m compileall apps/api/app -q`
- `python -m pytest apps/api/tests -q`

Resultado inicial:

- compileall: `PASS`
- pytest: `112 passed`

## 12. Checklist

- [x] Registrar rutas internas.
- [x] Validar source service.
- [x] Validar target service.
- [x] Validar event type.
- [x] Simular dispatch.
- [x] Registrar auditoria.
- [x] Preparar dead letter.
- [x] Exponer dependencies.
- [x] Exponer status.
- [x] No conectar apps externas.

## 13. Recomendaciones

Siguiente bloque recomendado:

`BLOCK_6_CONTRACTS`

Antes de avanzar:

1. Crear rama de backup.
2. Registrar recovery point.
3. Ejecutar pruebas completas.
