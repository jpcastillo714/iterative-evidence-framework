---
name: "ief.gates"
description: "Consulta o cambia cuánto exige el proyecto para firmar una compuerta humana"
---

# Política de firma de las compuertas (`/speckit.ief.gates`)

## Propósito

Una compuerta la firma una persona. Desde 0.15.0 la firma guarda la huella del artefacto
aprobado y el canal por el que se dio:

| `approved_via` | Significa |
|---|---|
| `interactive` | Alguien la confirmó en una terminal, escribiendo el slug del incremento |
| `declared` | Se registró sin terminal: pudo hacerlo cualquier programa con acceso al motor |

Este comando decide si el proyecto **exige** la primera. La decisión y sus límites están
en `docs/decisiones/ADR-001-firma-humana-ligada-al-contenido.md` del bundle.

## Uso

```bash
python core/scripts/verify_frame.py --mode gate-policy                          # consultar
python core/scripts/verify_frame.py --mode gate-policy --require-interactive on  # exigir
python core/scripts/verify_frame.py --mode gate-policy --require-interactive off # dejar de exigir
```

Con la exigencia activada, `approve-step` se niega a firmar fuera de una terminal.
Desactivarla también exige estar en una terminal: si un programa pudiera apagarla, podría
apagarla y después firmar en nombre de otro.

## Reglas para el agente

- **Activarla o desactivarla lo decide el usuario.** Puedes proponerlo, no hacerlo por tu
  cuenta.
- **Si `approve-step` responde que el proyecto exige firmar desde una terminal**,
  presenta el artefacto y pídele al usuario que ejecute él mismo el comando. No intentes
  simular una terminal.
- **Si una firma aparece vencida** (el artefacto cambió después de firmado), muéstrale al
  usuario qué cambió y pídele que lo revise y vuelva a firmar:
  `--mode approve-step --increment <slug> --step <ref>`. No vuelvas a firmar tú.

## Límite

No es un mecanismo de seguridad: un proceso con una pseudoterminal puede simular una
terminal. Distingue la firma que alguien dio escribiendo de la que un programa registró
por su cuenta, que es la confusión que sí ocurre en la práctica.
