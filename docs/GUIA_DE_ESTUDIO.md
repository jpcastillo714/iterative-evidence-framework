# Guía de estudio del Iterative Evidence Framework (IEF)

> **Motor:** v0.14.0 · **Escrita:** 2026-09-10
>
> Todas las salidas de comandos que aparecen en esta guía se **ejecutaron** contra el
> motor al escribirla, sobre proyectos de prueba. No están reconstruidas de memoria. Si
> alguna no coincide con lo que ves, el motor cambió después: manda lo que ves.

---

## Cómo leer esta guía

Está pensada para estudiarse, no para consultarse de pasada. Tiene cuatro partes y cada
una se apoya en la anterior:

| Parte | Qué contiene | Cuándo leerla |
|---|---|---|
| **I. Qué es y por qué** | El problema, las cuatro garantías, el vocabulario | Primero, entera |
| **II. Las piezas** | Ejes, carpetas, presets, ciclos, pasos, estados, frentes, reglas | Despacio, con el motor abierto al lado |
| **III. Casos de uso** | Cinco proyectos contados de principio a fin | Cuando las piezas ya te suenen |
| **IV. Referencia** | Todos los comandos, las skills, los malentendidos, los límites | Para volver a ella |

Si solo tienes veinte minutos: lee la sección 3 (las cuatro garantías), la 10 (la vida de
un paso) y la sección 26 (malentendidos frecuentes). Con eso se evita el 80% de los
errores.

### Índice

**Parte I — Qué es y por qué**
1. El problema que resuelve
2. Relación con spec-kit
3. Las cuatro garantías
4. Glosario

**Parte II — Las piezas**
5. Los tres ejes: layout, preset, ciclo
6. Anatomía de un proyecto
7. Roles y layouts
8. Presets
9. La escala de rigor: de una línea a siete pasos
10. La vida de un paso
11. Los estados de un incremento
12. Varios frentes a la vez
13. Reglas: de un incremento al proyecto
14. La constitución
15. Entradas externas
16. Criterios de aceptación ejecutables
17. Cuando algo sale mal
18. `doctor`, pieza por pieza
19. Informes
20. Adoptar un proyecto que ya existe
21. El trabajo pequeño: `log`

**Parte III — Casos de uso**
22. Una memoria de título, de la primera semana a la defensa
23. Un pipeline de datos en equipo
24. Un análisis que termina en sistema
25. Un modelo de aprendizaje automático

**Parte IV — Referencia**
26. Malentendidos frecuentes
27. Todos los comandos
28. Las skills
29. Límites conocidos
30. Cómo seguir estudiando

---
---

# Parte I — Qué es y por qué

## 1. El problema que resuelve

### El desarrollo guiado por especificaciones, en una frase

Primero se escribe **qué** debe hacer el sistema, con precisión suficiente para poder
comprobarlo; después se construye; y la especificación **manda** sobre el código. Si el
código y la especificación discrepan, se corrige el código — o, si la especificación
estaba mal, se corrige la especificación explícitamente, dejando constancia.

