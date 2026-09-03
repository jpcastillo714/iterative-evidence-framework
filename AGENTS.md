# AGENTS.md — Léeme antes de tocar nada

## ⛔ Este directorio NO es un proyecto de trabajo

Esto es el **bundle del framework**: la plantilla, el molde, el esquema. No es un
proyecto en curso y **no se trabaja aquí dentro**.

Concretamente, dentro de este directorio **nunca**:

- crees `initiative/`, `state.yml`, incrementos, charters ni artefactos de ningún paso;
- ejecutes `--mode init` apuntando a esta carpeta;
- añadas datos, notebooks, modelos, resultados ni código de ningún proyecto;
- introduzcas nada que mencione un proyecto, cliente, instrumento, dataset o tesis
  concretos.

El IEF **se aplica a otros repositorios**, no a sí mismo. Un `initiative/` aquí significa
que alguien confundió el molde con la pieza.

## Cómo se usa de verdad

```bash
cd /ruta/de/tu/proyecto/real            # <-- OTRO directorio
python /ruta/al/spec-kit_bundle/core/scripts/verify_frame.py \
    --mode init --preset data-science --initiative-name "Mi proyecto"
```

El proyecto vive allá. Aquí solo vive el framework que lo gobierna.

---

## Qué sí se hace aquí

Trabajo sobre el framework mismo, y nada más:

| Tarea | Dónde |
|---|---|
| Cambiar el ciclo de un preset | `presets/<id>/preset.yml` |
| Añadir un preset | `presets/<nuevo>/` |
| Cambiar el motor de estado | `core/scripts/verify_frame.py` |
| Cambiar cómo se cargan los presets | `core/scripts/ief_preset.py` |
| Cambiar la traducción YAML → pytest | `core/scripts/compile_acceptance_tests.py` |
| Cambiar plantillas o instrucciones de paso | `core/templates/`, `core/steps/` |
| Cambiar lo que lee un agente | `extension/commands/` |

Después de cualquier cambio:

```bash
python core/scripts/verify_frame.py --mode check-bundle
python core/scripts/verify_frame.py --mode check-preset
python core/scripts/verify_frame.py --mode check-steps
pytest tests/ -q
```

---

## Reglas de contenido

1. **Neutralidad de dominio.** El núcleo (`core/`) no sabe de ningún campo de aplicación.
   Nada de vocabulario específico de un dominio, ni ejemplos atados a un proyecto real.
   Si algo solo sirve para un tipo de trabajo, va en un preset; si solo sirve para *un*
   proyecto, no va en este repositorio.

2. **`core/scripts/` es una lista cerrada:** `verify_frame.py`, `ief_preset.py`,
   `compile_acceptance_tests.py`. Cualquier otro script ahí es código de dominio que se
   coló. `--mode check-bundle` lo detecta y falla.

3. **Un preset trae lo suyo.** Sus scripts, plantillas y documentos viven en
   `presets/<id>/`, nunca en `core/`.

4. **Nada de material generado sin verificar.** Este repositorio ya arrastró informes
   que citaban código inexistente y resultados de tests que nunca se ejecutaron. Si vas a
   escribir que algo funciona, ejecútalo primero y pega la salida.

5. **Si no aporta, no entra.** Sin carpetas de archivo histórico, sin `dist/` con
   versiones viejas, sin informes de fases pasadas, sin borradores. Para eso está el
   historial de git.

---

## Qué es este framework

El **Iterative Evidence Framework (IEF)**: una extensión de
[spec-kit](https://github.com/github/spec-kit) que reemplaza el flujo lineal por ciclos
incrementales, donde el ciclo lo define el preset, los criterios de aceptación se
ejecutan y las compuertas humanas bloquean de verdad.

Detalle del método en [`SKILL.md`](SKILL.md). Uso y presets en [`README.md`](README.md).
