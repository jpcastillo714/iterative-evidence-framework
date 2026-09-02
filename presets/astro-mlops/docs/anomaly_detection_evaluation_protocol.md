# Protocolo de evaluación — detección de anomalías en telemetría

**Framework:** Iterative Evidence Framework (IEF) V3 · **Preset:** `astro-mlops`
**Herramientas:** `presets/astro-mlops/scripts/inject_faults.py`, `presets/astro-mlops/scripts/eval_anomaly.py`
**Ámbito:** detección no supervisada sobre series temporales de instrumentación, sin
historial de fallas etiquetado.

Este documento fija **cómo se mide** un detector antes de haberlo construido. Su función
es impedir la secuencia habitual: entrenar, probar métricas hasta que una salga bonita, y
escribir el capítulo alrededor de ese número.

---

## 1. El problema de fondo

Un equipo bien mantenido no falla. Seis meses de telemetría de un instrumento en operación
suelen ser **enteramente nominales**: cero eventos positivos. De ahí se siguen tres cosas
incómodas:

1. No hay recall que medir. Cualquier afirmación sobre "detecta fallas" es, de entrada, una
   extrapolación.
2. El conjunto de prueba no tiene negativos "limpios" garantizados: se asume que todo es
   nominal, y esa suposición **es una hipótesis del trabajo**, no un hecho.
3. La métrica que sí se puede medir con rigor es la **tasa de falsas alarmas**. Es también,
   por lejos, la que decide si el sistema se queda encendido en operación.

El protocolo se construye sobre esa asimetría: **la tasa de falsas alarmas se mide, la
sensibilidad se acota**.

---

## 2. Particiones: por episodio y en el tiempo

| Regla | Motivo |
|---|---|
| Partición **temporal**: test posterior a train | Un modelo que ve el futuro no se reproduce en operación |
| Partición **por episodio**, nunca por fila | Dos ventanas solapadas del mismo episodio son casi el mismo dato: partirlas infla el desempeño |
| Ningún episodio en dos particiones | Verificable con un test (`TST-ACC-004`) |
| Escalador, PCA y cuantiles ajustados **solo en train nominal** | Cualquier estadístico global calculado sobre todo el conjunto filtra información del test |

El error más caro y más frecuente de esta familia de trabajos no es elegir mal el modelo:
es normalizar antes de partir.

---

## 3. Umbral: se calibra sobre nominal, se declara antes de mirar

```
umbral = quantile(scores_nominal_train, q)
```

- `q` se **fija antes** de ver los resultados de evaluación y se declara en el artefacto del
  Paso 5, junto con la tasa de falsas alarmas teórica que implica.
- Elegir el umbral que maximiza F1 sobre el conjunto evaluado es fuga de información. El
  número resultante no se reproduce en operación y no es publicable.
- `eval_anomaly.py` marca en el reporte el origen del umbral. Si se calibró sobre los
  negativos del propio test, lo dice explícitamente en `advertencias`.

### Confirmación k-de-n

Un score sobre el umbral no es una alarma. Se exigen `k` excedencias dentro de `n` muestras
consecutivas. La histéresis convierte una tasa puntual en una tasa operacional manejable a
cambio de un retraso acotado — que el reporte cuantifica en `retraso_mediano_min`. Ambos
números se publican juntos: subir `k` siempre mejora la FAR y siempre empeora el retraso.

---

## 4. Métricas: qué se reporta y en qué orden

### 4.1 Por eventos (métrica principal)

Un evento se considera **detectado** si alguna alarma confirmada lo intersecta. Las alarmas
se agrupan en tramos contiguos; un tramo que no intersecta ningún evento es una **falsa
alarma**, cuente 3 muestras o 300.

- `recall_eventos` — de las degradaciones presentes, cuántas se vieron.
- `precision_eventos` — de las veces que el sistema habló, cuántas tenían razón.
- `alarmas_falsas` — el conteo crudo, sin normalizar.

### 4.2 Falsas alarmas por unidad operacional (la que decide el despliegue)

