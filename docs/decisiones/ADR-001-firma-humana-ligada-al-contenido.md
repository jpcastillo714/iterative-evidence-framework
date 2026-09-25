# ADR-001: Firma humana ligada al contenido y al canal por el que se dio

## Estado

Aceptada (2026-09-24)

## Contexto

Las compuertas humanas son la garantía 2 del IEF: ciertas decisiones (el alcance de un
trabajo, las reglas que van a gobernar el proyecto, el criterio con que se juzgará si algo
funciona) las firma una persona, y el motor no deja avanzar sin esa firma. Hoy la firma
tiene dos huecos, y ambos se reproducen con el motor 0.14.0.

**1. Cualquier proceso puede firmar en nombre de cualquiera.** `cmd_approve_step`
(`core/scripts/verify_frame.py`) guarda `approved_by = --by` o, si falta, la variable
`USER`. No hay otra comprobación. Un agente que ejecuta el motor puede registrar la firma
de otra persona sin que nada lo distinga de una firma real.

**2. La firma no queda ligada a lo que se firmó.** La aprobación guarda quién y cuándo,
pero no qué contenido tenía el artefacto en ese momento. Si el artefacto cambia después,
la compuerta sigue aprobada.

Reproducción sobre un proyecto nuevo (`--preset generic`, incremento `prototype`), con
entrada estándar cerrada, es decir, sin nadie en una terminal:

```text
$ verify_frame.py --mode approve-step --by "Ana (responsable)" </dev/null
[APPROVED] paso 1: Hipótesis y Criterio de Éxito

state.yml →  approvals:
               1_charter:
                 approved_by: Ana (responsable)

$ echo "Criterio de exito: CUALQUIER resultado sirve." >> .../001_alfa/charter.md
$ verify_frame.py --mode check-gates
  PASS  001_alfa · paso 1 (Hipótesis y Criterio de Éxito) APPROVED
[OK] todas las compuertas alcanzadas estan aprobadas
```

El criterio de éxito cambió después de la firma y `check-gates`, que es condición de
merge, respondió que todo estaba en orden.

Hoy la garantía depende de que el agente lea y respete una instrucción («pedirte que
hagas algo no es aprobarlo»). El framework no la hace cumplir.

A esto se suma un fallo ya documentado en `docs/ESTADO_Y_PENDIENTES.md` §5.1:
`approve-step` acepta `--increment` pero no lo lee, así que la firma cae siempre sobre el
incremento enfocado, y el mensaje no dice sobre cuál. Se corrige aquí porque es la misma
función.

## Decisión

1. **La firma guarda la huella del artefacto.** Al aprobar un paso que produce un
   artefacto, `approve-step` registra `artifact_sha256` (SHA-256 del archivo). Un paso sin
   artefacto registra `null`.
2. **Una firma sobre un contenido que cambió está vencida.** `check-gates` recalcula la
   huella de cada artefacto aprobado. Si no coincide, informa `aprobación vencida: el
   artefacto cambió después de la firma` y sale con código 1. `doctor` lo reporta como
   problema. El estado del paso no se modifica al leerlo: se informa, y la persona decide.
3. **Volver a firmar un paso vencido.** `approve-step --increment <slug> --step <ref>`
   acepta un paso `APPROVED` cuya huella ya no coincide, y registra la nueva firma. El
   historial conserva las dos.
4. **La firma registra el canal por el que se dio.** `approved_via` vale:
   - `interactive` cuando la entrada y la salida estándar son una terminal y la persona
     confirma escribiendo el slug del incremento;
   - `declared` en cualquier otro caso, que es el comportamiento de hoy.
5. **Cada proyecto elige cuánto exige.** Si `state.yml` declara
   `initiative.gates.require_interactive: true`, `approve-step` rechaza las firmas
   `declared`. Si no, las acepta y `doctor` las reporta como aviso. El valor por defecto
   en esta versión es `false`; si cambia, lo decide otro ADR según la política de
   [ADR-002](ADR-002-compatibilidad-entre-versiones.md).
6. **Se corrige `--increment`.** `approve-step` (y `advance`, que tiene el mismo fallo)
   actúan sobre el incremento pedido, y la salida lo nombra:
   `[APPROVED] 001_alfa · paso 1: …`.

