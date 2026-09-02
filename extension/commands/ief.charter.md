---
name: "ief.charter"
description: "Paso 1: Crea el Charter (Inicio de incremento build)"
step_number: 1
---

# Paso 1: Charter (`/speckit.ief.charter`)

Inicia o continúa el Paso 1 de un incremento tipo `build`.

## Protocolo
1. Si se invoca sin incremento activo:
   a. Generar un slug para el incremento (ej. `005_migracion_api`)
   b. Crear `initiative/increments/<SLUG>/`
   c. Registrar en `state.yml` como tipo `build`, status `ACTIVE`
2. Si ya hay un incremento, operar sobre él.
3. Crear o actualizar `initiative/increments/<SLUG>/01_charter/charter.md` (o el alias del preset).
4. El Charter debe definir objetivo, alcance, métricas. Si hay un incremento `exploration` previo, usar sus hallazgos.
5. **Human Gate**: Pedir explícitamente aprobación al usuario.
6. Si el usuario aprueba, marcar paso como `APPROVED` en `state.yml` y sugerir ir al paso 2.
