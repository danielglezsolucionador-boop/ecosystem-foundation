# FORJA CEREBRO Relationship Map

Fecha: 2026-06-06
Rama: `integration/forja-cerebro`
Bloque: 4 - FORJA + CEREBRO

## Resultado

FORJA y CEREBRO quedan mapeados como capacidades complementarias del ecosistema, sin conexion runtime real y sin transferencia de secretos.

## Roles

| App | Rol ecosystem | Estado |
| --- | --- | --- |
| `forja` | Construccion, ejecucion controlada, Local Agent, Human Cabin operacional | `prepared_for_discovery` |
| `cerebro` | Direccion ejecutiva, memoria operacional, conversacion CEO, governance-first | `prepared_for_discovery` |

## Relacion esperada

- CEREBRO puede actuar como cabina ejecutiva y origen de decisiones humanas.
- FORJA puede actuar como capacidad de construccion y ejecucion controlada.
- El backbone `ecosystem-foundation` registra ambos como discovery profiles, contratos y gates.
- Ninguna app llama a la otra desde este bloque.
- Ninguna app es invocada por `ecosystem-foundation` en runtime.

## Secuencia controlada futura

1. CEREBRO produce o valida una decision ejecutiva.
2. Governance del backbone registra evidencia y aprobacion.
3. FORJA podria recibir una tarea solo en una fase futura con contrato de conexion aprobado.
4. Audit y Observability registrarian la operacion antes de cualquier conexion real.

## Contratos actuales

| App | Contrato actual | Conexion real |
| --- | --- | --- |
| `forja` | `forja.discovery.v1` | `false` |
| `cerebro` | `cerebro.discovery.v1` | `false` |

No se crea `forja.integration.v1` ni `cerebro.integration.v1` en este bloque porque no hay conexion runtime segura aprobada.

## Governance

- FORJA: `protected=false` para discovery controlado.
- CEREBRO: `protected=false` para discovery controlado.
- DCFT: sigue protegido y bloqueado.
- CENTINELA: sigue registry-only.
- Las conexiones reales siguen deshabilitadas.

## Integration Bus

- Servicio `forja` presente con `status=prepared_for_discovery`.
- Servicio `cerebro` presente con `status=prepared_for_discovery`.
- Eventos de discovery preparados:
  - `platform.forja.discovery.completed`
  - `platform.cerebro.discovery.completed`
- Consumers preparados:
  - `forja-discovery-consumer`
  - `cerebro-discovery-consumer`

## Riesgos y controles

- Riesgo: confundir discovery con conexion runtime.
  Control: `external_connection_enabled=false` en registry, bus, contracts, discovery y Control Center.
- Riesgo: arrastrar gates antiguos de produccion como protected.
  Control: Governance reconcilia `protected` desde `PROTECTED_APP_IDS` y libera FORJA/CEREBRO a no protegido sin conectar runtime.
- Riesgo: tocar DCFT o CENTINELA por error.
  Control: DCFT permanece `no_touch_external`; CENTINELA permanece `registry_only`.

## Conclusion

FORJA y CEREBRO quedan relacionados en el backbone como discovery profiles controlados, listos para validacion productiva del bloque 4 y sin conexiones reales activadas.
