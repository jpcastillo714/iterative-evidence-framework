# Estado del bundle y trabajo pendiente

**Última revisión: 2026-09-24.** Documento **vivo**: cuando algo de aquí se resuelve, se
edita o se borra la entrada. No se acumula historial — para eso está `git log`.

Si vienes a proponer o implementar mejoras en el framework, esto es lo que necesitas
saber antes de tocar nada.

---

## 1. Qué leer antes

En este orden, y no son opcionales:

| Documento | Para qué |
|---|---|
| [`AGENTS.md`](../AGENTS.md) | Las reglas de este directorio. Lo primero. |
| [`docs/GUIA_DE_ESTUDIO.md`](GUIA_DE_ESTUDIO.md) | Cómo funciona el framework, con ejemplos ejecutados. 30 secciones; si tienes prisa, la 3 (garantías), la 10 (vida de un paso) y la 26 (malentendidos). |
| Skill `ief-authoring` | Dónde va cada tipo de cambio y qué se verifica después. |
| Este documento | Qué está a medias, qué está roto y qué se discutió sin implementar. |

**Este directorio no es un proyecto.** Nunca crees un `initiative/` aquí ni ejecutes
`--mode init` apuntando a esta carpeta: el bundle es el molde, no la pieza.

---

## 2. Qué es el IEF hoy

Herramienta autónoma, inspirada en spec-kit e instalable por él, para llevar un proyecto
por incrementos verificables. Tres ejes independientes, y mezclarlos otra vez es el error
de diseño que este repositorio ya cometió una vez:

| Eje | Decide | Se elige |
|---|---|---|
| **Layout** | Cómo se llaman las carpetas | Una vez, por proyecto |
| **Preset** | Vocabulario y ceremonia | Una vez, por proyecto |
| **Ciclo** | Cuánto rigor lleva un trabajo | En cada incremento |

Estado medido el 2026-09-24 con los cuatro chequeos del bundle:

- **Versión** 0.14.0 en `bundle.yml` y `extension/extension.yml` (un test exige que
  coincidan). `schema_version` del `state.yml` que escribe el motor: **4.0**.
- **6 presets:** `generic`, `research`, `product`, `analysis`, `modeling` (mixin
  abstracto) y `product-modeling` (composición `product` + `modeling`).
- **4 ciclos:** `task` (2 pasos, 0 compuertas), `exploration` (4, 0), `prototype` (4, 1),
  `build` (7, 3 — 8 y 4 cuando entra el mixin `modeling`).
- **104 pasos** con sus instrucciones y plantillas en los 6 presets.
- **23 comandos** `/speckit.ief.*` declarados en `extension/extension.yml`, todos con su
  archivo en `extension/commands/`.
- Las skills globales `ief-workflow` e `ief-authoring` pasan sus 44 comprobaciones
  contra el `--help` real del motor.

---

## 3. El árbol de trabajo no está limpio

**Lo primero que tienes que resolver.** Hay trabajo terminado y sin commitear en `main`:

| Archivo | Qué cambia |
|---|---|
| `core/scripts/verify_frame.py` | Una sola definición de «artefacto promovible» (`artefactos_promovibles`) compartida por `merge-increment` y `doctor`. Antes `doctor` pedía promover un `task` terminado y el merge respondía que no había nada que promover: dos respuestas contradictorias del mismo motor. |
| `tests/test_concurrencia.py` | El test de regresión de eso. |
| `presets/product-modeling/` + `bundle.yml` | Preset nuevo: composición pura de `product` + `modeling`, para que `--preset` pueda elegirla con un solo id. No redefine pasos. |
| `core/templates/agents-template.md` | Reescritura: el `AGENTS.md` que se genera en cada proyecto ahora enseña a preguntarle al motor (`status --json`) en vez de fijar un ciclo, y trae la tabla de modos para no editar `state.yml` a mano. |
| `core/steps/01_charter`, `02_empirical_inspection`, `07_verification` | Rutas corregidas: los artefactos viven en `initiative/increments/<SLUG>/`, no en `initiative/`. Las instrucciones decían la ruta vieja. |
| `AGENTS.md`, `SKILL.md`, `README.md`, `extension/commands/ief.init.md` | Documentación desactualizada, corregida el 2026-09-24: el ejemplo de `init` usaba el preset `data-science`, que ya no existe; `ief.init.md` ofrecía `engineering` y `academic` (borrados desde hace tres versiones) y mandaba a añadir carpetas en `presets/<id>/directory-convention.yml`, archivo que tampoco existe; el `README` y el `SKILL` hablaban de «los tres ciclos» habiendo cuatro. |
| `tests/test_presets.py`, `tests/test_higiene.py` | Los tests que recorren el árbol ignoran `.claude/worktrees/`. Un worktree de git es otro checkout del mismo repositorio dentro de él, y el test de coherencia de claves de paso fallaba señalando archivos de otra rama. Fallaba solo en local, nunca en CI, que es la peor variante. |
| `docs/ESTADO_Y_PENDIENTES.md` | Este documento. |

