# {{TAREA}}

> Ciclo `task`: trabajo real pero pequeño. Media página basta — si necesitas más,
> probablemente no era un `task`.

## Qué se pide

Una o dos frases. Qué debe hacer el sistema que hoy no hace.

## Cómo sabremos que está

El criterio, en concreto y comprobable. No «que funcione bien», sino algo que se pueda
mirar y responder sí o no:

- [ ] {{criterio}}

Si el criterio se puede automatizar, este es el momento de escribir el test. Si no se
puede, dilo aquí: un criterio que solo se comprueba a ojo también sirve, pero conviene
saber que lo es.

## Qué se toca

Los archivos o zonas que van a cambiar. Sirve para dos cosas: darte cuenta de si el
alcance es mayor de lo que creías, y que quien mire esto en el futuro sepa dónde buscar.

## Qué NO se toca

Lo que queda deliberadamente fuera. Es la parte que evita que un `task` de media tarde
se convierta en tres días.

---

**Si al escribir esto aparecen decisiones que otros van a heredar** —una definición
nueva, un supuesto sobre los datos, una regla— entonces esto ya no es un `task`.
Ciérralo y abre un `prototype` o un `build`: las decisiones que otros heredan necesitan
una compuerta.
