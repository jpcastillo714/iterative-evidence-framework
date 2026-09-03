---
name: "ief.rules"
description: "Paso 4: Reglas de Negocio (build)"
step_number: 4
---

# Paso 4: Reglas de Negocio (`/speckit.ief.rules`)

Extraer la logica de dominio a reglas con ID (`BR-001`), prioridad y estado.

## Rutas

El motor resuelve la ruta del artefacto desde el preset. **No inventes subcarpetas**:
el artefacto de este paso va exactamente en

```
initiative/increments/<SLUG>/business-rules.yml
```

Consultala siempre con `python core/scripts/verify_frame.py --mode status --json`.

## Protocolo

1. Comprobar que el paso anterior este `COMPLETED` y, si tiene compuerta, `APPROVED`.
2. Escribir el artefacto en la ruta de arriba, partiendo de la plantilla que el
   preset declara para este paso.
3. Verificar antes de cerrar:
   ```bash
   python core/scripts/verify_frame.py --mode verify-step --step 4
   ```
4. Marcar el paso como `COMPLETED` en `state.yml`.

   **Compuerta humana.** Pedir aprobacion explicita al usuario y, solo si aprueba:
   ```bash
   python core/scripts/verify_frame.py --mode approve-step --by "<usuario>"
   ```
   El motor NO deja avanzar sin esto, y la CI lo comprueba con `--mode check-gates`.

5. Avanzar:
   ```bash
   python core/scripts/verify_frame.py --mode advance
   ```
