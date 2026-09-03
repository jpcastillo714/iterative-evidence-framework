---
name: "ief.focus"
description: "Cambia a qué incremento apuntan los comandos"
---

# Foco (`/speckit.ief.focus`)

## Propósito

Decir **sobre cuál de los frentes abiertos** operan los comandos que no llevan
`--increment`.

## Por qué existe

`status: ACTIVE` y «el incremento en el que estoy trabajando» son cosas distintas:

| | Significa | Cuántos |
|---|---|---|
| `status: ACTIVE` | Este frente tiene trabajo en curso | **varios** |
| `focus` | A cuál apuntan los comandos sin `--increment` | **uno** |

Antes vivían en el mismo campo. Activar un segundo incremento robaba el puntero **en
silencio**, y a partir de ahí `advance`, `approve-step` y `rewind` caían sobre un
incremento distinto del que creías. Nada fallaba: simplemente avanzabas el equivocado.

## Uso

```bash
# Ver el foco actual y los frentes abiertos
python core/scripts/verify_frame.py --mode focus

# Moverlo
python core/scripts/verify_frame.py --mode focus --increment 003_ingesta
```

Al mover el foco, si las reglas del proyecto cambiaron desde que ese incremento se
abrió, el motor lo avisa: puede que su charter haya quedado obsoleto mientras
trabajabas en otra cosa.

## Reglas

- Un incremento `COMPLETED`, `MERGED` o `ABANDONED` **no puede recibir el foco**.
- `set-status --status ACTIVE` **no mueve el foco** salvo que se le pase `--focus`.
- Al cerrar el incremento enfocado, el motor propone un sucesor en vez de dejar el
  proyecto sin foco.
