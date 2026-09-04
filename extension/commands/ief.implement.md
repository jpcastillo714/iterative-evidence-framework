---
name: "ief.implement"
description: "Paso 6: Implementacion (build)"
step_number: 6
---

# Paso 6: Implementacion (`/speckit.ief.implement`)

Escribir el codigo cumpliendo los contratos y las reglas aprobadas.

## Rutas

El motor resuelve la ruta del artefacto desde el preset. **No inventes subcarpetas**:
el artefacto de este paso va exactamente en

```
(este paso no produce artefacto: el codigo va en src/ y tests/)
```

Consultala siempre con `python core/scripts/verify_frame.py --mode status --json`.

## Protocolo

1. Comprobar que el paso anterior este `COMPLETED` y, si tiene compuerta, `APPROVED`.
2. Escribir el artefacto en la ruta de arriba, partiendo de la plantilla que el
   preset declara para este paso.
3. Verificar antes de cerrar:
   ```bash
   python core/scripts/verify_frame.py --mode verify-step --step 6
   ```
4. Cerrar el paso con el motor (verifica el artefacto antes de darlo por hecho):
   `python core/scripts/verify_frame.py --mode complete-step`
5. Avanzar:
   ```bash
   python core/scripts/verify_frame.py --mode advance
   ```
