---
name: "ief.charter"
description: "Paso 1: Charter (build)"
step_number: 1
---

# Paso 1: Charter (`/speckit.ief.charter`)

Definir objetivo, alcance, hipotesis y criterios de exito del incremento.

## Rutas

El motor resuelve la ruta del artefacto desde el preset. **No inventes subcarpetas**:
el artefacto de este paso va exactamente en

```
initiative/increments/<SLUG>/charter.md
```

Consultala siempre con `python core/scripts/verify_frame.py --mode status --json`.

## Protocolo

1. Comprobar que el paso anterior este `COMPLETED` y, si tiene compuerta, `APPROVED`.
2. Escribir el artefacto en la ruta de arriba, partiendo de la plantilla que el
   preset declara para este paso.
3. Verificar antes de cerrar:
   ```bash
   python core/scripts/verify_frame.py --mode verify-step --step 1
   ```
4. Cerrar el paso con el motor (verifica el artefacto antes de darlo por hecho):
   `python core/scripts/verify_frame.py --mode complete-step`

   **Compuerta humana.** Pedir aprobacion explicita al usuario y, solo si aprueba:
   ```bash
   python core/scripts/verify_frame.py --mode approve-step --by "<usuario>"
   ```
   El motor NO deja avanzar sin esto, y la CI lo comprueba con `--mode check-gates`.

5. Avanzar:
   ```bash
   python core/scripts/verify_frame.py --mode advance
   ```
