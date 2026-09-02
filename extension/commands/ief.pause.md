---
name: "ief.pause"
description: "Pausa el incremento activo"
step_number: null
---

# Pausar (`/speckit.ief.pause`)

Preguntar al usuario la razon y despues:

```bash
python core/scripts/verify_frame.py --mode set-status \
    --increment <SLUG> --status PAUSED --reason "<razon>"
```

## PAUSED o BLOCKED

- **PAUSED**: decision propia (cambio de prioridad, falta de tiempo).
- **BLOCKED**: dependencia externa. Requiere ademas `--blocked-by "<de quien depende>"`.

Distinguirlos importa: un `BLOCKED` es una peticion pendiente a alguien mas, y se
revisa distinto que un `PAUSED`.

## Al retomar

```bash
python core/scripts/verify_frame.py --mode set-status --increment <SLUG> --status ACTIVE
```

Esto lo vuelve el incremento activo y limpia la razon de pausa.
