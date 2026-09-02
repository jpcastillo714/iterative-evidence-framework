* **Especificaciones YAML-First:** Prioriza el diseño de pipelines, esquemas y transformaciones en YAML antes de escribir código Python/SQL.
* **Calidad de Datos:** Todo pipeline debe incluir verificaciones explícitas de calidad de datos en sus extremos (entradas y salidas).
* **Fuentes Claras:** Los datos fuente o las configuraciones de conexión a ellos deben documentarse en `initiative/sources/`.
* **Ciclos de Trabajo (IEF V3):** Usa incrementos tipo `exploration` (Objetivo, Análisis, Contrato, Hallazgos) para descubrir la forma de los datos crudos, perfilar volumetrías y validar asunciones antes de construir el pipeline. Usa incrementos tipo `build` (7 pasos) para la construcción robusta del pipeline.
* **Puertas de Aprobación Humanas:** En ciclos `build`, solicita revisión (status: `APPROVED`) en Charter (Paso 1), Reglas de Negocio/Transformación (Paso 4), y Tests de Aceptación (Paso 5).
* **Rollback Ligero:** Si los datos reales rompen el contrato de datos asumido, usa `/speckit.ief.rewind` para regresar al Paso 3 o 4, marcar los entregables como `NEEDS_REVISION` y reajustar.
