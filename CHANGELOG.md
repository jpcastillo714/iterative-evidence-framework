# Registro de cambios

Los cambios de cada versión del IEF, para personas. El formato sigue
[Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/) y el versionado,
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

**Política de compatibilidad** ([ADR-002](docs/decisiones/ADR-002-compatibilidad-entre-versiones.md)).
Mientras el bundle esté en 0.y.z, se aplica una regla más estricta que la de SemVer:
ningún cambio incompatible para los proyectos existentes se aplica sin aviso previo.
Lo que se retira se anuncia antes como **Obsoleto** en una versión anterior, y el motor
sigue aceptándolo con una advertencia mientras tanto.

Lo mismo, en forma que el motor filtra por la versión de cada proyecto y con la acción
concreta para los agentes, está en [`core/cambios.yml`](core/cambios.yml). En un proyecto:
`--mode upgrade-notes`.

## [0.15.0] - 2026-09-24

Implementa [ADR-002](docs/decisiones/ADR-002-compatibilidad-entre-versiones.md) y
[ADR-001](docs/decisiones/ADR-001-firma-humana-ligada-al-contenido.md).

### Añadido
- `state.yml` registra `ief_version`, la versión del IEF con la que el proyecto está al día.
- `--mode upgrade-notes`: qué cambió entre la versión del proyecto y la del motor, y qué hacer.
- `--mode migrate`: lleva el proyecto a la versión del motor. Sin `--yes` solo muestra qué
  haría. Con `--yes` respalda `state.yml` (y `AGENTS.md`, si lo toca) antes de escribir. Es
  idempotente.
- `status --json` trae `ief_version`, `engine_version`, `upgrade` y, por paso, `signature`.
- La firma de una compuerta guarda la huella SHA-256 del artefacto (`artifact_sha256`) y el
  canal por el que se dio (`approved_via`: `interactive` o `declared`).
- `--mode gate-policy --require-interactive on|off`: exigir que las compuertas se firmen
  desde una terminal interactiva.
- Un motor más viejo que el proyecto se niega a escribir en él.
- `core/cambios.yml`, este archivo, y su validación en `--mode check-bundle`.
- `docs/decisiones/` y `docs/REFERENCIAS.md`: decisiones de diseño con su evidencia
  verificada.

### Cambiado
- La parte del IEF en el `AGENTS.md` de cada proyecto la escribe el motor (`init`, `adopt`,
  `migrate`) entre los marcadores `<!-- IEF:INICIO vX -->` y `<!-- IEF:FIN -->`. Lo escrito
  fuera de ellos no se toca.
- Una firma sobre un artefacto que cambió después está vencida: `check-gates` falla,
  `doctor` lo marca como problema y `advance` no deja pasar. Firmar los criterios de
  aceptación los congela.
- `doctor` informa si el proyecto está desactualizado, si la sección del IEF en `AGENTS.md`
  falta o es vieja, las firmas vencidas, y resume las firmas declaradas o sin huella.

### Corregido
- `approve-step` y `advance` respetan `--increment` y nombran el incremento en la salida.
  Antes actuaban siempre sobre el incremento enfocado, y una firma podía caer sobre el
  incremento equivocado sin aviso.

## [0.14.0] - 2026-09-24

Primera versión con registro de cambios. La historia anterior está en `git log`.
