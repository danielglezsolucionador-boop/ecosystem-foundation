# ARSENAL Governed Blueprint

Fecha: 2026-06-09

## Proposito

ARSENAL es el almacen estrategico de capacidades del ecosistema IA.

No es solo biblioteca. Es infraestructura estrategica para registrar, clasificar, evaluar, auditar y preparar capacidades antes de construir o vender.

Estado de este bloque:

- blueprint gobernado;
- metadata only;
- no runtime real;
- no conexion externa;
- no secretos guardados;
- no proveedores con costo activos;
- no APIs externas reales;
- no pagos reales;
- no SUNAT real.

## Modelo

ARSENAL contiene catalogos preparados de:

- APIs internas;
- APIs vendibles;
- skills internas;
- skills vendibles;
- modelos IA;
- conectores;
- prompts/sistemas;
- automatizaciones;
- productos tecnicos vendibles;
- herramientas operativas por departamento.

Cada item del catalogo debe tener:

- nombre;
- tipo;
- categoria;
- uso interno;
- uso vendible;
- costo;
- requiere secreto;
- requiere API externa;
- estado;
- riesgo;
- monetizacion;
- owner;
- audit_status;
- technical_status;
- created_at.

Regla maxima:

- ARSENAL guarda metadata, nunca secretos.
- Si una capacidad requiere clave, token, password o credential, se marca como `requires_secret=true`, pero el valor no se guarda.

## Categorias iniciales

- APIs internas: empty/prepared si no hay items.
- APIs vendibles: empty/prepared si no hay items.
- Skills internas: empty/prepared si no hay items.
- Skills vendibles: empty/prepared si no hay items.
- Modelos IA: empty/prepared si no hay items.
- Conectores: empty/prepared si no hay items.
- Automatizaciones: empty/prepared si no hay items.
- Prompts/sistemas: empty/prepared si no hay items.
- Herramientas de contenido: empty/prepared si no hay items.
- Herramientas de marketing: empty/prepared si no hay items.
- Herramientas de ecommerce: empty/prepared si no hay items.
- Herramientas de ciberseguridad: empty/prepared si no hay items.
- Herramientas contables/tributarias: empty/prepared si no hay items.
- Herramientas cloud: empty/prepared si no hay items.
- Herramientas de investigacion: empty/prepared si no hay items.
- Experimentos: empty/prepared si no hay items.

No se inventan recursos reales para llenar categorias vacias.

## Permisos

Ver:

- CEO;
- admin;
- operator;
- auditor.

Agregar item:

- CEO;
- admin;
- operator.

Evaluar:

- CEO;
- admin;
- operator;
- auditor.

Aprobar costo o credenciales:

- CEO;
- admin.

Mandar a FORJA:

- CEO;
- admin;
- operator.

Marcar como vendible:

- CEO;
- admin;
- operator, con AUDITORIA requerida.

## Seguridad

Reglas obligatorias:

- Si requiere costo: aprobacion CEO.
- Si requiere credenciales: aprobacion CEO.
- Si es interno sin costo: CEREBRO puede mover como tarea preparada.
- Si es vendible: AUDITORIA debe revisar.
- Si toca DCFT o SENTINELA: flujo gobernado, sin runtime real.
- Si toca NUBE: revisar costo/cloud antes de construir.
- Si requiere API externa: registrar solo metadata y riesgo; no conectar.

Payloads prohibidos:

- api_key;
- secret;
- token;
- password;
- credential;
- private_key;
- valores tipo sk-*.

## Relacion con CEREBRO

CEREBRO puede:

- consultar catalogo;
- crear item preparado;
- pedir evaluacion;
- enviar tarea preparada a FORJA;
- pedir AUDITORIA;
- pedir evaluacion Revenue OS.

CEREBRO no puede:

- conectar API externa;
- guardar secreto;
- activar proveedor con costo;
- declarar capacidad viva si es blueprint;
- tocar DCFT/SENTINELA reales.

## Relacion con CREADOR APIs/SKILLS

CREADOR APIs/SKILLS aporta:

- candidatos tecnicos;
- APIs vendibles;
- skills vendibles;
- capacidades internas reutilizables;
- especificaciones que FORJA podria construir.

## Relacion con FORJA

FORJA recibe:

- tarea preparada;
- alcance;
- owner;
- riesgo;
- estado de aprobacion.

FORJA no recibe:

- secreto;
- token;
- conexion externa;
- autorizacion implicita para tocar runtime externo.

## Relacion con AUDITORIA

AUDITORIA revisa:

- seguridad;
- calidad;
- costo;
- vendibilidad;
- riesgo comercial;
- riesgo tecnico;
- evidencia.

Todo item vendible requiere AUDITORIA antes de venta real.

## Relacion con NUBE

NUBE registra:

- costos cloud potenciales;
- riesgos de despliegue;
- requisitos de variables;
- readiness de infraestructura.

NUBE no despliega por este bloque.

## Relacion con Revenue OS

Revenue OS evalua:

- monetizacion;
- ingreso esperado;
- utilidad neta;
- probabilidad;
- ROI;
- contribucion a meta USD 6,000;
- separacion e-commerce si aplica.

Revenue OS no declara ingresos reales si no hay evidencia.

## Criterios de monetizacion

Un item puede considerarse vendible si:

- tiene uso claro;
- tiene cliente o mercado probable;
- no depende de secreto sin aprobacion;
- tiene costo conocido;
- tiene riesgo controlado;
- AUDITORIA puede revisarlo;
- Revenue OS puede estimar utilidad sin inventar.

## Criterios de costo

Un item debe escalar a CEO si:

- cost_usd > 0;
- requiere proveedor con costo;
- requiere cuenta externa con costo;
- requiere credenciales;
- requiere API externa pagada;
- requiere inventario, contratacion o pago real.

## Readiness para construccion

ARSENAL queda listo para construccion cuando:

- existe catalogo minimo;
- categorias clave tienen items;
- items vendibles estan auditados;
- costos y secretos estan aprobados por CEO;
- riesgos altos estan cerrados;
- Revenue OS separa monetizacion estimada de ingresos reales;
- FORJA recibe solo tareas preparadas.
