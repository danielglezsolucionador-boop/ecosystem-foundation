# Environment Policy

Estado: `FOUNDATION_TEMPLATE`

## 1. Objetivo

Definir la politica minima de entornos para el ecosistema.

## 2. Entornos

Entornos obligatorios futuros:

1. `local`
2. `staging`
3. `production`

## 3. Reglas

- `local` no debe depender de rutas absolutas de una maquina especifica.
- `staging` debe parecerse a `production`.
- `production` no debe usar datos de prueba.
- Cada entorno debe tener secrets separados.
- Ningun secret debe vivir en repositorio.
- Toda app debe declarar variables requeridas y opcionales.
- Todo deploy debe registrar commit, fecha, version y responsable.

## 4. Gates por Entorno

### Local

- build PASS si existe stack;
- tests PASS si existen;
- health local si aplica;
- no secrets impresos.

### Staging

- variables configuradas;
- migraciones probadas si aplica;
- health live;
- runtime/status live;
- smoke test;
- rollback documentado.

### Production

- aprobacion humana;
- backups activos si hay datos;
- monitoreo activo;
- alertas activas;
- rollback validado;
- no debug publico.

## 5. Auditoria

- [x] No contiene secrets.
- [x] No asume proveedor cloud.
- [x] No crea recursos reales.

