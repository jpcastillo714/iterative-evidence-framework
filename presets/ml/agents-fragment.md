* **Estructura:** configuracion en `conf/` (ningun hiperparametro vive en el codigo), datos en `data/`, pipeline en `pipelines/`, artefactos en `models/`, comparaciones en `experiments/`.
* **Fugas primero:** el Paso 2 busca activamente fuga de informacion antes que cualquier otra cosa. Una feature construida con informacion del futuro produce metricas excelentes e inutiles.
* **La particion se justifica:** temporal, por grupo o aleatoria; el Paso 3 declara cual y por que. Una particion aleatoria sobre datos con estructura temporal o de grupo infla el resultado.
* **El criterio se acuerda antes:** la metrica objetivo y su umbral se aprueban en el Paso 5, antes de existir resultados. Bajar el umbral despues no es aprobar: es cambiar la vara.
* **Paso 6b, Evaluacion del Modelo:** este preset separa "el modelo generaliza" de "el pipeline funciona". Lleva compuerta humana y produce una model card con lo que el modelo NO puede hacer y lo que se probo y fallo.
* **Linea base obligatoria:** un numero sin comparacion no es un resultado. Siempre contra una prediccion trivial y una linea base simple.
* **El conjunto de prueba se toca una vez.** Cada mirada lo gasta como estimacion honesta.
