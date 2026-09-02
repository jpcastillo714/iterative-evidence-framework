---
name: "ief.tests"
description: "Paso 5: Tests de Aceptación (build)"
step_number: 5
---

# Paso 5: Tests de Aceptación (`/speckit.ief.tests`)

## Protocolo
1. Verificar que Paso 4 esté `APPROVED`.
2. Crear/actualizar `initiative/increments/<SLUG>/05_acceptance_tests/`.
3. Escribir tests que referencien los IDs del Paso 4 (trazabilidad).
4. **Human Gate**: Pedir aprobación al usuario.
5. Si aprueba, marcar como `APPROVED`.

## Si el preset es `astro-mlops`

- Partir de `core/steps/05_acceptance_tests/template.anomaly.yml`.
- El bloque `presupuesto_operacional` (falsas alarmas por noche, cobertura mínima, lead time,
  severidad mínima detectable) **es lo que se aprueba en el gate**. Se acuerda antes de ver
  resultados; cambiarlo después exige `/speckit.ief.rewind`.
- Si no hay historial de fallas etiquetado, construir el banco sintético en este paso:

  ```bash
  python core/scripts/inject_faults.py bench --data <episodios> --column <objetivo> \
      --out 05_datos/benchmark_sintetico --params params.yaml
  ```

- Un criterio que hoy no se puede ejecutar se marca `status: blocked` con su bloqueo y su vía
  alternativa. **No se rebaja para que quepa el resultado disponible.**
- Protocolo de referencia: `core/docs/anomaly_detection_evaluation_protocol.md`.
