* **Tono Académico:** Redacta todos los documentos formales con un estilo académico riguroso, neutral y estructurado (tipo tesis o artículo científico).
* **Manejo de Citas:** Todo dato empírico, afirmación teórica o referencia debe contar con su debida citación y gestión en la bibliografía.
* **Directorio Numerado:** Respeta estrictamente la jerarquía numerada (00 a 08) para garantizar un orden secuencial que refleje el proceso de investigación.
* **Ciclos de Trabajo (IEF V3):** En investigación empírica, usa incrementos `exploration` para pilotaje, análisis exploratorio o formulación de variables. Usa incrementos `build` (7 pasos metodológicos) para la ejecución estructurada de modelos y verificación formal de hipótesis.
* **Puertas de Aprobación Humanas:** En ciclos `build`, requiere la validación del investigador principal (status: `APPROVED`) al definir la Hipótesis/Alcance (Paso 1), Reglas del Modelo (Paso 4), y Criterios de Evaluación (Paso 5).
* **Rollback Ligero:** Si los datos o resultados no permiten sostener la hipótesis bajo las condiciones dadas, usa `/speckit.ief.rewind` para ajustar el modelo o las reglas, marcando iteraciones previas como `NEEDS_REVISION`.
