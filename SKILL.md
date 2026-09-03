---
name: iterative-evidence-framework
description: >
  Iterative Evidence Framework (IEF) — extensión de spec-kit con tres ejes separados
  (layout, preset, ciclo), varios frentes de trabajo simultáneos con foco explícito y
  bloqueos tipados, criterios de aceptación que se compilan a pytest, y reglas que se
  descubren en los incrementos y se promueven al proyecto con detección de conflictos.
---

# Iterative Evidence Framework (IEF)

> **El bundle no es un proyecto.** Nunca crees un `initiative/` dentro del directorio del
> framework: el IEF se aplica a otros repositorios. Ver `AGENTS.md` del bundle.

## La regla que gobierna todo lo demás

**Pregúntale al motor, no adivines.** El ciclo, las rutas, las compuertas y las
plantillas salen del preset y el layout activos, y cambian entre proyectos:

```bash
python core/scripts/verify_frame.py --mode status --json
```

Esa salida dice el foco, el paso actual, su `key`, si tiene compuerta y en qué ruta
exacta va su artefacto. **No inventes subcarpetas ni nombres de archivo.**

## Los tres ejes

| Eje | Decide | Se elige |
|---|---|---|
| **Layout** | Cómo se llaman las carpetas (`flat` · `numbered`) | al iniciar el proyecto |
| **Preset** | Vocabulario y ceremonia | al iniciar el proyecto |
| **Ciclo** | Cuánto rigor lleva *este* trabajo | **en cada incremento** |

El rigor es una propiedad del trabajo, no del proyecto: un proyecto serio abre un
incremento `prototype` cuando explora y uno `build` cuando construye en firme.

## Los tres ciclos

| Ciclo | Pasos | Compuertas | Para |
|---|---|---|---|
| `exploration` | 4 | ninguna | Investigar antes de construir |
| `prototype` | 4 | 1 | Descubrir si algo vale la pena |
| `build` | 7 (8 con `modeling`) | 1·4·5 | Construir algo que tiene que aguantar |

Ciclo `build` en el preset `generic`:

| Paso | Artefacto | Compuerta |
|---|---|---|
| 1. Charter | `charter.md` | ✋ |
| 2. Inspección Empírica | `inspection-report.md` | |
| 3. Contratos de Datos | `data-contract.yml` | |
| 4. Reglas | `rules.yml` | ✋ |
| 5. Criterios de Aceptación | `acceptance-tests.yml` | ✋ |
| 6. Implementación | *(código)* | |
| 7. Verificación | `increment-report.md` | |

**Otros presets cambian esta tabla.** El nombre del paso 4 es «Reglas de Negocio» en
`product`, «Reglas del Modelo» en `research` y «Definiciones y Métricas» en `analysis`;
la clave (`4_rules`) y el archivo (`rules.yml`) **no cambian nunca**. Por eso se
consulta, no se memoriza.

## Varios frentes a la vez

`status: ACTIVE` (varios) y `focus` (uno) son cosas distintas. Los comandos sin
`--increment` operan **sobre el foco**.

```bash
verify_frame.py --mode focus                        # ver el foco y los frentes abiertos
verify_frame.py --mode focus --increment 002_panel  # moverlo
```

`PAUSED` es voluntario; `BLOCKED` es forzado y declara su tipo:

```bash
verify_frame.py --mode set-status --increment 001_x --status BLOCKED \
    --blocked-kind external --reason "esperando datos de otro equipo" --expected 2026-09-20
```

`--blocked-kind increment` valida que el bloqueante exista y rechaza ciclos.
`--mode doctor` diagnostica bloqueos vencidos, dependencias imposibles, frentes de más
y reglas sin promover. **Ejecútalo al volver a un proyecto tras un tiempo fuera.**

## Comandos

