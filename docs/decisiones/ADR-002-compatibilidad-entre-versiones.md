# ADR-002: Compatibilidad entre versiones: qué cambió, qué hacer y cómo migrar

## Estado

Propuesta

## Contexto

Un proyecto que usa el IEF puede durar meses, como una tesis o un pipeline en producción.
En ese tiempo el bundle cambia. Hoy el framework no tiene cómo decirle a un proyecto, ni
al agente que lo opera, qué cambió entre la versión con la que se creó y la actual, qué
tiene que hacer o si algo se va a romper. Lo que hay, medido en la versión 0.14.0:

- **Una sola señal, sin contenido.** `state.yml` declara `schema_version`. Si no coincide
  con la del motor, `doctor` avisa con una línea («el archivo viene de una versión anterior
  del IEF») sin decir qué cambió ni qué hacer. Ningún otro modo lo mira.
- **Ninguna defensa ante un motor más viejo.** `load_state` no compara versiones, así que
  un motor antiguo escribe sin aviso sobre un `state.yml` producido por uno más nuevo.
- **No hay registro de cambios.** La historia de versiones solo existe en los mensajes de
  commit.
- **No hay modo de migración.** El esquema ya pasó por las versiones 1.0, 2.0 y 4.0, y cada
  transición se resolvió a mano.
- **El `AGENTS.md` de cada proyecto no es del motor.** Lo arma el agente siguiendo
  `extension/commands/ief.init.md` («combinar la plantilla con el fragmento del preset; si
  ya existe, hacer append»). Cada proyecto tiene una copia distinta, sin versión, que el
  motor nunca lee. Cuando cambia un modo o un flag, esa copia sigue enseñando el comando
  viejo. `docs/ESTADO_Y_PENDIENTES.md` §9 ya lo señala como riesgo.

La consecuencia práctica es la que motiva este ADR. Un agente que retoma un proyecto
después de una actualización ejecuta lo que dice su `AGENTS.md`, que puede estar
obsoleto. Si algo falla, no tiene de dónde saber por qué ni qué hacer.

## Decisión

### 1. Política de versiones

El bundle sigue Semantic Versioning. Mientras siga en 0.y.z, además, aplica una regla más
estricta que la norma: **ningún cambio incompatible para proyectos existentes se aplica
sin aviso previo.**

Se considera incompatible:
- renombrar o quitar un campo de `state.yml`;
- renombrar o quitar un modo o un flag;
- mover un artefacto de ruta;
- cambiar lo que significa una compuerta.

Ese cambio sigue tres fases:
- **Expandir.** En la versión N, lo nuevo convive con lo viejo. El motor sigue aceptando lo
  viejo y emite un aviso que nombra lo que lo reemplaza.
- **Migrar.** Los proyectos pasan a lo nuevo, con `--mode migrate` cuando haga falta.
- **Contraer.** Lo viejo se retira, no antes de la versión N+1.

### 2. Dos registros de cambios

- **`CHANGELOG.md`**, para personas, con las categorías añadido, cambiado, obsoleto,
  retirado y corregido.
- **`core/cambios.yml`**, para el motor. Por versión, una entrada por cambio que afecte a
  proyectos existentes, con los campos:
  - `id`;
  - `tipo`: `añadido | cambiado | obsoleto | retirado | corregido`;
  - `afecta`: `state | modo | flag | ruta | plantilla | agents`;
  - `que_cambia`;
  - **`que_hacer`**: la acción concreta, escrita para que un agente la ejecute;
  - `migracion`: el id de la migración, o `null`.

### 3. El proyecto recuerda con qué versión se escribió

`state.yml` guarda `ief_version`, la versión del motor que lo escribió por última vez,
además de `schema_version`. Un proyecto sin ese campo se trata como anterior a la versión
que introduce este ADR.

### 4. El motor dice qué cambió, filtrado para ese proyecto

- **`status --json`** incluye un bloque `upgrade` cuando el proyecto es más viejo que el
  motor: `from`, `to`, las entradas de `cambios.yml` entre ambas versiones y las
  migraciones pendientes.
- **Los modos para personas** imprimen una sola línea: «Este proyecto se escribió con IEF
  0.14.0 y el motor es 0.15.0: hay N cambios que lo afectan. Ver `--mode upgrade-notes`».
- **`--mode upgrade-notes`** lista esos cambios con su `que_hacer`.
- **`doctor`** lo reporta en su sección de estado.

### 5. Un motor más viejo no escribe sobre un proyecto más nuevo

Si `ief_version` o la versión mayor de `schema_version` del proyecto supera las del motor,
los modos que escriben se niegan con un mensaje que dice qué versión del bundle hace
falta. Los modos de solo lectura funcionan, con un aviso.

### 6. Migraciones explícitas

`--mode migrate` funciona así:
- **Muestra, no escribe.** Sin `--yes`, muestra exactamente qué cambiaría.
- **Copia antes de escribir.** Con `--yes`, guarda `state.yml.bak-<versión de origen>` y
  aplica.
