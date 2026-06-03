# Security Baseline Checklist

Estado: `FOUNDATION_TEMPLATE`

## 1. Objetivo

Definir el checklist minimo de seguridad antes de integrar o desplegar cualquier aplicacion del ecosistema.

## 2. Checklist

### Secrets

- [ ] No hay secrets en repositorio.
- [ ] No hay `.env` versionado.
- [ ] No hay API keys en frontend.
- [ ] No hay passwords hardcodeados.
- [ ] Variables secretas viven en gestor seguro o entorno.
- [ ] Existe plan de rotacion.

### Auth

- [ ] No existe admin default inseguro.
- [ ] Tokens expiran.
- [ ] Sesiones son revocables.
- [ ] Permisos se validan en backend.
- [ ] Rutas administrativas requieren rol elevado.

### Datos

- [ ] Base de datos no esta expuesta publicamente sin control.
- [ ] Conexiones cifradas si el proveedor lo soporta.
- [ ] Datos sensibles se enmascaran en logs.
- [ ] Backups cifrados si aplica.

### APIs

- [ ] CORS restrictivo.
- [ ] Rate limits definidos.
- [ ] Errores sin stack traces publicos.
- [ ] Request ID en logs.
- [ ] Rutas internas no expuestas.

### Archivos

- [ ] Storage persistente.
- [ ] Archivos privados por defecto.
- [ ] Links temporales expiran.
- [ ] Metadata y owner registrados.

## 3. Gate de Seguridad

Una app no debe pasar a staging si falla cualquiera de:

- secrets expuestos;
- auth insegura;
- permisos solo frontend;
- storage efimero para datos finales;
- logs con secrets;
- backup inexistente si persiste datos.

## 4. Auditoria

- [x] Checklist no contiene secrets.
- [x] No modifica aplicaciones.
- [x] Se alinea con documentos 01, 02 y 03.

