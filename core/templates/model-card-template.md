# Model Card — {{NOMBRE_DEL_MODELO}}

> Plantilla del paso `6b_model_evaluation` (preset `ml`).
> Lo que no se sepa se marca `PENDING`. Un campo inventado es peor que uno vacío.

| Campo | Valor |
|---|---|
| Incremento | {{SLUG}} |
| Versión del modelo | {{VERSION}} |
| Fecha de evaluación | {{FECHA}} |
| Commit | {{COMMIT}} |
| Semilla | {{SEMILLA}} |

---

## 1. Para qué sirve

**Tarea:** {{clasificación / regresión / ranking / …}}

**Decisión que informa:** qué cambia en el mundo por lo que este modelo diga. Si no
cambia nada, el modelo no hace falta.

**Usuarios previstos:** quién consume la salida y con qué expectativa.

---

## 2. Para qué NO sirve

Los usos fuera del alcance para los que este modelo **no** fue evaluado. Esta sección
protege más que la anterior: un modelo aplicado fuera de su dominio falla en silencio.

- {{uso fuera de alcance}}

**Dominio de validez:** el rango de entradas sobre el que las métricas de abajo son
válidas. Fuera de él, el modelo no tiene garantías.

---

## 3. Datos

| | |
|---|---|
| Fuente | {{origen}} |
| Período | {{desde – hasta}} |
| Partición | {{temporal / por grupo / aleatoria}} — y **por qué** esa y no otra |
| Tamaño train / val / test | {{n / n / n}} |
| Fuga de información | Cómo se descartó. Qué se comprobó, no qué se supone. |

**Desbalance y sesgos conocidos:** {{...}}

---

## 4. Resultados

La métrica objetivo se acordó en el Paso 1 y el umbral de aceptación en el Paso 5,
**antes** de ver estos números. Si aquí aparece una métrica que no estaba acordada, hay
que decirlo explícitamente.

| Métrica | Test | Umbral acordado (Paso 5) | Cumple |
|---|---|---|---|
| {{métrica objetivo}} | | | |
| {{métrica secundaria}} | | | |

**Línea base:** contra qué se compara. Un modelo sin línea base no tiene resultado, tiene
un número.

| Modelo | {{métrica}} |
|---|---|
| Trivial (mayoritaria / media / persistencia) | |
| Línea base simple | |
| **Este modelo** | |

**Desempeño por segmento:** el promedio esconde a quién falla el modelo.

| Segmento | n | {{métrica}} |
|---|---|---|

---

## 5. Qué se probó y falló

Lo que no funcionó es información, no vergüenza. Omitirlo condena al siguiente a
repetirlo.

- {{enfoque descartado y por qué}}

---

## 6. Limitaciones y riesgos

- **Degradación esperada:** qué haría caer el desempeño (deriva, estacionalidad, cambio
  de proceso) y cada cuánto revisarlo.
- **Modo de fallo:** cómo se equivoca cuando se equivoca, y a quién afecta.
- **Coste del error:** falso positivo frente a falso negativo. Rara vez cuestan igual.

---

## 7. Reproducción

```bash
{{comando exacto que reproduce estos números}}
```

| | |
|---|---|
| Entorno | {{versión de Python y dependencias fijadas}} |
| Tiempo de entrenamiento | {{...}} |
| Hardware | {{...}} |

---

## 8. Decisión

- [ ] **Aprobado.** Cumple los criterios del Paso 5. Puede pasar al Paso 7.
- [ ] **Rechazado.** No los cumple. → `/speckit.ief.rewind` al paso que corresponda.
- [ ] **Aprobado con condiciones:** {{cuáles y hasta cuándo}}

**Aprobado por:** {{persona}} · **Fecha:** {{fecha}}

> Bajar un umbral para que el modelo quepa dentro de él no es aprobar: es cambiar el
> criterio después de ver el resultado. Si el umbral estaba mal, se retrocede al Paso 5,
> se corrige con su motivo, y se vuelve a evaluar.
