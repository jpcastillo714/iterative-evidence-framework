---
name: "ief.inspect"
description: "Paso 2: Inspeccion Empirica (build)"
step_number: 2
---

# Paso 2: Inspeccion Empirica (`/speckit.ief.inspect`)

Inspeccionar los datos o el sistema REAL. Nada de suposiciones: numeros, rangos, huecos, casos borde.

## Rutas

El motor resuelve la ruta del artefacto desde el preset. **No inventes subcarpetas**:
el artefacto de este paso va exactamente en

```
initiative/increments/<SLUG>/inspection-report.md
```

Consultala siempre con `python core/scripts/verify_frame.py --mode status --json`.

## Protocolo

1. Comprobar que el paso anterior este `COMPLETED` y, si tiene compuerta, `APPROVED`.
2. Escribir el artefacto en la ruta de arriba, partiendo de la plantilla que el
   preset declara para este paso.
3. Verificar antes de cerrar:
   ```bash
   python core/scripts/verify_frame.py --mode verify-step --step 2
   ```
4. Marcar el paso como `COMPLETED` en `state.yml`.
5. Avanzar:
   ```bash
   python core/scripts/verify_frame.py --mode advance
   ```
