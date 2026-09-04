# Relación con spec-kit

El IEF es una **herramienta autónoma** inspirada en
[**spec-kit**](https://github.com/github/spec-kit) (MIT, Copyright GitHub, Inc.). Se usa
por sí sola y no requiere tener spec-kit instalado.

De spec-kit toma la idea central —especificaciones que gobiernan el trabajo— y el formato
de sus manifiestos, para poder convivir con él sin chocar.

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

Es el mismo sentido en que un plugin de un editor sigue la API del editor sin ser una
copia de él.

## Hasta dónde llega la interoperabilidad (medido, no supuesto)

Comprobado con la CLI real de spec-kit **v1.0.4**:

| | |
|---|---|
| `specify bundle validate` | ✅ *«is well-formed and valid»* |
| `specify extension add ./extension --dev` | ✅ instala los comandos `speckit.ief.*` |
| El motor (`core/scripts/`) | ❌ no viaja: spec-kit solo copia lo que vive dentro de `extension/` |
| `presets/` | ❌ **no son presets de spec-kit** |

Sobre lo último, porque es la confusión más fácil de tener: **la palabra «preset»
significa dos cosas distintas.** Un preset de spec-kit es un paquete que *reemplaza
plantillas de comando* (`speckit.specify`, `speckit.plan`…). Un preset del IEF define *el
ciclo de trabajo*: qué pasos hay, cuáles llevan compuerta, qué artefacto produce cada uno
y con qué vocabulario se llaman. Son conceptos sin relación que comparten nombre.

Por eso en [`bundle.yml`](bundle.yml) los nuestros van bajo `provides.cycles` y no bajo
`provides.presets`: declararlos como presets hacía que `specify preset add` los tomara
por paquetes de plantillas y fallara con `Missing required field: schema_version`.

**La forma soportada de usar el IEF es autónoma:** clonar este repositorio y llamar al
motor desde el proyecto. La extensión de comandos es un extra opcional para quien ya
trabaje dentro de un proyecto spec-kit.

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
