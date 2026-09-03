---
name: "ief.rules"
description: "Paso 4: Reglas (build)"
step_number: 4
---

# Paso 4: Reglas (`/speckit.ief.rules`)

> El **nombre** de este paso lo pone el preset: «Reglas de Negocio» en `product`,
> «Reglas del Modelo» en `research`, «Definiciones y Métricas» en `analysis`. La
> **clave** (`4_rules`) y el **archivo** (`rules.yml`) no cambian nunca. Consulta el
> nombre real con `--mode status --json`.

## Protocolo

1. Verificar que el paso 3 esté `COMPLETED`.
2. Extraer las reglas de lo que descubriste en los pasos 2 y 3. **No inventes reglas
   plausibles**: una regla que no salió de los datos ni de una decisión del usuario es
   una suposición disfrazada de norma.
3. Escribir `rules.yml` con el esquema de `core/steps/04_rules/template.yml`.
4. Comprobar contra `initiative/specs/constitution.md` y contra las reglas ya vigentes
   en `initiative/specs/rules.yml`.
5. **Human Gate**: pedir aprobación explícita.

## Cada regla lleva tres cosas

```yaml
- id: RUL-003-001
  statement: "Un pedido sin cliente se asigna al cliente generico"   # normativo y verificable
  rationale: "Descartarlos perdia 3% de facturacion real: eran ventas de mostrador"
  applies_to: "pedidos.validacion"                                    # lo que gobierna
```

- **`statement`** debe poder verificarse. Si no puedes decir qué test lo comprobaría,
  la regla está mal formulada.
- **`rationale`** es lo que antes sería una bitácora de decisiones aparte. Va dentro
  porque separada se desincroniza siempre.
- **`applies_to`** es lo que permite al motor detectar que dos incrementos se
  contradicen. Sin él, la contradicción se cuela en silencio.

## Si contradice una regla vigente

Lee `initiative/specs/rules.yml`. Si tu regla gobierna el mismo `applies_to` que una
activa:

- **La reemplaza** → declara `supersedes: RUL-XXX-YYY` y explica en el `rationale` qué
  aprendiste que la vieja no sabía.
- **No la reemplaza** → entonces se contradicen, y hay que decidir cuál rige antes de
  seguir.

Sin `supersedes`, `--mode merge-increment` **detiene la promoción**.

## Decisiones abiertas

Lo que no se decide va a `decisiones_pendientes` y **se resuelve en la compuerta**. Una
decisión aplazada hasta la implementación la termina tomando el código, en silencio y
sin que nadie la haya aprobado.

## Referencias

`core/steps/04_rules/step-instructions.md` — el protocolo completo.
