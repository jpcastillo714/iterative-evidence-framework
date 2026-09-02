# Instrucciones: Paso 02 - Analysis (Exploration)

| Campo | Valor |
|-------|-------|
| **Inputs** | `objective.md` |
| **Output** | Artefactos de análisis (notebooks, scripts, visualizaciones, métricas) |
| **Human Gate** | NO |
| **Aplica a** | exploration |

## Propósito
Ejecutar el análisis tal como se definió en el objetivo, generando evidencia real y concreta.

## Protocolo
1. Revisa `objective.md` para entender qué datos o sistemas inspeccionar.
2. Produce artefactos de análisis concretos (ej. un Jupyter Notebook con código, consultas SQL, gráficos de resultados, scripts de extracción).
3. Documenta temporalmente hallazgos intermedios si es necesario.
4. Si durante tu análisis descubres estructuras de datos que necesitan formalización estricta (esquemas), entonces procede de forma opcional al paso `2b_data_contract` antes de cerrar la exploración.

## Criterios de Calidad
- Los artefactos generados deben ser transparentes, reproducibles o demostrables.
- No basta con afirmaciones sin respaldo; el output debe incluir el cómo se analizaron los datos.