- **Es idempotente.** Correrla dos veces da el mismo resultado.
- **Queda registrada.** Anota `MIGRATE` en el historial y actualiza `ief_version`.
- **Cada migración es un paso con nombre** (de la versión X a la Y), con su test.

Igual que `adopt`, el agente muestra la propuesta y es la persona quien la aplica.

### 7. El `AGENTS.md` del proyecto tiene una sección del motor

El motor escribe la parte del IEF entre dos marcadores:

```markdown
<!-- IEF:INICIO v0.15.0 — generado por verify_frame.py; no editar dentro -->
…
<!-- IEF:FIN -->
```

- **`init`** la genera (deja de hacerlo el agente, y `ief.init.md` se ajusta).
- **`migrate`** reemplaza solo lo que está entre los marcadores. Lo escrito fuera no se
  toca.
- **Un `AGENTS.md` sin marcadores:** `migrate` propone insertar la sección al principio,
  no borra nada y avisa que puede haber instrucciones duplicadas para que la persona las
  limpie.
- **La sección es breve y accionable.** Incluye como primera regla: «Si
  `status --json` trae `upgrade`, antes de cualquier otra cosa muéstrale al usuario los
  cambios (`--mode upgrade-notes`) y propón `--mode migrate`».
- **`doctor`** avisa cuando la versión del marcador no coincide con la del motor, o cuando
  no hay marcadores.

### 8. Pruebas de actualización

`tests/fixtures/proyectos/<versión>/` guarda un proyecto mínimo escrito por cada versión
publicada, empezando por 0.14.0. Un test comprueba, para cada uno, que:
- el motor actual lo lee;
- `doctor` informa la actualización;
- `migrate` sin `--yes` no escribe nada;
- `migrate --yes` es idempotente;
- los modos de lectura funcionan después de migrar.

Cada versión nueva agrega su fixture.

## Evidencia

- **Por qué hace falta una política propia en 0.y.z.** SemVer dice que en la versión cero
  cualquier cosa puede cambiar [@semver2]. Pero en la práctica muchos paquetes se usan en
  serio sin salir nunca de 0.y.z [@decan2021], y quien los usa espera estabilidad igual.
- **Por qué no basta con el número de versión.** En Maven, más de un tercio de las
  versiones menores y casi una cuarta parte de los parches rompen compatibilidad
  [@raemaekers2017]. Por eso el motor declara explícitamente qué cambió, en vez de dejar
  que se deduzca del número.
- **Período de obsolescencia antes de retirar.**
  - SemVer recomienda al menos una versión menor con el aviso antes de retirar algo
    [@semver2].
  - Keep a Changelog separa lo obsoleto de lo retirado, y pide que se pueda actualizar en
    ese orden [@keepachangelog].
  - El patrón de expandir, migrar y contraer lo describe Sato [@sato2014].
  - Los ecosistemas estudiados por Bogart et al. usan estas prácticas para comunicar
    cambios: marcar como obsoleto, escribir guías de migración y llevar un registro de
    cambios [@bogart2021].
  - En la práctica ese patrón casi no se cumple si nada lo exige [@raemaekers2017]. De ahí
    que el motor lo haga cumplir.
- **Por qué el registro para el motor va aparte y filtrado por versión.**
  - El registro de cambios está pensado para personas [@keepachangelog].
  - Bogart et al. encontraron que pocos usuarios monitorean los cambios de lo que usan, y
    que los avisos generales tienen poca señal frente al ruido [@bogart2021]. Por eso el
    motor muestra solo lo que afecta a *ese* proyecto.
- **Por qué hay que darle al agente el contenido del cambio, no solo la versión.**
  - Los modelos son poco sensibles a que se les indique la versión [@wu2024].
  - Poner en el contexto la documentación del cambio sí mejora mucho a los modelos
    capaces [@liu2025].
  - Recuperar la documentación de la versión correcta ayuda, pero deja más del 40% de los
    problemas sin resolver [@misra2026].
  - Por eso el `que_hacer` va acompañado de guardas del motor (puntos 1 y 5), que no
    dependen de que el agente lo lea.
- **Por qué las instrucciones viejas son peligrosas.** Cuando el contexto usa la API vieja,
  los modelos la reproducen entre el 70% y el 90% de las veces, y una instrucción en el
  prompt no lo corrige, mientras que una intervención determinista sí [@wang2025]. Un
  `AGENTS.md` desactualizado es exactamente ese contexto viejo. La documentación
  desincronizada es, además, el tipo de problema de contenido más frecuente en la
  documentación de software [@aghajani2019].
- **Por qué un bloque con marcadores y no sobrescribir el archivo.**
  - Los archivos de contexto para agentes se editan a mano con frecuencia [@chatlatanagulchai2026]:
    sobrescribirlos borraría el trabajo del usuario.
  - Los agentes siguen bien las instrucciones concretas de estos archivos, pero no los
    resúmenes descriptivos, y cada línea agrega costo [@gloaguen2026]. De ahí que la
    sección sea breve y accionable.
