---
name: "ief.next"
description: "Avanza al siguiente paso del incremento activo"
step_number: null
---

# Siguiente paso (`/speckit.ief.next`)

```bash
python core/scripts/verify_frame.py --mode verify-step   # el paso actual esta bien?
python core/scripts/verify_frame.py --mode advance
```

## Que hace el motor

Lee el ciclo del preset y decide. Rechaza el avance si:

- el paso actual no esta `COMPLETED`;
- el paso actual tiene **compuerta humana** y no esta `APPROVED`.

En el segundo caso, pedir aprobacion explicita al usuario y solo entonces:

```bash
python core/scripts/verify_frame.py --mode approve-step --by "<usuario>"
```

## Regla

No marcar un paso como `APPROVED` editando `state.yml`. La aprobacion se registra con
autor y fecha en el historial; escribirla a mano destruye esa constancia y es
exactamente lo que la compuerta existe para impedir.
