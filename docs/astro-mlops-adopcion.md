# Adoptar el preset `astro-mlops` en un proyecto ya iniciado

Guía de migración para un proyecto que ya corre bajo el preset `academic` y quiere sumar la
capa de trazabilidad MLOps sin rehacer nada.

**Coste de migración: cero movimientos de archivo.** `astro-mlops` extiende `academic` y
conserva la numeración `00_admin/` … `08_presentaciones/`. Todo lo que añade es aditivo.

---

## 1. Cambio de preset (5 minutos)

1. En `initiative/state.yml`:

   ```yaml
   initiative:
     preset: "astro-mlops"    # antes: academic
   ```

2. En `AGENTS.md`, reemplazar el fragmento del preset por
   `presets/astro-mlops/agents-fragment.md`. El resto del archivo (contexto del proyecto,
   invariantes, trampas conocidas de los datos) se conserva tal cual: es más valioso que
   cualquier plantilla.

3. Registrar el cambio en el historial del incremento activo. Un cambio de preset es una
   decisión metodológica, no un detalle de configuración.

Nada más. Los incrementos existentes siguen válidos, los pasos completados siguen completados
y los alias de paso solo cambian de nombre visible.

---

## 2. Crear los directorios nuevos, cuando hagan falta

```
04_codigo/conf/                 configuración declarativa (Hydra)
04_codigo/pipelines/            etapas reproducibles
05_datos/benchmark_sintetico/   banco de fallas + manifiesto
06_resultados/experimentos/     mlruns/ y reportes de evaluación
```

Crearlos vacíos por adelantado solo genera ruido. Se crean cuando el incremento los usa.

---

## 3. Formalizar el contrato de telemetría que ya existe

Si el proyecto ya tiene un `data-contract.yml` escrito a mano en el incremento de
exploración, **no se reescribe desde cero**: se le añaden las claves que lo vuelven
ejecutable.

| Ya lo tienes | Añade | Para qué |
|---|---|---|
| descripción por canal | `clase:` | impedir que una consigna entre a un modelo como si midiera |
| unidades en prosa | `unidad:` y `factor_a_fisica:` | que el validador pueda comprobar rangos |
| rangos observados | `rango_valido:` (dominio físico) | separar violación de contrato de anomalía real |
| valores vistos de un canal de estado | `valores_observados:` | detectar un valor nuevo el día que aparezca |
| centinelas descritos | `centinela:` | contarlos en vez de comerlos como dato |
| reglas de consolidación | `tiempo:` (monótono, duplicados, hueco mínimo) | auditar el eje temporal |
| el dominio donde el modelo base vale | `dominio_de_validez:` | que el detector se abstenga en vez de alarmar |

Referencia: [`core/steps/03_data_contracts/template.telemetry.yml`](../core/steps/03_data_contracts/template.telemetry.yml).

Luego, ejecutarlo:

```bash
python presets/astro-mlops/scripts/validate_data_contract.py \
    --contract initiative/increments/<SLUG>/data-contract.yml \
    --data 05_datos/processed/<archivo>.parquet \
    --report 06_resultados/experimentos/contrato_report.json
```

La primera ejecución casi siempre encuentra algo. Eso es la señal de que valía la pena.

**Efecto secundario más útil que el contrato mismo:** cuando lleguen datos nuevos —otro
periodo, otra unidad, otra extracción— el validador dirá en segundos si el mundo cambió. Sin
él, ese cambio se descubre semanas después, disfrazado de resultado de modelado.

---

## 4. Fabricar el ground truth que falta

Si el periodo analizado resultó enteramente nominal, no hay eventos positivos y no hay recall
que reportar. El banco sintético convierte esa pared en un resultado:

```bash
python presets/astro-mlops/scripts/inject_faults.py bench \
    --data 05_datos/processed/episodios.parquet \
    --column residuo --out 05_datos/benchmark_sintetico \
    --params params.yaml
```

Recomendaciones al configurarlo:

- Inyectar sobre la **variable objetivo del detector** (típicamente el residuo respecto del
  modelo base), no sobre la señal cruda.
- Mantener la fracción anómala por debajo del 10 %. La herramienta avisa sobre 20 %.
- Incluir siempre `valor_congelado`: es el fallo más común de una cadena de adquisición y el
  que más detectores basados en desviación pasan por alto, porque la varianza **cae**.
- Versionar `injections.yml`. Es el artefacto que hace reproducible cada número de sensibilidad.

