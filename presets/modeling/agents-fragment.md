* **Estructura:** hiperparametros en `config`, artefactos en `modelos`, corridas y comparaciones en `experimentos`.
* **Paso 6b, Evaluacion del Modelo.** Este mixin separa "el modelo generaliza" de "el pipeline funciona". Son preguntas distintas: un modelo puede pasar todos los tests de integracion y no servir para nada. Lleva compuerta humana y produce una model card.
* **Fugas primero.** El paso 2 busca activamente fuga de informacion antes que ninguna otra cosa. Una feature construida con informacion del futuro produce metricas excelentes e inutiles.
* **La particion se justifica.** Temporal, por grupo o aleatoria; el paso 3 declara cual y por que. Una particion aleatoria sobre datos con estructura temporal o de grupo infla el resultado.
* **El criterio se acuerda antes de ver resultados.** La metrica objetivo y su umbral se aprueban en el paso 5. Bajar el umbral despues no es aprobar: es cambiar la vara.
* **Linea base obligatoria.** Un numero sin comparacion no es un resultado: un F1 de 0.87 puede estar por debajo de predecir siempre la clase mayoritaria.
* **El conjunto de prueba se toca una vez.** Cada mirada lo gasta como estimacion honesta.
