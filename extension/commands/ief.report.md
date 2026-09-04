---
name: "ief.report"
description: "Redacta el borrador del informe del incremento con lo que el motor ya sabe"
---

# Borrador de informe (`/speckit.ief.report`)

## Propósito

Escribir el informe del incremento con **todo lo que el motor ya sabe**, y dejar
marcado en el hueco lo único que no puede saber.

## Por qué existe

El motor conoce qué pasos se hicieron, quién aprobó qué y en qué fecha, qué reglas se
propusieron y qué tests las sostienen. Pedirle a una persona que transcriba eso a mano es
pedirle **trabajo de copista**, y el trabajo de copista se hace mal: se omiten cosas y se
ponen fechas de memoria.

## Uso

```bash
# El incremento enfocado
python core/scripts/verify_frame.py --mode draft-report

# Uno concreto
python core/scripts/verify_frame.py --mode draft-report --increment 003_ingesta
```

Se niega a pisar un informe ya escrito. Para reemplazarlo hace falta
`--force-overwrite`, explícito y a propósito.

## Lo que rellena solo

Recorrido de los pasos con su estado, quién firmó cada compuerta y cuándo, y si el
artefacto está en disco · las reglas propuestas con su motivo, su cadena de reemplazo y
su evidencia · los criterios de aceptación, señalando los que **no son verificables** por
no tener bloque `verify` · las decisiones que quedaron abiertas · el historial.

## Lo que deja en blanco, y por qué

Los **aprendizajes** y la **deuda que queda** salen como preguntas explícitas:

> **¿Qué supuesto resultó falso?** De los que diste por buenos al empezar, cuál se cayó
> al mirar los datos o al implementar.

Eso no lo puede escribir una máquina, y **fingir que sí es peor que dejar el hueco**: un
informe con aprendizajes inventados se lee como si tuviera aprendizajes. Es también la
única parte que seguirá sirviendo dentro de un año.

`todo bien` no es un aprendizaje.