Verificado el 2026-09-24 con ese árbol: `check-bundle`, `check-preset` y `check-steps`
pasan, y el verificador de skills da 44 comprobaciones y 0 fallos.

**Decisión pendiente del usuario:** commitear esto antes de empezar cualquier cosa nueva.
Trabajar encima sin commitear mezcla tu cambio con el de otro en el mismo diff.

---

## 4. Cómo se verifica un cambio

Los cuatro, siempre. El bundle ya arrastró una clave de paso divergente que rompía un
ciclo entero y que ningún test detectaba.

```bash
python core/scripts/verify_frame.py --mode check-bundle
python core/scripts/verify_frame.py --mode check-preset
python core/scripts/verify_frame.py --mode check-steps
pytest tests/ -q
```

Y, si tocaste modos, flags o rutas de `core/`:

```bash
python ~/.claude/skills/ief-authoring/scripts/verificar_skills.py
```

La suite son **209 tests y tarda unos cuatro minutos**: casi cada uno lanza el motor como
subproceso sobre un proyecto temporal. No la interrumpas pensando que se colgó. Hay CI en
GitHub Actions que corre lo mismo.

Si trabajas en un worktree de git, recuerda que es **otro checkout del mismo repositorio**:
comprueba en qué carpeta estás antes de editar, porque las dos tienen los mismos archivos
con contenidos distintos.

De extremo a extremo, siempre **fuera** del bundle:

```bash
python core/scripts/verify_frame.py --mode init --project-dir /tmp/prueba \
    --preset product-modeling --layout numbered --initiative-name "Prueba"
```

---

## 5. Fallos conocidos, medidos

Todos reproducidos ejecutando el motor, no leyendo el código. En orden de gravedad.

### 5.1 `approve-step` y `advance` aceptan `--increment` y no lo leen

**Lo más grave que hay abierto.** Ambos actúan siempre sobre el incremento **enfocado**.
El `argparse` acepta el flag, así que no hay error ni aviso.

Medido el 2026-09-24, con el foco en `002_beta` y los dos charters completados:

```
python verify_frame.py --mode approve-step --increment 001_alfa --by Ana
[APPROVED] paso 1: Charter

state.yml →  001_alfa  1_charter: COMPLETED    ← el que se pidió firmar
             002_beta  1_charter: APPROVED     ← el que quedó firmado
```

Una **firma humana** queda registrada en el incremento equivocado y el mensaje no dice en
cuál. Es el mismo fallo que ya se corrigió en `rewind`, pero con consecuencias peores:
las compuertas son el único punto del framework donde interviene una persona.

Está en el despacho de `main()`: `cmd_advance(proj)` y `cmd_approve_step(proj, args.by)`
no reciben `args.increment`, y sus firmas no tienen el parámetro. La corrección es la que
ya se aplicó a `rewind`: pasar el slug, resolverlo con `get_increment(state, slug)` y
nombrar el incremento en la salida. Necesita tests de regresión para los dos modos.

**Si lo corriges, actualiza también** los avisos de `docs/GUIA_DE_ESTUDIO.md` (secciones
26, 27 y 29), la skill `ief-workflow` y el `agents-template.md`, que hoy dicen «cae sobre
el enfocado: compruébalo antes».

### 5.2 `adopt` ignora `--layout`

