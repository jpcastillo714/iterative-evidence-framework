## Preset `astro-mlops` — reglas operativas

Proyecto de detección de anomalías sobre telemetría de instrumentación. Rigor académico
del preset `academic` más la disciplina de trazabilidad de un pipeline de MLOps.

### Ciclos y puertas

* **Ciclos de trabajo (IEF V3):** `exploration` para auditar telemetría, perfilar canales y
  probar hipótesis de modelado; `build` (7 pasos) para construir pipelines, detectores y
  cualquier resultado que se cite en el informe.
* **Puertas humanas:** Paso 1 (Hipótesis y Alcance), Paso 4 (Reglas del Detector) y Paso 5
  (Criterios Operacionales). Detente y pide aprobación explícita. No la asumas.
* **Rewind, no parche:** si los datos nuevos rompen el contrato, si el detector resulta
  inviable bajo las reglas aprobadas o si aparece deriva de régimen, usa
  `/speckit.ief.rewind` al Paso 3 o 4. Ajustar un umbral a mano para que "pase" es
  falsificación de evidencia.

### Contrato de telemetría (Paso 3) — antes de modelar nada

* **Clase antes que valor.** Ningún canal entra a un modelo sin `clase` declarada:
  `medicion` · `consigna` · `comando` · `ambiente` · `derivada` · `descartada`.
  Alimentar una consigna a un detector como si fuera una medición produce un modelo que
  aprende el calendario de operación, no la salud del equipo.
* **Unidades y factores de escala explícitos.** Un canal sin unidad declarada es un canal
  sin contrato. Documenta el `factor_a_fisica` cuando el PLC entrega enteros escalados.
* **Centinelas, no ceros.** Los valores imposibles (0 mbar, 0 °C, −999) son centinelas de
  "sin lectura": se convierten a NaN y se declaran. Nunca se imputan en silencio.
* **Conjunto cerrado de valores para canales de estado.** Declara `valores_observados`.
  Que aparezca un valor nuevo es un evento de contrato, no una anomalía del equipo: puede
  ser un cambio de firmware, de configuración o de versión del archivador.
* **Ejecutable, no declarativo.** El contrato se valida contra los datos reales con
  `presets/astro-mlops/scripts/validate_data_contract.py`. Un contrato que nadie ejecuta es un comentario.
* Plantilla: `core/steps/03_data_contracts/template.telemetry.yml`.

### Segmentación y fuga de información

* **La unidad de análisis es el episodio operacional, no la fila ni la serie continua.**
  Define el episodio en el contrato (mismo objetivo, mismo régimen, continuidad temporal).
* **Nunca mezcles regímenes.** Seguimiento continuo y reposicionamiento son procesos
  distintos; un solo punto del régimen equivocado dentro de una ventana destruye la
  correlación y produce un falso positivo garantizado.
* **Particiones temporales y por episodio.** Nada de `shuffle`, nada de partición por fila.
  El conjunto de prueba va después del de entrenamiento en el tiempo.
* **El escalador se ajusta solo sobre entrenamiento nominal.** Vale para normalizadores,
  PCA, umbrales, cuantiles y cualquier estadístico global.

### Modelado

* **Modelo base explícito y dominio de validez declarado.** Si el detector opera sobre el
  residuo de un modelo físico o estadístico, ese modelo tiene un rango de validez. Fuera de
  él, el detector **se abstiene** (`no_evaluable`) en vez de alarmar. El error del modelo
  base disfrazado de anomalía es la primera fuente de falsos positivos.
* **El error de reconstrucción no es la métrica de anomalía.** Enfoque híbrido: extractor
  → espacio latente → detector clásico con distancia calibrada.
* **Un modelo por régimen o por unidad cuando la evidencia lo exija.** Si el nominal difiere
  entre equipos, un modelo único es una decisión que hay que justificar, no un ahorro.

### Sin etiquetas: el banco sintético (Paso 5)

* Cuando no hay historial de fallas, **el ground truth se fabrica y se declara**:
  `presets/astro-mlops/scripts/inject_faults.py` inyecta deriva lenta, fricción/stiction, juego mecánico,
  pérdida de ganancia, salto de encoder, ruido creciente, cuantización, valor congelado y
  dropouts, con severidad expresada en **unidades de σ nominal**.
* El manifiesto de inyección (`injections.yml`) es un **artefacto de evidencia**: sin él, la
  métrica no es reproducible ni citable.
* La inyección sintética **no reemplaza** la validación contra mantenimiento real: la
  antecede y la hace posible. Declara siempre esa limitación en el informe.

### Evaluación (Paso 7) — lo que se reporta y lo que no

* **Métricas obligatorias:** precisión/exhaustividad **por eventos**, **falsas alarmas por
  noche** (o por unidad operacional), y **lead time** de detección. Un F1 puntual sin FAR
  operacional no le dice nada a quien opera el instrumento.
* **Point-adjust:** permitido solo si se reporta junto a la métrica por eventos y al delta
  entre ambas. Infla resultados de forma conocida; presentarlo solo es engañoso.
* **Umbral calibrado sobre nominal**, con el cuantil declarado. Nunca se elige el umbral que
  maximiza F1 en el conjunto de evaluación.
* Herramienta: `presets/astro-mlops/scripts/eval_anomaly.py`. Protocolo completo:
  `presets/astro-mlops/docs/anomaly_detection_evaluation_protocol.md`.

### Trazabilidad y reproducibilidad

* **Toda cifra publicable proviene de un run registrado.** `core/scripts/evidence_run.py`
  ejecuta el comando, captura stdout/stderr/exit code/duración y emite la carpeta
  `VRN-<INC>-<TST>-<n>/` con su `metadata.yml`, `result.yml` y `artifacts.yml`.
* **Enlace MLflow ↔ IEF.** Si MLflow está disponible, el run se etiqueta con
  `ief.increment`, `ief.claim`, `ief.criterion`, `ief.test` y el `run_id` se escribe en
  `artifacts.yml`. Así, desde una afirmación del informe se llega al dato, al commit, a la
  semilla y a la figura. Detalle: `presets/astro-mlops/docs/mlops_traceability_spec.md`.
* **Datos versionados.** La telemetría cruda es de solo lectura y se referencia por hash
  (DVC). Los derivados se regeneran con un comando; si no se pueden regenerar, no existen.
* **Configuración fuera del código.** Hiperparámetros, rutas y ventanas en `04_codigo/conf/`.
  Cero rutas absolutas en el código fuente.
* **Semilla fija y declarada** en todo experimento con componente estocástica.

### Anti-alucinación

* Una cifra sin script que la reproduzca es `PENDING`, no un resultado.
* Una interpretación de un canal sin diccionario oficial se marca como **inferida** y se
  registra en la tabla de información pendiente del charter.
* Los huecos del archivado no son ceros, no son paradas del equipo y no son anomalías
  mientras no exista un registro externo que lo confirme.
