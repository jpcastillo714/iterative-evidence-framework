---
name: "ief.rewind"
description: "Retrocede a un paso anterior marcando los intermedios como NEEDS_REVISION"
step_number: null
---

# Retroceso (`/speckit.ief.rewind`)

```bash
python core/scripts/verify_frame.py --mode rewind \
    --to-step <N> --reason "<que se descubrio>"
```

## Cuando usarlo

- La implementacion revela que una regla de negocio es infactible.
- Los datos reales no coinciden con el contrato.
- Un criterio de aceptacion resulta no ser verificable.

## Que hace

Marca `NEEDS_REVISION` desde el paso destino hasta el actual, **revoca las aprobaciones**
de esos pasos y registra la razon en el historial. La compuerta debera volver a pasarse.

## Regla

Si la especificacion esta mal, se corrige la especificacion. **No se parcha el codigo
para que quepa dentro de una regla equivocada**: eso deja el artefacto y el sistema
divergiendo en silencio, que es justo lo que este framework existe para evitar.

`--reason` es obligatorio. Un retroceso sin motivo declarado no deja aprender nada.
