# Iterative Evidence Framework (IEF)

> Extensión de [spec-kit](https://github.com/github/spec-kit): el mismo espíritu de
> desarrollo guiado por especificaciones, con ciclos incrementales, varios frentes de
> trabajo a la vez y reglas que se descubren trabajando.

> [!NOTE]
> **No es un fork de spec-kit ni contiene código suyo.** Es un bundle independiente que
> interopera con él siguiendo su formato de extensiones. Sin afiliación con GitHub, Inc.
> Detalle en [`NOTICE.md`](NOTICE.md).

> [!IMPORTANT]
> **Este directorio es el framework, no un proyecto.** Nunca se crea un `initiative/`
> aquí dentro ni se trabaja sobre esta carpeta: el IEF se aplica a *otros* repositorios.
> Ver [`AGENTS.md`](AGENTS.md).

---

## Los tres ejes

El error que este diseño corrige es haber tratado como «tipo de proyecto» tres cosas que
son independientes. Ahora se eligen por separado:

| Eje | Decide | Se elige | Opciones |
|---|---|---|---|
| **Layout** | Cómo se llaman las carpetas | al iniciar el proyecto | `flat` · `numbered` |
| **Preset** | Vocabulario y ceremonia | al iniciar el proyecto | `generic` `research` `product` `analysis` + mixin `modeling` |
| **Ciclo** | Cuánto rigor lleva *este* trabajo | **en cada incremento** | `exploration` · `prototype` · `build` |

Un MVP no es un tipo de proyecto: es un **incremento** `prototype` que cualquier
proyecto abre cuando lo necesita. Y las presentaciones no son «de proyectos
académicos»: son un **rol** que casi todos usan.

---

## Qué añade sobre spec-kit

| | |
|---|---|
| **Reglas de abajo arriba** | spec-kit escribe la constitución al principio. El IEF además **descubre reglas trabajando** y las promueve al proyecto, con detección de conflictos. |
| **El ciclo lo define el preset** | Qué pasos hay, cuáles llevan compuerta y dónde vive cada artefacto sale de `presets/<id>/preset.yml`. Un mixin inyecta un paso **sin tocar código**. |
| **Criterios ejecutables** | `acceptance-tests.yml` se compila a pytest. Un criterio sin forma de verificarse **falla**. |
| **Compuertas mecánicas** | `check-gates` sale con código 1 si un paso con compuerta quedó sin aprobar. Es condición de merge, no un recordatorio. |
| **Varios frentes a la vez** | `ACTIVE` (varios) y `focus` (uno) son cosas distintas, con bloqueos tipados y diagnóstico. |

---

## ¿Esto merece un incremento?

El riesgo de un framework así no es equivocarse: es **pesar tanto que se abandone**. El
eje para decidir no es el tamaño, es la **consecuencia**.

| Pregunta | Si es que sí |
|---|---|
| ¿Alguien va a **citar** este número? | Necesita evidencia reproducible |
| ¿Alguien más va a **mantener** esto? | Necesita especificación |
| ¿**Cambia una regla** del proyecto? | Necesita el ciclo entero |
| ¿Ninguna de las tres? | **Hazlo y anótalo** |

| Nivel | Cuándo | Coste |
|---|---|---|
| `--mode log` | Un gráfico, un documento, un arreglo de diez minutos | Una línea en `worklog.md` |
| ciclo `task` | Código pequeño; nadie hereda decisiones nuevas | 2 pasos, sin compuertas |
| ciclo `prototype` | Hay una hipótesis que puede fallar | 4 pasos, 1 compuerta |
| ciclo `build` | Otros dependerán de esto | 7 pasos, 3 compuertas |

```bash
python $IEF/verify_frame.py --mode log     --message "gráfico de margen por categoría para el comité"     --output reports/figures/margen_cat.png --from notebooks/03_margen.ipynb
```

## Adoptar el IEF en un proyecto que ya existe

`init` impone rutas; sobre un proyecto empezado crearía una estructura **paralela**.
`adopt` hace lo contrario: descubre las rutas que ya hay y **no mueve un solo archivo**.

```bash
python $IEF/verify_frame.py --mode adopt --preset analysis         # propone
python $IEF/verify_frame.py --mode adopt --preset analysis --yes   # aplica
```

```
  Carpetas reconocidas:
    src                      -> codigo
    notebooks                -> exploracion
    datos_crudos             -> datos_raw
    salidas                  -> resultados

  Carpetas que no supe clasificar (se dejan como estan, intactas):
    cosas_raras
```

Lo reconocido se guarda en `initiative.role_paths` y manda sobre el layout.

## Instalación

```bash
pip install -r requirements-dev.txt
python core/scripts/verify_frame.py --mode check-bundle
pytest tests/ -q
```

El núcleo solo necesita `PyYAML`.

---

## Uso

Siempre desde el directorio del **proyecto**, no desde aquí:

```bash
IEF=/ruta/al/spec-kit_bundle/core/scripts
cd /ruta/de/mi/proyecto

# 1. Iniciar: preset y layout son decisiones separadas
python $IEF/verify_frame.py --mode init --preset analysis --layout numbered \
    --initiative-name "Mi proyecto"

# 2. Escribir la constitución antes del primer incremento
$EDITOR initiative/specs/constitution.md

# 3. Abrir un frente de trabajo, con el rigor que pida
python $IEF/verify_frame.py --mode new-increment --type build --name "Ingesta de ventas"

# 4. Trabajar el paso, verificarlo, aprobarlo si lleva compuerta, avanzar
python $IEF/verify_frame.py --mode verify-step
python $IEF/verify_frame.py --mode approve-step --by "yo"
python $IEF/verify_frame.py --mode advance

# 5. Compilar y ejecutar los criterios de aceptación
python $IEF/compile_acceptance_tests.py --increment 001_ingesta_de_ventas
pytest tests/generated -v

# 6. Cerrar y promover sus reglas al proyecto
python $IEF/verify_frame.py --mode check-gates
python $IEF/verify_frame.py --mode merge-increment --increment 001_ingesta_de_ventas

# En cualquier momento: qué está mal
python $IEF/verify_frame.py --mode doctor

# Por qué el sistema hace esto
python $IEF/verify_frame.py --mode explain --rule RUL-003-001

# El informe del incremento, con lo que el motor ya sabe
python $IEF/verify_frame.py --mode draft-report --increment 001_ingesta_de_ventas
```

### `explain`: el linaje de una regla

```
  RUL-001-001
  ======================================================================
  Un pedido sin cliente se descarta

  estado    : superseded   (rige todo el proyecto)
  nace en   : 001_ingesta   (promovida el 2026-09-03)

  POR QUE EXISTE
    El 3% del historico no tiene cliente y son pruebas del ERP

  LINAJE
    SUPERADA por RUL-002-001   Un pedido sin cliente NO se descarta...
    -> esta regla ya NO rige. La vigente es RUL-002-001
```

Responde la pregunta más cara de un proyecto de meses: *¿por qué el sistema hace esto?*

---

## Varios frentes de trabajo

**Sí puedes tener dos incrementos activos.** Lo que hay que separar es *tener trabajo en
curso* de *dónde estás ahora*:

| | Significa | Cuántos |
|---|---|---|
| `status: ACTIVE` | Este frente tiene trabajo en curso | **varios** |
| `focus` | A cuál apuntan los comandos sin `--increment` | **uno** |

```bash
python $IEF/verify_frame.py --mode focus                          # ver
python $IEF/verify_frame.py --mode focus --increment 002_panel    # mover
```

### Pausar y bloquear no es lo mismo

| Estado | Significa | Quién lo saca de ahí |
|---|---|---|
| `PAUSED` | **Tú** decidiste parar; cambió la prioridad | Tú, cuando quieras |
| `BLOCKED` | **Algo externo** impide avanzar | El bloqueante, al resolverse |

Un bloqueo declara de qué tipo es, y eso permite diagnosticarlo:

```bash
# Dependo de que otro equipo me pase datos
python $IEF/verify_frame.py --mode set-status --increment 001_ingesta --status BLOCKED \
    --blocked-kind external --reason "esperando extracto de BI" --expected 2026-09-20

# Abro otro frente y sigo trabajando
python $IEF/verify_frame.py --mode new-increment --type prototype --name "Panel de calidad"

# Llegan los datos: reanudo y recupero el foco
python $IEF/verify_frame.py --mode set-status --increment 001_ingesta --status ACTIVE --focus
```

En ese último paso el motor compara contra qué reglas se abrió el incremento y avisa si
el mundo cambió mientras estabas en otra cosa:

```
  [!] Las reglas del proyecto cambiaron desde que abriste este incremento.
        ~ RUL-001-003    Un pedido sin cliente se descarta
        + RUL-004-001    Un pedido sin cliente va al cliente generico
      Revisa charter.md y data-contract.yml antes de seguir.
```

`--blocked-kind increment` valida que el bloqueante exista y **rechaza dependencias
circulares**. `--mode doctor` avisa de bloqueos vencidos, frentes de más y reglas sin
promover.

---

## Reglas: de un incremento al proyecto

Dos capas, con direcciones opuestas y ambas necesarias:

| | **Constitución** | **Reglas promovidas** |
|---|---|---|
| Describe | **Cómo se trabaja** | **Qué es cierto del dominio** |
| Ejemplo | «Ninguna cifra sin evidencia ejecutable» | «Un episodio dura ≥ 5 min» |
| Nace | Al inicio, de una vez | En el paso 4 de un incremento |
| Dirección | Arriba→abajo (como spec-kit) | **Abajo→arriba (aporte del IEF)** |

Una regla tiene tres vidas:

```
   PASO 4 del incremento          merge-increment           incremento posterior
  ┌────────────────────┐        ┌──────────────────┐      ┌──────────────────┐
  │  proposed          │ ─────► │   active         │ ───► │   superseded     │
  │  scope: increment  │        │  scope: project  │      │  apunta a la que │
  │  rige solo aquí    │        │  rige todo       │      │  la reemplaza    │
  └────────────────────┘        └──────────────────┘      └──────────────────┘
```

```yaml
rules:
  - id: RUL-003-001            # la procedencia va en el id
    statement: "Un pedido sin cliente se asigna al cliente genérico"
    rationale: "Descartarlos perdía 3% de facturación real: eran ventas de mostrador"
    evidence: [TST-ACC-014]
    applies_to: "pedidos.validacion"    # lo que el motor compara para detectar choques
    scope: increment
    status: proposed
    supersedes: RUL-001-004             # obligatorio si contradice una regla vigente
```

Si dos incrementos promueven reglas sobre el mismo `applies_to` sin declarar
`supersedes`, **la promoción se detiene**:

```
[CONFLICTO] La promocion se detiene. Sin esto, dos reglas
            contradictorias convivirian sin que nadie lo notara.

  - RUL-002-001 gobierna `pedidos.validacion`, que ya rige RUL-001-001.
    Declara `supersedes: RUL-001-001` si la reemplaza.
```

La regla superada **no se borra**: queda marcada apuntando a la nueva. El proyecto
necesita recordar que un día pensó lo contrario, y por qué.

---

## Presets

| Preset | Vocabulario del paso 4 | Roles que añade |
|---|---|---|
| `generic` | «Reglas» | núcleo mínimo |
| `research` | «Reglas del Modelo» | referencias, documento, presentaciones, avances, admin |
| `product` | «Reglas de Negocio» | pipelines, despliegue, onboarding, config |
| `analysis` | «Definiciones y Métricas» | exploración, resultados, avances |
| `modeling` *(mixin)* | añade el paso 6b con compuerta | modelos, experimentos, config |

`modeling` se **compone** con cualquier base, que es lo que la herencia simple no
permitía:

```yaml
extends: [analysis, modeling]     # análisis que entrena modelos
extends: [product, modeling]      # sistema con un modelo dentro
```

### Personalizar un ciclo

```yaml
extends: generic
cycles:
  build:
    rename:        {4_rules: "Definiciones"}          # solo la etiqueta
    human_gates:   [1_charter, 5_acceptance_tests]    # mueve las compuertas
    remove:        [3_data_contracts]                 # quita pasos
    insert_after:  {6_implementation: [ {...} ]}      # inserta sin redeclarar el ciclo
    steps:         [...]                             # reemplaza el ciclo entero
```

```bash
python core/scripts/verify_frame.py --mode check-preset --preset mi-preset
```

---

## Roles y layouts

Un **rol** es una necesidad («un sitio para las presentaciones»); el **layout** la
convierte en una ruta. El catálogo de roles es único porque un estudiante de memoria, un
ingeniero de datos y un analista acumulan casi lo mismo: lo que cambia entre ellos es el
vocabulario, no las carpetas.

```
rol              numbered               flat
────────────────────────────────────────────────────────
admin         →  00_admin/           |  admin/
onboarding    →  01_inicio/          |  docs/onboarding/
referencias   →  02_referencias/     |  references/
metodologia   →  03_metodologia/     |  docs/method/
codigo        →  04_codigo/src       |  src/
datos_raw     →  05_datos/raw        |  data/raw/
resultados    →  06_resultados/...   |  reports/figures/
documento     →  07_documento/       |  docs/
presentaciones→  08_presentaciones/  |  presentations/
avances       →  09_avances/         |  reports/progress/
```

`avances` (muchos reportes cortos) y `documento` (el entregable largo) son roles
**distintos** a propósito: distinta cadencia, distinta audiencia. Catálogo completo en
[`core/roles.yml`](core/roles.yml) y [`core/layouts.yml`](core/layouts.yml).

---

## Los tres ciclos

### `exploration` — investigar antes de construir
`objective.md` → análisis → *(contrato opcional)* → `findings.md`. Sin compuertas.

### `prototype` — descubrir si algo vale la pena
Cuatro pasos, una compuerta: hipótesis y criterio de éxito → cómo sabremos si funciona →
construir → aprender y decidir. Los pasos que se saltan **no están**, en vez de fingirse
completados.

### `build` — construir algo que tiene que aguantar

| Paso | Artefacto | Compuerta |
|---|---|---|
| 1. Charter | `charter.md` | ✋ |
| 2. Inspección Empírica | `inspection-report.md` | |
| 3. Contratos de Datos | `data-contract.yml` | |
| 4. Reglas | `rules.yml` | ✋ |
| 5. Criterios de Aceptación | `acceptance-tests.yml` | ✋ |
| 6. Implementación | *(código)* | |
| 7. Verificación | `increment-report.md` | |

**Una ruta por artefacto**, declarada en el preset y consultable con
`--mode status --json`.

---

## Criterios que se ejecutan

```yaml
tests:
  - test_id: TST-ACC-001
    linked_rule: RUL-001-001
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

Sin `verify` el test **falla** con un mensaje que lo explica. `status: blocked` +
`blocked_reason` lo salta declarando por qué no se puede medir.

---

## Estructura

```
core/
  roles.yml                           qué acumula un proyecto
  layouts.yml                         cómo se llaman esas carpetas
  scripts/verify_frame.py             estado, foco, compuertas, merge, doctor
  scripts/ief_preset.py               presets, herencia múltiple, roles
  scripts/compile_acceptance_tests.py YAML -> pytest
  steps/ · templates/                 instrucciones y plantillas
extension/commands/                   los comandos /speckit.ief.*
presets/<id>/                         ciclo, vocabulario y roles
tests/                                suite del framework
```

`core/` no sabe de ningún dominio, y `--mode check-bundle` lo verifica.

---

## Verificación

```bash
python core/scripts/verify_frame.py --mode check-bundle
python core/scripts/verify_frame.py --mode check-preset
python core/scripts/verify_frame.py --mode check-steps
pytest tests/ -q
```

---

## Licencia y atribución

MIT — ver [`LICENSE`](LICENSE).

Diseñado para funcionar con [spec-kit](https://github.com/github/spec-kit)
(MIT, Copyright GitHub, Inc.). Este repositorio no incluye código de spec-kit ni está
afiliado a GitHub, Inc.; ver [`NOTICE.md`](NOTICE.md) para el detalle de qué toma
prestado y en qué se aparta.
