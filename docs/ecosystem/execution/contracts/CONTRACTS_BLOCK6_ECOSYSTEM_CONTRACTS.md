# Contracts Block 6: Ecosystem Contracts

Estado: `IMPLEMENTED_LOCAL`

## 1. Objetivo

Crear el sistema que define como se comunican las aplicaciones del Ecosistema,
sin conectar aplicaciones reales todavia.

## 2. Modulos Implementados

- Contract Registry.
- Schema Registry.
- Payload Validator.
- Version Compatibility.
- Contract History.
- Contract Audit.
- Contract Testing.
- Contract Status.
- Breaking Change Detector.
- Contract Documentation.

## 3. Endpoints

| Endpoint | Proposito |
| --- | --- |
| `GET /api/v1/contracts` | Lista contratos con filtro por app. |
| `POST /api/v1/contracts` | Registra contrato. |
| `GET /api/v1/contracts/{contract_id}` | Lee contrato. |
| `PUT /api/v1/contracts/{contract_id}` | Actualiza contrato y crea version. |
| `POST /api/v1/contracts/{contract_id}/validate` | Valida payload contra schema. |
| `GET /api/v1/contracts/{contract_id}/versions` | Lista versiones. |
| `POST /api/v1/contracts/{contract_id}/compatibility-check` | Detecta breaking changes. |
| `GET /api/v1/contracts/audit` | Auditoria de contratos. |
| `GET /api/v1/contracts/status` | Estado operacional. |

## 4. Schema Registry

Formato soportado:

```json
{
  "type": "object",
  "required": ["id"],
  "properties": {
    "id": {"type": "string"}
  }
}
```

Tipos soportados:

- `string`
- `integer`
- `number`
- `boolean`
- `object`
- `array`

## 5. Breaking Change Detector

Detecta:

- campo requerido nuevo;
- propiedad eliminada;
- cambio de tipo.

## 6. Persistencia

Tablas:

- `ecosystem_contracts`
- `ecosystem_contract_versions`
- `ecosystem_contract_audit_events`

## 7. Auditoria

Se auditan:

- creacion;
- actualizacion;
- validacion de payload;
- compatibility check.

## 8. Riesgos

- No hay contratos externos activos.
- No hay handshake con aplicaciones reales.
- La produccion debe usar PostgreSQL.
- Schemas avanzados de JSON Schema quedan para fase posterior.

## 9. Auditoria Interna

Validaciones ejecutadas:

- `python -m compileall apps/api/app -q`
- `python -m pytest apps/api/tests -q`

Resultado inicial:

- compileall: `PASS`
- pytest: `124 passed`

## 10. Checklist

- [x] Registrar contratos por aplicacion.
- [x] Validar app registrada.
- [x] Validar payload contra schema.
- [x] Detectar cambios incompatibles.
- [x] Mantener versiones.
- [x] Permitir pruebas de contrato.
- [x] Auditar acciones.
- [x] No conectar aplicaciones reales.

## 11. Recomendaciones

Siguiente bloque recomendado:

`BLOCK_7_CENTRALIZED_AUDIT`

Antes de avanzar:

1. Crear rama de backup.
2. Registrar recovery point.
3. Ejecutar pruebas completas.