- **Por qué migraciones explícitas, probadas y con copia de respaldo.**
  - La evolución de esquemas es crítica y propensa a errores, y conviene hacerla con
    operadores bien definidos, pasos que se puedan probar y la historia registrada
    [@curino2008prism].
  - En Wikipedia, cerca del 9% de los pasos de evolución fueron vueltas a un esquema
    anterior [@curino2008wiki], lo que justifica la copia de respaldo antes de migrar.
- **Por qué registrar las decisiones de diseño.** Es lo que da sentido a este mismo ADR: las
  decisiones que quedan implícitas se pierden, y con ellas las reglas que imponían
  [@jansen2005].

## Límites de la evidencia

- Los estudios de versionado [@raemaekers2017] [@decan2021] [@bogart2021] son de
  ecosistemas de paquetes, no de frameworks de procesos cuyos usuarios guardan estado y
  una copia de instrucciones. La transferencia es por analogía.
- Los estudios sobre modelos y cambios de versión miden generación de código contra APIs
  de bibliotecas [@wang2025] [@wu2024] [@liu2025] [@misra2026], no agentes que siguen un
  framework. [@wu2024], [@liu2025], [@chatlatanagulchai2026] y [@gloaguen2026] son
  preprints. Las actualizaciones de API de [@liu2025] son sintéticas.
- **Sin respaldo empírico directo, y declaradas como decisiones de ingeniería:**
  - la guarda que impide escribir sobre un proyecto más nuevo (punto 5);
  - la idempotencia de las migraciones;
  - el uso de proyectos fixture por versión.
- La evidencia sobre evolución de esquemas [@curino2008prism] [@curino2008wiki] viene de
  bases de datos relacionales, no de archivos YAML.
- Que el agente muestre la actualización al usuario (punto 7) depende de que lea su
  `AGENTS.md`. Las guardas del motor (puntos 1 y 5) no dependen de eso.

## Alternativas descartadas

- **Solo un `CHANGELOG.md` para personas.** Es lo mínimo, pero ningún agente lo
  consulta por sí solo, pocos usuarios monitorean los cambios [@bogart2021], y el número
  de versión solo no le sirve al modelo [@wu2024].
- **Migrar en silencio al cargar el estado.** Reescribir el `state.yml` de un proyecto sin
  mostrarlo ni respaldarlo contradice la idea de pasos explícitos que se puedan
  probar [@curino2008prism]. Tampoco es aceptable en proyectos donde el estado es evidencia.
- **Sobrescribir el `AGENTS.md` entero en cada actualización.** Borraría las reglas que
  cada proyecto agregó [@chatlatanagulchai2026].
- **Congelar una copia del motor dentro de cada proyecto.** Da estabilidad, pero el
  proyecto deja de recibir correcciones, incluidas las de seguridad de sus compuertas
  (ADR-001). Sigue siendo posible fijar una versión apuntando `IEF_HOME` a una etiqueta del
  repositorio. Este ADR no lo prohíbe, pero no lo adopta como mecanismo.
- **Declarar ya la versión 1.0.0.** SemVer sugiere hacerlo cuando el software se usa en
  producción [@semver2]. Es una decisión de quien mantiene el repositorio, independiente
  de esta: la política del punto 1 aplica igual antes y después de 1.0.

## Cómo se verifica

- `tests/test_actualizacion.py` corre sobre cada fixture de `tests/fixtures/proyectos/`
  lo descrito en el punto 8.
- Un test comprueba que cada versión en `bundle.yml` tenga su sección en `CHANGELOG.md` y
  su bloque en `core/cambios.yml`, aunque esté vacío.
- Un test comprueba que el motor se niega a escribir sobre un proyecto con `ief_version`
  mayor que la suya.
- Un test comprueba que `migrate` sobre un `AGENTS.md` con texto propio fuera de los
  marcadores deja ese texto intacto byte a byte.
- `check-bundle` valida el esquema de `core/cambios.yml`, y que todo `migracion:` nombre
  una migración que existe.

## Consecuencias

- **Para un proyecto largo que ya usa el IEF** (en 0.14.0): al actualizar el bundle, nada
  se rompe.
  - `doctor` y `status --json` informan que hay una actualización.
  - `upgrade-notes` explica los cambios.
  - `migrate` agrega `ief_version` y la sección con marcadores al `AGENTS.md`, sin borrar
    lo que el proyecto había escrito.
- **Para los agentes:** al abrir una sesión, `status --json` les dice si el proyecto está
  desactualizado y qué hacer, en vez de que lo descubran cuando un comando falla.
- **Para quien mantiene el bundle:** cada cambio de comportamiento exige una entrada en
  `cambios.yml` con su `que_hacer`, y cada versión publicada, un fixture. Es trabajo
  adicional en cada versión, y es el precio de que actualizar no rompa proyectos.
- **Orden de implementación:** este ADR va antes que ADR-001. Así, los campos nuevos de la
  firma llegan a los proyectos como la primera entrada del registro de cambios, con su
  `que_hacer`.