El punto 1 tiene una consecuencia que conviene explicitar. Cuando el paso aprobado es el
de criterios de aceptación, **la firma congela los criterios**: si alguien los edita
después, la compuerta se vence y hay que volver a firmar.

## Evidencia

- **La revisión del propio autor no funciona como control externo.** Sin retroalimentación
  externa, pedirle a un modelo que revise su propia respuesta no mejora el razonamiento y
  a veces lo empeora [@huang2024]. La autocorrección solo es confiable cuando hay una
  señal externa fiable [@kamoi2024]. Una aprobación que registra el mismo agente que hizo
  el trabajo es, en la práctica, una autorrevisión.
- **La verificación es un modo de falla frecuente en sistemas de agentes.** En la
  taxonomía MAST, la verificación ausente o incompleta y la verificación incorrecta suman
  el 17,3% de las fallas anotadas, y muchos verificadores se quedan en comprobaciones
  superficiales [@cemri2025].
- **Ligar un paso firmado al hash de sus productos es la forma establecida de detectar
  alteraciones posteriores.** in-toto registra, en cada paso de una cadena, los hashes de
  sus entradas y salidas, para que un verificador detecte cualquier cambio entre pasos
  [@torresarias2019].
- **La autorización debe venir de un canal que el contenido no puede escribir.** CaMeL
  separa el flujo de control, que sale solo de la consulta confiable del usuario, de los
  datos no confiables [@debenedetti2025]. Michael y Roesner distinguen la *derivación* de
  una política a partir de lo que el usuario pidió, de su *aplicación* en tiempo de
  ejecución [@michael2026]. El hueco 1 es justamente que el motor no separa ambas cosas:
  «el usuario me pidió el charter» termina registrado como «el usuario aprobó el
  charter». Registrar el canal (`approved_via`) hace visible esa diferencia.
- **Cuánta autonomía tiene un agente es una decisión de diseño explícita.** Por eso el
  punto 5 la deja en manos de cada proyecto [@feng2025].
- **La compuerta sobre los criterios es la que más vale proteger.** Cuando el código del
  agente es difícil de revisar, los desarrolladores delegan la verificación en los tests
  [@dhanorkar2026]. Y los agentes con acceso a los tests los explotan: dejarlos en solo
  lectura reduce la trampa, aunque no la elimina [@zhong2026].
- **Una instrucción no reemplaza una comprobación del motor.** En el uso de APIs
  obsoletas, una intervención determinista corrige la mayoría de los casos, mientras que
  agregar la instrucción al prompt no alcanza [@wang2025].

## Límites de la evidencia

- Ninguno de los trabajos citados estudia compuertas de aprobación en un framework de
  procesos como este. La evidencia sobre autocorrección [@huang2024] [@kamoi2024] viene
  de tareas de razonamiento; aquí se usa por analogía.
- El caso de ChatDev en MAST (25,0% → 34,4% → 40,6%) es chico (32 tareas), sin
  repeticiones, y sus autores no lo consideran una mejora sustancial [@cemri2025]. No se
  cita como prueba de que una jerarquía de aprobación funciona.
- ImpossibleBench [@zhong2026] y el estudio sobre APIs obsoletas [@wang2025] miden tareas
  de programación. Dhanorkar et al. [@dhanorkar2026], CaMeL [@debenedetti2025] y Michael y
  Roesner [@michael2026] son preprints.
- **El canal `interactive` no es un mecanismo de seguridad.** Un proceso que abra una
  pseudoterminal puede simularlo. Protege contra la confusión y la racionalización (un
  agente que cree que el encargo equivale a una aprobación), no contra alguien que quiere
  falsificar la firma. Para eso hacen falta firmas criptográficas.
- **Un hash da integridad, no autenticidad.** Prueba que el contenido no cambió desde la
  firma, pero no quién firmó. in-toto usa firmas para ambas cosas [@torresarias2019]; este
  ADR adopta solo la parte de integridad.
- Detectar ediciones mostró poco valor como detector de trampas en EvilGenie
  [@gabor2025]. Aquí el objetivo es distinto: la huella no busca descubrir intenciones,
  sino invalidar una firma cuyo objeto ya no existe. Su valor no depende de atrapar a
  nadie.

## Alternativas descartadas

