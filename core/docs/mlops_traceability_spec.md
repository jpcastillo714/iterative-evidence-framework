# Trazabilidad IEF ↔ MLOps

**Framework:** Iterative Evidence Framework (IEF) V3 · **Preset:** `astro-mlops`
**Implementación:** `core/scripts/evidence_run.py`
**Complementa:** [`verification_contract_spec.md`](verification_contract_spec.md)

---

## 1. Por qué hace falta un puente

Un stack MLOps convencional y el IEF resuelven mitades distintas del mismo problema y ninguno
resuelve la otra:

| | Responde | No responde |
|---|---|---|
| **MLflow / DVC** | qué se ejecutó, con qué datos, qué métricas dio | por qué se ejecutó, contra qué criterio, quién lo aprobó |
| **IEF** | qué se afirma, qué criterio lo mide, quién aprobó | qué versión exacta de datos y código produjo el número |

Sin puente, el informe cita una figura que nadie puede rastrear hasta el run que la produjo, y
el run existe sin ninguna afirmación que lo justifique. La cadena completa es:

```
CLM-001  afirmación del informe
  └── INC-003  incremento que la sostiene
       └── CRT-002  criterio que la mide
            └── TST-ACC-007  definición del test
                 └── VRN-003-007-001  ejecución fechada  ← evidence_run.py
                      ├── stdout/stderr/exit code/duración   (evidencia cruda)
                      ├── artifacts.yml → figuras y tablas    (evidencia derivada)
                      ├── mlflow run_id → params y métricas   (el experimento)
                      └── git commit + dvc hash               (el estado del mundo)
```

---

## 2. Vocabulario de etiquetas

`evidence_run.py` estampa estas etiquetas en el run de MLflow. Son el índice inverso: desde
la interfaz de MLflow se filtra por afirmación o por incremento.

| Etiqueta | Contenido | Obligatoria |
|---|---|---|
| `ief.increment` | slug del incremento (`003_pipeline_segmentacion`) | sí |
| `ief.claim` | `CLM-XXX` que el run sustenta | antes de citar |
| `ief.criterion` | `CRT-XXX` que el run mide | antes de citar |
| `ief.test` | `TST-XXX` que el run ejecuta | sí |
| `ief.vrn` | id de la carpeta de evidencia | sí |
| `ief.verification_level` | `asserted` … `independently-reviewed` | sí |
| `ief.requirement` | `required` / `optional` | sí |
| `ief.status` | `passed` / `failed` / `error` | sí |
| `git.commit`, `git.dirty` | estado del repositorio | sí |

Un run con `ief.claim: PENDING` es válido como exploración, pero **no se cita en el informe**.
Es la regla que separa un experimento de un resultado.

---

## 3. Qué escribe cada ejecución

```
initiative/increments/<slug>/verification/runs/VRN-<INC>-<TST>-<NNN>/
    command.txt      línea exacta ejecutada
    stdout.txt       salida cruda, sin truncar
    stderr.txt       error crudo, sin truncar
    metadata.yml     ids, exit codes, duración, entorno, git, semilla
    result.yml       status, observaciones y métricas escalares
    artifacts.yml    archivos nuevos o modificados + run_id de MLflow
```

`artifacts.yml` se llena detectando qué archivos cambiaron en los directorios vigilados
durante la ejecución. Es deliberadamente tonto y por eso es confiable: no depende de que el
script bajo prueba declare sus salidas.

### Distinguir los tres modos de no-éxito

`verification_contract_spec.md` §2 los separa y el puente lo respeta:

- **fallo de ejecución** — el comando reventó (dependencia, sintaxis, entorno).
- **hipótesis rechazada** — el comando corrió limpio y el resultado contradice el criterio.
- **verificación bloqueada** — faltó un prerrequisito (los datos de mantenimiento no llegaron).

Solo el segundo es un resultado científico. Confundirlo con el primero produce el patrón
clásico de arreglar el código cuando lo que falla es la hipótesis.

---

## 4. Configuración local-first

La telemetría de un instrumento rara vez puede salir de la red del laboratorio. El preset
asume backend local y trata la nube como opcional:

```yaml
# 04_codigo/conf/config.yaml
mlflow:
  tracking_uri: "file:./06_resultados/experimentos/mlruns"
```

- **MLflow local** (`file:`) no necesita servidor y versiona igual.
- **MinIO** da un backend S3-compatible dentro del laboratorio si se quiere el mismo código
  que en la nube.
- **DVC** con remoto local o en un disco compartido: lo que importa es el **hash**, no dónde
  vive el archivo.
- SageMaker, S3 y ECR quedan como ejercicio de portabilidad, nunca como dependencia del
  resultado.

Si MLflow no está instalado, `evidence_run.py` **no falla**: emite el VRN igual y omite el
enlace. La evidencia mínima nunca depende de una biblioteca opcional.

---

## 5. Cómo se cita en el documento

Formato sugerido para pie de figura o tabla:

> **Figura 4.3.** Tasa de falsas alarmas frente al cuantil de calibración.
> `VRN-003-007-002` · MLflow `8a1c4f…` · datos `dvc:md5 3f2a…` · commit `a91b2c` · semilla 42.

Con eso, cualquiera de la comisión puede pedir el run y reproducirlo. Sin eso, la figura es
una afirmación de autoridad.

---

## 6. Correspondencia con un curso de MLOps

El preset está pensado para convivir con un currículo de MLOps estándar (uv, DVC, MLflow,
Hydra, Docker, CI, FastAPI, monitoreo). Dónde encaja cada paso IEF:

| Paso IEF | Herramienta MLOps | Artefacto |
|---|---|---|
| 1 Charter *(gate)* | Git / issue de propuesta | `charter.md` |
| 2 Auditoría de telemetría | notebooks + DVC | `inspection-report.md` |
| 3 Contrato de telemetría | validador + stage de pipeline | `data-contract.yml` + `contrato_report.json` |
| 4 Reglas del detector *(gate)* | Hydra (parámetros) | `business-rules.yml` |
| 5 Criterios operacionales *(gate)* | pytest + Model Registry | `acceptance-tests.yml` |
| 6 Pipeline y experimentos | DVC + MLflow + Docker | `dvc.lock`, runs |
| 7 Evaluación y evidencia | `evidence_run.py` | `VRN-*/`, `increment-report.md` |
| Human gate | promoción en el Registry, merge protegido | CI verde + `APPROVED` |
| `rewind` | drift detectado en monitoreo | `NEEDS_REVISION` en `state.yml` |

La división de trabajo es limpia: **el stack MLOps aporta el cómo, el IEF aporta el porqué y
la firma.** Ninguno de los dos necesita modificar al otro para que el puente funcione.

---

## 7. Errores que este puente busca evitar

1. **La figura huérfana.** Un PNG en el informe que nadie sabe regenerar.
2. **El run anónimo.** Cien experimentos en MLflow sin saber cuál sustenta qué afirmación.
3. **El umbral ajustado a posteriori.** Cambiar un parámetro después de ver el resultado y
   dejar el texto anterior.
4. **El dato que se movió.** Reprocesar el crudo, obtener otro número y no poder decir cuál
   de los dos estaba en el informe.
5. **La aprobación implícita.** Avanzar de un gate porque nadie dijo que no.
