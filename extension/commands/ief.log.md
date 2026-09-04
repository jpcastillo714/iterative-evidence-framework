---
name: "ief.log"
description: "Anota trabajo que no merece un incremento: un gráfico, un documento, un arreglo"
---

# Bitácora (`/speckit.ief.log`)

## Propósito

Dejar constancia de trabajo real que **no justifica abrir un incremento**.

## Por qué existe

El riesgo de este framework nunca fue equivocarse: era **pesar tanto que se abandonara**.
Un sistema que exige un ciclo de cuatro pasos para hacer un gráfico se deja de usar en
tres semanas, y entonces no protege de nada.

Pero el problema que resuelve el registro sigue estando: dentro de seis meses alguien
encuentra ese PNG en una carpeta y no sabe de dónde salió. Una línea aquí lo responde y
cuesta cinco segundos.

## Cuándo usar esto y cuándo no

El eje no es el tamaño, es la **consecuencia**:

| Pregunta | Si la respuesta es sí |
|---|---|
| ¿Va a citarlo alguien? | necesita evidencia → incremento |
| ¿Va a mantenerlo alguien? | necesita especificación → incremento |
| ¿Cambia una regla del proyecto? | necesita compuerta → incremento |
| **Ninguna de las tres** | **hazlo y anótalo aquí** |

## Uso

```bash
python core/scripts/verify_frame.py --mode log \
    --message "gráfico de margen por categoría para el comité" \
    --output "reports/figures/margen_cat.png" \
    --from "notebooks/03_margen.ipynb"
```

`--message` es obligatorio: la anotación **es** el contenido. `--output` y `--from` son
opcionales, pero son justo lo que responde «¿de dónde salió esto?».

Queda en `initiative/worklog.md` y como evento `LOG` en el historial. No crea
incrementos, no toca el foco y no exige aprobación de nadie.

## Regla

Si algo que anotaste aquí empieza a crecer, a ser citado o a cambiar una regla, **deja de
pertenecer a esta lista**: ábrele un incremento. La bitácora es para lo que nace y muere
pequeño, no un vertedero para saltarse el proceso.
