---
name: "ief.explore"
description: "Inicia o continua un incremento de exploracion (ciclo ligero)"
step_number: null
---

# Exploracion (`/speckit.ief.explore`)

Ciclo ligero para investigar antes de construir. No tiene compuertas humanas: su
producto es conocimiento, no sistema.

## Pasos del ciclo

| Paso | Nombre | Artefacto |
|---|---|---|
| 1 | Objetivo | `objective.md` |
| 2 | Analisis | `analysis.md` (mas notebooks y figuras) |
| 2b | Contrato de Datos (opcional) | `data-contract.yml` |
| 3 | Hallazgos | `findings.md` |

Todos van en `initiative/increments/<SLUG>/`. Confirmar con:

```bash
python core/scripts/verify_frame.py --mode status --json
```

## Protocolo

1. Preguntar al usuario que quiere explorar y por que.
2. Generar el slug (`004_eda_correlaciones`) y crear `initiative/increments/<SLUG>/`.
3. Registrar el incremento en `state.yml` con `type: exploration` y `status: ACTIVE`.
4. Recorrer los pasos con `--mode advance`, igual que en un ciclo build.

## Para que sirve de verdad

`findings.md` alimenta el Charter de un futuro incremento `build`. La exploracion es
donde se permite equivocarse barato: si un hallazgo contradice lo que se creia, ese es
el resultado, no un fracaso.

## Regla

Nada de lo producido aqui se cita en un informe sin haber pasado por un ciclo `build`
con sus criterios de aceptacion. Un notebook exploratorio no es evidencia.