`cmd_adopt(project_dir, preset_id, aplicar)` no recibe el layout, así que las carpetas
que falten se crean siempre con los nombres de `flat`. Un proyecto con carpetas numeradas
que se adopta pidiendo `--layout numbered` termina con ambas nomenclaturas. Mientras no
se corrija, en esos casos conviene adoptar y mover las carpetas a mano con `role_paths`.

### 5.3 Nada comprueba que los comandos nombren presets y ciclos que existen

Los cuatro chequeos validan que los comandos declarados en `bundle.yml` **existan como
archivo**, pero no lo que dicen dentro. Por eso `ief.init.md` pasó tres versiones
ofreciendo presets borrados y mandando a editar un archivo inexistente, con los chequeos
en verde: es el único lugar del bundle donde la documentación puede mentirle a un agente
sin que nada falle.

Lo que arreglaría la clase entera de fallo: un test que recorra `extension/commands/*.md`
y las plantillas, extraiga los ids de preset y los nombres de ciclo que citan y los
compare con los que el motor resuelve de verdad. Sería el equivalente, dentro del
repositorio, de lo que `verificar_skills.py` ya hace con las skills.

---

## 6. Límites conocidos que no son fallos

No están rotos: están sin hacer, o son decisiones. Si vas a cambiar alguno, cámbialo a
propósito.

| Límite | Consecuencia práctica |
|---|---|
| `merge-increment` **copia** `data-contract.yml` y `acceptance-tests.yml` a `specs/`, no los fusiona | En `specs/` quedan solo los del último incremento promovido. Por eso un prototipo cuya hipótesis no se sostuvo se cierra `ABANDONED`, no se promueve. |
| Los ids de entradas externas (`EXT-NNN`) se asignan **por conteo** | Si se borra una entrada del `inputs.yml` a mano, el siguiente id se repite. |
| No hay modo para **retirar** una entrada externa | Una entrada mal registrada solo se corrige editando `inputs.yml`, que es justo lo que el framework pide no hacer. |
| No hay `migrate-layout` | Cambiar de nomenclatura a mitad de proyecto es trabajo manual más `role_paths`. |
| `adopt` se niega si ya existe `state.yml` | Re-adoptar un proyecto migrado a medias exige borrar el estado, y eso pierde el historial. |
| `modeling` es abstracto | `--preset modeling` y `--preset analysis,modeling` se rechazan. `product-modeling` cubre la composición con `product`; la de `analysis` no existe como preset elegible. |
| El motor solo **avisa** de la rama de git, nunca la cambia | Un incremento con `branch` declarado puede trabajarse desde otra rama; queda en el aviso y en `doctor`. |

---

## 7. En discusión, sin implementar: una línea legible por sesión

Discutido el 2026-09-18. **No implementado, y la decisión de hacerlo es del usuario.**

**El problema.** Lo que el worklog y los commits registran está escrito para quien conoce
el proyecto («sesión 6, unidades U4, hallazgo H-5»). Cualquier consumidor externo del
estado —una persona que vuelve en seis meses, o un agente que resume el avance— solo
recibe códigos. Y en los proyectos donde el avance diario es código, entre el cierre de un
incremento y el siguiente **no hay prosa en ninguna parte**: el `findings.md` se escribe
al cerrar.

**Lo que se propone.** Que el agente que trabajó deje, al cerrar la sesión, una frase en
lenguaje normal: qué se entendió, qué se decidió o qué cambió, legible sin conocer los
códigos del proyecto.

**Decisiones a las que llegó esa discusión**, para que no se rehaga desde cero:

1. **Dónde:** el `initiative/worklog.md` que ya existe, con un flag nuevo
   `--mode log --increment <slug>` que asocie la entrada a un incremento. No un archivo
   nuevo, no el `history` del `state.yml` (es un archivo de máquina, y su prosa no la lee
   nadie).
2. **Esto cambia el significado del worklog.** Hoy su cabecera dice «trabajo que no llegó
   a incremento». Pasaría a ser el diario del proyecto, con las entradas de incremento
   etiquetadas. Hay que cambiar la cabecera, `extension/commands/ief.log.md` y la sección
   correspondiente de la guía.
3. **El motor sella el commit actual** en cada línea. Sin eso, la frase es el lugar más
   fácil del framework para que un agente invente avances, y nadie puede comprobarla.
