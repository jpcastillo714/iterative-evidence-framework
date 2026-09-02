---
name: "ief.status"
description: "Muestra el estado del entorno IEF V3"
step_number: null
---

# Estado (`/speckit.ief.status`)

## Protocolo
1. Leer `state.yml`.
2. Mostrar los incrementos (Activos, Pausados, Completados).
3. Para el incremento activo, mostrar el tipo (`build` o `exploration`), el paso actual, el status del paso.
4. Recordar si el paso actual requiere aprobación humana (Human Gate).
