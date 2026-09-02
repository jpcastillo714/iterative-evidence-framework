# Iterative Evidence Framework (IEF) — Spec Kit Bundle

> Define, inspecciona, verifica y construye en ciclos empíricos, con cualquier agente de IA.

Un bundle de [Spec Kit](https://github.com/github/spec-kit) que reemplaza el flujo lineal
por ciclos incrementales con evidencia ejecutable: criterios que se corren, compuertas que
bloquean de verdad, y una especificación que se consolida en vez de duplicarse.

---

## Qué lo distingue

| | |
|---|---|
| **El ciclo lo define el preset** | Los pasos, su orden, cuáles llevan compuerta humana y dónde vive cada artefacto salen de `presets/<id>/preset.yml`. Un preset puede quitar pasos, agregarlos o mover una compuerta **sin tocar código**. |
| **Criterios ejecutables** | `acceptance-tests.yml` se compila a pytest. Un criterio sin forma de verificarse **falla**; no se aprueba por omisión. |
| **Compuertas mecánicas** | `--mode check-gates` sale con código 1 si un paso con compuerta quedó terminado sin aprobación. Es una condición de merge, no un recordatorio. |
| **Especificación viva** | `--mode merge-increment` promueve las reglas del incremento a `initiative/specs/`, con la procedencia de cada una. Sin esto, cada incremento acumula su copia y nadie sabe cuál rige. |
| **Multi-incremento** | Varios frentes coexisten con estados `ACTIVE`, `PAUSED`, `BLOCKED`, `COMPLETED`, `MERGED`, `ABANDONED`. |
| **Retroceso con motivo** | `--mode rewind` marca los pasos como `NEEDS_REVISION`, revoca sus aprobaciones y registra por qué. |

---

## Instalación

```bash
pip install -r requirements.txt        # núcleo + presets con datos
pip install -r requirements-dev.txt    # además, la suite de tests
```

Comprobar que el bundle está sano antes de usarlo:

```bash
python core/scripts/verify_frame.py --mode check-bundle
python core/scripts/verify_frame.py --mode check-preset
pytest tests/ -q
```

---

## Inicio rápido

```bash
# 1. Inicializar (crea los directorios del preset, state.yml y initiative/specs/)
python core/scripts/verify_frame.py --mode init \
    --preset academic --initiative-name "Mi tesis"

# 2. Ver el estado en cualquier momento
python core/scripts/verify_frame.py --mode status

# 3. Trabajar el paso actual, verificarlo y avanzar
python core/scripts/verify_frame.py --mode verify-step
python core/scripts/verify_frame.py --mode approve-step --by "juanp"   # si hay compuerta
python core/scripts/verify_frame.py --mode advance

# 4. Compilar y ejecutar los criterios de aceptación
python core/scripts/compile_acceptance_tests.py --increment 001_mi_incremento
pytest tests/generated -v

# 5. Cerrar y consolidar en la especificación viva
python core/scripts/verify_frame.py --mode check-gates
python core/scripts/verify_frame.py --mode merge-increment --increment 001_mi_incremento
```

Con un agente, los mismos pasos son `/speckit.ief.init`, `/speckit.ief.status`,
`/speckit.ief.next`, `/speckit.ief.verify`.

---

## Los ciclos

### Build (7 pasos)

Para construir algo verificable. Compuertas humanas en 1, 4 y 5.

| Paso | Artefacto | Compuerta |
|---|---|---|
| 1. Charter | `charter.md` | ✋ |
| 2. Inspección Empírica | `inspection-report.md` | |
| 3. Contratos de Datos | `data-contract.yml` | |
| 4. Reglas de Negocio | `business-rules.yml` | ✋ |
| 5. Criterios de Aceptación | `acceptance-tests.yml` | ✋ |
| 6. Implementación | *(código en `src/`)* | |
| 7. Verificación | `increment-report.md` | |

Todos los artefactos viven en `initiative/increments/<SLUG>/`. **Una ruta por artefacto**,
declarada en el preset; consultarla con `--mode status --json`.

### Exploration (3+1 pasos)

Para investigar antes de construir. Sin compuertas: su producto es conocimiento.
`objective.md` → análisis → *(contrato opcional)* → `findings.md`, que alimenta un
futuro Charter.

---

## Criterios que se ejecutan

Un `given/when/then` en prosa es una intención, no un criterio. Declarando `verify`, el
compilador lo convierte en un test real:

```yaml
tests:
  - test_id: TST-ACC-001
    linked_rule: BR-001
    given: "el banco de fallas inyectadas"
    when: "se evalúa a severidad 4 sigma"
    then: "el recall por evento supera 0.80"
    verify:
      kind: metric                    # metric | command | python
      report: "resultados/evaluacion.json"
      path: "por_evento.recall"
      op: ">="
      value: 0.80
```

- Sin bloque `verify` → el test **falla** con un mensaje que lo explica.
- `status: blocked` con `blocked_reason` → se salta, declarando por qué no se puede medir.
- `--check` detecta que el YAML cambió y los tests generados quedaron obsoletos.

---

## Presets

| Preset | Extiende | Para qué |
|---|---|---|
| `generic` | — | Cualquier proyecto de software. Define el ciclo base. |
| `engineering` | `generic` | Pipelines, ETL, ingeniería de datos. |
| `academic` | `generic` | Tesis y papers. Numeración `00_admin` … `08_presentaciones`. |
| `astro-mlops` | `academic` | Detección de anomalías sobre telemetría. |

### Crear o ajustar un preset

Tres niveles, de menos a más invasivo:

```yaml
cycles:
  build:
    rename:       {2_empirical_inspection: "Auditoría de Telemetría"}   # solo la etiqueta
    human_gates:  [1_charter, 5_acceptance_tests]                       # mueve las compuertas
    steps:        [...]                                                 # reemplaza el ciclo entero
```

Validar antes de usarlo:

```bash
python core/scripts/verify_frame.py --mode check-preset --preset mi-preset
```

---

## Preset `astro-mlops`

Para proyectos que monitorean la salud de un equipo a partir de su telemetría.
Hereda la numeración de `academic`, así que **un proyecto `academic` lo adopta sin mover
un solo archivo**. Todo lo suyo vive en `presets/astro-mlops/`.

| Capa | Qué aporta |
|---|---|
| **Contrato de telemetría** | Cada canal declara su `clase`, unidad, rango válido y centinelas. Es un test, no un documento. |
| **Reglas del detector** | Abstención fuera del dominio de validez, umbral calibrado sobre nominal, confirmación k-de-n. |
| **Criterios operacionales** | Falsas alarmas por noche, cobertura, lead time y severidad mínima detectable, acordados **antes** de ver resultados. |
| **Evidencia trazable** | `CLM → CRT → TST → VRN → EVI`, con hash de entradas y salidas, commit y semilla. |

```bash
S=presets/astro-mlops/scripts

# El contrato de datos como test
python $S/validate_data_contract.py --contract data-contract.yml --data datos.parquet

# Ground truth fabricado cuando no hay historial de fallas etiquetado
python $S/inject_faults.py bench --data episodios.parquet --column residuo --out benchmark/

# Evaluación por eventos: falsas alarmas por noche y lead time
python $S/eval_anomaly.py --scores scores.parquet --labels benchmark/injections.yml \
    --calib scores_nominal.parquet

# Cualquier cifra citable nace de un run registrado
python core/scripts/evidence_run.py --test TST-ACC-007 --seed 42 \
    --input datos.parquet -- python pipelines/evaluar.py
```

Documentación: [protocolo de evaluación](presets/astro-mlops/docs/anomaly_detection_evaluation_protocol.md) ·
[trazabilidad MLOps](presets/astro-mlops/docs/mlops_traceability_spec.md) ·
[guía de adopción](docs/astro-mlops-adopcion.md)

---

## Estructura

```
core/                       el motor. Sin lógica de dominio.
  scripts/verify_frame.py             estado, compuertas, avance, merge
  scripts/ief_preset.py               carga de presets con herencia
  scripts/compile_acceptance_tests.py YAML -> pytest
  scripts/evidence_run.py             ejecución -> carpeta VRN con hashes
  steps/ templates/ docs/             plantillas e instrucciones genéricas
extension/commands/         los comandos /speckit.ief.*
presets/<id>/               ciclo, convención de directorios y lo propio del dominio
tests/                      suite del bundle (108 tests)
docs/legacy/                material histórico — ver su LEEME.md antes de creerle
```

---

## Una advertencia sobre la documentación

Varios documentos de `docs/legacy/` fueron escritos por agentes y contienen citas de
código que no corresponden a ninguna versión real del repositorio. Se conservan como
registro, no como especificación. Si necesitas saber cómo se comporta el framework,
**ejecútalo**: es el mismo principio que impone a los proyectos que gestiona.

---

## Licencia

MIT
