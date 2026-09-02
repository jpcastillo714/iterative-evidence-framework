# /speckit.ief.pause

Pausa el incremento activo actual.

## Protocolo
1. Leer state.yml → identificar incremento activo
2. Preguntar al usuario la razón de la pausa
3. Actualizar state.yml: status → PAUSED, paused_at_step, paused_reason
4. Actualizar el README.md del incremento
5. Informar al usuario: "Incremento <SLUG> pausado en Paso X. Razón: ..."
6. Si el usuario quiere trabajar en otro incremento, sugerir crear uno nuevo o reactivar uno pausado
