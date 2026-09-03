* **Pregunta al motor, no adivines.** El ciclo, las rutas y las compuertas salen del preset activo: `verify_frame.py --mode status --json`. No inventes subcarpetas ni nombres de archivo.
* **Tres ciclos por incremento.** `exploration` para investigar, `prototype` para descubrir si algo vale la pena, `build` para construir en firme. El rigor se elige por incremento, no por proyecto.
* **Compuertas humanas.** No avanzas de un paso con compuerta sin `--mode approve-step --by <usuario>`. Nunca escribas `APPROVED` editando `state.yml`: eso destruye la constancia que la compuerta existe para dejar.
* **`state.yml` no se edita a mano.** Es la maquina de estados; se toca con `verify_frame.py`, que escribe de forma atomica y deja historial.
* **Si la especificacion esta mal, se corrige la especificacion.** No parchees el codigo para que quepa en una regla equivocada: `--mode rewind` con su motivo.
* **Un incremento no termina hasta consolidarse.** `--mode merge-increment` promueve sus reglas a `initiative/specs/rules.yml`. Sin ese paso, cada incremento guarda su copia y nadie sabe cual rige.
