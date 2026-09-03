# Iterative Evidence Framework (IEF)

> Extensión de [spec-kit](https://github.com/github/spec-kit): mismo espíritu de
> desarrollo guiado por especificaciones, con ciclos incrementales, presets configurables
> y criterios de aceptación que se ejecutan.

> [!IMPORTANT]
> **Este directorio es el framework, no un proyecto.** Nunca se crea un `initiative/`
> aquí dentro ni se trabaja sobre esta carpeta: el IEF se aplica a *otros* repositorios.
> Ver [`AGENTS.md`](AGENTS.md).

---

## Qué añade sobre spec-kit

| | |
|---|---|
| **El ciclo lo define el preset** | Qué pasos existen, en qué orden, cuáles requieren aprobación humana y dónde vive cada artefacto sale de `presets/<id>/preset.yml`. Un preset quita pasos, agrega pasos o mueve una compuerta **sin tocar código**. |
| **Criterios ejecutables** | `acceptance-tests.yml` se compila a pytest. Un criterio sin forma de verificarse **falla**; no se aprueba por omisión. |
| **Compuertas mecánicas** | `check-gates` sale con código 1 si un paso con compuerta quedó terminado sin aprobación. Es una condición de merge, no un recordatorio. |
| **Especificación viva** | `merge-increment` promueve las reglas del incremento a `initiative/specs/`, con la procedencia de cada una. Sin esto, cada incremento acumula su copia y nadie sabe cuál rige. |
| **Multi-incremento** | Varios frentes coexisten: `ACTIVE`, `PAUSED`, `BLOCKED`, `COMPLETED`, `MERGED`, `ABANDONED`. |
| **Retroceso con motivo** | `rewind` marca pasos como `NEEDS_REVISION`, revoca sus aprobaciones y registra por qué. |

---

## Instalación

```bash
pip install -r requirements-dev.txt
python core/scripts/verify_frame.py --mode check-bundle
pytest tests/ -q
```

El núcleo solo necesita `PyYAML`. `requirements.txt` es el mínimo; el `-dev` añade pytest.

---

## Uso

Siempre desde el directorio del **proyecto**, no desde aquí:

```bash
IEF=/ruta/al/spec-kit_bundle/core/scripts
cd /ruta/de/mi/proyecto

# 1. Inicializar: crea los directorios del preset, state.yml y initiative/specs/
python $IEF/verify_frame.py --mode init --preset data-science --initiative-name "Mi proyecto"

# 2. Ver el estado (--json para consumo programático)
python $IEF/verify_frame.py --mode status

# 3. Trabajar el paso, verificarlo y avanzar
python $IEF/verify_frame.py --mode verify-step
python $IEF/verify_frame.py --mode approve-step --by "yo"     # si hay compuerta
python $IEF/verify_frame.py --mode advance

# 4. Compilar y ejecutar los criterios de aceptación
python $IEF/compile_acceptance_tests.py --increment 001_mi_incremento
pytest tests/generated -v

# 5. Cerrar y consolidar
python $IEF/verify_frame.py --mode check-gates
python $IEF/verify_frame.py --mode merge-increment --increment 001_mi_incremento
```

Con un agente: `/speckit.ief.init`, `/speckit.ief.status`, `/speckit.ief.next`, etc.

---

## Presets

| Preset | Extiende | Ciclo build | Para qué |
|---|---|---|---|
| `generic` | — | 7 pasos, compuertas 1·4·5 | Base. Cualquier proyecto de software. |
| `engineering` | `generic` | 7 pasos | Pipelines, ETL, ingeniería de datos. |
| `data-science` | `generic` | 7 pasos | Análisis y respuestas a partir de datos. |
| `ml` | `generic` | **8 pasos**, compuertas 1·4·5·6b | Modelos. Añade *Evaluación del Modelo* con model card. |
| `mvp` | `generic` | **4 pasos**, 1 compuerta | Prototipos. Cambia rigor por velocidad, declarándolo. |
| `academic` | `generic` | 7 pasos | Tesis y papers. Numeración `00_admin` … `08_presentaciones`. |

Que `ml` tenga 8 pasos y `mvp` tenga 4 no requirió tocar el motor: está en sus
`preset.yml`.

### Crear o ajustar un preset

Tres niveles, de menos a más invasivo:

```yaml
extends: generic
cycles:
  build:
    rename:      {2_empirical_inspection: "Perfilado de Fuentes"}   # solo la etiqueta
    human_gates: [1_charter, 5_acceptance_tests]                    # mueve las compuertas
    steps:       [...]                                              # reemplaza el ciclo
```

Un preset trae lo suyo en su carpeta: `preset.yml`, `directory-convention.yml`,
`agents-fragment.md`, y si necesita scripts, en `presets/<id>/scripts/`. Validar:

```bash
python core/scripts/verify_frame.py --mode check-preset --preset mi-preset
```

---

## El ciclo base

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

Todo en `initiative/increments/<SLUG>/`. **Una ruta por artefacto**, declarada en el
preset y consultable con `--mode status --json`.

### Exploration — investigar antes de construir

`objective.md` → análisis → *(contrato opcional)* → `findings.md`. Sin compuertas: su
producto es conocimiento, y alimenta un futuro Charter.

---

## Criterios que se ejecutan

Un `given/when/then` en prosa es una intención. Con un bloque `verify`, el compilador lo
convierte en un test real:

```yaml
tests:
  - test_id: TST-ACC-001
    linked_rule: BR-001
    given: "el conjunto de validación"
    when: "se evalúa el modelo"
    then: "el F1 macro supera 0.80"
    verify:
      kind: metric                    # metric | command | python
      report: "reports/evaluacion.json"
      path: "macro.f1"
      op: ">="
      value: 0.80
```

- Sin `verify` → el test **falla** con un mensaje que lo explica.
- `status: blocked` + `blocked_reason` → se salta, declarando por qué no se puede medir.
- `--check` detecta que el YAML cambió y los tests generados quedaron obsoletos.

---

## Estructura

```
core/
  scripts/verify_frame.py             estado, compuertas, avance, merge
  scripts/ief_preset.py               carga de presets con herencia
  scripts/compile_acceptance_tests.py YAML -> pytest
  steps/                              instrucciones y plantillas de cada paso
  templates/                          plantillas de artefacto
extension/commands/                   los comandos /speckit.ief.*
presets/<id>/                         ciclo, directorios y lo propio de cada tipo de trabajo
tests/                                suite del framework
```

`core/` no sabe de ningún dominio, y `--mode check-bundle` lo verifica.

---

## Verificación

```bash
python core/scripts/verify_frame.py --mode check-bundle    # estructura
python core/scripts/verify_frame.py --mode check-preset    # presets y sus rutas
python core/scripts/verify_frame.py --mode check-steps     # archivos de cada paso
pytest tests/ -q
```

---

## Licencia

MIT