| Comando | Qué hace |
|---|---|
| `/speckit.ief.init` | Estructura del preset y layout, `state.yml`, constitución |
| `/speckit.ief.constitution` | Escribe los principios del proyecto |
| `/speckit.ief.charter` · `.explore` · `.prototype` | Abre un incremento build, exploration o prototype |
| `/speckit.ief.inspect` · `.contracts` · `.rules` · `.tests` · `.implement` · `.verify` | Los pasos del ciclo build |
| `/speckit.ief.status` · `.focus` · `.doctor` | Estado, foco, diagnóstico |
| `/speckit.ief.next` | Verifica y avanza al siguiente paso |
| `/speckit.ief.pause` · `.rewind` | Pausar; retroceder con motivo declarado |

## Reglas del agente

1. **Anti-alucinación.** Lo que falta se marca `PENDING`. Una cifra sin ejecución detrás
   no es un resultado.

2. **Compuertas humanas.** Los pasos con ✋ no avanzan sin aprobación explícita:
   ```bash
   verify_frame.py --mode approve-step --by "<usuario>"
   ```
   **Nunca escribas `APPROVED` editando `state.yml`.** Eso destruye la constancia que la
   compuerta existe para dejar.

3. **`state.yml` no se edita a mano.** Se toca con `verify_frame.py`, que escribe de
   forma atómica y deja historial.

4. **Comprueba el foco antes de avanzar.** Si hay varios frentes abiertos, `advance` y
   `approve-step` caen sobre el enfocado. Verifica con `--mode focus`.

5. **Los criterios se ejecutan.** Todo test del paso 5 lleva un bloque `verify`. Uno sin
   él **falla**, no se aprueba por omisión. Uno que hoy no se puede medir se marca
   `status: blocked` con su razón; **no se rebaja para que quepa el resultado disponible.**

6. **Si la especificación está mal, se corrige la especificación.** No parchees el código
   para que quepa en una regla equivocada: `--mode rewind` con su motivo.

7. **Un incremento no termina hasta consolidarse.** `--mode merge-increment` promueve sus
   reglas. Sin ese paso, cada incremento guarda su copia y nadie sabe cuál rige.

8. **Zero clutter.** Cada artefacto en la ruta que declara el preset. Lo temporal, en
   `scratch/`.

## Las reglas y sus dos capas

| | **Constitución** | **Reglas promovidas** |
|---|---|---|
| Describe | **Cómo se trabaja** | **Qué es cierto del dominio** |
| Ejemplo | «Ninguna cifra sin evidencia ejecutable» | «Un episodio dura ≥ 5 min» |
| Vive en | `initiative/specs/constitution.md` | `initiative/specs/rules.yml` |
| Dirección | Arriba→abajo | Abajo→arriba |

Una regla lleva su `rationale` **dentro**: separada en una bitácora aparte se
desincroniza siempre. Y lleva `applies_to`, que es lo que permite detectar que dos
incrementos se contradicen. Al promover:

- Dos reglas sobre el mismo `applies_to` sin `supersedes` → **la promoción se detiene**.
- Con `supersedes` → la anterior queda `superseded` apuntando a la nueva, **sin borrarse**.

## Un `failed` admite tres lecturas

Hay que elegir una explícitamente; confundirlas corrompe el informe:

- **Fallo de ejecución** → arreglar el código o el entorno y volver a correr.
- **Hipótesis rechazada** → es un resultado. Va al informe.
- **Verificación bloqueada** → falta un prerrequisito. Se marca `blocked`; no se reporta
  como fracaso de lo que se construyó.

## Presets

| Preset | Para qué |
|---|---|
| `generic` | Base, cualquier proyecto |
| `research` | Tesis, memorias, papers |
| `product` | Sistemas que se despliegan y alguien mantiene |
| `analysis` | Responder preguntas con datos |
| `modeling` | **Mixin**: añade la Evaluación del Modelo. `extends: [analysis, modeling]` |

Un preset puede renombrar pasos, mover compuertas, quitar pasos, insertar pasos o
reemplazar el ciclo entero. El núcleo no conoce ningún dominio.
