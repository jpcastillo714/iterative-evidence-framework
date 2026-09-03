# Paso 4: Reglas

## Cabecera del Paso

| Campo | Valor |
|-------|-------|
| **Paso** | 4 — Reglas |
| **Ciclo** | `build` |
| **Inputs obligatorios** | Contrato de datos (paso 3) e inspección empírica (paso 2) |
| **Output** | `initiative/increments/<SLUG>/rules.yml` |
| **Human Gate** | ✋ Sí |

> El **nombre** de este paso cambia según el preset: «Reglas» en `product`,
> «Reglas del Modelo» en `research`, «Definiciones y Métricas» en `analysis`. La
> **clave** (`4_rules`) y el **archivo** (`rules.yml`) no cambian nunca. Consulta el
> nombre real con `--mode status --json`.

---

## Objetivo

Escribir lo que el sistema **debe cumplir**, con su porqué al lado, de forma que el
paso 5 pueda convertirlo en tests.

Este paso captura lo que descubriste en los pasos 2 y 3, que es lo que ningún documento
escrito antes de mirar los datos podía saber.

## Una regla lleva su justificación dentro

Dos cosas relacionadas pero distintas:

- Una **regla** es normativa y verificable: *«un episodio dura al menos 5 minutos»*.
- Su **rationale** es histórico: *«por debajo de 5 minutos el 80% son reposicionamientos,
  no operación útil; verificado sobre tres meses de historial»*.

Van en el mismo objeto a propósito. Separadas en dos artefactos —reglas por un lado,
bitácora de decisiones por otro— se desincronizan sin falta: alguien cambia la regla,
nadie actualiza la bitácora, y medio año después la regla parece arbitraria y el
siguiente que pasa la deshace.

## `applies_to` es lo que hace posible detectar contradicciones

Es el campo que el motor compara al promover. Dos reglas con el mismo `applies_to`
gobiernan lo mismo: o una reemplaza a la otra —y lo dice con `supersedes`— o el
proyecto se está contradiciendo.

Sin este campo la contradicción no se puede detectar, y dos incrementos acaban
imponiendo reglas incompatibles sin que nadie se entere hasta que algo falla en
producción o hasta que el informe se contradice a sí mismo.

---

## Protocolo

### 1. Extraer las reglas de lo que ya sabes

Recorre el informe de inspección y el contrato de datos. Cada restricción, umbral,
definición o caso límite que descubriste es candidato a regla.

**No inventes reglas plausibles.** Una regla que no salió de los datos ni de una
decisión explícita del usuario es una suposición disfrazada de norma.

### 2. Escribir cada regla verificable

Antes de dar una regla por escrita, responde: *¿qué test la comprobaría?* Si no hay
respuesta, la regla está mal formulada. Reescríbela hasta que la haya.

| Mal | Bien |
|---|---|
| «Los datos deben ser de calidad» | «Ningún registro tiene `id` nulo» |
| «El modelo debe ser bueno» | «El F1 macro sobre el conjunto de prueba supera 0.80» |
| «Procesar rápido» | «Un lote de 10⁶ filas termina en menos de 5 minutos» |

### 3. Comprobar contra la constitución

Lee `initiative/specs/constitution.md`. Una regla **no puede contradecir** un principio
constitucional. Si necesita hacerlo, primero se enmienda la constitución, explícitamente.

### 4. Comprobar contra las reglas vigentes

Lee `initiative/specs/rules.yml`. Si alguna regla nueva gobierna el mismo `applies_to`
que una vigente:

- **La reemplaza** → declara `supersedes: RUL-XXX-YYY` y explica en el `rationale` qué
  aprendiste que la vieja no sabía.
- **No la reemplaza** → entonces contradicen, y hay que decidir cuál rige antes de
  seguir. No se promueven ambas.

### 5. Listar las decisiones abiertas

Todo lo que aún no se decide va a `decisiones_pendientes`, y se resuelve **en la
compuerta de este paso**. Una decisión que se aplaza hasta la implementación la termina
tomando el código, en silencio, sin que nadie la haya aprobado.

### 6. Compuerta humana

```bash
python core/scripts/verify_frame.py --mode verify-step --step 4
python core/scripts/verify_frame.py --mode approve-step --by "<usuario>"
```

---

## Reglas críticas

1. **Una regla sin `rationale` es deuda.** Funciona hoy y nadie sabe tocarla mañana.
2. **Una regla que no se puede verificar no es una regla.** Reescríbela o descártala.
3. **`applies_to` no es opcional en la práctica:** sin él, el motor no puede protegerte
   de una contradicción al promover.
4. **Las reglas nacen con `scope: increment`.** Solo `merge-increment` las sube a
   `project`, y solo cuando el incremento cierra con sus compuertas aprobadas.
5. **Una regla superada nunca se borra.** Queda marcada `superseded` apuntando a la que
   la reemplaza. El proyecto necesita recordar que un día pensó lo contrario, y por qué.

---

## Salidas

- `rules.yml` con todas las reglas verificables y su justificación.
- `decisiones_pendientes` vacío, o con cada punto resuelto en la compuerta.
- El paso en `APPROVED`.
