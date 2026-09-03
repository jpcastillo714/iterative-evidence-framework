# Relación con spec-kit

Este bundle está diseñado para funcionar con
[**spec-kit**](https://github.com/github/spec-kit) (MIT, Copyright GitHub, Inc.), del
que toma su formato de bundles, extensiones y presets.

## Qué NO es este repositorio

- **No es un fork de spec-kit** ni contiene código suyo. Todo el código de
  `core/scripts/` está escrito desde cero para este bundle.
- **No está afiliado a GitHub, Inc. ni respaldado por ella.** El nombre «spec-kit» y la
  marca GitHub pertenecen a sus dueños; aquí se usan únicamente para describir con qué
  herramienta interopera este bundle.

## Qué sí toma de spec-kit

**Convenciones de interoperabilidad**, no código:

| | |
|---|---|
| Formato de manifiestos | `bundle.yml`, `extension/extension.yml` |
| Espacio de nombres de comandos | `speckit.ief.*` — es la forma en que spec-kit direcciona los comandos de una extensión |
| Concepto de constitución | Principios del proyecto escritos una vez, bajo los que viven las especificaciones |

Estas convenciones son la interfaz de su sistema de extensiones: seguirlas es lo que
permite que el bundle se instale. Es el mismo sentido en que un plugin de un editor
sigue la API del editor sin ser una copia de él.

## En qué se aparta

La aportación propia de este bundle es invertir la dirección de la especificación.

En spec-kit la constitución se escribe **de arriba abajo**, una vez, antes de empezar.
Aquí eso se conserva, pero se le añade la dirección contraria: las reglas de dominio se
**descubren trabajando** dentro de un incremento y se promueven al proyecto con
detección de conflictos y trazabilidad de qué regla reemplazó a cuál.

Un proyecto empírico —datos, modelos, investigación— no puede conocer sus reglas de
dominio antes de mirar los datos. De ahí todo lo demás: ciclos de rigor variable por
incremento, compuertas humanas mecánicas y criterios de aceptación ejecutables.

---

Este repositorio se distribuye bajo la licencia MIT (ver [`LICENSE`](LICENSE)).
