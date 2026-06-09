# Department Upgrade Pipeline - Modelo Local

Fecha: 2026-06-09

## Propósito

Department Upgrade Pipeline convierte brechas detectadas por AUDITORÍA en paquetes de mejora trazables.

Flujo:

AUDITORÍA detecta brecha -> CEREBRO prioriza -> FORJA recibe tarea preparada -> FORJA implementa o deja preparado según capacidad real -> AUDITORÍA revisa de nuevo -> CEREBRO reporta al CEO.

## Principio

No se inventa implementación completada. No se declara aprobación sin revisión AUDITORÍA.

Si FORJA no ejecuta realmente:

- `forge_status="prepared"`
- `technical_status="pending_execution"`

Si hay evidencia real local:

- se registra evidencia;
- queda `implemented_pending_audit`;
- AUDITORÍA debe revisar antes de aprobar.

## Datos

El pipeline guarda:

- `department_gaps`
- `upgrade_packages`
- `forge_work_orders`
- `upgrade_reviews`
- `upgrade_evidence`
- `upgrade_status_history`

Cada paquete contiene:

- department;
- source_audit_id;
- gaps;
- required_changes;
- priority;
- business_impact;
- revenue_link;
- forge_status;
- audit_status;
- ceo_visibility;
- technical_status;
- created_at;
- updated_at.

## Brechas

Una brecha puede venir de:

- auditoría departamental automatizada;
- instrucción CEO;
- revisión de CEREBRO;
- evidencia incompleta;
- bloqueo operativo.

Si no hay datos reales suficientes, el paquete debe decir `missing/unknown`.

## Priorización

CEREBRO prioriza usando:

- impacto económico;
- urgencia;
- relación con meta USD 6,000;
- relación con e-commerce USD 10,000;
- riesgo;
- bloqueo de misión;
- preparación comercial.

Prioridad:

- `p0`: riesgo crítico, bloqueo, seguridad, legal o tributario;
- `p1`: impacto comercial, revenue, e-commerce o misión activa;
- `p2`: mejora preparada o gobernada;
- `p3`: seguimiento menor.

## FORJA

FORJA recibe work orders internos preparados.

No se toca FORJA externa/productiva.

Estados:

- `not_sent`
- `prepared`
- `pending_execution`
- `implemented_with_evidence`

## AUDITORÍA

AUDITORÍA recibe revisión posterior del paquete.

Un paquete no puede pasar a `approved` si no existe revisión AUDITORÍA enlazada.

Estados:

- `not_requested`
- `pending_review`
- `in_review`
- `approved`
- `rejected`
- `observed`

## Criterios De Cierre

Para cerrar como aprobado:

- existe paquete;
- existe evidencia o paquete documental suficiente;
- existe revisión AUDITORÍA;
- AUDITORÍA aprueba;
- no hay claims falsos;
- no hay ejecución externa no autorizada;
- CEREBRO reporta al CEO.

## Departamentos Soportados

Soportados:

- PLUMA
- LENTE
- MARKETING
- MARCA PERSONAL
- BUSCADOR
- WEB FACTORY
- CREADOR APIs/SKILLS
- E-COMMERCE
- SNIFF AMAZON
- DCFT
- SENTINELA
- ARSENAL
- FORJA
- HERMES
- AUDITORÍA
- NUBE
- CEREBRO

DCFT, SENTINELA y ARSENAL quedan gobernados, no prohibidos. Pueden tener paquete de mejora, pero no runtime real ni conexión externa.

## Prohibido

- ejecutar FORJA externa real si no está conectada;
- inventar implementación completada;
- tocar cuentas externas;
- pagos;
- campañas pagadas;
- APIs con costo;
- SUNAT real;
- secretos.

## Trazabilidad

Cada transición registra historial:

- paquete creado;
- enviado a FORJA;
- evidencia registrada;
- revisión solicitada;
- aprobado;
- rechazado.

CEREBRO puede mostrar el estado al CEO en la cabina y en el Centro Diario.
