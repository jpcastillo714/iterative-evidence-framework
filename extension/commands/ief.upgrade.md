---
name: "ief.upgrade"
description: "Muestra qué cambió en el IEF desde la versión del proyecto y lo migra, con permiso del usuario"
---

# Actualizar el proyecto a la versión del IEF (`/speckit.ief.upgrade`)

## Propósito

Un proyecto dura meses y el bundle del IEF cambia mientras tanto. Este comando responde
*«¿qué cambió desde que este proyecto se puso al día, y qué tengo que hacer?»*, y lo
aplica sin perder nada. La decisión está en
`docs/decisiones/ADR-002-compatibilidad-entre-versiones.md` del bundle.

## Cuándo

- Cuando `--mode status --json` trae `upgrade` distinto de `null`. **Va antes que
  cualquier otra cosa en la sesión.**
- Cuando cualquier comando imprime `[IEF] Este proyecto esta al dia con IEF X y el motor
  es Y`.
- Cuando `doctor` avisa que el proyecto o la sección del IEF en `AGENTS.md` están
  desactualizados.

## Protocolo

1. **Qué cambió.** Muéstrale al usuario el resultado:

   ```bash
   python core/scripts/verify_frame.py --mode upgrade-notes
   ```

   Cada cambio trae un `que hacer`. Síguelo.

2. **Qué haría la migración.** Sin `--yes` no escribe nada:

   ```bash
   python core/scripts/verify_frame.py --mode migrate
   ```

3. **Esperar la respuesta del usuario.** La migración cambia `state.yml` y `AGENTS.md`:
   la decide el usuario. Que te pida actualizar el proyecto no es lo mismo que aprobar
   esta propuesta concreta. Preséntala y espera su «sí».

4. **Aplicar, con su permiso:**

   ```bash
   python core/scripts/verify_frame.py --mode migrate --yes
   ```

   Respalda antes de escribir (`state.yml.bak-<versión>` y, si lo toca,
   `AGENTS.md.bak-<versión>`). Es idempotente: correrlo otra vez no hace nada.

5. **Revisar `AGENTS.md` con el usuario.** Si el proyecto no tenía la sección del motor,
   `migrate` la insertó al principio sin borrar nada. Busca más abajo instrucciones del
   IEF viejas o duplicadas y propón borrarlas. Las reglas propias del proyecto se quedan.

## Reglas

- **No edites `state.yml` a mano para ponerte al día.** Para eso está `migrate`.
- **Si el motor dice que el proyecto es más nuevo que él** («actualiza el bundle antes de
  escribir en este proyecto»), no lo esquives: pídele al usuario que actualice el bundle.
- **No edites dentro de los marcadores** `<!-- IEF:INICIO -->` y `<!-- IEF:FIN -->` de
  `AGENTS.md`: `migrate` los reescribe. Las reglas del proyecto van fuera.
