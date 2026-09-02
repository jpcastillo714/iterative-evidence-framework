---
name: iterative-evidence-framework
description: >
  Iterative Evidence Framework (IEF) V3 — metodología de ciclos (build y exploration)
  para proyectos de software y datos operados por agentes de IA. El ciclo lo define el
  preset, no el código; los criterios de aceptación se compilan a pytest; las compuertas
  humanas bloquean el avance de forma mecánica; los incrementos se consolidan en una
  especificación viva.
---

# Iterative Evidence Framework (IEF) V3

## La regla que gobierna todo lo demás

**Pregúntale al motor, no adivines.** El ciclo, las rutas, las compuertas y las
plantillas salen del preset activo. Antes de escribir un artefacto:

```bash
python core/scripts/verify_frame.py --mode status --json
```

Esa salida dice el paso actual, su `key`, si tiene compuerta y en qué ruta exacta va su
artefacto. **No inventes subcarpetas ni nombres de archivo.**

## Los dos ciclos

### Build — construir algo verificable

| Paso | Artefacto | Compuerta |
|---|---|---|
| 1. Charter | `charter.md` | ✋ |
| 2. Inspección Empírica | `inspection-report.md` | |
| 3. Contratos de Datos | `data-contract.yml` | |
| 4. Reglas de Negocio | `business-rules.yml` | ✋ |
| 5. Criterios de Aceptación | `acceptance-tests.yml` | ✋ |
| 6. Implementación | *(código)* | |
| 7. Verificación | `increment-report.md` | |

Todos en `initiative/increments/<SLUG>/`. Un preset puede cambiar esta tabla; por eso
se consulta, no se memoriza.

### Exploration — investigar antes de construir

`objective.md` → análisis → *(contrato opcional)* → `findings.md`. Sin compuertas.
Nada de aquí se cita en un informe sin haber pasado por un ciclo build.

## Comandos

| Comando | Qué hace |
|---|---|
| `/speckit.ief.init` | Crea la estructura del preset, `state.yml` y `initiative/specs/` |
| `/speckit.ief.charter` · `.explore` | Abre un incremento build o exploration |
| `/speckit.ief.inspect` · `.contracts` · `.rules` · `.tests` · `.implement` · `.verify` | Los pasos del ciclo build |
| `/speckit.ief.status` | Estado de todos los incrementos |
| `/speckit.ief.next` | Verifica y avanza al siguiente paso |
| `/speckit.ief.pause` · `.rewind` | Pausar; retroceder con motivo declarado |
| `/speckit.ief.evidence` | Ejecuta un test y emite su carpeta `VRN-*` con hashes |

Modos del motor sin comando propio: `check-gates` (CI), `check-preset`, `check-bundle`,
`merge-increment`.

## Reglas del agente

1. **Anti-alucinación.** Lo que falta se marca `PENDING`. Nunca se inventa un dato, una
   métrica ni un resultado. Una cifra sin ejecución detrás no es un resultado.

2. **Compuertas humanas.** Los pasos con ✋ no avanzan sin aprobación explícita del
   usuario, registrada con autor y fecha:
   ```bash
   python core/scripts/verify_frame.py --mode approve-step --by "<usuario>"
   ```
   **Nunca escribas `APPROVED` editando `state.yml`.** Eso destruye la constancia y es
   exactamente lo que la compuerta existe para impedir.

3. **`state.yml` no se edita a mano.** Es la máquina de estados; se toca con
   `verify_frame.py`, que escribe de forma atómica y deja historial.

4. **Los criterios se ejecutan.** Todo test del Paso 5 lleva un bloque `verify`
   (`kind: metric | command | python`). Uno sin él **falla**, no se aprueba por omisión.
   Uno que hoy no se puede medir se marca `status: blocked` con su razón; **no se rebaja
   para que quepa el resultado disponible.**
   ```bash
   python core/scripts/compile_acceptance_tests.py --increment <SLUG>
   pytest tests/generated -v
   ```

5. **Si la especificación está mal, se corrige la especificación.** No se parchea el
   código para que quepa dentro de una regla equivocada: usar `/speckit.ief.rewind` con
   su motivo.

6. **Un incremento no termina hasta consolidarse.**
   ```bash
   python core/scripts/verify_frame.py --mode merge-increment --increment <SLUG>
   ```
   Promueve las reglas a `initiative/specs/` con su procedencia. Sin este paso, cada
   incremento acumula su propia copia de las reglas y el proyecto pierde su fuente única
   de verdad — el fallo que originó esta versión del framework.

7. **Zero clutter.** Cada artefacto en la ruta que declara el preset. Lo temporal, en
   `scratch/`.

## Un `failed` admite tres lecturas

Hay que elegir una explícitamente; confundirlas corrompe el informe:

- **Fallo de ejecución** → arreglar el código o el entorno y volver a correr.
- **Hipótesis rechazada** → es un resultado científico. Va al informe.
- **Verificación bloqueada** → falta un prerrequisito. Se marca `blocked`; no se reporta
  como fracaso del modelo.

## Presets

`generic` · `engineering` · `academic` · `astro-mlops`

Un preset define el ciclo completo y puede renombrar pasos, mover compuertas o
reemplazar la lista entera. `astro-mlops` extiende `academic` para detección de
anomalías sobre telemetría, con sus scripts en `presets/astro-mlops/scripts/`:
`validate_data_contract.py`, `inject_faults.py`, `eval_anomaly.py`.

## Sobre la documentación heredada

`docs/legacy/` contiene informes escritos por agentes con citas de código que no
corresponden a ninguna versión real del repositorio. **No los uses como especificación.**
Para saber cómo se comporta el framework, ejecútalo.
