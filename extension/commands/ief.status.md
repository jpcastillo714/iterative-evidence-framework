---
name: "ief.status"
description: "Muestra el estado de los incrementos IEF"
step_number: null
---

# Estado (`/speckit.ief.status`)

```bash
python core/scripts/verify_frame.py --mode status
```

Para leerlo de forma programatica (rutas, compuertas, paso actual):

```bash
python core/scripts/verify_frame.py --mode status --json
```

## Que informar al usuario

1. El incremento activo, su tipo (`build` o `exploration`) y su paso actual.
2. Si ese paso tiene **compuerta humana** y esta pendiente de aprobacion.
3. Los incrementos pausados o bloqueados, con su razon.
4. Si algun incremento esta `COMPLETED` pero no `MERGED`: sus reglas todavia no estan
   en `initiative/specs/` y el proyecto no tiene una fuente unica de verdad.

## No confundir

`--mode status` describe; **no verifica**. Para saber si algo esta bien:

```bash
python core/scripts/verify_frame.py --mode verify-step   # el paso actual
python core/scripts/verify_frame.py --mode check-gates   # todas las compuertas
```
