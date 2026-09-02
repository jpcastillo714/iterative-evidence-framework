---
name: "ief.contracts"
description: "Paso 3: Contratos de Datos (build)"
step_number: 3
---

# Paso 3: Contratos de Datos (`/speckit.ief.contracts`)

## Protocolo
1. Verificar que Paso 2 esté `COMPLETED` o superior.
2. Crear/actualizar `initiative/increments/<SLUG>/03_data_contracts/`.
3. Definir esquemas YAML (`data-contract.yml`) de entradas/salidas.
4. Marcar como `COMPLETED` en `state.yml`.

## Si el preset es `astro-mlops`

- Usar `core/steps/03_data_contracts/template.telemetry.yml`: cada canal declara `clase`
  (`medicion` · `consigna` · `comando` · `ambiente` · `derivada` · `descartada`), unidad,
  rango válido y centinelas.
- **El contrato no se da por COMPLETED sin ejecutarlo** contra los datos reales:

  ```bash
  python core/scripts/validate_data_contract.py \
      --contract initiative/increments/<SLUG>/data-contract.yml \
      --data <parquet> --report 06_resultados/experimentos/contrato_report.json
  ```

- Declarar `dominio_de_validez`: es lo que después permitirá al detector abstenerse en vez
  de alarmar donde el modelo base no vale.
