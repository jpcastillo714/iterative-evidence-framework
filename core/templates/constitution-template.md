# Constitución — {{PROYECTO}}

> Creada el {{FECHA}} · vive en `initiative/specs/constitution.md`

Los principios bajo los que trabaja este proyecto. Se escriben **una vez, al empezar**,
y cambian rara vez; cada cambio es un evento que se anota abajo.

**Qué va aquí y qué no.** Esta es una de dos capas, y confundirlas las vuelve inútiles:

| | Constitución *(este archivo)* | Reglas promovidas *(`rules.yml`)* |
|---|---|---|
| Describe | **Cómo se trabaja** | **Qué es cierto del dominio** |
| Ejemplo | «Ninguna cifra se cita sin evidencia ejecutable» | «Un episodio dura ≥ 5 minutos» |
| Nace | Aquí, antes del primer incremento | En el paso 4 de un incremento, empíricamente |
| Dirección | De arriba abajo | De abajo arriba |

Si algo lo descubriste trabajando, no es constitucional: es una regla, y su sitio es
`rules.yml`. Si es un compromiso que asumes antes de saber nada, va aquí.

---

## Principios

> Escribe entre tres y siete. Más de siete y nadie los recuerda; menos de tres y no
> restringen nada. Cada uno debe poder **violarse**: si es imposible incumplirlo, no
> es un principio, es una descripción.

### P1 — {{Título corto}}

**Principio:** {{Qué se compromete a hacer o a no hacer el proyecto.}}

**Por qué:** {{Qué sale mal si no se respeta. Sin esto, el principio se erosiona en
cuanto aprieta el plazo.}}

**Cómo se nota que se incumplió:** {{La señal observable.}}

### P2 — {{Título corto}}

**Principio:**

**Por qué:**

**Cómo se nota que se incumplió:**

### P3 — {{Título corto}}

**Principio:**

**Por qué:**

**Cómo se nota que se incumplió:**

---

## Principios de partida sugeridos

Bórralos, quédatelos o reescríbelos. Están aquí porque son los que más caro se pagan
cuando faltan, no porque sean obligatorios.

- **Nada se afirma sin poder ejecutarlo.** Una cifra en un informe sin un comando que
  la reproduzca es `PENDING`, no un resultado.
- **Los datos de origen son de solo lectura.** Nunca se editan en el sitio: todo
  derivado se reconstruye desde el pipeline.
- **La especificación manda sobre el código.** Si la implementación revela que una
  regla es inviable, se corrige la regla con `rewind`, no se parchea el código para
  que quepa.
- **Lo que no se sabe se marca `PENDING`.** Nunca se rellena con una suposición
  plausible.
- **Un rechazo es un resultado.** «El experimento no alcanzó el criterio» es
  información y va al informe; no es motivo para bajar el criterio.

---

## Cómo se relaciona con los incrementos

1. Un incremento **no puede contradecir** un principio de aquí. Si necesita hacerlo,
   primero se cambia la constitución, explícitamente y dejando constancia abajo.
2. El paso 1 (Charter) de cada incremento se lee **contra** estos principios.
3. Las reglas que un incremento promueve (`--mode merge-increment`) viven **debajo**
   de la constitución, nunca por encima.

---

## Historial de enmiendas

Cambiar la constitución es un evento, no un ajuste. Anota siempre qué te hizo cambiar
de opinión: dentro de un año esa es la única parte que importará.

| Fecha | Qué cambió | Por qué | Quién |
|---|---|---|---|
| {{FECHA}} | Versión inicial | — | |
