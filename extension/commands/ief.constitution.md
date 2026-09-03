---
name: "ief.constitution"
description: "Escribe o revisa los principios del proyecto"
---

# Constitución (`/speckit.ief.constitution`)

## Propósito

Escribir los principios bajo los que trabaja el proyecto: `initiative/specs/constitution.md`.

## Las dos capas

Este archivo es una de dos, y confundirlas las vuelve inútiles:

| | **Constitución** | **Reglas promovidas** (`rules.yml`) |
|---|---|---|
| Describe | **Cómo se trabaja** | **Qué es cierto del dominio** |
| Ejemplo | «Ninguna cifra se cita sin evidencia ejecutable» | «Un episodio dura ≥ 5 minutos» |
| Nace | Aquí, antes del primer incremento | En el paso 4 de un incremento |
| Dirección | De arriba abajo | De abajo arriba |

Si algo lo descubriste trabajando, **no es constitucional**: es una regla y su sitio es
`rules.yml`. Si es un compromiso que asumes antes de saber nada, va aquí.

## Protocolo

1. `--mode init` ya crea el archivo desde la plantilla. Ábrelo y **escríbelo antes del
   primer incremento**.
2. Entre tres y siete principios. Más de siete y nadie los recuerda; menos de tres y no
   restringen nada.
3. Cada principio debe **poder violarse**. Si es imposible incumplirlo, no es un
   principio: es una descripción.
4. Cada principio lleva su *por qué* y **cómo se nota que se incumplió**. Sin la señal
   observable, el principio se erosiona en cuanto aprieta el plazo.

## Enmendarla

Cambiar la constitución es un **evento**, no un ajuste. Se anota en la tabla de
enmiendas con qué cambió, por qué y quién. Lo que importará dentro de un año es qué te
hizo cambiar de opinión.

## Reglas

- Un incremento **no puede contradecir** un principio. Si lo necesita, primero se
  enmienda la constitución, explícitamente.
- El paso 1 (Charter) de cada incremento se lee **contra** estos principios.
- Las reglas que promueve un incremento viven **debajo** de la constitución, nunca por
  encima.
