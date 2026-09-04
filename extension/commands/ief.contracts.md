---
name: "ief.contracts"
description: "Paso 3: Contratos de Datos (build)"
step_number: 3
---

# Paso 3: Contratos de Datos (`/speckit.ief.contracts`)

Formalizar entradas y salidas como contrato ejecutable.

## Rutas

El motor resuelve la ruta del artefacto desde el preset. **No inventes subcarpetas**:
el artefacto de este paso va exactamente en

```
initiative/increments/<SLUG>/data-contract.yml
```

Consultala siempre con `python core/scripts/verify_frame.py --mode status --json`.

## Protocolo

1. Comprobar que el paso anterior este `COMPLETED` y, si tiene compuerta, `APPROVED`.
2. Escribir el artefacto en la ruta de arriba, partiendo de la plantilla que el
   preset declara para este paso.
3. Verificar antes de cerrar:
   ```bash
   python core/scripts/verify_frame.py --mode verify-step --step 3
   ```
4. Cerrar el paso con el motor (verifica el artefacto antes de darlo por hecho):
   `python core/scripts/verify_frame.py --mode complete-step`
5. Avanzar:
   ```bash
   python core/scripts/verify_frame.py --mode advance
   ```
