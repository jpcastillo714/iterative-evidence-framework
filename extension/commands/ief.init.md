---
name: "ief.init"
description: "Inicializa el entorno IEF V3 en un proyecto existente o nuevo"
step_number: null
---

# Inicializar IEF (`/speckit.ief.init`)

## Propósito
Prepara la estructura de directorios, el estado inicial y las reglas del agente para ejecutar ciclos IEF (build y exploration) con soporte multi-incremento.

## Precondiciones
- Ninguna. Opcionalmente, recibe un argumento `--preset` (generic | engineering | academic). Default: `generic`.

## Protocolo de Ejecución

### 1. Determinar el Preset
- Cargar la convención de directorios desde `presets/<preset>/directory-convention.yml`.

### 2. Crear Estructura de Directorios
Según el preset seleccionado, crear los directorios base:
```
initiative/
initiative/increments/
initiative/sources/
scratch/
src/
tests/
```

### 3. Inicializar Estado Persistente (V3)
- Crear `initiative/state.yml` con el esquema V3.
- Definir el estado general del proyecto y dejar la lista de incrementos vacía.

### 4. Generar AGENTS.md
- Usar `core/templates/agents-template.md` como base.
- Insertar el contenido de `presets/<preset>/agents-fragment.md`.
- Escribir `AGENTS.md` en la raíz. Si existe, hacer append.

### 5. Iniciar un Incremento (Opcional)
- Preguntar al usuario si desea crear un incremento de tipo `build` o `exploration`.
- Si responde sí, llamar a `/speckit.ief.charter` (para build) o `/speckit.ief.explore` (para exploration).

### 6. Confirmar al Usuario
Imprimir resumen:
```
✅ IEF V3 inicializado con preset: <preset>
📁 Estructura creada
📄 state.yml inicializado (Multi-incremento)
📄 AGENTS.md generado
```

## Postcondiciones
- Proyecto tiene estructura IEF.
- `initiative/state.yml` existe en formato V3.
