---
name: "ief.doctor"
description: "Diagnostica el estado real del proyecto: bloqueos, conflictos, olvidos"
---

# Diagnóstico (`/speckit.ief.doctor`)

## Propósito

Responder *«¿en qué estado real está esto?»*, que no es lo mismo que `status`.

`status` muestra **lo que hay**. `doctor` muestra **lo que está mal**: cosas que
ninguna pantalla revela porque cada una se decidió por separado, con semanas de
diferencia, y ninguna parecía un problema en su momento.

## Qué revisa

| Revisión | Por qué importa |
|---|---|
| Dependencias circulares | A bloquea B bloquea A: ninguno se desbloquearía nunca |
| Bloqueos vencidos o rancios | La fecha esperada pasó, o lleva más de 30 días parado |
| Bases de reglas obsoletas | Un incremento construido sobre reglas que ya cambiaron |
| Demasiados frentes activos | Más allá del límite blando suele ser dispersión |
| `COMPLETED` sin promover | Sus reglas nunca subieron a la especificación viva |
| Compuertas sin aprobar | Un paso terminado que nadie aprobó |
| Proyecto detenido | Todos los frentes pausados o bloqueados a la vez |
| Sin foco | Hay trabajo abierto y ningún incremento enfocado |

## Uso

```bash
python core/scripts/verify_frame.py --mode doctor
```

Sale con código 1 si hay problemas (no solo avisos), así que sirve en CI.

## Cuándo ejecutarlo

- Al **volver** a un proyecto tras un tiempo fuera. Es lo primero que hay que correr.
- Antes de cerrar un incremento.
- En CI, junto a `check-gates`.