```
FAR = tramos_de_alarma_falsos / unidades_operacionales_evaluadas
```

La unidad es la noche de observación, el turno o la jornada: lo que corresponda al equipo.
Un detector con recall 0.95 y dos falsas alarmas por noche se apaga en una semana; uno con
recall 0.40 y una falsa alarma al mes se queda. **Esta métrica va en el resumen del
informe, no en un apéndice.**

### 4.3 Tiempo

- `retraso_mediano_min` — desde que el efecto alcanza 1σ hasta la primera alarma confirmada.
- `anticipacion_mediana_min` — cuánto queda del evento tras la primera alarma; proxy del
  margen para agendar una intervención.

### 4.4 Por punto (contexto, no titular)

Precisión, recall, F1, PR-AUC y ROC-AUC puntuales. Sirven para comparar modelos entre sí en
igualdad de condiciones. **No** describen la experiencia de quien opera el instrumento.
Con clases muy desbalanceadas, PR-AUC es informativa y ROC-AUC es engañosamente alta.

### 4.5 Point-adjust: se reporta, nunca solo

El *point-adjust* marca como acierto **todas** las muestras de un evento si se detectó una
sola. Es la convención que sostiene buena parte de los resultados publicados en detección de
anomalías en series temporales, y se ha mostrado que un detector aleatorio puede obtener con
ella F1 altísimos. `eval_anomaly.py` lo calcula y publica dos deltas:

- `delta_f1_vs_puntual` — **cuánto aporta la convención y no el detector.** Una sola muestra
  acertada dentro de un evento de 60 pasa a valer 60. Si este delta es grande, el número
  bonito es del método de conteo.
- `delta_f1_vs_eventos` — cuánto difiere de la métrica que sí describe la operación.

Ambos van en el reporte. Si solo se publica el F1 con point-adjust, el resultado no es
comparable con nada.

**Lecturas para el marco teórico** (verificar y añadir a `library.bib`):
Tatbul et al., *Precision and Recall for Time Series*, NeurIPS 2018 · Kim et al., *Towards a
Rigorous Evaluation of Time-Series Anomaly Detection*, AAAI 2022 · Paparrizos et al.,
*Volume Under the Surface*, VLDB 2022 · Wu & Keogh, *Current Time Series Anomaly Detection
Benchmarks are Flawed*, TKDE.

---

## 5. Dominio de validez y abstención

Si el detector opera sobre el residuo de un modelo base, ese modelo base tiene un rango de
condiciones donde es válido. Fuera de él, el residuo mide **error del modelo**, no salud del
equipo.

- Las muestras fuera de dominio se marcan `no_evaluable` y **no** producen alarma.
- No cuentan como acierto ni como falsa alarma en la evaluación.
- La **cobertura** (fracción evaluable) se reporta como métrica de primer orden.

Una cobertura de 60 % no es un defecto que esconder: es un resultado. Dice exactamente sobre
qué fracción de la operación el sistema tiene derecho a opinar, y acota honestamente el
alcance de las conclusiones.

---

## 6. Banco sintético: fabricar el ground truth y declararlo

`inject_faults.py` inyecta nueve modos de degradación sobre tramos nominales, con severidad
en unidades de **σ nominal** (MAD robusto):

| Modo | Qué modela | Firma esperada |
|---|---|---|
| `deriva_lenta` | desgaste acumulativo | media que se corre, varianza estable |
| `stiction` | fricción estática | escalones; la señal se pega y se libera |
| `juego_mecanico` | backlash | error en cada inversión de sentido |
| `perdida_ganancia` | lazo con menos ganancia | misma dinámica, más amplitud |
| `salto_encoder` | pérdida de cuentas | escalón permanente |
| `ruido_creciente` | degradación del sensor | varianza que sube, media quieta |
| `cuantizacion` | pérdida de resolución | valores en rejilla |
| `valor_congelado` | canal congelado | **varianza que CAE a cero** |
| `dropout` | pérdida intermitente | NaN en ráfagas |

