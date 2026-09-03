* **Estructura:** datos en `data/` (`raw/` es SOLO LECTURA), codigo reutilizable en `src/`, exploracion en `notebooks/`, salidas en `reports/`.
* **De notebook a codigo:** nada de un notebook se cita en un informe sin haber migrado a `src/` con un test. Un notebook es un borrador de razonamiento, no un resultado.
* **Los supuestos son parte del contrato:** el Paso 3 declara no solo los tipos, sino los supuestos de los que depende el analisis (independencia, estacionariedad, ausencia de duplicados). Un supuesto sin verificar es una conclusion sin base.
* **Las definiciones se fijan antes de medir:** el Paso 4 define que cuenta como "cliente activo", "sesion" o "conversion". Cambiar una definicion despues de ver el resultado invalida la comparacion.
* **Toda cifra del informe es regenerable:** debe existir un comando que la produzca. Si no lo hay, la cifra es `PENDING`.
