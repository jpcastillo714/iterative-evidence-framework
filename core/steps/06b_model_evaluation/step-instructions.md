# Paso 6b: Evaluación del Modelo

## Cabecera del Paso

| Campo | Valor |
|-------|-------|
| **Paso** | 6b — Evaluación del Modelo |
| **Ciclo** | `build` del preset `ml` |
| **Inputs obligatorios** | Modelo entrenado (Paso 6) y criterios aprobados (Paso 5) |
| **Output** | `initiative/increments/<SLUG>/model-card.md` |
| **Human Gate** | ✋ Sí |

---

## Objetivo

Decidir si el modelo **sirve**, contra el criterio que se acordó antes de verlo.

Es un paso aparte del 7 porque responde una pregunta distinta:

| Paso | Pregunta |
|---|---|
| 6b — Evaluación del modelo | ¿Generaliza? ¿Supera la línea base? ¿Cumple el umbral acordado? |
| 7 — Verificación del sistema | ¿El pipeline corre, es reproducible y no rompió nada? |

Un modelo puede pasar todos los tests de integración y aun así no servir para nada.
Confundir ambas preguntas es cómo se publica un modelo que funciona perfectamente y no
predice nada útil.

---

## Protocolo

### 1. Recuperar el criterio acordado

Leer `acceptance-tests.yml` del incremento. Ahí está la métrica objetivo y su umbral,
aprobados en el Paso 5 **antes** de existir estos resultados.

Si el criterio no está declarado, este paso no puede ejecutarse: retroceder al Paso 5.
Evaluar sin criterio previo es elegir el umbral después de ver el número.

### 2. Evaluar sobre el conjunto de prueba

Una sola vez. El conjunto de prueba no es para iterar: cada mirada lo gasta.

Toda decisión de ajuste se toma sobre validación. Si hubo que volver a tocar el modelo
después de mirar el test, ese test ya no es una estimación honesta y hay que decirlo en
la model card.

### 3. Comparar contra líneas base

Un número sin comparación no es un resultado. Como mínimo:

- **Trivial** — clase mayoritaria, media, o persistencia (predecir el valor anterior).
- **Simple** — regresión lineal/logística, árbol poco profundo, o una regla explicita.

Si el modelo complejo no supera claramente a la línea base simple, ese es el hallazgo:
la complejidad no se está pagando sola.

### 4. Desglosar por segmento

El promedio esconde a quién le falla el modelo. Desglosar por las particiones que
importen al problema y reportar el peor segmento, no solo el agregado.

### 5. Escribir la model card

Usar `core/templates/model-card-template.md`. Las secciones **"Para qué NO sirve"** y
**"Qué se probó y falló"** no son opcionales: son las que evitan que otro repita el
trabajo o aplique el modelo donde no vale.

### 6. Compuerta humana

```bash
python core/scripts/verify_frame.py --mode verify-step --step 6b
python core/scripts/verify_frame.py --mode approve-step --by "<usuario>"
```

---

## Reglas críticas

1. **El umbral no se mueve después de ver el resultado.** Si estaba mal puesto, se
   retrocede al Paso 5 con `/speckit.ief.rewind`, se corrige declarando el motivo, y se
   vuelve a evaluar. Ajustarlo en silencio convierte la evaluación en una formalidad.

2. **Un rechazo es un resultado válido.** "El modelo no alcanza el criterio" es
   información que vale tanto como lo contrario. No es motivo para relajar el criterio.

3. **Reportar la comparación, no solo la cifra.** Sin línea base, un F1 de 0.87 no
   significa nada: puede estar por debajo de predecir siempre la clase mayoritaria.

4. **Las cifras salen de una ejecución, no de la memoria.** El comando que las produce va
   en la model card y debe volver a producirlas.

---

## Salidas

- `initiative/increments/<SLUG>/model-card.md` completa, con la decisión marcada.
- El paso en `APPROVED` (o un retroceso registrado con su motivo).
