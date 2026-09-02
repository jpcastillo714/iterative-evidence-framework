---
name: "ief.inspect"
description: "Paso 2: Inspección Empírica (build)"
step_number: 2
---

# Paso 2: Inspección Empírica (`/speckit.ief.inspect`)

## Protocolo
1. Verificar que el Paso 1 del incremento actual (`build`) esté `APPROVED`.
2. Crear/actualizar `initiative/increments/<SLUG>/02_empirical_inspection/`.
3. Analizar datos reales o sistemas existentes para descubrir edge cases.
4. Documentar en `inspection_report.md`.
5. Marcar como `COMPLETED` en `state.yml` (no requiere human gate por defecto).