Reglas de uso:

1. **Ventanas disjuntas y separadas**, para que las alarmas se atribuyan sin ambigüedad.
2. **Fracción anómala baja** (idealmente < 10 %). Si el banco corrompe más del 20 % de la
   serie, la precisión y la FAR quedan mal estimadas: la herramienta lo advierte.
3. El manifiesto `injections.yml` (tipo, severidad, ventana, semilla, σ) es un **artefacto de
   evidencia versionado**. Sin él la métrica no es reproducible.
4. `valor_congelado` merece atención aparte: la mitad de los detectores basados en desviación
   no lo ven, porque la varianza baja en vez de subir. Si el banco no lo incluye, el trabajo
   no sabe si el sistema es ciego al fallo más común de una cadena de adquisición.

### El resultado esperado no es "detecta todo"

Es la tabla `recall(tipo, severidad)`: qué detecta, **desde qué severidad**, y qué no detecta
nunca. Esa tabla es un resultado de la memoria por derecho propio y define el umbral de
detectabilidad del sistema.

### Limitación que va en el cuerpo del informe

Las fallas inyectadas son un **modelo** de degradación. El banco acota la sensibilidad; no
demuestra que el detector verá la próxima falla real. Es la antesala de la validación contra
mantenimiento, no su reemplazo.

---

## 7. Validación externa

El cierre del objetivo de validación exige contraste con evidencia externa. En orden de
preferencia:

1. **Historial de mantenimiento o tickets** con fechas: permite calcular lead time real.
2. **Una ventana con falla conocida**, aunque sea de otra unidad, otro periodo u otro equipo
   del mismo tipo: convierte novelty detection ciega en un problema con al menos un positivo.
   No exige desclasificar un historial completo: basta un rango de fechas.
3. **Definición operacional de anomalía** obtenida de quien opera: qué ve cuando algo va mal.
   Sin ella el detector no tiene contra qué validarse.
4. **Campaña dirigida de alta cadencia**, si el archivado decima la señal. Unas horas a alta
   frecuencia pueden valer más que meses decimados.

Si ninguna llega a tiempo, se declara el bloqueo en el artefacto del Paso 5
(`status: blocked` con su fecha de corte y su vía alternativa) y se documenta el impacto
sobre el objetivo. **No se rebaja el criterio para que quepa el resultado disponible.**

---

## 8. Deriva: cuándo el detector deja de ser válido

Un aumento sostenido de la tasa de alarmas rara vez significa que el equipo se degradó. Casi
siempre significa una de estas:

- cambio de régimen operacional (nueva campaña, nuevo modo, estación distinta),
- cambio de firmware, de configuración o del archivador,
- el modelo base salió de su dominio de validez.

La respuesta correcta es `/speckit.ief.rewind` al Paso 3 o 4: actualizar el contrato,
reajustar el modelo y **reentrenar**. Ajustar el umbral a mano rompe la correspondencia entre
lo que se reportó y lo que el sistema hace: es la forma más común de falsificar evidencia sin
proponérselo.

---

## 9. Lista de verificación previa a publicar una cifra

- [ ] La partición es temporal y por episodio; ningún episodio se repite entre particiones.
- [ ] Todo estadístico global se ajustó solo sobre train nominal.
- [ ] El umbral se calibró sobre nominal y su cuantil estaba fijado de antemano.
- [ ] Se reportan métrica por eventos, FAR por unidad operacional y cobertura.
- [ ] Si aparece point-adjust, aparece junto al delta contra la métrica por eventos.
- [ ] El banco sintético incluye `valor_congelado` y al menos un modo de deriva lenta.
- [ ] La fracción anómala del banco es baja y está declarada.
- [ ] El manifiesto de inyección, la semilla, el commit y el hash de datos están versionados.
- [ ] La cifra proviene de un VRN registrado con `evidence_run.py`.
- [ ] La limitación del ground truth sintético está escrita en el cuerpo, no en una nota.
