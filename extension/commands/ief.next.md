---
name: "ief.next"
description: "Avanza al siguiente paso del incremento activo"
step_number: null
---

# Siguiente Paso (`/speckit.ief.next`)

## Protocolo
1. Leer `state.yml` para el incremento `ACTIVE`.
2. Identificar el paso actual. Si tiene un Human Gate y no está `APPROVED`, informar al usuario.
3. Si está listo para avanzar, cambiar el estado del siguiente paso a `IN_PROGRESS` e iniciarlo.
