* **Estructura:** notebooks en `exploracion`, codigo reutilizable en `codigo`, figuras en `resultados`, reportes cortos en `avances`.
* **Solo dos compuertas: la pregunta y los criterios de validez.** Un analisis que no construye nada permanente no necesita aprobar su implementacion. Es una decision del preset, no un descuido.
* **Las definiciones se fijan ANTES de medir.** El paso 4 define que cuenta como "usuario activo", "sesion" o "conversion". Cambiar una definicion despues de ver el resultado invalida la comparacion y es la forma mas comun de enganarse a uno mismo.
* **Los supuestos son parte del contrato.** El paso 3 declara de que depende el analisis: independencia, estacionariedad, ausencia de duplicados. Un supuesto sin verificar es una conclusion sin base.
* **De notebook a codigo:** un notebook es un borrador de razonamiento, no un resultado. Nada se cita sin haber migrado a `src/` con un test.
* **Toda cifra del reporte es regenerable con un comando.** Si no lo hay, es `PENDING`.
