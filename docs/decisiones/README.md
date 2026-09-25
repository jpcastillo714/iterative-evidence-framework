# Decisiones de diseño

Cada cambio de comportamiento del IEF (un modo nuevo, una compuerta que cambia, un campo
que se agrega al `state.yml`) se registra aquí **antes** de implementarse, como un
*registro de decisión* (ADR, por sus siglas en inglés).

## Por qué

Un framework que exige trazabilidad a sus usuarios tiene que exigírsela a sí mismo. Si
el motor hace algo y nadie sabe por qué, el siguiente que lo toque lo deshará o lo
romperá sin darse cuenta. Jansen y Bosch llaman a esto *vaporización del conocimiento*:
las decisiones quedan implícitas en el diseño, se pierden, y con ellas se violan las
reglas que imponían y se acumulan decisiones obsoletas [@jansen2005]. La respuesta que
proponen es tratar cada decisión como un elemento explícito, con su justificación.

El formato sigue el de Nygard [@nygard2011], con dos secciones más que este repositorio
considera obligatorias: **Evidencia** (qué trabajo publicado respalda la decisión, con su
clave de [`REFERENCIAS.md`](../REFERENCIAS.md)) y **Límites de la evidencia** (hasta
dónde llega ese respaldo). La segunda existe porque la forma más común de exagerar un
argumento no es inventar una fuente, sino citarla para algo que no midió.

## Formato

```markdown
# ADR-NNN: título corto en forma de sustantivo

## Estado
Propuesta | Aceptada (AAAA-MM-DD) | Rechazada | Reemplazada por ADR-NNN

## Contexto
El problema, medido. Si es un fallo, cómo se reproduce.

## Decisión
Qué se hará, en voz activa.

## Evidencia
Qué respalda la decisión, con citas [@clave] a docs/REFERENCIAS.md.

## Límites de la evidencia
Dónde se midió lo citado y qué no cubre.

## Alternativas descartadas
Qué otras opciones había y por qué no.

## Cómo se verifica
Qué tests, chequeos o salidas del motor demuestran que la decisión está implementada.

## Consecuencias
Qué cambia para los proyectos existentes y qué deben hacer.
```

## Reglas

1. **Una decisión se propone, no se impone.** Nace en estado `Propuesta` y pasa a
   `Aceptada` solo cuando la aprueba quien mantiene el repositorio. Recién entonces se
   implementa.
2. **Una decisión aceptada no se edita: se reemplaza.** Si cambia, se escribe un ADR
   nuevo y el viejo pasa a `Reemplazada por ADR-NNN`. Así se ve qué se decidió, cuándo y
   por qué dejó de valer [@nygard2011].
3. **Solo se cita lo verificado.** Toda entrada de `REFERENCIAS.md` se abrió en su fuente
   primaria y dice qué hallazgo se usa y dónde está (sección, tabla o página). Un
   preprint se declara como tal.
4. **Nada de proyectos concretos.** La evidencia sale de la literatura o de fallos
   reproducidos con el propio motor, nunca de un proyecto, cliente o dataset con nombre.

`tests/test_referencias.py` hace cumplir las reglas 3 y el formato: falla si un
documento cita una clave que no existe, si una entrada no dice su estado o la ubicación
de sus hallazgos, si una referencia no la cita nadie, o si un ADR no tiene sus secciones
o no figura en el índice de abajo.

## Índice

| ADR | Título | Estado |
|---|---|---|
| [ADR-001](ADR-001-firma-humana-ligada-al-contenido.md) | Firma humana ligada al contenido y al canal por el que se dio | Aceptada (2026-09-24) |
| [ADR-002](ADR-002-compatibilidad-entre-versiones.md) | Compatibilidad entre versiones: qué cambió, qué hacer y cómo migrar | Aceptada (2026-09-24) |
