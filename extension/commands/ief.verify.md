---
name: "ief.verify"
description: "Paso 7: Verificación (build)"
step_number: 7
---

# Paso 7: Verificación (`/speckit.ief.verify`)

## Protocolo
1. Verificar que Paso 6 esté `COMPLETED`.
2. Ejecutar los tests definidos en el Paso 5.
3. Generar `initiative/increments/<SLUG>/07_verification/report.md`.
4. Si pasa, marcar el paso como `COMPLETED` y el incremento como `COMPLETED`.
5. Si falla o hay error de diseño, usar `/speckit.ief.rewind` para regresar a Pasos 4 o 5.

## Si el preset es `astro-mlops`

- Cada test se ejecuta con `/speckit.ief.evidence`, que emite su carpeta `VRN-*` y enlaza el
  run de MLflow. Una cifra sin VRN es `PENDING`, no un resultado.
- Las métricas se producen con `core/scripts/eval_anomaly.py`, nunca a mano: garantiza que el
  reporte traiga métrica por eventos, falsas alarmas por unidad operacional, cobertura y el
  point-adjust junto a sus deltas.
- Antes de dar por `COMPLETED`, verificar la lista del §9 de
  `core/docs/anomaly_detection_evaluation_protocol.md`.
- Un `status: failed` admite tres lecturas —fallo de ejecución, hipótesis rechazada,
  verificación bloqueada— y hay que elegir una explícitamente. Solo la segunda es un
  resultado científico; la tercera no se reporta como fracaso del modelo.
