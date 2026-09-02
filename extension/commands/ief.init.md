---
name: "ief.init"
description: "Inicializa el entorno IEF V3 en un proyecto"
step_number: null
---

# Inicializar IEF (`/speckit.ief.init`)

## Proposito

Prepara la estructura de directorios, el estado persistente y las reglas del agente.
La estructura **la decide el preset**, no este comando.

## Protocolo

1. Elegir el preset con el usuario. Ver los disponibles y su ciclo:

   ```bash
   python core/scripts/verify_frame.py --mode check-preset
   ```

   | Preset | Para que |
   |---|---|
   | `generic` | Cualquier proyecto de software o iniciativa estandar. |
   | `engineering` | Pipelines, ETL, ingenieria de datos. |
   | `academic` | Tesis, papers, experimentos (numeracion `00_admin` … `08_presentaciones`). |
   | `astro-mlops` | Deteccion de anomalias sobre telemetria. Extiende `academic`. |

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

- **No crear directorios a mano.** Si falta uno, se agrega a
  `presets/<preset>/directory-convention.yml` y se vuelve a ejecutar `init`.
- **No editar `state.yml` a mano.** Es la maquina de estados: se toca con
  `verify_frame.py`. Editarlo directamente rompe el historial y las aprobaciones.

## Postcondiciones

- Existe `initiative/state.yml` con `schema_version: "3.1"` y la lista de incrementos vacia.
- Existen los directorios que declara el preset elegido.
