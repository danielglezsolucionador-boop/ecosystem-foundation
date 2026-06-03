# Monitoring Conventions

Estado: `FOUNDATION_TEMPLATE`

## 1. Objetivo

Definir convenciones de monitoreo para aplicaciones y servicios compartidos del ecosistema.

## 2. Senales Minimas

- uptime;
- health;
- readiness;
- runtime/status;
- latencia;
- error rate;
- CPU/memoria si aplica;
- DB connectivity;
- storage connectivity;
- backup status;
- provider status;
- queue depth si aplica.

## 3. Alertas Iniciales

| Condicion | Severidad |
|---|---|
| `/health` falla | CRITICAL |
| DB inaccesible | CRITICAL |
| Storage persistente falla | CRITICAL |
| Backup falla | CRITICAL |
| Provider externo falla | DEGRADED |
| Error rate elevado | DEGRADED |
| Latencia elevada | WARNING |
| Cola acumulada | WARNING |

## 4. Freshness

Todo dato mostrado en Control Center debe tener:

- fuente;
- timestamp;
- estado;
- severidad;
- owner si aplica.

## 5. Auditoria

- [x] No crea monitores reales.
- [x] No asume proveedor.
- [x] Se alinea con documentos 01 y 04.