Esa es la idea de [spec-kit](https://github.com/github/spec-kit), la herramienta de
GitHub de la que el IEF parte.

### Por qué eso no basta en un proyecto con datos

Spec-kit supone que **se puede escribir la especificación antes de empezar**. En
software de producto suele ser cierto: el cliente sabe qué quiere que haga el botón.

En un proyecto empírico no lo es. Piensa en estas preguntas:

- ¿A partir de cuántos días sin comprar se considera que un cliente abandonó? ¿30? ¿90?
- ¿Qué valor de un sensor es una lectura fallida y cuál una medición extrema pero real?
- ¿Una sesión termina tras 5 minutos de inactividad o tras 30?

Ninguna tiene respuesta **antes de mirar los datos**. Si la escribes de antemano, estás
inventando. Si no la escribes, el código la decide en silencio, en un `if` que nadie
revisa, y seis meses después nadie sabe por qué el número del informe es el que es.

### Lo que hace el IEF

Conserva la especificación como autoridad, pero la hace **crecer por incrementos**:

```
   mirar los datos  ──►  descubrir una regla  ──►  proponerla  ──►  una persona la aprueba
                                                                           │
   ┌───────────────────────────────────────────────────────────────────────┘
   ▼
   la regla sube a la especificación del proyecto, con su motivo y su evidencia,
   y desde entonces rige todo lo que venga después
```

Cada incremento es un ciclo corto de trabajo con pasos definidos. Al terminar, lo que
descubrió se **promueve** a una especificación viva (`initiative/specs/`) que crece con
el proyecto. Esa es la aportación central: **la especificación se descubre de abajo
arriba, además de escribirse de arriba abajo.**

---

## 2. Relación con spec-kit

El IEF es una **herramienta autónoma inspirada en spec-kit**. No lo necesita para
funcionar: se clona el repositorio y se llama al motor desde el proyecto.

| | spec-kit | IEF |
|---|---|---|
| Unidad de trabajo | Una *feature* | Un **incremento**, con un ciclo elegido por su riesgo |
| La especificación | Se escribe de arriba abajo, antes de construir | **Además** se descubre de abajo arriba, al trabajar |
| Rigor | Uno para todo | **Cuatro niveles**, más una bitácora para lo trivial |
| Aprobaciones | Implícitas | **Compuertas humanas** registradas y exigidas por el motor |
| Criterios | En prosa | **Ejecutables**: si no se pueden correr, fallan |
| Varios frentes | No es su problema | Foco, bloqueos tipados, detección de ciclos |

### Hasta dónde interoperan (medido con la CLI de spec-kit v1.0.4)

| | |
|---|---|
| `specify bundle validate` | ✅ acepta el manifiesto |
| `specify extension add ./extension --dev` | ✅ instala los comandos `speckit.ief.*` |
| El motor (`core/scripts/`) | ❌ no viaja con la extensión |
| La carpeta `presets/` | ❌ **no son presets de spec-kit** |

> **La confusión más fácil de tener.** La palabra «preset» significa dos cosas sin
> relación. Un preset de **spec-kit** es un paquete que *reemplaza plantillas de
> comando*. Un preset del **IEF** define *el ciclo de trabajo*: qué pasos hay, cuáles
> llevan compuerta, qué produce cada uno y con qué vocabulario se llaman. Cuando esta
> guía dice «preset», siempre significa lo segundo.

---

## 3. Las cuatro garantías

Todo el framework —cada comando, cada campo de `state.yml`, cada comprobación— existe
para sostener cuatro garantías. Si entiendes estas cuatro, el resto se deduce.

### Garantía 1 — Anti-alucinación

**Lo que no se sabe se marca `PENDING`. Nunca se rellena con algo plausible.**

Es la regla que más cuesta cumplir, sobre todo a un agente de IA, porque rellenar un
hueco con algo razonable *parece* ayudar. No ayuda: un hueco marcado es información
(«esto falta»), un hueco rellenado a ojo es una mentira que alguien citará después.

Cómo la sostiene el motor:
- Un criterio de aceptación sin forma de ejecutarse **falla**, no pasa (sección 16).
- `draft-report` rellena lo que el motor sabe y deja **como preguntas** lo que no puede
  saber (sección 19).
- Una regla no puede citar evidencia que no existe (sección 13).

### Garantía 2 — Compuertas humanas

**Ciertas decisiones las firma una persona, y el motor lo exige.**

No todo paso necesita aprobación. Pero hay decisiones —el alcance de un trabajo, las
reglas que van a gobernar el proyecto, el criterio con que se juzgará si algo funciona—
que no debe tomar ni el código ni un agente. En esos pasos hay una **compuerta**: el
motor no deja avanzar hasta que alguien registra su aprobación con su nombre.

Dos frases que conviene memorizar:

> **Una compuerta detiene el avance, no el trabajo.** Puedes escribir todo el contenido
> del paso; lo que no puedes es pasar al siguiente sin la firma.

> **Pedirte que hagas algo no es aprobarlo.** Si el usuario le dice a un agente «haz el
> charter», el agente escribe el charter; no lo aprueba en nombre del usuario.

### Garantía 3 — Criterios ejecutables

**Un criterio de aceptación que no se puede ejecutar no cuenta como criterio.**

«El modelo debe ser preciso» no es un criterio: es un deseo. «`recall` sobre el conjunto
de validación ≥ 0,80» sí lo es, porque se puede comprobar. El IEF compila los criterios a
tests de `pytest` reales, y los que no declaran cómo comprobarse **fallan ruidosamente**.

### Garantía 4 — Trazabilidad

**Toda regla sabe de dónde viene, por qué existe, qué reemplazó y qué la sostiene.**

Seis meses después, alguien preguntará «¿por qué el sistema hace esto?». La respuesta
honesta exige saber en qué incremento nació la regla, cuál era su motivo, si reemplazó a
otra, y qué test o qué hecho externo la respalda. El IEF guarda las cuatro cosas y
`--mode explain` las reúne.

---

## 4. Glosario

Vuelve a esta tabla cada vez que una palabra te suene rara.

| Término | Qué es | Dónde vive |
|---|---|---|
| **Iniciativa** | El proyecto entero, visto por el IEF | `initiative/` |
| **Incremento** | Una unidad de trabajo con un ciclo de pasos | `initiative/increments/NNN_slug/` |
| **Slug** | El identificador de un incremento: número + nombre | `003_ingesta_ventas` |
| **Ciclo** | La secuencia de pasos de un incremento: `task`, `exploration`, `prototype`, `build` | Definido en el preset |
| **Paso** | Una etapa del ciclo, que produce un artefacto | `state.yml`, campo `steps` |
| **Artefacto** | El archivo que produce un paso | `charter.md`, `rules.yml`… |
| **Compuerta** | Un paso que exige firma humana para avanzar | `human_gate: true` en el preset |
| **Foco** | El incremento sobre el que actúan los comandos sin `--increment` | `state.yml`, campo `focus` |
| **Preset** | El vocabulario y la ceremonia del proyecto | `presets/<id>/preset.yml` |
| **Mixin** | Un preset que no se usa solo: aporta piezas a otro | `presets/modeling/` |
| **Layout** | Cómo se llaman las carpetas | `core/layouts.yml` |
| **Rol** | Una necesidad del proyecto («un sitio para los datos crudos») | `core/roles.yml` |
| **Regla** | Algo que es cierto del dominio, con su motivo y su evidencia | `rules.yml` |
| **Constitución** | Los principios de cómo se trabaja, escritos una vez | `initiative/specs/constitution.md` |
| **Especificación viva** | Lo que ya rige el proyecto: reglas promovidas y constitución | `initiative/specs/` |
| **Promover** | Subir las reglas de un incremento a la especificación viva | `--mode merge-increment` |
| **Entrada externa** | Un hecho que llegó de fuera: una reunión, un correo | `initiative/specs/inputs.yml` |
| **Bitácora** | Registro del trabajo que no merece un incremento | `initiative/worklog.md` |
| **Motor** | El programa que lee y escribe el estado | `core/scripts/verify_frame.py` |

---
---

# Parte II — Las piezas

## 5. Los tres ejes: layout, preset, ciclo

Esta es la decisión de diseño que gobierna todo lo demás, y la que más cuesta ver.

Hay **tres preguntas distintas** que un proyecto responde, y cada una se contesta en un
momento distinto:

| Eje | Pregunta que responde | Se elige | Ejemplo |
|---|---|---|---|
| **Layout** | ¿Cómo se llaman las carpetas? | Una vez, al empezar el proyecto | `flat` (`src/`, `data/`) o `numbered` (`04_codigo/`, `05_datos/`) |
| **Preset** | ¿Con qué vocabulario y cuánta ceremonia trabajamos? | Una vez, al empezar el proyecto | `research` llama al paso 4 «Reglas del Modelo»; `product`, «Reglas de Negocio» |
| **Ciclo** | ¿Cuánto rigor merece **este** trabajo concreto? | **Cada vez** que se abre un incremento | Un filtro nuevo es `task`; un pipeline que otros usarán es `build` |

### Por qué están separados

Porque varían de forma independiente. Una tesis puede usar `research` con carpetas
`numbered` o con carpetas `flat`: el nombre de las carpetas es cuestión de gusto y de
herramientas, no de tipo de proyecto. Y dentro de esa misma tesis, un día harás una
exploración de una tarde y otro día un pipeline que tiene que aguantar un año: el rigor
depende del trabajo, no del proyecto.

Si los tres ejes se funden en uno, cada combinación necesita su propio preset y el
catálogo explota. Así se llegó, en una versión anterior, a tener presets llamados como
niveles de rigor (`mvp`) o como tipos de proyecto que en realidad compartían todas sus
carpetas.

### Señales de que alguien está mezclando ejes

- **Un preset que declara rutas de carpetas** → eso es del layout.
- **Un preset llamado como un nivel de rigor** (`mvp`, `rapido`, `estricto`) → eso es un
  ciclo.
- **Dos presets que difieren en un solo paso** → eso es un mixin, que se compone con
  `extends: [base, mixin]`.

---

## 6. Anatomía de un proyecto

### Lo que crea `init`

Proyecto de prueba con `--preset research --layout flat`:

```bash
python "$IEF/verify_frame.py" --mode init --preset research --layout flat \
    --initiative-name "Tesis de ejemplo"
```

```
.
├── admin/              ← rol admin
├── data/
│   ├── processed/      ← rol datos_processed
│   └── raw/            ← rol datos_raw        (solo lectura, siempre)
├── docs/               ← rol documento        (el entregable largo)
│   ├── method/         ← rol metodologia
│   └── onboarding/     ← rol onboarding
├── initiative/         ← EL MOTOR
│   ├── increments/     ← un subdirectorio por incremento
│   ├── specs/          ← la especificación viva
│   │   └── constitution.md
│   └── state.yml       ← el estado de todo
├── notebooks/          ← rol exploracion
├── presentations/      ← rol presentaciones
├── references/         ← rol referencias
├── reports/
│   ├── figures/        ← rol resultados
│   └── progress/       ← rol avances
├── scratch/            ← rol scratch
├── src/                ← rol codigo
└── tests/              ← rol tests
```

Cada carpeta existe porque el preset `research` declara el **rol** correspondiente, y el
layout `flat` le da ese nombre. Con `--layout numbered`, las mismas carpetas se llamarían
`00_admin/`, `05_datos/raw/`, `07_documento/`…

### Lo que hay dentro de `initiative/` con el tiempo

```
initiative/
├── state.yml                         el estado: incrementos, pasos, foco, historial
├── worklog.md                        la bitácora (aparece con el primer `log`)
├── specs/                            LA ESPECIFICACIÓN VIVA — lo que ya rige
│   ├── constitution.md               cómo se trabaja (sección 14)
│   ├── rules.yml                     qué es cierto del dominio (sección 13)
│   └── inputs.yml                    lo que se aprendió de fuera (sección 15)
└── increments/
    ├── 001_eda_clientes/             un incremento cerrado
    │   ├── objective.md
    │   ├── analysis.md
    │   ├── data-contract.yml
    │   ├── findings.md
    │   └── rules.yml                 reglas PROPUESTAS, que aún no rigen
    └── 002_pipeline_churn/           uno en curso
        ├── charter.md
        └── ...
```

La diferencia entre `increments/NNN/rules.yml` y `specs/rules.yml` es la diferencia entre
**proponer** y **regir**. Una regla vive en el incremento mientras se trabaja; al
promoverla, pasa a `specs/` y desde ese momento gobierna todo el proyecto.

### `state.yml`, anotado

Este es el `state.yml` real que dejó `init` más un `new-increment`:

```yaml
schema_version: '4.0'              # la versión del formato; el motor actual escribe 4.0
initiative:
  id: TESIS-DE-EJEMPLO
  name: Tesis de ejemplo
  preset: research                 # eje 2
  layout: flat                     # eje 1
  created_at: '2026-09-10T15:37:56+00:00'
focus: 001_pipeline_de_limpieza    # a qué incremento apuntan los comandos sin --increment
max_active: 3                      # límite blando de frentes ACTIVE a la vez
increments:
- id: '001'
  slug: 001_pipeline_de_limpieza
  name: Pipeline de limpieza
  type: build                      # eje 3: el ciclo de ESTE incremento
  status: ACTIVE
  current_step: '1'                # el ref del paso actual (siempre texto: existe "2b")
  steps:                           # una clave por paso del ciclo
    1_charter: IN_PROGRESS
    2_empirical_inspection: PENDING
    3_data_contracts: PENDING
    4_rules: PENDING
    5_acceptance_tests: PENDING
    6_implementation: PENDING
    7_verification: PENDING
  branch: inc/001-limpieza         # la rama de git que se declaró (opcional)
  rules_base: sha256:sin-reglas    # huella de las reglas vigentes al abrirlo (sección 12)
  opened_at: '2026-09-10T15:37:57+00:00'
history:                           # todo lo que pasó, en orden
- action: INIT
  ...
- action: NEW_INCREMENT
  ...
```

> **`state.yml` no se edita a mano.** Todo cambio pasa por un comando, que verifica antes
> de escribir y deja rastro en `history`. La única excepción aceptable es migrar un
> proyecto desde una versión anterior del IEF, una sola vez; `doctor` (sección 18) te
> dice qué está mal si el archivo viene de una versión vieja.

---

## 7. Roles y layouts

### Un rol es una necesidad, no una ruta

«Necesito un sitio para las presentaciones» es un rol. Que ese sitio se llame
`presentations/` o `08_presentaciones/` lo decide el layout.

El catálogo de roles salió de un ejercicio concreto: ponerse en el lugar de un estudiante
de memoria, un ingeniero de datos, un científico de datos, un equipo de MVP y un
investigador de aprendizaje automático, y anotar qué se les acumula a lo largo del
proyecto. La conclusión fue que **acumulan casi lo mismo**; lo que cambia es el
vocabulario y la ceremonia. Por eso hay un solo catálogo.

### Los 21 roles y sus dos nombres

| Rol | `flat` | `numbered` | Para qué |
|---|---|---|---|
| `initiative` | `initiative/` | `initiative/` | El motor. Siempre presente |
| `admin` | `admin/` | `00_admin/` | Cronograma, requisitos, actas, estado administrativo |
| `onboarding` | `docs/onboarding/` | `01_inicio/` | Qué es esto y cómo empiezo. Para quien llega nuevo… y para tu yo de dentro de un año |
| `referencias` | `references/` | `02_referencias/` | Papers, bibliografía, documentación externa |
| `metodologia` | `docs/method/` | `03_metodologia/` | Diseño experimental, decisiones de arquitectura |
| `codigo` | `src/` | `04_codigo/src/` | Código reutilizable: lo que sobrevive a la exploración |
| `config` | `conf/` | `04_codigo/conf/` | Configuración declarativa. Ningún parámetro vive en el código |
| `pipelines` | `pipelines/` | `04_codigo/pipelines/` | Etapas reproducibles |
| `exploracion` | `notebooks/` | `04_codigo/notebooks/` | Notebooks desechables. Nada de aquí se cita sin migrar a código |
| `despliegue` | `deploy/` | `04_codigo/app/` | App, API, runbooks |
| `datos_raw` | `data/raw/` | `05_datos/raw/` | Datos de origen. **Solo lectura** |
| `datos_interim` | `data/interim/` | `05_datos/interim/` | Pasos intermedios, reproducibles desde raw |
| `datos_processed` | `data/processed/` | `05_datos/processed/` | Conjuntos listos para usar |
| `resultados` | `reports/figures/` | `06_resultados/figuras/` | Figuras, tablas, métricas. Regenerables con un comando |
| `experimentos` | `experiments/` | `06_resultados/experimentos/` | Corridas y comparaciones contra líneas base |
| `modelos` | `models/` | `06_resultados/modelos/` | Artefactos de modelo versionados |
| `documento` | `docs/` | `07_documento/` | **El entregable largo**: tesis, informe final, paper |
| `presentaciones` | `presentations/` | `08_presentaciones/` | Decks, pósters, defensas |
| `avances` | `reports/progress/` | `09_avances/` | **Muchos reportes cortos**: quincenales, de sprint |
| `tests` | `tests/` | `tests/` | Pruebas, incluidos los criterios compilados |
| `scratch` | `scratch/` | `scratch/` | Playground. Nada sobrevive al incremento |

> **Por qué `avances` y `documento` van separados.** Muchos reportes cortos y un
> entregable largo son necesidades distintas: cadencia distinta, audiencia distinta. Si
> se mezclan, ninguno de los dos se encuentra cuando se busca.

> **Por qué `tests` y `scratch` están en la raíz en los dos layouts.** Es una excepción
> deliberada: las herramientas del ecosistema (pytest, linters) los buscan ahí.

### Qué roles usa cada preset

Los roles se **acumulan** por herencia: un preset tiene los suyos más los de sus padres.

| Preset | Roles |
|---|---|
| `generic` | `initiative`, `codigo`, `tests`, `scratch` |
| `research` | los de `generic` + `admin`, `onboarding`, `referencias`, `metodologia`, `exploracion`, `datos_raw`, `datos_processed`, `resultados`, `avances`, `documento`, `presentaciones` |
| `product` | los de `generic` + `onboarding`, `metodologia`, `config`, `pipelines`, `despliegue`, `datos_raw`, `datos_interim`, `datos_processed`, `resultados`, `avances` |
| `analysis` | los de `generic` + `referencias`, `exploracion`, `datos_raw`, `datos_interim`, `datos_processed`, `resultados`, `avances`, `presentaciones` |
| `modeling` *(mixin)* | aporta `config`, `modelos`, `experimentos` |

### Cuando tus carpetas no se llaman como dice el layout: `role_paths`

Si el proyecto ya tiene una carpeta para un rol con otro nombre, se declara en
`state.yml` y **tiene prioridad sobre el layout**:

```yaml
initiative:
  layout: numbered
  role_paths:
    onboarding: "01_idea"          # el layout diría 01_inicio
    referencias: "02_bibliografia" # el layout diría 02_referencias
```

A partir de ahí el motor escribe en `01_idea/`, no en `01_inicio/`. Nada se renombra.
`--mode adopt` (sección 20) escribe esto por ti al adoptar un proyecto existente.

---

## 8. Presets

### Qué decide un preset

Tres cosas, y ninguna es la estructura de carpetas:

1. **El vocabulario.** Cómo se llama cada paso. El archivo que produce el paso 4 se llama
   siempre `rules.yml`, pero el paso se llama distinto según a quién le hablas.
2. **La ceremonia.** Qué pasos llevan compuerta.
3. **Qué roles necesita** el proyecto.

### Los cinco presets

| Preset | Para | El entregable es |
|---|---|---|
| `generic` | La base. Cualquier cosa | Lo que sea |
| `research` | Tesis, memorias, papers | Un documento defendible |
| `product` | Sistemas que se despliegan y alguien mantiene | Un sistema que funciona |
| `analysis` | Responder preguntas con datos | Un hallazgo con su evidencia |
| `modeling` | *Mixin*: se compone con cualquiera de los anteriores | Añade la evaluación del modelo |

### El mismo ciclo `build`, con cuatro vocabularios

| Paso | `generic` | `research` | `product` | `analysis` |
|---|---|---|---|---|
| 1 | Charter | Hipótesis y Alcance | Charter | Pregunta y Alcance |
| 2 | Inspección Empírica | Exploración de Datos | Perfilado de Fuentes | Perfilado de Datos |
| 3 | Contratos de Datos | Esquema de Datos | Contrato de Datos | Esquema y Supuestos |
| 4 | Reglas | Reglas del Modelo | Reglas de Negocio | Definiciones y Métricas |
| 5 | Criterios de Aceptación | Criterios de Evaluación | Criterios de Aceptación | Criterios de Validez |
| 6 | Implementación | Implementación | Implementación del Pipeline | Análisis |
| 7 | Verificación | Evaluación y Resultados | Verificación y Despliegue | Hallazgos y Evidencia |
| **Compuertas** | **1, 4, 5** | **1, 4, 5** | **1, 4, 5** | **1, 5** |

Fíjate en la última fila. Es la diferencia de ceremonia más importante entre presets, y
tiene una consecuencia que conviene conocer.

> **En `analysis`, el paso 4 no lleva compuerta.** El preset lo justifica así: un
> análisis que no construye nada permanente no necesita aprobar su implementación, y
> las definiciones se fijan con el criterio de validez (paso 5). Pero eso significa que
> **nadie firmó las reglas en el ciclo**. Por eso, al promoverlas, el motor pide la firma
> en ese momento:
>
> ```
> ERROR: el ciclo `build` no tiene ninguna compuerta sobre las reglas, asi que
>        nadie ha aprobado estas 1. Promoverlas las hace validas para
>        todo el proyecto.
>
>        Ensenaselas a quien decide y vuelve con su firma:
>          --mode merge-increment --increment 001_churn --by "<nombre>"
> ```
>
> No es un error del preset: es la firma, puesta donde está la consecuencia (sección 13).

### El ciclo `exploration`, con sus vocabularios

| Paso | `generic` / `product` | `research` | `analysis` |
|---|---|---|---|
| 1 | Objetivo | Pregunta de Investigación | Pregunta Exploratoria |
| 2 | Análisis | Análisis Exploratorio | Análisis Exploratorio |
| 2b | Contrato de Datos | Formalización de Datos | Formalización del Esquema |
| 3 | Hallazgos | Hallazgos | Hallazgos |

Los ciclos `prototype` y `task` usan el mismo vocabulario en todos los presets.

### Componer presets: herencia y mixins

Un preset **hereda** de otro con `extends` y solo redefine lo que cambia. Todos heredan de
`generic`. La herencia acepta **una lista**, y así se componen mixins:

```yaml
extends: [analysis, modeling]     # un análisis que entrena modelos
extends: [product, modeling]      # un sistema con un modelo dentro
extends: [research, modeling]     # una tesis con componente de aprendizaje automático
```

Un **mixin** declara `abstract: true` y no se puede usar solo. `modeling` es el único que
viene incluido. Su contenido entero es este:

```yaml
roles:
  - config
  - modelos
  - experimentos

cycles:
  build:
    insert_after:                  # no redeclara el ciclo: inyecta un paso
      6_implementation:
        - key: "6b_model_evaluation"
          ref: "6b"
          name: "Evaluacion del Modelo"
          artifact: "model-card.md"
          human_gate: true
```

`insert_after` es lo que hace que un mixin sea pequeño. Si tuviera que copiar los siete
pasos para añadir uno, cualquier cambio en el ciclo base habría que replicarlo aquí.

> **Por qué el paso 6b existe y lleva compuerta.** «El pipeline funciona» y «el modelo
> generaliza» son preguntas distintas. Un modelo puede pasar todos los tests de
> integración y aun así no servir. Y publicar un modelo es una decisión, no un trámite.

### Cómo elegir

| Si tu entregable es… | Usa |
|---|---|
| Un documento que se defiende ante un tribunal o un comité | `research` |
| Algo que se despliega y alguien mantiene | `product` |
| Una respuesta a una pregunta, respaldada por datos | `analysis` |
| Cualquiera de los anteriores, con un modelo entrenado dentro | ese preset + `modeling` |
| No lo sabes todavía | `generic` |

Crear un preset nuevo o modificar uno es trabajo de la skill `ief-authoring` (sección
28), no de un proyecto.

---

## 9. La escala de rigor: de una línea a siete pasos

### El error que esta escala evita

El riesgo real de un framework como este **no es equivocarse: es pesar tanto que se deje
de usar.** Si hacer un gráfico exige abrir un incremento con cuatro pasos, a las tres
semanas trabajas fuera del sistema, y entonces no protege de nada.

Por eso hay cinco niveles, y **el eje para elegir no es el tamaño del trabajo, sino su
consecuencia.**

### Las cuatro preguntas

| Pregunta | Si la respuesta es sí… |
|---|---|
| ¿Lo va a **citar** alguien? | necesita evidencia |
| ¿Lo va a **mantener** alguien? | necesita especificación |
| ¿Hay una **hipótesis que puede fallar**? | necesita un criterio de éxito aprobado |
| ¿**Cambia una regla** del proyecto o dependerán otros de ello? | necesita el ciclo completo |
| **Ninguna de las anteriores** | hazlo y anótalo en una línea |

### La escala

| Nivel | Pasos | Compuertas | Cuándo | Ejemplo |
|---|---|---|---|---|
| `--mode log` | 0 | 0 | Trabajo sin consecuencias que nadie heredará | Un gráfico para una reunión |
| ciclo `task` | 2 | 0 | Código real y pequeño, sin decisiones nuevas | Añadir un filtro a un tablero |
| ciclo `exploration` | 4 | 0 | Una pregunta abierta sobre los datos | «¿Qué calidad tienen estas fuentes?» |
| ciclo `prototype` | 4 | 1 | Una hipótesis que puede fallar | «¿Un modelo simple supera a la regla actual?» |
| ciclo `build` | 7 | 3 | Algo que otros usarán o que fija reglas | El pipeline de ingesta del proyecto |

### `task` — dos pasos

| Ref | Clave | Artefacto | Compuerta |
|---|---|---|---|
| 1 | `1_task` | `task.md` | — |
| 2 | `7_verification` | `increment-report.md` | — |

Para trabajo que **es código de verdad pero no arrastra decisiones**.

> **La alarma que lleva dentro.** Si al escribir `task.md` aparece una decisión que
> **otros van a heredar** —una definición de métrica, un criterio de exclusión— eso ya no
> es un `task`. Un `task` no tiene compuerta donde aprobar esa decisión, así que la regla
> acabaría rigiendo sin que nadie la mirara. Ciérralo y abre un `prototype` o un `build`.

### `exploration` — cuatro pasos, sin compuertas

| Ref | Clave | Artefacto | Compuerta |
|---|---|---|---|
| 1 | `1_objective` | `objective.md` | — |
| 2 | `2_analysis` | `analysis.md` | — |
| 2b | `2b_data_contract` | `data-contract.yml` | — *(forma libre)* |
| 3 | `3_findings` | `findings.md` | — |

Para **investigar antes de construir**. No tiene compuertas porque explorar no obliga a
nadie a nada: es mirar.

Dos particularidades:

- **El paso 2b declara `structure: free`.** El contrato de datos de una exploración
  formaliza *lo que se encontró*, y eso es del dominio: puede organizarse por capas
  semánticas, por canales, por fuentes. El motor comprueba que el archivo existe y es YAML
  legible, pero no le impone forma de tabla. (El contrato del paso 3 de un `build`, en
  cambio, sí se valida estrictamente: allí gobierna un pipeline.)
- **Una exploración puede proponer reglas.** Si descubre una verdad del dominio, escribe
  un `rules.yml` en su carpeta y se promueve. Como el ciclo no tiene compuertas, la firma
  se pide al promover (sección 13).

### `prototype` — cuatro pasos, una compuerta

| Ref | Clave | Artefacto | Compuerta |
|---|---|---|---|
| 1 | `1_charter` | `charter.md` | **sí** |
| 2 | `5_acceptance_tests` | `acceptance-tests.yml` | — |
| 3 | `6_implementation` | — | — |
| 4 | `7_verification` | `increment-report.md` | — |

Para **descubrir si algo vale la pena**. La única compuerta está donde importa: la
hipótesis y su criterio de éxito se aprueban **antes** de construir. Si no, es demasiado
fácil mover la portería después de ver el resultado.

> **Fíjate en `ref` y `clave`.** El paso que escribes como `--step 2` se guarda como
> `5_acceptance_tests`. El **ref** es el número corto que tecleas; la **clave** es lo que
> se guarda en `state.yml` y es la misma en todos los ciclos. Por eso un `prototype`
> tiene los refs 1-2-3-4 pero las claves 1-5-6-7: reutiliza los pasos del `build` sin
> copiarlos.

### `build` — siete pasos, tres compuertas

| Ref | Clave | Artefacto | Compuerta | Qué pregunta responde |
|---|---|---|---|---|
| 1 | `1_charter` | `charter.md` | **sí** | ¿Qué vamos a hacer y por qué? ¿Cuándo lo abandonamos? |
| 2 | `2_empirical_inspection` | `inspection-report.md` | — | ¿Qué hay realmente en los datos? |
| 3 | `3_data_contracts` | `data-contract.yml` | — | ¿Qué forma tienen, formalmente? |
| 4 | `4_rules` | `rules.yml` | **sí** * | ¿Qué es cierto del dominio? |
| 5 | `5_acceptance_tests` | `acceptance-tests.yml` | **sí** | ¿Cómo sabremos que funciona? |
| 6 | `6_implementation` | — | — | Construirlo |
| 7 | `7_verification` | `increment-report.md` | — | ¿Funcionó? ¿Qué aprendimos? |

\* Salvo en `analysis`, donde el paso 4 no lleva compuerta (sección 8).

Para **construir algo que tiene que aguantar**. El orden importa: primero se mira (2),
luego se formaliza (3), luego se decide qué es cierto (4), luego cómo se comprobará (5), y
solo entonces se construye (6). Construir antes de decidir las reglas es exactamente lo
que el framework existe para evitar: la regla la termina decidiendo el código.

### Cómo se abre cada uno

```bash
python "$IEF/verify_frame.py" --mode log --message "..."                       # nivel 0
python "$IEF/verify_frame.py" --mode new-increment --type task        --name "..."
python "$IEF/verify_frame.py" --mode new-increment --type exploration --name "..."
python "$IEF/verify_frame.py" --mode new-increment --type prototype   --name "..."
python "$IEF/verify_frame.py" --mode new-increment --type build       --name "..."
```

---

## 10. La vida de un paso

### Los cinco estados de un paso

| Estado | Significa | Símbolo en `status` |
|---|---|---|
| `PENDING` | No se ha empezado | `.` |
| `IN_PROGRESS` | Es el paso actual | `~` |
| `COMPLETED` | Terminado y su artefacto verificado | `o` |
| `APPROVED` | Terminado **y firmado** por una persona (solo pasos con compuerta) | `*` |
| `NEEDS_REVISION` | Hay que rehacerlo tras un retroceso | `!` |

### El recorrido

```
                    escribes el artefacto
                            │
                            ▼
   IN_PROGRESS ── verify-step ── ¿el artefacto está y es válido?
        │                              │
        │                         no ──┴── corrige y vuelve a verificar
        │
   complete-step  (verifica otra vez; si falla, se niega)
        │
        ▼
    COMPLETED ── ¿el paso tiene compuerta?
        │                  │
        │ no               │ sí
        │                  ▼
        │           approve-step --by "Nombre"     ← SOLO la persona que decide
        │                  │
        │                  ▼
        │              APPROVED
        │                  │
        └────────┬─────────┘
                 ▼
             advance  → el siguiente paso pasa a IN_PROGRESS
```

### El recorrido real, comando a comando

Paso 1 de un `build` en `research` («Hipótesis y Alcance»), con `charter.md` escrito.

**1. Verificar.** No cambia nada; solo comprueba.

```
$ verify_frame.py --mode verify-step

  PASS  [Artefacto] charter.md existe
  PASS  [Compuerta] paso 1 aun no terminado (IN_PROGRESS)
  PASS  [Estado] state.yml tiene los campos obligatorios

[OK] paso 1 verificado
```

**2. Darlo por terminado.** Verifica de nuevo antes de marcar: si el artefacto no está,
se niega. Y como el paso lleva compuerta, lo dice:

```
$ verify_frame.py --mode complete-step

[COMPLETED] paso 1: Hipotesis y Alcance
            lleva compuerta: pide aprobacion al usuario y registrala con
            --mode approve-step --by "<usuario>"
```

**3. Intentar avanzar sin firma.** El motor se niega:

```
$ verify_frame.py --mode advance

ERROR: el paso 1 (Hipotesis y Alcance) requiere aprobacion del usuario.
       Ejecuta: verify_frame.py --mode approve-step
```

**4. La persona que decide lo aprueba:**

```
$ verify_frame.py --mode approve-step --by "Ana Perez"

[APPROVED] paso 1: Hipotesis y Alcance
```

**5. Ahora sí se avanza:**

```
$ verify_frame.py --mode advance

[ADVANCE] paso 2: Exploracion de Datos
          plantilla: core/steps/02_empirical_inspection/template.md
          artefacto: initiative/increments/001_pipeline_de_limpieza/inspection-report.md
```

**6. El tablero:**

```
$ verify_frame.py --mode status

  IEF — Tesis de ejemplo
  preset research (generic -> research) · layout flat · schema 4.0
  foco: 001_pipeline_de_limpieza
  --------------------------------------------------------------------

  * 001_pipeline_de_limpieza  (build)  [~] ACTIVE  [inc/001-limpieza]
      *  1. Hipotesis y Alcance          APPROVED        (compuerta)
      ~  2. Exploracion de Datos         IN_PROGRESS     <--
      .  3. Esquema de Datos             PENDING
      .  4. Reglas del Modelo            PENDING         (compuerta)
      .  5. Criterios de Evaluacion      PENDING         (compuerta)
      .  6. Implementacion               PENDING
      .  7. Evaluacion y Resultados      PENDING

  leyenda: o COMPLETED  * APPROVED  ~ IN_PROGRESS  . PENDING  ! NEEDS_REVISION
           el * de la izquierda marca el incremento con el FOCO
```

Lee el tablero así: el `*` de la izquierda del incremento marca el **foco**; el `*` a la
izquierda de un paso marca **APPROVED**. El `<--` señala el paso actual. `(compuerta)`
avisa de qué pasos exigirán firma.

### Lo que hay que entender de las compuertas

**Completar y aprobar son dos actos distintos, de dos personas distintas.** `complete-step`
lo ejecuta quien hizo el trabajo. `approve-step` lo ejecuta quien decide. Cuando las dos
son la misma persona —trabajando solo— siguen siendo dos actos: el primero dice «está
hecho», el segundo dice «lo he leído y lo acepto».

**El motor no puede comprobar quién firma.** `--by "Ana Perez"` registra un nombre; no
verifica una identidad. La compuerta funciona porque quien la usa es honesto, y por eso
la regla para agentes de IA es tajante: **un agente nunca firma en nombre del usuario.**
Si el usuario le pide al agente que avance, el agente le enseña el artefacto y le pide
que lo apruebe; no escribe su nombre en `--by`.

> **La racionalización exacta que hay que vigilar.** «El usuario ya autorizó esto en su
> mensaje.» Pedir que se haga algo no es aprobar la compuerta de ese algo. Si te
> sorprendes razonando así, estás a punto de firmar en nombre de otro.

**Una compuerta detiene el avance, no el trabajo.** Mientras esperas la firma del paso 1
puedes adelantar trabajo; lo que no puedes es marcar como avanzado el ciclo.

---

## 11. Los estados de un incremento

### Los seis estados

| Estado | Significa | Quién lo saca de ahí |
|---|---|---|
| `ACTIVE` | Tiene trabajo en curso | Avanza con normalidad |
| `PAUSED` | **Tú** decidiste parar: cambió la prioridad | Tú, cuando quieras |
| `BLOCKED` | **Algo ajeno** impide avanzar | El bloqueo, al resolverse |
| `COMPLETED` | Pasos terminados; reglas **sin promover** todavía | `merge-increment` |
| `MERGED` | Reglas promovidas al proyecto | Nadie: es final |
| `ABANDONED` | Se descarta; queda el registro y el aprendizaje | Nadie: es final |

`ACTIVE`, `PAUSED` y `BLOCKED` se consideran **abiertos**; los otros tres, **cerrados**.

### `PAUSED` no es `BLOCKED`

Se confunden porque los dos significan «no estoy trabajando en esto». Pero:

- `PAUSED` es **voluntario**: tú decidiste parar. Puedes retomarlo cuando quieras.
- `BLOCKED` es **forzado**: depende de que otra cosa se resuelva. No puedes retomarlo
  aunque quieras.

La diferencia importa porque solo un bloqueo se puede **diagnosticar**: tiene un
responsable, una fecha esperada, y puede formar ciclos con otros bloqueos.

### Cómo se cierra un incremento

```
   ACTIVE  ──(último paso terminado)──►  COMPLETED  ──(merge-increment)──►  MERGED
      │
      └──(se descarta)──►  ABANDONED
```

`COMPLETED` y `MERGED` son distintos a propósito. Un incremento terminado cuyas reglas
**nadie ha promovido** es un olvido frecuente: el trabajo está hecho, pero lo que
descubrió no rige nada. `doctor` los lista.

`ABANDONED` no borra nada. Un incremento abandonado con un buen informe de por qué se
abandonó es de lo más valioso que produce un proyecto: evita que alguien lo repita.

---

## 12. Varios frentes a la vez

### `ACTIVE` y foco son cosas distintas

| | Significa | Cuántos puede haber |
|---|---|---|
| `status: ACTIVE` | Este frente tiene trabajo en curso | **Varios** |
| `focus` | A cuál apuntan los comandos que no llevan `--increment` | **Uno** |

En una versión anterior eran el mismo campo, y activar un segundo incremento robaba el
puntero **en silencio**. A partir de ahí, `advance` o `approve-step` caían sobre un
incremento distinto del que creías. Nada fallaba: simplemente avanzabas el equivocado.

### Un escenario completo, ejecutado

Un equipo de datos con el preset `analysis`. Abre una exploración sobre la calidad de las
fuentes y, después, un `build` para un tablero.

**Abrir el segundo frente mueve el foco, y lo dice:**

```
$ verify_frame.py --mode new-increment --type build --name "Tablero de ventas"

[NUEVO] 002_tablero_de_ventas  (build)
        directorio : initiative/increments/002_tablero_de_ventas
        foco       -> 002_tablero_de_ventas
        paso 1: Pregunta y Alcance
```

**La exploración queda esperando datos de otro equipo. Se bloquea, diciendo de qué tipo
es la espera:**

```bash
python "$IEF/verify_frame.py" --mode set-status \
    --increment 001_calidad_de_fuentes --status BLOCKED \
    --blocked-kind external --blocked-on "equipo de BI" \
    --reason "esperando el extracto mensual" --expected 2026-09-20
```

**El tablero lo muestra con su espera:**

```
    001_calidad_de_fuentes  (exploration)  [X] BLOCKED
      ~  1. Pregunta Exploratoria        IN_PROGRESS     <--
      .  2. Analisis Exploratorio        PENDING
      . 2b. Formalizacion del Esquema    PENDING
      .  3. Hallazgos                    PENDING
      bloqueado [external] por equipo de BI · esperando 0 dia(s)
        esperando el extracto mensual
        fecha esperada: 2026-09-20

  * 002_tablero_de_ventas  (build)  [~] ACTIVE
      ~  1. Pregunta y Alcance           IN_PROGRESS     (compuerta) <--
      ...
```

**Llegan los datos. Reactivar no roba el foco:**

```
$ verify_frame.py --mode set-status --increment 001_calidad_de_fuentes --status ACTIVE

  [i] 001_calidad_de_fuentes queda ACTIVE, pero el foco sigue en 002_tablero_de_ventas.
      Para moverlo: --mode focus --increment 001_calidad_de_fuentes
[STATUS] 001_calidad_de_fuentes -> ACTIVE
```

Si quieres reactivarlo **y** trabajar en él, añade `--focus`. O mueve el foco después:

```bash
python "$IEF/verify_frame.py" --mode focus --increment 001_calidad_de_fuentes
```

### Los tres tipos de bloqueo

| `--blocked-kind` | Cuándo | Qué hace el motor |
|---|---|---|
| `increment` | Dependes de otro incremento tuyo | Valida que exista y **detecta ciclos** |
| `external` | Otro equipo, un proveedor, un permiso | Muestra cuánto llevas esperando; avisa si pasa la fecha esperada |
| `decision` | Falta que alguien decida algo | Igual que `external`, y lo lista en `doctor` |

**Nunca desbloquea solo.** Aunque el incremento del que dependías se cierre, el motor te
avisa, pero reanudar es decisión tuya.

### Los ciclos de dependencia se rechazan

El 001 queda bloqueado esperando al 002. Si ahora alguien intenta bloquear el 002
esperando al 001:

```
$ verify_frame.py --mode set-status --increment 002_tablero_de_ventas --status BLOCKED \
    --blocked-kind increment --blocked-on 001_calidad_de_fuentes --reason "..."

ERROR: dependencia circular entre incrementos: 002_tablero_de_ventas -> 001_calidad_de_fuentes -> 002_tablero_de_ventas
       Ninguno de los dos podria desbloquearse nunca.
```

### El límite blando de frentes

`max_active: 3` en `state.yml`. Al abrir el cuarto frente activo, el motor **avisa**
—¿es foco o dispersión?—, pero no lo impide. La decisión es tuya.

### Reanudar en un mundo que cambió: `rules_base`

Pausas un incremento tres semanas. Mientras tanto, otro incremento promueve reglas nuevas
o reemplaza alguna. Al volver, tu charter se escribió **contra reglas que ya no rigen**.

Para detectarlo, cada incremento guarda al abrirse una huella (`rules_base`) de las reglas
vigentes en ese momento. Si al retomarlo la huella ya no coincide, el motor te avisa de
qué cambió, para que revises el charter y el contrato antes de seguir. (Si no había
reglas al abrirlo, la huella es `sha256:sin-reglas`.)

### La rama de git

Si abres un incremento con `--branch inc/003-ingesta`, el motor comprueba en cada
`advance` que estés en esa rama, y `doctor` lo lista:

```
[!] El incremento 003_ingesta declara la rama `inc/003-ingesta` y estas en `main`.
    Lo que hagas ahora quedara anotado en ese incremento pero vivira en
    esta otra rama. Cambia de rama, o corrige la declarada con:
      --mode set-status --increment 003_ingesta --branch main
```

Es **aviso, no error**: el motor no sabe por qué estás donde estás. Un incremento sin
`--branch` no promete nada y nunca avisa. Si el proyecto no usa git, esto no existe.

## 13. Reglas: de un incremento al proyecto

Esta es la sección más importante de la guía, porque es donde el IEF aporta algo que
spec-kit no tiene: **la especificación que se descubre trabajando.**

### Dos capas, que no hay que confundir

| | Constitución *(sección 14)* | Reglas promovidas *(esta sección)* |
|---|---|---|
| Describe | **Cómo se trabaja** | **Qué es cierto del dominio** |
| Ejemplo | «Ninguna cifra se cita sin evidencia ejecutable» | «Un pedido sin cliente es una venta de mostrador» |
| Nace | Al empezar, de una vez | Dentro de un incremento, al mirar los datos |
| Dirección | De arriba abajo | **De abajo arriba** |
| Archivo | `specs/constitution.md` | `specs/rules.yml` |

### Anatomía de una regla

Así se escribe una regla en el `rules.yml` de un incremento:

```yaml
rules:
  - id: "RUL-003-001"
    statement: >-
      Un pedido sin cliente se clasifica como venta de mostrador.
    rationale: >-
      No eran pruebas del sistema ni errores: el equipo del sistema de ventas confirmó
      que desde marzo las ventas de mostrador se registran sin cliente a propósito.
    evidence: ["EXT-001", "TST-ACC-004"]
    applies_to: "pedidos.sin_cliente"
    scope: increment
    status: proposed
    priority: high
    supersedes: "RUL-002-001"
    since: "2026-09-10"
```

Campo por campo:

| Campo | Qué es | Por qué importa |
|---|---|---|
| `id` | `RUL-NNN-XXX`: `NNN` es el incremento donde nació, `XXX` un correlativo | **La procedencia va en el nombre.** `RUL-003-001` nació en el incremento 003, sin tener que buscarlo |
| `statement` | El enunciado, normativo y verificable | Si no puedes escribir un test que la compruebe, todavía no es una regla: es una intención |
| `rationale` | Por qué existe: qué se descubrió, qué alternativa se descartó | Es la parte que nadie recuerda en seis meses. Va **dentro** de la regla a propósito: una bitácora de decisiones aparte se desincroniza siempre |
| `evidence` | Qué la sostiene: tests (`TST-*`) o entradas externas (`EXT-*`) | El motor comprueba que lo citado **exista**. Una regla que cita evidencia inexistente es peor que una sin evidencia: parece respaldada |
| `applies_to` | Qué gobierna | **Es la clave con que se detectan los conflictos.** Dos reglas con el mismo `applies_to` gobiernan lo mismo: o una reemplaza a la otra, o se contradicen |
| `scope` | `increment` mientras se propone; `project` cuando se promueve | Lo cambia `merge-increment`; no se toca a mano |
| `status` | `proposed` · `active` · `superseded` · `rejected` | Ver «Las vidas de una regla» |
| `priority` | `critical` · `high` · `medium` · `low` | Las `critical` y `high` necesitan además tests de casos límite |
| `supersedes` | La regla vigente que esta reemplaza | **Obligatorio** si contradice una regla que ya rige. Sin él, la promoción se detiene |
| `since` | Fecha | |

### Las decisiones que todavía no se toman

Al final del `rules.yml` de un incremento hay un bloque para lo que aún no se ha decidido:

```yaml
decisiones_pendientes:
  - pregunta: "¿Una devolución parcial cuenta como devolución?"
    opciones: ["sí, siempre", "solo si supera el 50% del monto"]
    bloquea: ["RUL-003-002"]
    resolver_en: "la compuerta del paso 4"
```

Se resuelven **en la compuerta del paso 4**, no después. Una decisión aplazada hasta la
implementación la termina tomando el código, en silencio, y sin que nadie la haya
aprobado.

### Las vidas de una regla

```
   rules.yml del incremento            merge-increment              un incremento posterior
  ┌──────────────────────┐        ┌─────────────────────┐        ┌───────────────────────────┐
  │  proposed            │ ─────► │  active             │ ─────► │  superseded               │
  │  scope: increment    │        │  scope: project     │        │  superseded_by: RUL-004-… │
  │  rige solo aquí      │        │  rige todo          │        │  ya NO rige               │
  └──────────────────────┘        └─────────────────────┘        │  pero NO se borra         │
                                                                  └───────────────────────────┘
```

Y un cuarto estado, `rejected`: una propuesta que se consideró y se descartó. Si se
promueve con ese estado, **queda registrada como rechazada** en la especificación viva.
Es útil: evita que dentro de un año alguien vuelva a proponer lo mismo sin saber que ya se
descartó y por qué.

### Promover: qué exige `merge-increment`

```bash
python "$IEF/verify_frame.py" --mode merge-increment --increment <slug>
python "$IEF/verify_frame.py" --mode merge-increment --increment <slug> --dry-run
```

Tres condiciones:

1. El incremento está `COMPLETED` o `ACTIVE`.
2. **Todas** sus compuertas están `APPROVED`.
3. Si propone reglas y **ningún paso con compuerta las aprobó**, hace falta una firma:
   `--by "<nombre>"`.

La tercera depende del ciclo y del preset:

| Ciclo | ¿Algún paso con compuerta aprueba las reglas? | ¿Pide `--by` al promover reglas? |
|---|---|---|
| `build` en `generic`, `research`, `product` | Sí: el paso 4 | No |
| `build` en `analysis` | No: su paso 4 no lleva compuerta | **Sí** |
| `prototype` | No: su única compuerta es el charter | **Sí** |
| `exploration` | No hay compuertas | **Sí** |
| `task` | No hay compuertas | **Sí** |

La idea detrás: **la firma va donde está la consecuencia.** Explorar no obliga a nadie a
nada; por eso `exploration` no tiene compuertas. Pero promover una regla la hace valer para
todo el proyecto, y eso sí lo decide una persona. Si el ciclo no lo decidió en un paso, se
decide al promover.

Cuando falta la firma, el motor lo dice así:

```
ERROR: el ciclo `exploration` no tiene ninguna compuerta sobre las reglas, asi que
       nadie ha aprobado estas 1. Promoverlas las hace validas para
       todo el proyecto.

       Ensenaselas a quien decide y vuelve con su firma:
         --mode merge-increment --increment 001_eda --by "<nombre>"

       Pedirte que promuevas no es aprobar: la firma es de una persona.
```

### Promover: qué hace `merge-increment`

1. **Detecta conflictos.** Si una regla nueva gobierna el mismo `applies_to` que una
   vigente y no declara `supersedes`, **se detiene**. También se detiene si `supersedes`
   apunta a una regla que no existe.
2. **Marca las reemplazadas**, sin borrarlas: `status: superseded`, `superseded_by` y
   `superseded_at`.
3. **Sube las nuevas** a `specs/rules.yml` con `scope: project`, `status: active` y un
   campo `_origen` con el incremento y la fecha.
4. **Copia** `data-contract.yml` y `acceptance-tests.yml` del incremento a `specs/`, si
   existen. (Los reemplaza: ver «Límites conocidos», sección 29.)
5. Marca el incremento `MERGED`. Si tenía el foco, el foco pasa al siguiente candidato.
6. Deja en el historial qué se promovió y, si hubo firma, **de quién**.

Con `--dry-run` enseña lo que haría sin escribir nada.

### Un caso completo, ejecutado

Una tienda con el preset `product`. Tres exploraciones, una detrás de otra, sobre la misma
pregunta: ¿qué se hace con un pedido que llega sin cliente?

**Incremento 001.** Una exploración sobre la calidad de los pedidos concluye que son pruebas
del sistema:

```yaml
- id: RUL-001-001
  statement: "Un pedido sin cliente se descarta"
  rationale: "El 3% del historico no tiene cliente y parecian pruebas del sistema"
  applies_to: "pedidos.sin_cliente"
```

```
$ verify_frame.py --mode merge-increment --by "Ana Perez"

  [FIRMA] 1 regla(s) de un ciclo sin compuertas, aprobadas por Ana Perez
[MERGE] 001_calidad_de_pedidos -> initiative\specs
        rules.yml: +1 promovidas, ~0 superadas, 1 vigentes

[OK] 001_calidad_de_pedidos marcado MERGED. La especificacion viva esta actualizada.
```

**Incremento 002.** Otra exploración mira mejor y descubre que no eran pruebas: son ventas
reales. Propone una regla **sobre lo mismo** (`applies_to: pedidos.sin_cliente`), pero se
le olvida decir que reemplaza a la anterior:

```
$ verify_frame.py --mode merge-increment --by "Ana Perez"

  [FIRMA] 1 regla(s) de un ciclo sin compuertas, aprobadas por Ana Perez
[CONFLICTO] La promocion se detiene. Sin esto, dos reglas
            contradictorias convivirian sin que nadie lo notara.

  - RUL-002-001 gobierna `pedidos.sin_cliente`, que ya rige RUL-001-001. Declara `supersedes: RUL-001-001` si la reemplaza.

Resuelvelo declarando `supersedes` en la regla que manda, o
retrocede con --mode rewind si la nueva regla estaba mal planteada.
```

Dos salidas, y elegir entre ellas es **una decisión, no un trámite**:

- La nueva manda → se declara `supersedes: RUL-001-001`.
- La nueva estaba mal planteada → `rewind` y se replantea.

Aquí la nueva manda. Con `supersedes` declarado:

```
[MERGE] 002_pedidos_sin_cliente -> initiative\specs
        rules.yml: +1 promovidas, ~1 superadas, 2 vigentes
```

**Incremento 003.** Una reunión con el equipo del sistema de ventas revela que esos pedidos
son ventas de mostrador registradas sin cliente a propósito (se cuenta en la sección 15).
Una tercera regla reemplaza a la segunda y cita la reunión como evidencia.

Al final, `specs/rules.yml` guarda **las tres**:

```yaml
- id: RUL-001-001
  status: superseded
  superseded_by: RUL-002-001
- id: RUL-002-001
  status: superseded
  supersedes: RUL-001-001
  superseded_by: RUL-003-001
- id: RUL-003-001
  status: active
  supersedes: RUL-002-001
```

### `explain`: la respuesta a «¿por qué el sistema hace esto?»

```
$ verify_frame.py --mode explain --rule RUL-003-001

  RUL-003-001
  ======================================================================
  Un pedido sin cliente se clasifica como venta de mostrador

  estado    : active   (rige todo el proyecto)
  gobierna  : pedidos.sin_cliente
  nace en   : 003_ventas_de_mostrador   (promovida el 2026-09-10)

  POR QUE EXISTE
    Confirmado por el equipo del sistema de ventas: es un registro intencional

  LINAJE
    reemplaza a RUL-002-001    Un pedido sin cliente se asigna al cliente gen
    reemplaza a RUL-001-001    Un pedido sin cliente se descarta

  QUE LA SOSTIENE
    EXT-001
```

Recorre la cadena entera hacia atrás. Y sobre la primera regla:

```
$ verify_frame.py --mode explain --rule RUL-001-001

  RUL-001-001
  ======================================================================
  Un pedido sin cliente se descarta

  estado    : superseded   (rige todo el proyecto)
  gobierna  : pedidos.sin_cliente
  nace en   : 001_calidad_de_pedidos   (promovida el 2026-09-10)

  POR QUE EXISTE
    El 3% del historico no tiene cliente y parecian pruebas del sistema

  LINAJE
    es la primera regla sobre este asunto
    SUPERADA por RUL-002-001   Un pedido sin cliente se asigna al cliente gen
    -> esta regla ya NO rige. La vigente es RUL-002-001

  QUE LA SOSTIENE
    nada declarado — la regla no cita evidencia
```

Dos líneas para leer con cuidado:

- **`-> esta regla ya NO rige`** es la importante. Una regla superada se conserva, pero
  seguir aplicándola es exactamente el error que `explain` existe para evitar.
- **`nada declarado`** no significa que la regla sea falsa: significa que nadie escribió
  qué la sostiene. Es una deuda, y conviene verla.

`explain` busca tanto en las reglas vigentes como en las **propuestas** que aún viven dentro
de un incremento sin promover. Si el id no existe, lista los que sí.

### Por qué la regla superada no se borra

Imagina la defensa, o una auditoría. Alguien señala una cifra de un informe de hace cuatro
meses: «aquí se excluyeron 1.200 pedidos, ¿por qué?». Con el historial puedes responder:
*«en ese momento regía RUL-001-001, que los trataba como pruebas del sistema; el incremento
002 la reemplazó por este motivo, y esta es la cifra corregida»*.

Si la regla se hubiera borrado, la respuesta honesta sería «no me acuerdo».

## 14. La constitución

### Qué es

Los principios de **cómo se trabaja** en el proyecto. Se escriben una vez, al empezar, y
cambian rara vez. `init` deja la plantilla en `initiative/specs/constitution.md` y te
pide escribirla antes del primer incremento:

```
       constitucion: initiative\specs\constitution.md
       Escribela antes del primer incremento: son los principios bajo los
       que trabajaras, y las reglas que descubras viviran debajo.
```

Es la parte que el IEF conserva de spec-kit: la dirección **de arriba abajo**. Las reglas
de la sección 13 son la dirección contraria. Las dos conviven y no se sustituyen.

### La prueba para distinguirla de una regla

Una sola pregunta: **¿lo descubriste trabajando?** Entonces es una regla y su sitio es
`rules.yml`. ¿Es un compromiso que asumes **antes** de saber nada del dominio? Entonces es
constitucional.

| Frase | ¿Qué es? | Por qué |
|---|---|---|
| «Ninguna cifra se cita sin un comando que la reproduzca» | Constitución | Es cómo se trabaja; se asume antes de ver un solo dato |
| «Una sesión termina tras 30 minutos de inactividad» | Regla | Se decidió mirando la distribución de pausas |
| «Los datos de origen nunca se editan en el sitio» | Constitución | Compromiso de método |
| «La columna `fecha` viene en UTC» | Regla o contrato de datos | Es un hecho del dominio |
| «Un resultado negativo también va al informe» | Constitución | Es una postura ante la evidencia |

### Cómo se escribe un principio

Entre **tres y siete**. Más de siete y nadie los recuerda; menos de tres y no restringen
nada. Cada uno lleva tres partes:

```markdown
### P2 — La configuración vive fuera del código

**Principio:** Todo umbral, ruta o hiperparámetro se lee de `config/`. Ningún número
mágico vive en un archivo `.py`.

**Por qué:** Un umbral escrito en el código se cambia sin dejar rastro, y la cifra del
informe deja de ser reproducible sin que nadie lo note.

**Cómo se nota que se incumplió:** Aparece un literal numérico con significado de
negocio en el código (`if score > 0.8`) en lugar de una lectura de configuración.
```

La tercera parte es la que distingue un principio de un deseo. **Un principio tiene que
poder violarse.** «Trabajamos con rigor» es imposible de incumplir, así que no restringe
nada: es una descripción. «Todo parámetro vive en `config/`» se incumple el día que
alguien escribe `umbral = 0.8` en un script, y ese día se nota.

### Los principios de partida que trae la plantilla

Bórralos, quédatelos o reescríbelos. Están ahí porque son los que más caro se pagan cuando
faltan:

- **Nada se afirma sin poder ejecutarlo.** Una cifra sin un comando que la reproduzca es
  `PENDING`, no un resultado.
- **Los datos de origen son de solo lectura.** Todo derivado se reconstruye desde el
  pipeline.
- **La especificación manda sobre el código.** Si la implementación revela que una regla
  es inviable, se corrige la regla con `rewind`; no se parchea el código para que quepa.
- **Lo que no se sabe se marca `PENDING`.** Nunca se rellena con una suposición plausible.
- **Un rechazo es un resultado.** «No se alcanzó el criterio» es información y va al
  informe; no es motivo para bajar el criterio.

### Cómo se relaciona con los incrementos

1. Un incremento **no puede contradecir** un principio. Si necesita hacerlo, primero se
   cambia la constitución, explícitamente y dejando constancia.
2. El charter de cada incremento (paso 1) se lee **contra** estos principios.
3. Las reglas promovidas viven **debajo** de la constitución, nunca por encima.

### Cambiarla es un evento

Al final de la plantilla hay un historial de enmiendas:

| Fecha | Qué cambió | Por qué | Quién |
|---|---|---|---|
| 2026-09-01 | Versión inicial | — | Ana Pérez |
| 2026-11-14 | P3 deja de exigir revisión por pares de cada notebook | Frenaba la exploración y nadie revisaba notebooks que se iban a descartar | Ana Pérez |

Dentro de un año, la columna «Por qué» es la única que importará.

### Quién la escribe

La persona responsable del proyecto. Un agente de IA puede redactar un **borrador** a
partir de lo que ya dicen tus documentos, y es un buen punto de partida, pero debe:

- marcar de qué documento sale cada principio,
- señalar cuáles vienen de la plantilla y no de ti, y
- no darla por vigente hasta que la leas y la apruebes.

Una constitución que su dueño no ha leído no gobierna nada.

## 15. Entradas externas

### El hueco que cubren

Todo lo de la sección 13 da por hecho que una verdad del dominio **se descubre
trabajando**: nace en un incremento, se propone en un paso, se promueve con firma.

Pero la mitad de lo que cambia un proyecto no se descubre: **llega.**

- Una reunión donde quien provee los datos dice que el sistema de origen cambió en marzo.
- Un correo que retira un permiso de acceso.
- Un documento del cliente que contradice un supuesto del charter.
- Un dataset que llega con una advertencia: «la columna X dejó de medirse en junio».

Eso no es una regla —nadie lo dedujo— ni es una tarea —todavía no hay nada que hacer—.
Antes no tenía dónde ir: o se enterraba en `worklog.md`, sin id y sin poder citarse, o se
convertía en una regla, que exige un incremento entero para registrar algo que ya es
cierto. El rol `admin` («actas de reunión») era solo una carpeta que el motor no leía.

### Lo caro no es perder el acta

El acta suele estar en alguna parte. Lo caro es otra cosa: **que una reunión tumbe tres
afirmaciones del proyecto y las tres sigan vigentes seis meses después**, porque nadie
volvió a abrir la carpeta. Por eso lo que importa de las entradas externas no es
registrarlas: es que el motor **no deje olvidar** lo que ponen en duda.

### Registrar una

Siguiendo el caso de la tienda de la sección 13. Tras la reunión con el equipo del sistema
de ventas:

```bash
python "$IEF/verify_frame.py" --mode record-input \
    --source "Reunion con el equipo del sistema de ventas" \
    --kind meeting \
    --date 2026-09-08 \
    --summary "Desde marzo, las ventas de mostrador se registran sin cliente a proposito" \
    --file "admin/acta_2026-09-08.md" \
    --invalidates RUL-002-001
```

```
[ENTRADA] EXT-001  Desde marzo, las ventas de mostrador se registran sin cliente a proposito
          initiative\specs\inputs.yml
          Ya se puede citar como evidencia: `evidence: [EXT-001]`

  Declara que invalida RUL-002-001, pero NO las ha tocado.
  Anotar un hecho es gratis; cambiar lo que gobierna el proyecto lleva
  firma. `doctor` te lo recordara hasta que alguien decida:
    - reemplazarlas con una regla que declare `supersedes`, o
    - descartar la entrada si al mirarla no era para tanto.
```

### Qué guarda

| Campo | Flag | Obligatorio | Nota |
|---|---|---|---|
| `id` | — | — | Se asigna solo: `EXT-001`, `EXT-002`… |
| `date` | `--date` | No | Por defecto, hoy. Pon la fecha **del hecho**, no la de hoy |
| `source` | `--source` | **Sí** | Sin saber de dónde viene, un hecho no es evidencia de nada |
| `kind` | `--kind` | No | `meeting` (por defecto) · `document` · `dataset` · `decision` · `correspondence` |
| `summary` | `--summary` | **Sí** | Qué dice, en una frase |
| `artifacts` | `--file` | No | El acta o el documento. Se **enlaza**, no se copia; varios, separados por comas |
| `invalidates` | `--invalidates` | No | Reglas del proyecto que esto pone en duda. Deben existir |

Queda en `initiative/specs/inputs.yml` y como evento `RECORD_INPUT` en el historial.

### La deuda que abre `--invalidates`

**Registrar una entrada no toca ninguna regla.** Es deliberado: anotar un hecho es gratis,
pero cambiar lo que gobierna el proyecto lleva firma, y la entrada no decide por ti.

Lo que sí hace es abrir una deuda que `doctor` trata como **problema, no como aviso**:

```
$ verify_frame.py --mode doctor

[DOCTOR] Tienda

  FAIL  EXT-001 (2026-09-08) dice que invalida RUL-002-001, y RUL-002-001 sigue activa. Reemplazala con una regla que declare `supersedes: RUL-002-001`, o retira esa linea de la entrada si al mirarla no era para tanto

1 problema(s), 0 aviso(s)
```

Y `explain` la muestra como pendiente:

```
$ verify_frame.py --mode explain --input EXT-001

  EXT-001
  ======================================================================
  Desde marzo, las ventas de mostrador se registran sin cliente a proposito

  fecha     : 2026-09-08
  procede de: Reunion con el equipo del sistema de ventas
  tipo      : meeting
  documento : admin/acta_2026-09-08.md

  QUE PONE EN DUDA
    RUL-002-001    SIGUE ACTIVA  <- pendiente de resolver

  QUE SE APOYA EN ELLA
    ninguna regla la cita todavia
```

### Cerrar la deuda: dos salidas, las dos de una persona

**1. Reemplazar la regla.** Se abre un incremento, se propone una regla que declara
`supersedes` y cita la entrada como evidencia:

```yaml
- id: RUL-003-001
  statement: "Un pedido sin cliente se clasifica como venta de mostrador"
  rationale: "Confirmado por el equipo del sistema de ventas: es un registro intencional"
  applies_to: "pedidos.sin_cliente"
  supersedes: RUL-002-001
  evidence: [EXT-001]
```

Se promueve, y la deuda se cierra sola:

```
[MERGE] 003_ventas_de_mostrador -> initiative\specs
        rules.yml: +1 promovidas, ~1 superadas, 3 vigentes

$ verify_frame.py --mode doctor
  Sin hallazgos. 3 incremento(s), 0 activo(s).

$ verify_frame.py --mode explain --input EXT-001
  QUE PONE EN DUDA
    RUL-002-001    ya superseded

  QUE SE APOYA EN ELLA
    RUL-003-001
```

**2. Retirar la acusación.** Si al mirarlo con calma resulta que la reunión no invalidaba
la regla, se quita la línea de `invalidates` de la entrada. Hoy eso se hace **editando
`inputs.yml`**: no hay un comando para retirar una entrada (ver sección 29).

Ninguna de las dos la decide un agente. Si trabajas con uno, lo correcto es que te enseñe
la entrada y lo que pone en duda, y espere.

### Citar una entrada como evidencia

Una entrada se cita igual que un test:

```yaml
evidence: [EXT-001, TST-ACC-004]
```

Hay hechos que no se demuestran con un `assert`. «El sistema de origen cambió el formato
en marzo» se demuestra con **quién lo dijo y cuándo**, y eso es exactamente lo que registra
una entrada. El motor comprueba que la entrada citada exista, igual que con los tests.

### Cuándo registrar una y cuándo no

| Situación | ¿Entrada externa? | Tipo |
|---|---|---|
| Una reunión cambia un supuesto del proyecto | **Sí** | `meeting` |
| Una reunión de seguimiento sin novedades | No. Si acaso, una línea en `log` | — |
| Llega un dataset con una advertencia sobre sus columnas | **Sí** | `dataset` |
| Tu profesor guía o tu cliente decide acotar el alcance | **Sí** | `decision` |
| Un correo retira el acceso a una fuente | **Sí** | `correspondence` |
| Un documento técnico del proveedor contradice tu contrato de datos | **Sí** | `document` |
| Hiciste un gráfico para una reunión | No: eso es trabajo tuyo, va a `log` | — |

> **Una pista para proyectos que ya estaban en marcha.** Si el proyecto tiene actas de
> reunión en su carpeta de `admin` y ninguna entrada registrada, es muy probable que haya
> deuda invisible ahí dentro: afirmaciones que alguna reunión tumbó y que siguen rigiendo.

## 16. Criterios de aceptación ejecutables

### El problema

El paso 5 produce `acceptance-tests.yml`: criterios escritos como *dado / cuando /
entonces*, cada uno con un campo `status`. Durante mucho tiempo ese campo se actualizaba
**a mano**. Nada conectaba el documento con código que se ejecutara, así que un criterio
podía decir `passing` sin que nadie hubiera corrido nada.

Es la garantía 3 (sección 3) en su forma más concreta: **un criterio que no se puede
ejecutar no cuenta como criterio.**

### Cómo es un criterio

```yaml
tests:
  - id: "TST-ACC-001"
    linked_rule: "RUL-001-001"        # qué regla comprueba: trazabilidad obligatoria
    scenario: "El pipeline termina sin errores"
    given: "El extracto crudo del mes"
    when: "Se ejecuta el pipeline de limpieza"
    then: "Termina con código 0"
    status: "pending"                 # pending | passing | failing | blocked
    verify:                           # CÓMO se comprueba. Sin esto, falla.
      kind: command
      run: "python pipelines/limpiar.py"
      expected_exit_code: 0
```

Tres reglas del paso 5 que conviene conocer:

- **Cada test apunta a una regla** (`linked_rule`). Un test sin regla no sabe qué protege.
- **Cada regla tiene al menos un test.** Una regla sin test es una intención.
- Las reglas de prioridad `critical` o `high` necesitan además tests de **casos límite**:
  qué pasa con el valor vacío, con el extremo, con el dato malformado.

### Las tres formas de `verify`

**`command`** — ejecuta un comando; éxito es el código de salida esperado.

```yaml
verify:
  kind: command
  run: "python pipelines/evaluar.py"
  expected_exit_code: 0
```

**`python`** — llama a una función importable que devuelve `True` o `False`.

```yaml
verify:
  kind: python
  callable: "mi_paquete.checks:nulos_bajo_umbral"
```

**`metric`** — compara una métrica guardada en un JSON contra un umbral. Es la forma
natural para análisis y modelos:

```yaml
verify:
  kind: metric
  report: "reports/metrics/evaluacion.json"
  path: "validacion.recall"            # ruta con puntos dentro del JSON
  op: ">="                             # >=  >  <=  <  ==  !=
  value: 0.80
```

Y una salida honesta para lo que todavía no se puede medir: `status: blocked` con un
`blocked_reason`. Se traduce en un test **omitido** (`pytest.skip`), no aprobado.

### Compilar y ejecutar

```bash
python "$IEF/compile_acceptance_tests.py" --project-dir . \
    --increment 001_pipeline_de_limpieza --out tests/generated/
pytest tests/generated/ -v
```

Ejecutado con dos criterios, uno con `verify` y otro sin él:

```
[COMPILE] 2 criterio(s) -> tests\generated\test_acceptance_001_pipeline_de_limpieza.py
          1 SIN bloque `verify`, fallaran hasta declararlo:
            - TST-ACC-002
```

```
E       Failed: TST-ACC-002 no declara `verify`: es prosa, no un criterio verificable.
E       Agrega un bloque verify (kind: command | python | metric) o marca el test como status: blocked con su razon.

1 failed, 1 passed in 0.80s
```

El criterio con `verify` pasa. El que es prosa **falla, y dice por qué**. Esa es la regla:
un criterio sin forma de verificarse no se cuela como aprobado.

Cada función generada lleva en su docstring el id del test, la regla que protege y el
*dado / cuando / entonces*, y queda marcada con `@pytest.mark.ief`, así que puedes correr
solo los criterios del IEF con `pytest -m ief`.

### En integración continua

```bash
python "$IEF/compile_acceptance_tests.py" --project-dir . --increment <slug> --check
```

`--check` no escribe nada: **falla si el archivo generado ya no coincide** con el YAML. Así
se detecta que alguien cambió los criterios y no volvió a compilar.

### Qué hace bueno a un criterio

| Malo | Bueno |
|---|---|
| «El modelo debe ser preciso» | `validacion.recall >= 0.80` sobre el conjunto de validación congelado |
| «Los datos deben estar limpios» | Ninguna columna con más del 1% de nulos tras el pipeline |
| «Debe ser rápido» | El pipeline completo termina en menos de 10 minutos con el extracto mensual |

La diferencia no es de estilo: el de la izquierda no se puede ejecutar, así que se
«cumple» siempre. Y un criterio que se cumple siempre no protege de nada.

## 17. Cuando algo sale mal

### Volver atrás: `rewind`

Descubres en el paso 3 que la hipótesis del paso 1 estaba mal planteada. No se parchea el
trabajo para que quepa: **se retrocede**, explícitamente y dejando constancia.

```bash
python "$IEF/verify_frame.py" --mode rewind --to-step 1 \
    --reason "la hipotesis estaba mal planteada"
```

`--reason` es obligatorio: el retroceso queda en el historial. `--increment <slug>` elige
sobre qué incremento se retrocede; sin él, cae sobre el foco.

Lo que dice el motor, **antes** de hacerlo:

```
  Este retroceso marca NEEDS_REVISION en 2 pasos, no solo en el 1:
    1    Hipotesis y Alcance          APPROVED -> NEEDS_REVISION
    2    Exploracion de Datos         IN_PROGRESS -> NEEDS_REVISION
  Su trabajo se apoyaba en lo que vas a revisar.

[REWIND] 2 -> 1: Hipotesis y Alcance
         marcados NEEDS_REVISION: 1, 2
         razon: la hipotesis estaba mal planteada
         este paso vuelve a requerir aprobacion humana
```

Tres cosas que conviene entender:

**Retroceder arrastra lo que venía después.** Retroceder al paso 1 marca el 1 **y todos
los posteriores que tenían trabajo**. No es un efecto secundario: ese trabajo se apoyaba en
lo que ahora vas a revisar, y darlo por bueno sería peor. El motor lo anuncia antes, con el
estado del que viene cada paso, para que sepas cuánto estás reabriendo.

**Una firma retrocedida se pierde.** El paso 1 estaba `APPROVED`; ahora está
`NEEDS_REVISION` y **vuelve a necesitar aprobación**. Si cambias la hipótesis, la
aprobación anterior ya no vale: se aprobó otra cosa.

**Cómo se sigue.** Se rehace cada paso en orden: se corrige el artefacto, `complete-step`,
`approve-step` si lleva compuerta, `advance`. Igual que la primera vez.

> **Antes de retroceder, mira los artefactos de los pasos que vas a arrastrar.** Si alguno
> no pasa la validación del motor (el caso de abajo), no podrá volver con
> `complete-step`, y el retroceso te habrá dejado atascado.

### Un artefacto que el motor no entiende

Este es el caso que peor sienta la primera vez, porque parece que el framework te
bloquea sin salida.

El paso 3 de un `build` produce `data-contract.yml`, y el motor valida su forma: conoce dos
formas genéricas (`schemas[].fields[]` y `sources[].columns[]`). Si tu contrato está bien
hecho pero organizado de otra manera —por capas del dominio, por ejemplo— el motor no lo
reconoce:

```
$ verify_frame.py --mode verify-step

[VERIFY] 001_pipeline · paso 3: Esquema de Datos

  PASS  [Artefacto] data-contract.yml existe
  PASS  [Artefacto] data-contract.yml es YAML valido
  FAIL  [Estructura] data-contract.yml estructura valida (no reconocida: ni `schemas[].fields[]` ni `sources[].columns[]`. Si la forma es del dominio, declara `structure: free` en el paso del preset)
```

Y como `complete-step` verifica antes de marcar, y `advance` exige el paso terminado, las
tres puertas se cierran a la vez. En una versión anterior del motor, la única salida era
editar `state.yml` a mano: justo lo que el framework prohíbe. Ahora el error enseña las dos
salidas legítimas:

```
$ verify_frame.py --mode complete-step

ERROR: el paso 3 no se puede dar por terminado:
       - data-contract.yml estructura valida (no reconocida: ...)

       Si el artefacto es correcto y quien no lo entiende es el motor,
       aceptalo de forma explicita y quedara registrado:
         --mode complete-step --step 3 --force \
             --reason "por que este artefacto vale igual"

       No uses --force para saltarte trabajo que falta de verdad.
```

#### Salida 1: `structure: free` — la limpia

Un paso del preset puede declarar que la forma de su artefacto **es del dominio**. Entonces
el motor comprueba que el archivo existe y es YAML legible, y no opina de su organización:

```yaml
- key: "2b_data_contract"
  ref: "2b"
  artifact: "data-contract.yml"
  structure: free
```

El paso 2b de `exploration` ya lo trae declarado en todos los presets: el contrato de una
exploración formaliza lo que se encontró, y eso es del dominio. El paso 3 de `build` **no**
lo trae, a propósito: allí el contrato gobierna un pipeline que alguien va a mantener, y la
forma genérica es lo que permite comprobarlo.

Declararlo en otro paso es modificar un preset, y eso es trabajo de la skill
`ief-authoring` (sección 28), no del proyecto.

#### Salida 2: `--force` — la de emergencia

Acepta un artefacto que no valida. Exige motivo:

```
$ verify_frame.py --mode complete-step --force

ERROR: --force exige --reason: hay que poder saber despues por que se acepto un artefacto que no valida
```

```
$ verify_frame.py --mode complete-step --force \
    --reason "el contrato va por capas del dominio; el esquema tabular llega en el paso 6"

  [FORZADO] el paso 3 se acepta pese a 1 comprobacion(es) fallida(s):
            - data-contract.yml estructura valida (no reconocida: ...)
            motivo: el contrato va por capas del dominio; el esquema tabular llega en el paso 6
[COMPLETED] paso 3: Esquema de Datos
            --mode advance para pasar al siguiente
```

Queda escrito en el incremento (campo `forced_steps`, con el motivo, la fecha y **qué
comprobaciones fallaron**), y `doctor` lo recuerda mientras el incremento siga abierto:

```
$ verify_frame.py --mode doctor

  WARN  001_pipeline paso `3_data_contracts` se acepto con --force el 2026-09-10: el contrato va por capas del dominio; el esquema tabular llega en el paso 6
```

Un paso forzado **nunca vuelve a parecer un paso normal**. Esa es la condición que hace
aceptable tener una salida de emergencia.

#### Cuál usar

| Situación | Qué hacer |
|---|---|
| El artefacto está bien y su forma es estable y propia del dominio | `structure: free` en el preset |
| El artefacto está bien, pero es un caso aislado | `--force --reason` |
| El artefacto está incompleto | **Ninguna de las dos.** Termínalo |

> **`--force` no sirve para saltarse trabajo que falta de verdad.** Es para cuando el
> artefacto está bien y quien no lo entiende es el motor. Si lo usas porque el archivo
> está a medias, has convertido el estado en una ficción, y todo el ciclo posterior confía
> en él. Ante la duda, no fuerces: pregunta.

`--force` sobre un paso que **sí** valida no hace nada especial: se completa normalmente y
no deja marca.

### Pausar, retomar, abandonar

**Pausar** (voluntario):

```bash
python "$IEF/verify_frame.py" --mode set-status --increment 002_x --status PAUSED \
    --reason "cambio de prioridad: primero el informe de avance"
```

**Retomar**, y de paso moverle el foco:

```bash
python "$IEF/verify_frame.py" --mode set-status --increment 002_x --status ACTIVE --focus
```

Si las reglas del proyecto cambiaron mientras estaba parado, el motor te avisa (sección
12, `rules_base`). Revisa el charter antes de seguir.

**Abandonar**:

```bash
python "$IEF/verify_frame.py" --mode set-status --increment 004_x --status ABANDONED \
    --reason "la hipotesis no se sostuvo: el criterio de exito quedo lejos"
```

Abandonar no borra nada. Antes de hacerlo, genera el informe con `draft-report` y escribe
**por qué** se abandona. Un incremento abandonado con un buen informe es de lo más valioso
que produce un proyecto: evita que alguien lo repita dentro de seis meses.

### Un estado que viene de una versión anterior del IEF

Si abres un proyecto empezado con una versión anterior, el motor puede no entender parte
de su `state.yml`: estados que ya no existen, claves de paso renombradas, un preset que se
eliminó. Lo primero es `doctor`, que lista exactamente qué está mal (sección 18).

Corregirlo es la **única** excepción a «`state.yml` no se edita a mano», y se hace **una
sola vez**. Si te encuentras editándolo una segunda vez, has cogido el camino equivocado.

## 18. `doctor`, pieza por pieza

### Para qué sirve

`status` muestra **lo que hay**. `doctor` muestra **lo que está mal**: una dependencia
imposible, un bloqueo que nadie mira desde hace tres meses, una regla que una reunión tumbó
y sigue rigiendo, un paso con compuerta que alguien dio por terminado sin firma.

```bash
python "$IEF/verify_frame.py" --mode doctor
```

Distingue dos niveles:

- **`FAIL`** — un problema. El comando termina con código de error, así que sirve en
  integración continua.
- **`WARN`** — un aviso. Algo que conviene mirar, pero que no impide trabajar.

Cuándo ejecutarlo: **lo primero** al llegar a un proyecto que no abriste tú, **lo último**
antes de cerrar una sesión de trabajo, y **siempre** en integración continua.

Un proyecto sano responde así:

```
[DOCTOR] Tienda

  Sin hallazgos. 3 incremento(s), 0 activo(s).
```

### Todo lo que revisa

Se revisa en este orden, y el orden importa: primero el propio archivo, porque si el
estado está roto, lo demás se diagnostica sobre arena.

#### A. El propio `state.yml`

| Comprueba | Nivel | Qué significa | Cómo se arregla |
|---|---|---|---|
| `schema_version` distinto del que escribe el motor | WARN | El archivo viene de una versión anterior del IEF | Migrarlo una vez |
| El foco apunta a un incremento que no existe | FAIL | Los comandos sin `--increment` no tienen sobre qué actuar | `--mode focus --increment <slug>` |
| Un incremento con un `status` que no existe | FAIL | El motor no sabe si está abierto o cerrado, y lo saca de los recuentos | Usar uno de los seis válidos |
| Un incremento de un ciclo que el preset no define | FAIL | Sus pasos no se pueden revisar | Corregir el `type` |
| Un paso con un estado que no existe | FAIL | Por ejemplo `DONE`, de una versión antigua | Usar uno de los cinco válidos |
| **Claves de paso que el ciclo no reconoce** | FAIL | Ver abajo: es la más cara | Renombrar la clave |
| Pasos del ciclo que el incremento no declara | WARN | Se asumen `PENDING` | Normalmente, nada |

Los mensajes tienen esta forma:

```
FAIL  <slug> tiene status `<X>`, que no existe. Validos: ACTIVE, PAUSED, BLOCKED, COMPLETED, MERGED, ABANDONED
FAIL  <slug> paso `<clave>` esta en `<X>`, que no existe. Validos: PENDING, IN_PROGRESS, COMPLETED, APPROVED, NEEDS_REVISION
FAIL  <slug> tiene claves de paso que el ciclo `<ciclo>` no reconoce: `<clave>`. El motor las ignora y da esos pasos por PENDING, aunque digan otra cosa
WARN  state.yml declara schema_version <viejo> y este motor escribe 4.0; el archivo viene de una version anterior del IEF
```

> **Por qué las claves huérfanas son lo más caro.** Cuando una clave de paso se renombra en
> una versión nueva del framework, el motor busca la clave nueva, no la encuentra, y da el
> paso por `PENDING` — **aunque el archivo diga `COMPLETED`**. Es trabajo hecho que
> desaparece sin que nada avise. Ya pasó dos veces durante el desarrollo del IEF, y por
> eso `doctor` lo busca expresamente.

Antes de que existiera esta revisión, `doctor` respondía «Sin hallazgos» ante un
`state.yml` lleno de estados inexistentes: diagnosticaba todo menos el archivo del que vive.

#### B. Firmas y excepciones

| Comprueba | Nivel | Mensaje |
|---|---|---|
| Un paso **con compuerta** en `COMPLETED` sin aprobar | FAIL | `<slug> paso <ref> (<nombre>): COMPLETED sin aprobar` |
| Un paso aceptado con `--force`, en un incremento abierto | WARN | `<slug> paso <clave> se acepto con --force el <fecha>: <motivo>` |
| Una entrada externa que invalida una regla que sigue activa | **FAIL** | `EXT-001 (<fecha>) dice que invalida RUL-X, y RUL-X sigue activa...` |

La primera merece una nota: un paso con compuerta **terminado pero sin firmar** es justo el
estado en que un trabajo se da por aprobado sin que nadie lo haya aprobado. Por eso es
`FAIL` y no aviso.

#### C. Frentes y bloqueos

| Comprueba | Nivel | Mensaje |
|---|---|---|
| Dependencia circular entre incrementos | FAIL | `dependencia circular: A -> B -> A` |
| Bloqueado por un incremento que no existe | FAIL | `<slug> esta bloqueado por <otro>, que no existe` |
| La fecha esperada de desbloqueo ya pasó | WARN | `<slug>: la fecha esperada (<fecha>) ya paso` |
| Bloqueado hace más de 30 días | WARN | `<slug> lleva N dias bloqueado. Sigue vivo o se abandona?` |
| Más incrementos `ACTIVE` que `max_active` | WARN | `N incrementos ACTIVE (limite blando 3): ...` |
| Todos los incrementos abiertos están detenidos | FAIL | `los N incremento(s) abiertos estan detenidos...` |
| El incremento con foco declara otra rama de git | WARN | `<slug> (enfocado) declara la rama X pero estas en Y` |
| Hay trabajo abierto y ningún foco | WARN | `hay incrementos abiertos y ningun foco: --mode focus --increment <slug>` |

«Todos detenidos» es `FAIL` porque es fácil no darse cuenta: cada bloqueo se decidió por
separado, con semanas de diferencia, y un día el proyecto entero está parado sin que nadie
lo haya decidido.

#### D. Reglas y olvidos

| Comprueba | Nivel | Mensaje |
|---|---|---|
| Un incremento abierto se construyó sobre reglas que ya cambiaron | WARN | `<slug> se construyo sobre reglas que ya cambiaron; revisa su charter` |
| Un incremento `COMPLETED` sin promover | WARN | `<slug> esta COMPLETED pero sus reglas no se han promovido (--mode merge-increment)` |

### `doctor` como lista de tareas

En un proyecto heredado, la salida de `doctor` es literalmente la lista de lo que hay que
arreglar, en orden de gravedad. Y es también la verificación: **cuando `doctor` calla,
has terminado.**

## 19. Informes

### El borrador que escribe el motor: `draft-report`

El último paso de casi todos los ciclos produce `increment-report.md`. Buena parte de lo
que va ahí **ya lo sabe el motor**: qué pasos se hicieron, quién firmó cada compuerta y
cuándo, qué reglas se propusieron, qué criterios se declararon. Pedirle a una persona que
lo transcriba a mano es pedirle trabajo de copista, y el trabajo de copista se hace mal:
se omiten cosas y se ponen fechas de memoria.

```bash
python "$IEF/verify_frame.py" --mode draft-report                     # el foco
python "$IEF/verify_frame.py" --mode draft-report --increment 003_x   # uno concreto
```

```
[BORRADOR] initiative\increments\001_pipeline_de_limpieza\increment-report.md
           Los datos ya estan. Escribe los aprendizajes y la deuda:
           son la parte que ningun motor puede rellenar por ti.
```

### Lo que rellena solo

Del borrador real de un `build` a medio camino:

```markdown
## Recorrido

| Paso | Estado | Aprobado por | Artefacto |
|---|---|---|---|
| 1. Hipotesis y Alcance | APPROVED | Ana Perez (2026-09-10) | `charter.md` |
| 2. Exploracion de Datos | IN_PROGRESS | — | `inspection-report.md`  (ausente) |
| 3. Esquema de Datos | PENDING | — | `data-contract.yml`  (ausente) |
| 4. Reglas del Modelo | PENDING | — **falta** | `rules.yml`  (ausente) |
| 5. Criterios de Evaluacion | PENDING | — **falta** | `acceptance-tests.yml` |

## Criterios de aceptacion

| Test | Regla | Estado | Verificable |
|---|---|---|---|
| `TST-ACC-001` | `RUL-001-001` | pending | si |
| `TST-ACC-002` | `RUL-001-002` | pending | **no** — sin bloque `verify` |
```

Fíjate en tres señales que pone por su cuenta:

- **`(ausente)`** — el paso declara un artefacto que no está en disco.
- **`— falta`** — un paso con compuerta que todavía no tiene firma.
- **`no — sin bloque verify`** — un criterio que es prosa (sección 16).

Si el incremento propuso reglas, también aparecen con su motivo, lo que reemplazan y lo
que las sostiene, y las decisiones que quedaron abiertas.

### Lo que deja en blanco, a propósito

```markdown
## Aprendizajes

Esta es la parte que no sale de ningun archivo y la unica que servira dentro de
un ano. Responde en concreto; "todo bien" no es un aprendizaje.

**Que salio mejor de lo esperado, y por que.**

**Que costo mas de lo previsto.** Si algo tardo el triple, di que era.

**Que harias distinto en el proximo incremento.**

**Que supuesto resulto falso.** De los que diste por buenos al empezar, cual se
cayo al mirar los datos o al implementar.

## Deuda que queda
```

Los aprendizajes salen **como preguntas**, no como huecos que se rellenan solos. Eso no lo
puede escribir una máquina, y **fingir que sí es peor que dejar el hueco**: un informe con
aprendizajes inventados se lee como si tuviera aprendizajes. Es la garantía 1 aplicada a
un informe.

`draft-report` **se niega a pisar un informe ya escrito**. Para reemplazarlo hace falta
`--force-overwrite`, explícito y a propósito.

### Informes de avance y el documento largo

`draft-report` cubre el informe de **un incremento**. Los otros dos tipos de informe
tienen su propio rol, y conviene no mezclarlos:

| Tipo | Rol | Cadencia | Ejemplo |
|---|---|---|---|
| Informe de incremento | dentro del incremento | Uno por incremento | `increment-report.md` |
| Avance | `avances` | Frecuente, corto | El resumen quincenal para el profesor guía |
| Entregable | `documento` | Uno, largo, crece todo el proyecto | La memoria, la tesis, el informe final |

Un avance típico se construye **citando** incrementos y reglas: «esta quincena se cerró
el 004; rigen RUL-004-001 y RUL-004-002; la entrada EXT-002 invalidó una afirmación del
capítulo 3». Si el avance dice algo que no se puede rastrear hasta un incremento, una
regla o una entrada, conviene preguntarse de dónde salió.

---

## 20. Adoptar un proyecto que ya existe

### El problema

`init` da por hecho un proyecto que nace con el framework: crea sus carpetas desde cero.
En un proyecto que lleva meses en marcha, eso construye una estructura **paralela** a la
que ya hay: acabas con `datos_crudos/` **y** `data/raw/`, y ninguna de las dos es la
buena.

Pedirle a un proyecto que renombre sus carpetas para entrar al framework es pedirle que
reorganice su trabajo para complacer a una herramienta. `adopt` invierte la dirección:
**descubre las rutas en vez de imponerlas.**

### Primero propone

Proyecto de prueba con carpetas `notebooks/`, `datos_crudos/`, `salidas/`, `src/`,
`documentacion/` y `cosas_raras/`:

```
$ verify_frame.py --mode adopt --preset analysis

[ADOPT] guia_adopt  ·  preset `analysis`
        Nada se mueve: solo se registra donde esta cada cosa.

  Carpetas reconocidas:
    src                      -> codigo
    notebooks                -> exploracion
    datos_crudos             -> datos_raw
    salidas                  -> resultados

  Roles del preset sin carpeta (se crearan con el nombre del layout):
    tests                       Pruebas, incluidos los criterios de aceptaci
    scratch                     Playground. Nada de aqui sobrevive al increm
    referencias                 Papers, bibliografia, documentacion externa,
    datos_interim               Pasos intermedios, reproducibles desde raw.
    datos_processed             Conjuntos listos para usar, reproducibles po
    avances                     Reportes cortos y periodicos: quincenales, d
    presentaciones              Decks, posters, defensas y material compleme

  Reconocidas, pero el preset `analysis` no usa esos roles:
    documentacion            -> documento
    Si las necesitas, quiza el preset que buscas es otro, o el rol
    puede anadirse al preset (ver la skill `ief-authoring`).

  Carpetas que no supe clasificar (se dejan como estan, intactas):
    cosas_raras

  Esto es una propuesta. Revisala y, si te cuadra, repite con --yes.
```

Cuatro listas, y **la última es la que más importa**: lo que no se entiende se dice, no se
ignora. Una herramienta que calla lo que no supo clasificar te deja creyendo que lo revisó
todo.

La tercera lista también enseña algo: `documentacion/` se reconoció como el rol
`documento`, pero `analysis` no usa ese rol. Si tu proyecto sí tiene un entregable largo,
quizá el preset que buscas es `research`.

### Luego aplica

```
$ verify_frame.py --mode adopt --preset analysis --yes

  Adoptado. 4 carpeta(s) existentes reconocidas, 8 creada(s).
    nueva: initiative
    nueva: tests
    nueva: scratch
    nueva: references
    nueva: data/interim
    nueva: data/processed
    nueva: reports/progress
    nueva: presentations
```

Carpetas después: las seis originales siguen **exactamente donde estaban**, más las que
faltaban.

### Qué garantiza

- **No mueve, renombra ni borra ningún archivo.** Nunca, ni con `--yes`.
- Guarda el mapa en `initiative.role_paths` (sección 7), que tiene prioridad sobre el
  layout: el motor escribirá en `datos_crudos/`, no en `data/raw/`.
- Solo crea las carpetas de roles que el preset necesita y no existen.
- **Se niega si el proyecto ya tiene `state.yml`**: para eso ya está `init`, y adoptar
  dos veces pisaría el estado.

---

## 21. El trabajo pequeño: `log`

### Para qué

Para trabajo real que **no justifica un incremento**: un gráfico para una reunión, un
resumen, un arreglo de diez minutos. Nadie lo mantiene, no cambia ninguna regla.

Pero dentro de seis meses alguien encontrará ese PNG en una carpeta y no sabrá de dónde
salió. Una línea lo responde, y cuesta cinco segundos.

```bash
python "$IEF/verify_frame.py" --mode log \
    --message "grafico de nulos por columna para la reunion con el profesor" \
    --output "reports/figures/nulos.png" \
    --from "notebooks/02_nulos.ipynb"
```

```
[LOG] grafico de nulos por columna para la reunion con el profesor
      initiative\worklog.md
```

Y en `initiative/worklog.md`:

```markdown
- **2026-09-10** — grafico de nulos por columna para la reunion con el profesor
  - salida: `reports/figures/nulos.png`
  - desde: `notebooks/02_nulos.ipynb`
```

`--message` es obligatorio: la anotación **es** el contenido. `--output` y `--from` son
opcionales, pero son justo lo que responde «¿de dónde salió esto?». No crea incrementos,
no mueve el foco y no pide firma a nadie. Queda como evento `LOG` en el historial.

### Cuándo deja de ser un `log`

El propio `worklog.md` lo dice en su cabecera:

> Si algo de aquí empieza a crecer, a ser citado o a cambiar una regla del proyecto,
> deja de pertenecer a esta lista: ábrele un incremento.

La bitácora es para lo que nace y muere pequeño. Si la usas para saltarte el proceso, se
convierte en un vertedero donde nadie encuentra nada.

### `log` no es `record-input`

Se confunden porque los dos son una línea con fecha. Pero:

| | `log` | `record-input` (sección 15) |
|---|---|---|
| Registra | **Trabajo que hiciste** | **Un hecho que te llegó de fuera** |
| Ejemplo | «Hice el gráfico de nulos» | «El proveedor cambió el formato en marzo» |
| Tiene id | No | Sí: `EXT-001` |
| Se cita como evidencia | No | Sí |
| Puede invalidar reglas | No | Sí, y `doctor` lo vigila |

Si una reunión cambió lo que el proyecto sabe, no va a la bitácora: va a `record-input`.

---
---

# Parte III — Casos de uso

Cuatro proyectos contados de principio a fin. Cada uno ejercita piezas distintas; léelos
aunque tu proyecto se parezca solo a uno, porque los errores que evitan se repiten en todos.

---

## 22. Una memoria de título, de la primera semana a la defensa

**El proyecto:** una memoria sobre la calidad del aire en una ciudad, con datos de
estaciones de medición públicas. Una estudiante, un profesor guía, un año.

**Preset y layout:** `research` con `numbered`, porque la universidad espera carpetas
ordenadas y el entregable es un documento defendible.

### Semana 1 — Arranque

```bash
python "$IEF/verify_frame.py" --mode init --preset research --layout numbered \
    --initiative-name "Calidad del aire urbana"
```

Antes de abrir nada, **la constitución**. Tres principios bastan para empezar:

- **P1 — Ninguna cifra sin comando.** Todo número que aparezca en la memoria sale de un
  script que se puede volver a ejecutar.
- **P2 — Los datos de las estaciones son de solo lectura.** Nunca se corrigen en el sitio;
  toda limpieza vive en el pipeline.
- **P3 — Un resultado negativo va a la memoria.** Si un modelo no supera la línea base, se
  cuenta.

Y el material de entrada en `01_inicio/`: qué es el proyecto, dónde están los datos, cómo se
corre todo. Parece prematuro en la semana 1. No lo es: tu yo de dentro de seis meses es un
recién llegado.

### Semanas 1–2 — La primera exploración

Todavía no hay nada que construir: hay que mirar los datos.

```bash
python "$IEF/verify_frame.py" --mode new-increment --type exploration \
    --name "Calidad de las estaciones"
```

Los cuatro pasos:

1. **`objective.md`** — la pregunta y **cuándo se da por respondida**: «¿Qué estaciones y
   qué periodos son usables? Se cierra cuando cada estación tenga un veredicto».
2. **`analysis.md`** — lo que se hizo: notebooks en `04_codigo/notebooks/`, figuras en
   `06_resultados/figuras/`.
3. **`data-contract.yml`** (2b) — la formalización de lo encontrado. En una exploración su
   forma es libre, así que puede organizarse por estación, por contaminante o como el
   dominio pida.
4. **`findings.md`** — los hallazgos.

Cada paso: escribir el artefacto, `complete-step`, `advance`. No hay compuertas: explorar
no obliga a nadie a nada.

### Semana 2 — Los hallazgos que son reglas

Algunos hallazgos son solo observaciones («la estación 3 tiene más ruido»). Otros son
**verdades que van a condicionar todo lo que venga después**:

- Las lecturas negativas de PM2.5 son fallos del sensor, no mediciones.
- Las estaciones 4 y 7 comparten calibración con el resto.

Esas se escriben como reglas en el `rules.yml` de la exploración:

```yaml
rules:
  - id: RUL-001-001
    statement: "Una lectura negativa de PM2.5 es un fallo del sensor y se descarta"
    rationale: "Fisicamente imposible; aparecen en rafagas tras cortes de energia"
    applies_to: "lecturas.pm25.negativas"
    scope: increment
    status: proposed
  - id: RUL-001-002
    statement: "Todas las estaciones comparten la misma calibracion"
    rationale: "Asi lo indica la documentacion publica de la red"
    applies_to: "estaciones.calibracion"
    scope: increment
    status: proposed
```

Como la exploración no tiene compuertas, **al promover se pide firma**. En una memoria
firma la persona responsable del proyecto: tú. Pero antes de firmar reglas que van a
gobernar toda la memoria, conviene enseñárselas al profesor guía.

```bash
python "$IEF/verify_frame.py" --mode merge-increment --by "Tu Nombre"
```

Fíjate en que RUL-001-002 **no cita evidencia**: se apoya en la documentación nominal. Es
una deuda, y `explain` la mostrará como tal («nada declarado»).

### Semana 3 — La reunión que cambia las cosas

Reunión con la agencia municipal que gestiona la red. Dicen algo que nadie había escrito:
**las estaciones 4 y 7 se recalibraron en mayo.**

No es trabajo tuyo, así que no va a `log`. Es un hecho que llegó de fuera:

```bash
python "$IEF/verify_frame.py" --mode record-input \
    --source "Reunion con la agencia municipal de la red de monitoreo" \
    --kind meeting --date 2026-10-02 \
    --summary "Las estaciones 4 y 7 se recalibraron en mayo" \
    --file "00_admin/acta_agencia_2026-10-02.md" \
    --invalidates RUL-001-002
```

Desde este momento `doctor` falla hasta que alguien decida. Lo que se decide es abrir una
exploración pequeña para medir el efecto de la recalibración, que termina proponiendo:

```yaml
- id: RUL-002-001
  statement: "Las estaciones 4 y 7 se tratan como dos series distintas antes y despues de mayo"
  rationale: "La agencia confirmo la recalibracion; el salto medido en la mediana es de 3 ug/m3"
  applies_to: "estaciones.calibracion"
  supersedes: RUL-001-002
  evidence: [EXT-001]
```

Se promueve con firma, `doctor` vuelve a callar, y la regla vieja queda marcada como
superada **sin borrarse**.

### Cada dos semanas — Los avances

Un informe corto en `09_avances/` para el profesor guía. La costumbre que conviene tomar:
**cada afirmación del avance cita algo rastreable.**

> Esta quincena se cerró la exploración 002. Rige RUL-002-001 (las estaciones 4 y 7 se
> parten en mayo), que reemplaza a RUL-001-002 a raíz de la reunión con la agencia
> (EXT-001). Pendiente: el pipeline de agregación horaria.

Si una frase del avance no se puede rastrear hasta un incremento, una regla o una entrada,
conviene preguntarse de dónde salió.

### Mes 2 — El pipeline, con el ciclo completo

Ahora sí hay algo que otros capítulos van a usar durante meses: el pipeline que limpia y
agrega las lecturas por hora. Eso es un `build`:

```bash
python "$IEF/verify_frame.py" --mode new-increment --type build \
    --name "Pipeline de agregacion horaria"
```

Recorrido, con sus tres compuertas:

| Paso | Qué se escribe | Compuerta |
|---|---|---|
| 1. Hipótesis y Alcance | Qué hace el pipeline, qué **no** hace, cuándo se abandona | **Firma** |
| 2. Exploración de Datos | Qué hay en los datos que el pipeline va a tocar | — |
| 3. Esquema de Datos | El contrato, **con forma estricta** (`schemas[].fields[]`) | — |
| 4. Reglas del Modelo | «Una hora es válida si tiene al menos 45 minutos de lecturas» | **Firma** |
| 5. Criterios de Evaluación | Criterios ejecutables (ver abajo) | **Firma** |
| 6. Implementación | El código, en `04_codigo/pipelines/` | — |
| 7. Evaluación y Resultados | `draft-report` + aprendizajes | — |

Un criterio del paso 5, ejecutable:

```yaml
- id: TST-ACC-001
  linked_rule: RUL-003-001
  scenario: "Ninguna hora valida tiene menos de 45 minutos de lecturas"
  given: "El dataset agregado"
  when: "Se cuentan los minutos de cada hora marcada como valida"
  then: "Todas tienen al menos 45"
  verify:
    kind: python
    callable: "calidad_aire.checks:horas_validas_completas"
```

Aquí, al promover, **no se pide firma extra**: el paso 4 ya la tuvo.

### Mes 3 — Un prototipo que no sale

Hipótesis: «un modelo lineal con la velocidad del viento predice el PM2.5 del día
siguiente mejor que la persistencia». Un `prototype`:

- Paso 1, **con firma**: la hipótesis y el criterio de éxito, **antes** de construir:
  «error absoluto medio al menos un 10% menor que la persistencia».
- Pasos 2–4: criterio ejecutable, construir, medir.

Resultado: un 3% mejor. No alcanza. **Un rechazo es un resultado** (P3 de la
constitución): se escribe el informe con `draft-report`, se contesta con honestidad qué
supuesto resultó falso, y el incremento se cierra como `ABANDONED` con su motivo. En la
memoria, esto es una sección entera, no un fracaso escondido.

### Durante todo el año — El documento

`07_documento/` crece en paralelo. Cada capítulo cita reglas y entradas por su id. Y antes de
entregar:

```bash
python "$IEF/verify_frame.py" --mode doctor       # nada pendiente
python "$IEF/verify_frame.py" --mode explain --rule RUL-002-001   # por cada regla citada
```

### La defensa

La pregunta que más teme cualquier estudiante: *«¿por qué excluyó esos datos?»*. Con el IEF
la respuesta no depende de la memoria:

```bash
python "$IEF/verify_frame.py" --mode explain --rule RUL-002-001
```

Qué dice la regla, por qué existe, qué reemplazó, y qué la sostiene —en este caso, una
reunión con fecha y acta—.

---

## 23. Un pipeline de datos en equipo

**El proyecto:** la ingesta de pedidos de una tienda hacia un almacén de datos. Dos
personas: **Ana**, que lidera y firma, y **Luis**, que desarrolla.

**Preset y layout:** `product` con `flat`, porque es un sistema que se despliega y alguien
va a mantener.

### La constitución del equipo

- **P1 — Los datos de origen son de solo lectura.**
- **P2 — Todo parámetro vive en `conf/`.** Ningún umbral en el código.
- **P3 — Nada se despliega con un criterio de aceptación en rojo.**

### El primer `build`, con una rama por incremento

```bash
git switch -c inc/001-ingesta
python "$IEF/verify_frame.py" --mode new-increment --type build \
    --name "Ingesta de pedidos" --branch inc/001-ingesta
```

**Quién hace qué en cada compuerta.** Luis escribe el charter y lo da por terminado; Ana
lo lee y lo aprueba:

```bash
# Luis
python "$IEF/verify_frame.py" --mode complete-step

# Ana, después de leerlo
python "$IEF/verify_frame.py" --mode approve-step --by "Ana"
python "$IEF/verify_frame.py" --mode advance
```

Si Luis ejecutara `approve-step --by "Ana"`, el motor no podría impedirlo: registra un
nombre, no verifica una identidad. **La compuerta funciona porque el equipo es honesto con
ella.** Por eso conviene que las firmas se revisen en el historial de vez en cuando.

### Un contrato con forma estricta

En un `build`, el contrato del paso 3 se valida. Esta es la forma que el motor reconoce:

```yaml
schemas:
  - name: pedidos
    fields:
      - name: pedido_id
        type: string
      - name: cliente_id
        type: string
        nullable: true
      - name: monto
        type: float
        min: 0
      - name: canal
        type: string
        enum: [web, tienda, telefono]
```

Cada esquema necesita `name` y `fields`; cada campo, `name` y `type`. Lo demás
(`nullable`, `min`, `enum`…) es tuyo.

### El segundo frente, bloqueado por otro equipo

Las devoluciones dependen de un extracto que prepara el equipo del sistema de gestión:

```bash
python "$IEF/verify_frame.py" --mode new-increment --type build --name "Devoluciones"
python "$IEF/verify_frame.py" --mode set-status --increment 002_devoluciones \
    --status BLOCKED --blocked-kind external --blocked-on "equipo del sistema de gestion" \
    --reason "esperando el extracto de devoluciones" --expected 2026-10-15
```

Mientras tanto, Luis no se queda parado. Un cambio pequeño en el tablero —un filtro por
región— es un `task`:

```bash
python "$IEF/verify_frame.py" --mode new-increment --type task \
    --name "Filtro por region en el tablero"
```

`status` enseña los tres frentes; el bloqueo muestra cuántos días lleva esperando, y
`doctor` avisará si pasa el 15 de octubre sin novedades.

### Un conflicto entre dos incrementos

Cuando llega el extracto, el incremento de devoluciones propone una regla sobre
`pedidos.monto` que contradice una del incremento 001. La promoción se detiene con
`[CONFLICTO]`. **No es un error que haya que hacer desaparecer:** es exactamente el aviso
que el equipo necesita. Ana y Luis deciden cuál manda; la nueva declara `supersedes`, y la
vieja queda marcada con su historia.

### Integración continua

Un proyecto en equipo debería comprobar en cada cambio lo mismo que comprueba una persona
disciplinada:

```yaml
# fragmento de un workflow de CI
- name: El estado del proyecto es coherente
  run: python "$IEF/verify_frame.py" --mode doctor

- name: Ninguna compuerta quedo sin firmar
  run: python "$IEF/verify_frame.py" --mode check-gates

- name: Los criterios compilados estan al dia
  run: python "$IEF/compile_acceptance_tests.py" --increment <slug> --check

- name: Los criterios pasan
  run: pytest -m ief
```

### Cuando llega alguien nuevo

A los seis meses se incorpora una tercera persona. En lugar de una semana de preguntas:

1. `docs/onboarding/` — qué es esto y cómo se corre.
2. `initiative/specs/constitution.md` — cómo se trabaja aquí.
3. `initiative/specs/rules.yml`, y `explain` sobre las reglas que no se entiendan.
4. `status` y `doctor` — qué está abierto y qué está mal.

---

## 24. Un análisis que termina en sistema

**El proyecto:** el área comercial pregunta por qué cae la recompra. Una analista.

**Preset:** `analysis`. El producto es una respuesta defendible; muchos análisis cortos, la
mayoría descartados, y un puñado que acaban en algo que alguien lee para decidir.

### Lo que no merece incremento

Los primeros días son gráficos rápidos para entender el problema. Ninguno se va a mantener
ni a citar:

```bash
python "$IEF/verify_frame.py" --mode log \
    --message "recompra mensual por canal, primer vistazo" \
    --output "reports/figures/recompra_canal.png" --from "notebooks/01_vistazo.ipynb"
```

### Una exploración

```bash
python "$IEF/verify_frame.py" --mode new-increment --type exploration \
    --name "Recompra por cohorte"
```

Hallazgo: la caída se concentra en clientes cuya primera compra tuvo una entrega lenta.
Es una **hipótesis**, no una conclusión.

### Un prototipo para ponerla a prueba

```bash
python "$IEF/verify_frame.py" --mode new-increment --type prototype \
    --name "El tiempo de entrega explica la caida"
```

La compuerta del paso 1 fija el criterio **antes** de mirar el resultado:

```yaml
verify:
  kind: metric
  report: "reports/metrics/prototipo_entrega.json"
  path: "diferencia_recompra_puntos"
  op: ">="
  value: 5
```

Resultado: 8 puntos de diferencia. La hipótesis se sostiene.

### El `build`: un indicador que se mantendrá

Ahora sí hay algo que el área comercial va a mirar cada semana: un indicador de riesgo de
no recompra. Un `build`. Y aquí aparece la particularidad de `analysis`: **su paso 4
(«Definiciones y Métricas») no lleva compuerta.**

El paso 4 fija la definición central:

```yaml
- id: RUL-003-001
  statement: "Un cliente esta en riesgo si no ha recomprado 60 dias despues de una entrega lenta"
  rationale: "El prototipo 002 mostro que la diferencia se abre a partir de los 45-60 dias"
  applies_to: "cliente.riesgo_no_recompra"
```

Como ningún paso con compuerta aprobó esa definición, **al promover se pide firma**:

```
ERROR: el ciclo `build` no tiene ninguna compuerta sobre las reglas, asi que
       nadie ha aprobado estas 1. Promoverlas las hace validas para
       todo el proyecto.
```

Es razonable. «60 días» va a decidir a qué clientes se les ofrece una compensación: alguien
del área comercial debería leerla antes de que rija.

### El informe

`draft-report` genera el recorrido y deja las preguntas. La que más importa en un análisis:
**«¿qué supuesto resultó falso?»**. Aquí, que la caída era general: era de un segmento.

---

## 25. Un modelo de aprendizaje automático

**El proyecto:** un modelo que anticipa qué clientes dejarán de comprar.

### Primero: `modeling` no se usa solo

`modeling` es un **mixin**: añade el paso de evaluación del modelo, pero no es un preset
completo. El motor lo rechaza tal cual:

```
$ verify_frame.py --mode init --preset modeling ...
ERROR: `modeling` es un mixin: no se usa solo. Componlo con un preset base, por ejemplo `extends: [analysis, modeling]`.

$ verify_frame.py --mode init --preset "analysis,modeling" ...
ERROR: no existe el preset `analysis,modeling`. Disponibles: analysis, generic, modeling, product, research
```

La composición **no se escribe en la línea de comandos**: se escribe en un preset. Y hoy
el bundle no trae ninguno que componga `modeling`, así que hay que crearlo. Es trabajo de la
skill `ief-authoring`, en el bundle, no en el proyecto:

```yaml
# presets/analysis-ml/preset.yml
id: analysis-ml
name: "Analisis con modelos"
description: "Analisis de datos que entrena y evalua modelos."
extends: [analysis, modeling]
```

Después, `check-preset` lo valida, y el proyecto se inicia con él:

```bash
python "$IEF/verify_frame.py" --mode check-preset --preset analysis-ml
python "$IEF/verify_frame.py" --mode init --preset analysis-ml --layout flat \
    --initiative-name "Prediccion de abandono"
```

### Lo que aporta el mixin

Tres roles —`config`, `modelos`, `experimentos`— y un paso nuevo en el ciclo `build`,
insertado justo después de la implementación:

| Ref | Clave | Artefacto | Compuerta |
|---|---|---|---|
| 6b | `6b_model_evaluation` | `model-card.md` | **sí** |

El paso 6b existe porque **«el pipeline funciona» y «el modelo generaliza» son preguntas
distintas.** Un modelo puede pasar todos los tests de integración y aun así no servir. Y
lleva compuerta porque publicar un modelo es una decisión, no un trámite.

### Los criterios, contra una línea base

Un modelo no se evalúa en el vacío: se evalúa contra algo más simple. El criterio del paso 5:

```yaml
- id: TST-ACC-002
  linked_rule: RUL-004-002
  scenario: "El modelo supera a la regla de negocio actual"
  given: "El conjunto de validacion congelado"
  when: "Se comparan modelo y regla actual"
  then: "El recall del modelo supera al de la regla en al menos 10 puntos"
  verify:
    kind: metric
    report: "experiments/evaluacion.json"
    path: "validacion.recall_sobre_linea_base"
    op: ">="
    value: 0.10
```

Las corridas quedan en `experiments/`, los modelos versionados en `models/` y cada
hiperparámetro en `conf/`.

### La model card

El artefacto del 6b es la **model card**: qué hace el modelo, con qué datos se entrenó, cómo
se evaluó, dónde falla y para qué **no** debe usarse. Es lo que se lee antes de firmar la
compuerta, y lo que se consulta cuando alguien quiere usar el modelo para algo distinto de
aquello para lo que se construyó.

---
---

# Parte IV — Referencia

## 26. Malentendidos frecuentes

Cada uno de estos ha causado un error real durante el desarrollo o el uso del IEF.

### «Preset» significa lo mismo que en spec-kit
**No.** En spec-kit, un preset reemplaza plantillas de comando. En el IEF, define el ciclo
de trabajo: pasos, compuertas, artefactos y vocabulario. Son conceptos sin relación que
comparten nombre (sección 2).

### Completar un paso es aprobarlo
**No.** `complete-step` dice «está hecho» y lo ejecuta quien hizo el trabajo. `approve-step`
dice «lo he leído y lo acepto» y lo ejecuta quien decide. En un paso con compuerta hacen
falta los dos (sección 10).

### Si el usuario me pidió que avanzara, puedo firmar por él
**No.** Pedir que se haga algo no es aprobar la compuerta de ese algo. Un agente nunca
escribe el nombre del usuario en `--by`: le enseña el artefacto y espera su firma
(sección 3).

### Una compuerta me impide seguir trabajando
**No.** Una compuerta detiene el **avance**, no el trabajo. Mientras esperas la firma
puedes adelantar lo que quieras; lo que no puedes es marcar el ciclo como avanzado.

### El incremento `ACTIVE` es el que tiene el foco
**No necesariamente.** Puede haber varios `ACTIVE`; el foco es uno. Los comandos sin
`--increment` actúan sobre el foco, no sobre «el activo» (sección 12).

### `--increment` funciona igual en todos los comandos
**No.** `approve-step` y `advance` lo aceptan pero **no lo leen**: actúan siempre sobre el
foco. Con `approve-step`, eso significa que una firma puede caer sobre el incremento
equivocado sin ningún error. Mueve el foco antes de aprobar o avanzar (secciones 27 y 29).

### `PAUSED` y `BLOCKED` son lo mismo
**No.** `PAUSED` es voluntario; `BLOCKED` es forzado y tiene un responsable, un tipo y una
fecha esperada. Solo un bloqueo se puede diagnosticar (sección 11).

### Una exploración no puede producir reglas
**Sí puede.** Escribe un `rules.yml` en su carpeta y se promueve igual. Como no tiene
compuertas, al promover se pide firma (sección 13).

### `--by` solo sirve en `approve-step`
**No.** También en `merge-increment`, cuando las reglas no pasaron por ningún paso con
compuerta: exploraciones, prototipos, tareas y el `build` de `analysis` (sección 13).

### `state.yml` se puede editar a mano si sé lo que hago
**No.** Todo cambio pasa por un comando, que verifica y deja rastro. La única excepción es
migrar un proyecto desde una versión anterior del IEF, una sola vez (sección 6).

### Para marcar un paso terminado, lo pongo en `state.yml`
**No.** Para eso existe `complete-step`, que además verifica el artefacto antes de marcar.
Si ves instrucciones antiguas que digan «márcalo en `state.yml`», están desactualizadas.

### Un gráfico rápido necesita un incremento
**No.** Si nadie lo va a citar, mantener ni heredar como decisión, es una línea de `log`
(sección 9).

### Lo que aprendí en una reunión va a la bitácora
**No.** La bitácora es para **trabajo que hiciste**. Un hecho que te llegó de fuera va a
`record-input`, tiene id, se cita como evidencia y puede invalidar reglas (sección 15).

### Registrar que una reunión invalida una regla ya la cambia
**No.** Registrarlo **abre una deuda** que `doctor` vigila; cerrarla —con una regla que
declare `supersedes`, o retirando la acusación— es decisión de una persona (sección 15).

### `rewind` solo toca el paso al que retrocedo
**No.** Marca `NEEDS_REVISION` en ese paso **y en todos los posteriores que tenían trabajo**,
y una firma retrocedida se pierde. El motor lo anuncia antes (sección 17).

### `--force` es la forma rápida de desbloquearme
**No.** Es una salida de emergencia para cuando el artefacto está bien y el motor no lo
entiende. Exige motivo y `doctor` lo recuerda. Usarlo con un artefacto a medias convierte
el estado en una ficción (sección 17).

### Si mi contrato de datos no valida, es que está mal
**No necesariamente.** El motor solo conoce dos formas genéricas. En el paso 2b de una
exploración la forma es libre; en el paso 3 de un `build` es estricta a propósito
(sección 17).

### La constitución y las reglas son lo mismo con distinto nombre
**No.** La constitución dice **cómo se trabaja** y se escribe al empezar. Las reglas dicen
**qué es cierto del dominio** y se descubren trabajando. Prueba: ¿lo descubriste mirando
datos? Entonces es una regla (sección 14).

### Los hallazgos de `findings.md` ya rigen el proyecto
**No.** `findings.md` es prosa: no se puede citar como evidencia, ni entra en detección de
conflictos, ni se puede marcar como superado. Si un hallazgo va a condicionar lo que venga
después, conviértelo en regla y promuévelo.

### Una regla superada se borra
**Nunca.** Queda marcada, apuntando a la que la reemplaza. Borrarla perdería por qué el
proyecto pensó lo contrario un día (sección 13).

### Puedo usar `modeling` directamente
**No.** Es un mixin: hay que componerlo en un preset propio con `extends: [base, modeling]`
(sección 25).

### Si `doctor` no dice nada, todo está bien
**Casi.** `doctor` revisa la coherencia del estado, no la calidad del trabajo. Un charter
vacío pero existente pasa todas sus comprobaciones. El motor garantiza que el proceso se
siguió; que el contenido sea bueno sigue siendo cosa tuya.

## 27. Todos los comandos

Todos se invocan igual:

```bash
python "$IEF/verify_frame.py" --mode <modo> [opciones]
```

donde `$IEF` es la carpeta `core/scripts` del bundle. Todos aceptan `--project-dir
<ruta>`; sin él, actúan sobre el directorio actual. Los ejemplos de esta guía se ejecutan
desde el directorio del proyecto.

Las tablas dicen qué opciones **lee de verdad** cada modo. El motor acepta cualquier opción
con cualquier modo sin quejarse, así que una opción que no aparece en la fila de su modo
**se ignora en silencio**. Eso importa más de lo que parece: mira el aviso de la sección
«Avanzar un paso».

### Arrancar un proyecto

| Modo | Opciones | Qué hace |
|---|---|---|
| `init` | `--preset` (por defecto `generic`) · `--layout` (`flat` por defecto, o `numbered`) · `--initiative-name` | Crea las carpetas de los roles del preset, `state.yml` y la plantilla de la constitución |
| `adopt` | `--preset` (por defecto `generic`) · `--yes` | Adopta un proyecto existente sin mover nada. Sin `--yes`, solo propone. **No lee `--layout`:** las carpetas que falten se crean con los nombres de `flat` |

### Abrir trabajo

| Modo | Opciones | Qué hace |
|---|---|---|
| `new-increment` | `--type` (`task` · `exploration` · `prototype` · `build`) · `--name` **(obligatorio)** · `--branch` | Abre un incremento y le da el foco |
| `log` | `--message` **(obligatorio)** · `--output` · `--from` | Una línea en la bitácora. No abre nada |
| `record-input` | `--source` **(obligatorio)** · `--summary` **(obligatorio)** · `--kind` · `--date` · `--file` · `--invalidates` | Registra una entrada externa `EXT-NNN` |

### Mirar

| Modo | Opciones | Qué hace |
|---|---|---|
| `status` | `--json` | El tablero. Con `--json`, para que lo consuma otro programa |
| `focus` | `--increment` *(opcional)* | Sin él, muestra el foco y los frentes abiertos; con él, mueve el foco |
| `doctor` | — | Diagnóstico completo (sección 18) |
| `explain` | `--rule RUL-…` **o** `--input EXT-…` | El linaje de una regla, o qué dijo una entrada y qué se hizo con ella |
| `verify-step` | `--step` · `--increment` | Comprueba el artefacto y la compuerta de un paso. **No cambia nada** |

### Avanzar un paso

| Modo | Opciones | Qué hace |
|---|---|---|
| `complete-step` | `--step` · `--increment` · `--force` · `--reason` | Marca el paso `COMPLETED`, verificando antes el artefacto. `--force` exige `--reason` |
| `approve-step` | `--by` | Registra la firma de una compuerta. **Siempre sobre el foco** |
| `advance` | — | Pasa al siguiente paso. **Siempre sobre el foco** |
| `rewind` | `--to-step` · `--reason` **(obligatorio)** · `--increment` | Retrocede, marcando `NEEDS_REVISION` el destino y lo posterior |

> **⚠️ `approve-step` y `advance` ignoran `--increment`.** Actúan **siempre** sobre el
> incremento que tiene el foco, aunque escribas otro. Medido con el foco en `002_beta`:
>
> ```
> $ verify_frame.py --mode approve-step --increment 001_alfa --by Ana
> [APPROVED] paso 1: Charter
>
>   001_alfa   1_charter=COMPLETED      ← el que se pidió firmar: sigue sin firma
>   002_beta   1_charter=APPROVED       ← el que quedó firmado: otro
> ```
>
> Una firma puede caer sobre el incremento equivocado sin ningún error, y el mensaje ni
> siquiera dice sobre cuál. Hasta que se corrija: **mueve el foco antes de aprobar o
> avanzar**, y comprueba con `status` después.
>
> ```bash
> python "$IEF/verify_frame.py" --mode focus --increment 001_alfa
> python "$IEF/verify_frame.py" --mode approve-step --by "Ana"
> ```

### Gestionar un incremento

| Modo | Opciones | Qué hace |
|---|---|---|
| `set-status` | `--increment` · `--status` · `--reason` · `--blocked-kind` (`increment` · `external` · `decision`) · `--blocked-on` · `--expected` · `--focus` · `--branch` | Cambia el estado, declara un bloqueo o corrige la rama. `--status` es obligatorio salvo que solo corrijas la rama |

### Cerrar

| Modo | Opciones | Qué hace |
|---|---|---|
| `draft-report` | `--increment` · `--force-overwrite` | Borrador del informe con lo que el motor sabe. No pisa uno escrito sin `--force-overwrite` |
| `merge-increment` | `--increment` · `--dry-run` · `--by` | Promueve reglas, contrato y criterios a `specs/`. `--by` cuando ningún paso con compuerta aprobó las reglas |

### Verificación y mantenimiento

| Modo | Opciones | Qué hace |
|---|---|---|
| `check-gates` | — | Falla si alguna compuerta quedó sin firmar. Pensado para integración continua |
| `check-preset` | `--preset` *(opcional)* | Valida uno o todos los presets |
| `check-bundle` | — | Integridad del bundle. Para quien mantiene el framework |
| `check-steps` | — | Que cada paso tenga instrucciones y plantilla. Para quien mantiene el framework |

### El compilador de criterios

```bash
python "$IEF/compile_acceptance_tests.py" --project-dir . \
    --increment <slug> --out tests/generated/        # genera los tests de pytest
python "$IEF/compile_acceptance_tests.py" --increment <slug> --check   # CI: ¿están al día?
```

Sin `--increment`, usa el incremento activo.

### La secuencia de todos los días

```bash
python "$IEF/verify_frame.py" --mode doctor            # ¿algo roto?
python "$IEF/verify_frame.py" --mode status            # ¿dónde estoy?

# ... escribir el artefacto del paso actual ...

python "$IEF/verify_frame.py" --mode verify-step       # ¿está bien?
python "$IEF/verify_frame.py" --mode complete-step     # hecho
python "$IEF/verify_frame.py" --mode approve-step --by "<quien decide>"   # solo si lleva compuerta
python "$IEF/verify_frame.py" --mode advance           # al siguiente
```

## 28. Las skills

Para quien trabaja con un agente de IA (Claude u otro compatible), el IEF viene con dos
skills. Viven en `~/.claude/skills/` y son de alcance global: sirven en cualquier proyecto
de la máquina.

### `ief-workflow` — usar el IEF en un proyecto

Es la que se usa casi siempre. Se activa sola cuando se menciona el IEF, un incremento, una
compuerta, `state.yml`, un preset o cualquiera de los comandos, y también cuando el
proyecto tiene un `initiative/state.yml`, aunque nadie nombre el framework.

Lo que le enseña al agente:

- **Localizar el motor** antes de nada, en este orden: la variable `$IEF_HOME`, la
  ubicación por defecto en la máquina, una copia junto al proyecto. Si ninguna existe, le
  indica **preguntar al usuario** en lugar de improvisar comandos: un comando inventado que
  parece funcionar hace más daño que un error claro.
- Las reglas que no se negocian: anti-alucinación, no firmar compuertas, no editar
  `state.yml`.
- Cuándo algo merece un incremento y cuándo basta con `log`.
- Qué hacer con un artefacto que no valida, con un retroceso, con una entrada externa.

Y tiene tres referencias que carga solo cuando las necesita:

| Archivo | Cubre |
|---|---|
| `references/ciclos.md` | Los ciclos, paso a paso |
| `references/concurrencia.md` | Varios frentes, foco, bloqueos |
| `references/reglas.md` | El ciclo de vida de las reglas y la promoción |

### `ief-authoring` — modificar el propio framework

Para trabajar **dentro** del bundle: crear o modificar un preset, componer un mixin, añadir
un paso o un rol, crear un layout, cambiar el vocabulario de un paso, tocar el motor. **No
se usa para trabajar en un proyecto**: para eso está la otra.

Trae un verificador, `scripts/verificar_skills.py`, que comprueba que todo lo que las skills
documentan —cada modo, cada flag, cada ruta— existe de verdad en el motor. Si alguien
renombra un modo y no actualiza la skill, el verificador falla.

### Los comandos de la extensión

Si además usas spec-kit, `specify extension add ./extension --dev` instala 23 comandos
`/speckit.ief.*`, uno por cada operación habitual: `/speckit.ief.init`,
`/speckit.ief.charter`, `/speckit.ief.doctor`, `/speckit.ief.input`… Cada uno es una
página de instrucciones que termina llamando al motor. Son opcionales: el IEF funciona sin
spec-kit.

---

## 29. Límites conocidos

Lo que el IEF **no** hace hoy, o hace con alguna aspereza. Mejor saberlo antes de
tropezar.

**⚠️ `approve-step` y `advance` actúan siempre sobre el foco, y aceptan `--increment` sin
leerlo.** Es el límite más serio de esta lista, porque afecta a las firmas: con el foco en
un incremento, `approve-step --increment <otro> --by "Ana"` firma la compuerta del que
tiene el foco, no la del que escribiste, sin ningún error. Hasta que se corrija, **mueve el
foco antes de aprobar o avanzar** y comprueba con `status` (sección 27).

**`adopt` no lee `--layout`.** Las carpetas que falten se crean siempre con los nombres de
`flat`. En un proyecto con carpetas numeradas, revisa lo que crea antes de aceptar.

**El layout no se puede cambiar después de `init`.** No hay `migrate-layout`. Si empiezas
con `flat` y a los tres meses quieres `numbered`, hay que hacerlo a mano.

**`adopt` se niega si ya existe `state.yml`.** Para un proyecto que ya usa el IEF pero cuyas
carpetas no coinciden con el layout, `role_paths` se escribe a mano, una vez.

**No hay un modo de migración de esquema.** Un `state.yml` de una versión anterior se migra
editándolo una vez, guiándose por `doctor`.

**El mixin `modeling` no se puede usar tal cual.** Hay que crear un preset que lo componga
(sección 25).

**`merge-increment` copia el contrato y los criterios, no los fusiona.** Si un incremento
tiene `data-contract.yml` o `acceptance-tests.yml`, al promoverse **reemplaza** los que
hubiera en `specs/`. La especificación viva conserva el contrato y los criterios del
**último** incremento promovido, no la suma de todos. Las reglas, en cambio, sí se acumulan.

Una consecuencia práctica: un prototipo cuya hipótesis se refutó tiene criterios de
aceptación, y promoverlo los copiaría sobre los del proyecto. Por eso, un prototipo
refutado se cierra mejor como `ABANDONED`, con su informe, que con `merge-increment`.

**Las entradas externas no se pueden retirar con un comando.** Si una entrada resultó
equivocada, o su `invalidates` no procedía, se edita `inputs.yml`.

**Los ids `EXT-` se numeran por cuenta.** Si se borra una entrada a mano, la siguiente
podría repetir un id ya usado. No borres entradas: corrígelas.

**El motor no verifica identidades.** `--by "Ana"` registra un nombre. La compuerta
funciona porque quien la usa es honesto con ella.

**`doctor` revisa el proceso, no el contenido.** Un artefacto vacío pero existente pasa las
comprobaciones de existencia. La calidad del charter sigue siendo responsabilidad de quien
lo firma.

**La extensión de spec-kit no lleva el motor.** Los comandos `/speckit.ief.*` se instalan,
pero llaman a `core/scripts/verify_frame.py`, que tiene que estar disponible aparte.

**`log` no tiene id.** Una línea de bitácora no se puede citar. Si algo de la bitácora
empieza a importar, ha dejado de ser bitácora.

---

## 30. Cómo seguir estudiando

### Qué leer, y en qué orden

| Orden | Archivo | Por qué |
|---|---|---|
| 1 | Esta guía, secciones 3, 10 y 26 | Las garantías, la vida de un paso y los errores típicos |
| 2 | [`README.md`](../README.md) | La visión general, más breve |
| 3 | [`core/roles.yml`](../core/roles.yml) | Qué necesita un proyecto, explicado rol por rol |
| 4 | [`presets/generic/preset.yml`](../presets/generic/preset.yml) | El ciclo base: se lee como documentación |
| 5 | [`presets/research/preset.yml`](../presets/research/preset.yml) o el tuyo | Cómo un preset hereda y solo redefine lo que cambia |
| 6 | [`presets/modeling/preset.yml`](../presets/modeling/preset.yml) | Cómo un mixin inyecta un paso sin copiar el ciclo |
| 7 | [`core/templates/constitution-template.md`](../core/templates/constitution-template.md) | Qué va en la constitución y qué no |
| 8 | [`core/steps/04_rules/template.yml`](../core/steps/04_rules/template.yml) | La anatomía de una regla, comentada campo a campo |
| 9 | [`core/scripts/compile_acceptance_tests.py`](../core/scripts/compile_acceptance_tests.py) (su cabecera) | Las formas de `verify` |

Los archivos del bundle están escritos para leerse: los comentarios explican **por qué**
cada cosa es como es, no solo qué hace.

### Ejercicios

La mejor forma de entender el IEF es provocar sus mensajes a propósito. Todos se hacen en
un directorio de prueba, fuera de cualquier proyecto real:

```bash
mkdir /tmp/ief-practica && cd /tmp/ief-practica
python "$IEF/verify_frame.py" --mode init --preset generic --layout flat \
    --initiative-name "Practica"
```

1. **La compuerta.** Abre un `build`, escribe un `charter.md`, complétalo e intenta
   `advance` sin aprobar. Lee el error. Aprueba y avanza.
2. **El conflicto.** Reproduce la cadena de la sección 13: tres exploraciones con reglas
   sobre el mismo `applies_to`. Provoca el `[CONFLICTO]`, resuélvelo con `supersedes`, y
   recorre el linaje con `explain`.
3. **La deuda externa.** Registra una entrada que invalida una regla. Mira cómo `doctor`
   falla. Ciérrala con una regla nueva que la cite como evidencia. Mira cómo calla.
4. **El ciclo imposible.** Abre dos incrementos e intenta bloquear cada uno esperando al
   otro.
5. **El foco robado que ya no se roba.** Con dos frentes abiertos, reactiva el que no tiene
   el foco sin `--focus` y comprueba en `status` a cuál apuntan los comandos.
6. **El retroceso.** Avanza tres pasos de un `build` y retrocede al 1. Lee qué arrastra y
   comprueba que la firma del paso 1 se perdió.
7. **El artefacto raro.** En el paso 3 de un `build`, escribe un contrato con forma propia.
   Mira el error, fuerza el paso con motivo, y mira qué recuerda `doctor`.
8. **La adopción.** Crea un directorio con carpetas de nombres inventados y ejecuta
   `adopt` sin `--yes`. Lee las cuatro listas, sobre todo la última.

Si alguno no produce lo que dice esta guía, has encontrado algo que merece un informe.

