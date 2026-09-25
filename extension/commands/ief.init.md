---
name: "ief.init"
description: "Inicializa el entorno IEF en un proyecto"
step_number: null
---

# Inicializar IEF (`/speckit.ief.init`)

## Proposito

Prepara la estructura de directorios, el estado persistente y las reglas del agente.
La estructura **la decide el preset**, no este comando.

## Dos decisiones, no una

`init` fija los dos ejes que se eligen una vez por proyecto:

```bash
python core/scripts/verify_frame.py --mode init     --preset analysis --layout numbered --initiative-name "Mi proyecto"
```

| Eje | Opciones | Qué decide |
|---|---|---|
| `--preset` | `generic` `research` `product` `analysis` `product-modeling` (+ mixin `modeling`) | Vocabulario y ceremonia |
| `--layout` | `flat` `numbered` | Cómo se llaman las carpetas |

Son **independientes**: un proyecto de análisis puede usar carpetas numeradas y una
tesis puede usar `src/`. El layout es cuestión de herramientas y gusto, no de tipo de
trabajo.

El tercer eje —cuánto rigor lleva cada trabajo— **no se decide aquí**: se elige en cada
incremento con `--type task | exploration | prototype | build`.

## Protocolo

1. Elegir el preset con el usuario. Ver los disponibles y su ciclo:

   ```bash
   python core/scripts/verify_frame.py --mode check-preset
   ```

   | Preset | Para que |
   |---|---|
   | `generic` | Cualquier proyecto de software o iniciativa estandar. |
   | `product` | Sistemas que se despliegan y alguien mantiene: pipelines, ETL, servicios. |
   | `research` | Tesis, papers, experimentos: el entregable es un documento defendible. |
   | `analysis` | Preguntas que se responden con datos; el producto es una respuesta con su metrica. |
   | `product-modeling` | `product` + un modelo entrenado dentro, con model card y compuerta propia. |
   | `modeling` | Mixin: **no se usa solo**. Aporta el paso 6b a otro preset (`extends: [analysis, modeling]`). |

   La lista real la da `--mode check-preset`, con el ciclo y las compuertas de cada uno.
   Si esta tabla y esa salida no coinciden, manda la salida.

2. Inicializar. Esto crea los directorios del preset, `initiative/state.yml` y
   `initiative/specs/`:

   ```bash
   python core/scripts/verify_frame.py --mode init \
       --preset <preset> --initiative-name "<nombre>"
   ```

3. Generar `AGENTS.md` en la raiz combinando `core/templates/agents-template.md` con
   `presets/<preset>/agents-fragment.md`. Si ya existe, hacer append, nunca sobrescribir.

4. Ofrecer crear el primer incremento: `/speckit.ief.charter` (build) o
   `/speckit.ief.explore` (exploration).

## Reglas

- **No crear directorios a mano.** Las rutas las deciden el catalogo de roles
  (`core/roles.yml`) y el layout (`core/layouts.yml`), no el preset. Si falta un tipo de
  carpeta, se anade el rol ahi, se incluye en `roles:` del preset y se vuelve a ejecutar
  `init`.
- **No editar `state.yml` a mano.** Es la maquina de estados: se toca con
  `verify_frame.py`. Editarlo directamente rompe el historial y las aprobaciones.

## Postcondiciones

- Existe `initiative/state.yml` con `schema_version: "4.0"` y la lista de incrementos vacia.
- Existen los directorios que declara el preset elegido.


## Después de init

1. **Escribe la constitución.** `init` la crea desde plantilla en
   `initiative/specs/constitution.md`, vacía. Son los principios bajo los que vas a
   trabajar, y las reglas que descubras vivirán debajo de ellos.
2. **Abre el primer incremento** con el ciclo que pida el trabajo:
   ```bash
   python core/scripts/verify_frame.py --mode new-increment --type build --name "..."
   ```
