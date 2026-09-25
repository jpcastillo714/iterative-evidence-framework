# AGENTS.md: Reglas y Contexto del Proyecto (IEF)

## 1. Proyecto
* **Nombre:** {{INITIATIVE_NAME}}
* **ID:** {{INITIATIVE_ID}}
* **Preset:** {{PRESET_NAME}}

`$IEF` es la carpeta `core/scripts/` del bundle del IEF. Todos los comandos se ejecutan
desde la raíz de este proyecto.

## 2. La regla que gobierna todo lo demás: pregúntale al motor

```bash
python "$IEF/verify_frame.py" --mode status --json
```

Esa salida dice el foco, el paso en que está cada incremento, su `key` y si lleva
compuerta humana. **El ciclo cambia entre proyectos** (los presets renombran pasos,
mueven compuertas y añaden pasos), así que no supongas nada de eso.

Los artefactos de un incremento viven en su directorio, `initiative/increments/<slug>/`
(`new-increment` lo imprime al abrirlo), con el nombre que el preset declara para el
paso. `--mode verify-step` dice qué archivo busca: si falla con «no existe», el
artefacto está en otro sitio o con otro nombre. No inventes subcarpetas.

## 3. Reglas centrales

* **Anti-alucinación.** No inventes datos, variables, reglas ni esquemas. Lo que falta se
  marca `PENDING` y se pregunta. Una cifra sin una ejecución detrás no es un resultado.
* **Sin archivos sueltos.** Todo va a la carpeta de su rol; la ruta la da el motor.
* **`state.yml` no se edita a mano, nunca.** Es la máquina de estados: `verify_frame.py`
  escribe de forma atómica y deja historial. Todo cambio tiene su modo:

  | Quiero... | Modo |
  |---|---|
  | Dar un paso por terminado (re-verifica el artefacto) | `--mode complete-step` |
  | Registrar la aprobación de una compuerta | `--mode approve-step --by "<usuario>"` |
  | Pasar al siguiente paso | `--mode advance` |
  | Volver atrás porque la especificación estaba mal | `--mode rewind --to-step <ref> --reason "..."` |
  | Pausar, bloquear, completar o abandonar un incremento | `--mode set-status --increment <slug> --status <X>` |
  | Cambiar el incremento sobre el que operan los comandos | `--mode focus --increment <slug>` |

  Si crees que necesitas editarlo a mano, falta un modo: repórtalo en vez de abrir el archivo.

## 4. Protocolo de un paso

1. `--mode status --json` para saber el foco y el paso actual.
2. Leer **solo** las instrucciones de ese paso.
3. Producir el artefacto en el directorio del incremento (ver §2).
4. `--mode verify-step` y después `--mode complete-step`.
5. Si el paso lleva compuerta: presentar el artefacto al usuario y **esperar su
   aprobación explícita**. Solo entonces `--mode approve-step --by "<usuario>"`.
6. `--mode advance`.

Si hay varios frentes abiertos, `advance`, `approve-step` y `rewind` caen sobre el
**enfocado**: compruébalo antes, o pasa `--increment`.

## 5. Compuertas humanas

Las compuertas son del usuario, no tuyas. **Pedirte que hagas algo no es aprobar**:
«hazlo» o «dale» son encargos de trabajo; una aprobación es posterior al artefacto y se
refiere a él. Nunca apruebes en nombre del usuario.

Una compuerta detiene el *avance*, no el *trabajo*: redacta lo que se pidió y preséntalo
listo para que diga «sí» o «cambia esto».

Qué pasos llevan compuerta lo decide el preset: consúltalo en `status --json`
(`human_gate`), no lo supongas.

## 6. Ciclos

El rigor se elige **por incremento**, no por proyecto. En el ciclo base:

| Ciclo | Cuándo | Pasos | Compuertas |
|---|---|---|---|
| `task` | Código pequeño; nadie hereda decisiones nuevas | 2 | ninguna |
| `exploration` | Entender algo antes de decidir qué construir | 4 (`1`, `2`, `2b`, `3`) | ninguna |
| `prototype` | Hay una hipótesis que puede fallar | 4 | `1` |
| `build` | Otros dependerán de esto | 7 | `1`, `4`, `5` |

Los presets modifican esta tabla. Por ejemplo, el mixin `modeling` inserta en `build` el
paso `6b` (Evaluación del Modelo) **con compuerta**. Por eso la fuente de verdad es
`status --json`.

Si el trabajo ni siquiera merece un incremento (un gráfico, un arreglo de diez minutos),
anótalo con `--mode log --message "..."`.

Un `task` **no promueve reglas**: no pasó por compuerta. Si aparece una decisión que
otros van a heredar, cierra el `task` y abre un `prototype` o un `build`.

## 7. Estados

* **Incremento:** `ACTIVE`, `PAUSED`, `BLOCKED`, `COMPLETED`, `MERGED`, `ABANDONED`.
* **Paso:** `PENDING`, `IN_PROGRESS`, `COMPLETED`, `APPROVED`, `NEEDS_REVISION`.

## 8. Cuando la especificación está mal

Si la implementación revela que una regla es inviable, no parchees el código para que
quepa: `--mode rewind --to-step <ref> --reason "..."`. El retroceso marca
`NEEDS_REVISION` en el paso destino **y en todos los posteriores** que tenían trabajo.

Un criterio que no se puede medir hoy se marca `blocked`; no se rebaja el umbral.

## 9. Cerrar un incremento

```bash
python "$IEF/verify_frame.py" --mode check-gates
python "$IEF/verify_frame.py" --mode merge-increment --increment <slug> --dry-run
python "$IEF/verify_frame.py" --mode merge-increment --increment <slug>
```

`merge-increment` promueve reglas, contrato y criterios a la especificación viva del
proyecto. Si el ciclo no tenía compuerta sobre las reglas, exige `--by "<nombre>"`: esa
firma es de una persona, no tuya.

## 10. Al llegar a este proyecto

```bash
python "$IEF/verify_frame.py" --mode status
python "$IEF/verify_frame.py" --mode doctor
```

`doctor` revela lo que `status` no muestra: estado ilegible, bloqueos vencidos,
compuertas terminadas sin aprobar, entradas externas que invalidan reglas vigentes.
Si reporta `FAIL`, arréglalo antes de avanzar ningún paso.

## 11. Reglas específicas del preset
{{PRESET_FRAGMENT}}