4. **No se exige, se detecta.** Un aviso (WARN) en `doctor` comparando las fechas de
   `git log` con las fechas del worklog: «días con commits sin línea». Nunca un error, y
   nunca un bloqueo en `advance`: una línea obligatoria produce relleno del tipo «se
   avanzó en la implementación», y el relleno no se detecta mientras la omisión sí.
5. **El motor no sabe qué es una sesión.** Sus unidades son el paso y el incremento. Por
   eso la verificación se ancla en los días con commits, que sí son observables.
6. **No se autogenera de noche a partir del diff.** El diff dice qué cambió, no qué se
   entendió; eso solo existe en el contexto del agente al terminar.
7. **Presets afectados: ninguno.** Ningún preset redefine la ruta del worklog. El costo
   está en el motor (unas 60 líneas y sus tests), en la documentación y en el
   `agents-template.md`.

**Coste que no se ve:** los proyectos ya adoptados tienen su propio `AGENTS.md`, copiado
al crearlos. Una convención nueva no les llega sola: hay que añadirla en cada uno.

---

## 8. Invariantes que no se rompen

1. **Neutralidad de dominio.** `core/` no conoce ningún campo de aplicación, y ningún
   archivo del repositorio alude a un proyecto, cliente o dataset concreto.
   `tests/test_higiene.py` lo hace cumplir por nombre.
2. **`core/scripts/` es una lista cerrada:** `verify_frame.py`, `ief_preset.py`,
   `compile_acceptance_tests.py`. Cualquier otro script ahí es código de dominio.
3. **Renombrar la clave de un paso es un cambio en cuatro sitios:** el `state.yml` de los
   proyectos vivos, el preset, los comandos y las instrucciones. A medias deja el motor
   buscando un archivo que nadie escribe, sin error visible. Hay un test de regresión de
   coherencia de claves: extiéndelo **antes** de renombrar.
4. **Nada generado sin verificar.** Este repositorio ya arrastró informes que citaban
   código inexistente y resultados de tests que nunca se ejecutaron. Si vas a escribir
   que algo funciona, ejecútalo y pega la salida.
5. **Los presets no declaran rutas de carpeta.** Si necesitas una, es un rol: va en
   `core/roles.yml` y en **los dos** layouts.
6. **Un mixin usa `insert_after`, nunca `steps`.** Redeclarar el ciclo lo vuelve no
   componible.
7. **Las compuertas son del usuario.** Ningún cambio puede terminar aprobando pasos en su
   nombre, ni convertir una petición de trabajo en una aprobación.

---

## 9. Quién consume el estado fuera del bundle

Un cambio en el motor no se queda en el motor:

- **Los proyectos ya adoptados** tienen un `state.yml` con `schema_version: 4.0` y un
  `AGENTS.md` que es una **copia** de la plantilla del momento en que se crearon. Cambiar
  un modo o un flag no actualiza esas copias.
- **Las skills globales** `ief-workflow` (la que usan los proyectos) e `ief-authoring` (la
  que usa este repositorio) documentan modos, flags y rutas. Si cambias uno y no la skill,
  un agente ejecutará un comando que ya no existe: es un fallo silencioso, porque la skill
  parece correcta hasta que alguien la sigue. Para eso está `verificar_skills.py`.
- **Lectores externos del estado.** Hay herramientas fuera de este repositorio que leen
  `initiative/state.yml`, `initiative/worklog.md` y los `findings.md` para resumir el
  avance. Dependen del **formato** de esos archivos: añadir campos es seguro, renombrarlos
  o mover archivos no lo es. Si cambias alguno, hay que avisarlo, porque el bundle no
  puede saber quién lo lee.

---

## 10. Orden sugerido si vas a trabajar en esto

1. Commitear o descartar lo del §3, para empezar con el árbol limpio.
2. Corregir §5.1 (`--increment` en `approve-step` y `advance`) con sus dos tests, y
   actualizar guía, skill y plantilla.
3. Corregir §5.2 (`adopt --layout`).
4. Añadir el test de §5.3, que es lo que evita que la documentación de los comandos vuelva
   a desincronizarse en silencio.
5. Consultar al usuario antes de tocar §7: es un cambio de significado del worklog, no
   solo un flag.