- **Firmas criptográficas (GPG o SSH) por aprobación.** Darían autenticidad además de
  integridad [@torresarias2019], pero exigen gestionar llaves en cada máquina y agregan
  fricción en cada compuerta. Queda abierta para un ADR posterior si el canal
  `interactive` resulta insuficiente.
- **Aprobar con un commit firmado de git.** Ata el framework a que el proyecto use git con
  firma de commits, y no todos lo hacen.
- **Exigir terminal interactiva por defecto desde ya.** Rompería de golpe los flujos no
  interactivos de hoy (integración continua, scripts, la propia suite del bundle) sin el
  período de aviso que fija ADR-002.
- **Reforzar solo la documentación.** Es la situación actual. La plantilla de `AGENTS.md`
  y la skill ya dicen que pedir no es aprobar, y la reproducción de arriba muestra que el
  motor no lo impide.
- **Integrar un canal externo de aprobación (mensajería, tablero de tareas).** El bundle
  no puede conocer los sistemas de cada usuario. `approved_via` deja el campo listo para
  que un canal así se agregue sin cambiar el esquema.

## Cómo se verifica

Tests de regresión nuevos, en `tests/`:

1. Aprobar un paso y modificar su artefacto: `check-gates` sale con código 1 y nombra el
   incremento, el paso y la causa. `doctor` lo lista como problema.
2. Volver a firmar el paso vencido con `--increment` y `--step`: `check-gates` vuelve a
   pasar, y el historial conserva ambas firmas.
3. Aprobar sin terminal registra `approved_via: declared`, y `doctor` lo reporta como
   aviso.
4. Con `require_interactive: true`, aprobar sin terminal falla con un mensaje que explica
   cómo firmar.
5. `approve-step --increment X` con el foco en Y firma X, y la salida lo nombra. Lo mismo
   para `advance`. Es la regresión del §5.1.
6. Una firma anterior a este cambio, sin `artifact_sha256`, no hace fallar `check-gates`.
   `doctor` la reporta como «firma sin huella». Es el requisito de compatibilidad de
   ADR-002.

Además de los cuatro chequeos del bundle y de `verificar_skills.py`.

## Consecuencias

- **Para los proyectos existentes:** los campos `artifact_sha256` y `approved_via` se
  agregan. No se renombra ni se quita nada. Las firmas antiguas siguen valiendo y `doctor`
  las identifica. Es un cambio de tipo *añadido* en los términos de ADR-002, y va en su
  registro de cambios con la acción concreta para los agentes.
- **Para los agentes:** si `check-gates` informa una aprobación vencida, el agente no
  vuelve a firmar. Le muestra a la persona qué cambió y le pide la firma. La plantilla de
  `AGENTS.md`, la skill `ief-workflow` y las secciones 3, 26, 27 y 29 de la guía se
  actualizan en el mismo cambio.
- **Para quien firma:** editar un artefacto aprobado ya no es silencioso. Esto es
  intencional: es la única forma de que la firma signifique «aprobé *esto*».

## Notas de implementación

Implementado en 0.15.0. Precisiones respecto del texto aceptado:

- **La huella normaliza los fines de línea** (CRLF → LF) antes de calcular el SHA-256. Sin
  eso, clonar el proyecto en otro sistema operativo, donde git convierte los fines de
  línea, vencería todas las firmas sin que nadie hubiera cambiado una palabra.
- **También se puede volver a firmar una firma sin huella**, no solo una vencida (punto
  3). Es la forma de que una persona certifique una firma anterior a 0.15.0 si quiere
  hacerlo. Una firma vigente no se vuelve a firmar.
- **Cómo declara un proyecto su política** (punto 5): con `--mode gate-policy
  --require-interactive on|off`, para no pedirle a nadie que edite `state.yml` a mano.
  Apagar la exigencia requiere estar en una terminal: si un agente pudiera apagarla,
  podría apagarla y firmar después.
- **`advance` tampoco pasa sobre una firma vencida.** El punto 2 nombraba `check-gates` y
  `doctor`; dejar que `advance` avance sobre una compuerta cuyo objeto cambió contradecía
  el punto 2.
- **`doctor` resume** las firmas declaradas y las sin huella en una línea cada una, y
  solo cuenta las de incrementos abiertos. Las vencidas se listan una por una, como
  problemas.
