* **Estructura Estándar:** Mantén el código fuente en `src/` y las pruebas en `tests/`.
* **Uso de Scratch:** Utiliza la carpeta `scratch/` para scripts de prueba temporales que no deben formar parte del código base final.
* **Ciclos de Trabajo (IEF V3):** Este proyecto soporta incrementos tipo `build` (7 pasos para desarrollo formal con entregables estructurados) y `exploration` (3+1 pasos ligeros para investigar y analizar antes de construir).
* **Puertas de Aprobación Humanas:** En los ciclos `build`, debes solicitar explícitamente la revisión y aprobación del usuario (status: `APPROVED`) antes de avanzar desde el Paso 1 (Charter), Paso 4 (Business Rules), y Paso 5 (Acceptance Tests).
* **Rollback Ligero:** Si durante la implementación o verificación descubres que una regla o contrato es inviable, usa el comando `/speckit.ief.rewind` para retroceder al paso correspondiente y marcar los entregables intermedios como `NEEDS_REVISION`.
