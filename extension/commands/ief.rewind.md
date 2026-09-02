# /speckit.ief.rewind

Retroceso ligero — volver a un paso anterior cuando se detecta un error en las especificaciones.

## Protocolo
1. Identificar el paso actual y el paso destino
2. Marcar pasos intermedios como NEEDS_REVISION
3. Actualizar current_step al paso destino
4. Registrar en history con razón
5. Informar al usuario

## Cuándo Usar
- Implementación revela que una regla de negocio es infactible
- Datos reales no coinciden con contrato de datos
- Tests de aceptación no son verificables
