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
4. Marcar el paso como `COMPLETED` en `state.yml`.
5. Avanzar:
   ```bash
   python core/scripts/verify_frame.py --mode advance
   ```

## Si el preset es `astro-mlops`

La plantilla la resuelve el preset (`presets/astro-mlops/templates/data-contract.telemetry.yml`):
cada canal declara su `clase` (`medicion` · `consigna` · `comando` · `ambiente` ·
`derivada` · `descartada`), unidad, rango valido y centinelas.

**El contrato no se da por COMPLETED sin ejecutarlo** contra los datos reales:

```bash
python presets/astro-mlops/scripts/validate_data_contract.py     --contract initiative/increments/<SLUG>/data-contract.yml     --data <parquet> --report 06_resultados/experimentos/contrato_report.json
```

Declarar `dominio_de_validez`: es lo que despues permite al detector abstenerse en vez
de alarmar donde el modelo base no vale.