Y decirlo en el informe con todas sus letras: las fallas sintéticas **acotan** la sensibilidad,
no demuestran detección de una falla real futura.

---

## 5. Evaluar según el protocolo

```bash
python presets/astro-mlops/scripts/eval_anomaly.py \
    --scores 06_resultados/experimentos/scores.parquet \
    --labels 05_datos/benchmark_sintetico/injections.yml \
    --calib  06_resultados/experimentos/scores_nominal_train.parquet \
    --quantile 0.999 --k-de-n 3 5 --horas-por-unidad 10 \
    --report 06_resultados/experimentos/evaluacion.json
```

`--calib` es la diferencia entre un número publicable y uno optimista: sin él, el umbral se
calibra sobre los negativos del propio conjunto de evaluación y el reporte lo denuncia en su
sección de advertencias.

La salida trae la tabla `recall(tipo, severidad)`. Esa tabla, no un F1 global, es lo que
responde la pregunta que hará la comisión: *¿qué detecta y desde qué severidad?*

Protocolo completo: [`presets/astro-mlops/docs/anomaly_detection_evaluation_protocol.md`](../presets/astro-mlops/docs/anomaly_detection_evaluation_protocol.md).

---

## 6. Cerrar la cadena de evidencia

Desde que el preset está activo, toda cifra que vaya al documento nace de un run registrado:

```bash
python core/scripts/evidence_run.py \
    --test TST-ACC-007 --claim CLM-003-001 --criterion CRT-003-002 \
    --name "Tasa de falsas alarmas en operacion nominal" \
    --metrics-from 06_resultados/experimentos/evaluacion.json \
    -- python 04_codigo/pipelines/evaluar.py
```

Produce `initiative/increments/<SLUG>/verification/runs/VRN-*/` con la evidencia cruda y, si
MLflow está instalado, el `run_id` etiquetado con las claves `ief.*`. Si MLflow no está, la
evidencia se emite igual: el mínimo nunca depende de una dependencia opcional.

Formato de citación en el informe:

> **Figura 4.3.** … `VRN-003-007-002` · MLflow `8a1c4f…` · commit `a91b2c` · semilla 42.

Detalle: [`presets/astro-mlops/docs/mlops_traceability_spec.md`](../presets/astro-mlops/docs/mlops_traceability_spec.md).

---

## 7. Orden recomendado de adopción

No hay que adoptarlo todo de una vez. Por rendimiento decreciente:

| # | Paso | Rinde |
|---|---|---|
| 1 | Cambiar el preset y el fragmento de `AGENTS.md` | inmediato, sin riesgo |
| 2 | Volver ejecutable el contrato de telemetría existente | alto: detecta problemas de datos hoy |
| 3 | Banco sintético sobre la variable objetivo | alto: desbloquea el objetivo de validación |
| 4 | `eval_anomaly.py` como única vía de reportar métricas | alto: impide el F1 inflado |
| 5 | `evidence_run.py` para las cifras del informe | medio: paga al escribir el documento |
| 6 | `params.yaml` + `conf/config.yaml` | medio: saca los números del código |
| 7 | `dvc.yaml` | medio: cuando el pipeline se estabilice |
| 8 | CI con `ci/ief-verify.yml` | bajo hasta que existan tests que correr |

---

## 8. Convivencia con un curso o equipo de MLOps

El preset está diseñado para no chocar con un currículo estándar de MLOps (uv, DVC, MLflow,
Hydra, Docker, GitHub Actions, FastAPI, monitoreo). La división es explícita:

- **El stack MLOps aporta el cómo:** reproducibilidad, versionado, empaquetado, despliegue.
- **El IEF aporta el porqué y la firma:** qué se afirma, contra qué criterio, quién aprobó.

Lo que este preset puede aportar a un equipo que ya trabaja así, y que su stack no cubre:

1. **El contrato de datos ejecutable** con clase semántica por canal.
2. **Los criterios operacionales** acordados antes de ver resultados (FAR, cobertura, lead time).
3. **La cadena de evidencia** desde la afirmación hasta el run.
4. **Las puertas humanas** traducidas a condición mecánica de merge (`ci/ief-verify.yml`).
5. **El banco de fallas sintéticas**, útil para cualquiera que enseñe detección de anomalías
   sin un dataset etiquetado a mano.

Lo que conviene tomar prestado de ellos, y este preset no reemplaza: empaquetado con `uv`,
imágenes Docker, registro de modelos, servicio con FastAPI y monitoreo con Evidently o
Prometheus.
