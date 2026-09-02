# /speckit.ief.explore

Inicia un nuevo incremento de tipo `exploration` (ciclo ligero de 3+1 pasos).

## Protocolo
1. Preguntar al usuario qué quiere explorar
2. Generar un slug para el incremento (ej. `004_eda_correlaciones`)
3. Crear el directorio `initiative/increments/<SLUG>/`
4. Crear `initiative/increments/<SLUG>/README.md` desde template
5. Registrar el incremento en `state.yml` como tipo `exploration` con status `ACTIVE`
6. Actualizar `index.yml`
7. Iniciar Paso 1 (Objetivo)

## Pasos del Ciclo Exploration
| Paso | Nombre | Output |
|------|--------|--------|
| 1 | Objetivo | `objective.md` |
| 2 | Análisis | Notebooks, scripts, visualizaciones |
| 2b | Contrato de Datos (opcional) | `data-contract.yml` |
| 3 | Hallazgos | `findings.md` |
