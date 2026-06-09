# NUBE Internal Control Tower Model

Fecha: 2026-06-08

## Propósito

NUBE interna es la torre de control cloud del ecosistema IA dentro de `ecosystem-foundation`.

NUBE registra, visualiza y audita información cloud para que el CEO, CEREBRO y AUDITORIA puedan revisar el estado operativo sin tocar proveedores reales.

## Definición

NUBE es:

- Torre de control cloud.
- Registro interno de URLs, deploys, commits, proveedores, bases de datos, backups, variables, dominios, health checks, costos y riesgos cloud.
- Vigilante documental del estado de producción.
- Fuente de evidencia para CEREBRO y AUDITORIA.

NUBE no es:

- Proveedor cloud.
- Deployer automático.
- Editor de variables reales.
- Operador externo.
- Cliente de Vercel API.
- Conector de APIs cloud reales.
- La herramienta local `C:\Users\admin\nube`.

## Entidades

CloudProject:
Proyecto cloud registrado dentro del ecosistema. Incluye nombre, URLs, proveedor, estado, commit, tags, variables mascaradas, dominios, backups y base de datos.

CloudDeployment:
Evidencia interna de despliegue. Registrar un deployment no ejecuta deploy.

CloudProvider:
Proveedor declarado como dato interno. En este bloque Vercel está registrado como proveedor, pero sin API conectada.

CloudDatabase:
Base de datos registrada. El estado conocido es PostgreSQL persistent=true y temporal=false.

CloudVariable:
Variable requerida, configurada o desconocida. No guarda valores. El valor visible siempre debe ser `***masked***`.

CloudBackup:
Referencia documental a backups generados por bloques. No crea backup por sí sola.

CloudDomain:
Dominio o URL pública registrada.

CloudHealthCheck:
Evidencia de health check. En este bloque no ejecuta monitores externos.

CloudRisk:
Riesgo cloud que requiere revisión manual o decisión CEO.

CloudCostRecord:
Registro de costos. Si no hay costo real, `cost_status=unknown` y `requires_manual_review=true`.

## Datos Iniciales

Proyecto:
`ecosystem-foundation`

Producción:
`https://ecosystem-foundation.vercel.app`

Control Center:
`https://ecosystem-foundation.vercel.app/control-center`

Proveedor:
Vercel, registrado internamente.

Base de datos:
PostgreSQL, persistent=true, temporal=false.

Tags conocidos:

- `v1-ecosystem-company-cabin`
- `v1-cerebro-internal-bus`

Estado:

- `production_public_pass`
- `production_auth_pass_previous_closures`
- `persistent_session_status=pending_productive_closure`

Costos:
`unknown`, requiere revisión manual.

Variables:
Solo nombres y estado. No se guardan valores.

## Reglas de Seguridad

- Auth obligatoria para todos los endpoints.
- No se aceptan valores con forma de secreto.
- Las variables se devuelven con valor `***masked***`.
- No se imprime token.
- No se imprime contraseña.
- No se guarda password.
- No se llama Vercel API.
- No se modifica Vercel.
- No se modifica `C:\Users\admin\nube`.
- No se ejecuta deploy real.

## CEREBRO

CEREBRO puede consultar NUBE para:

- Estado de producción.
- URL principal.
- Control Center.
- Último commit registrado.
- Tags conocidos.
- Riesgos.
- Backups.
- Costos unknown.
- Pendientes.

CEREBRO no puede ordenar a NUBE desplegar.

## AUDITORIA

AUDITORIA puede pedir a NUBE evidencia interna sobre:

- Deploys registrados.
- Health checks registrados.
- Riesgos cloud.
- Estado de costos.
- Variables requeridas y mascaradas.

AUDITORIA no recibe secretos ni activa proveedores.

## Reglas Anti-Alucinación

- Si no hay costo real, responder `unknown`.
- Si una variable no fue confirmada, responder `unknown`.
- Si un deploy fue registrado, no decir que NUBE lo ejecutó.
- Si producción fue validada por un cierre anterior, decirlo como evidencia previa.
- Si se requiere revisión manual, mantener `requires_manual_review=true`.
- No declarar integración externa real.
- No declarar que NUBE local fue tocada.
