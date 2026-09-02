# Paso 5: Pruebas de Aceptación (Acceptance Tests)

## Cabecera del Paso

| Campo | Valor |
|-------|-------|
| **Paso** | 5 — Tests de Aceptación |
| **Tipo de Incremento** | `build` |
| **Inputs obligatorios** | `initiative/increments/<SLUG>/business-rules.yml`, `initiative/increments/<SLUG>/data-contract.yml` |
| **Output** | `initiative/increments/<SLUG>/acceptance-tests.yml` |
| **Human Gate** | ✅ Sí — REQUIERE aprobación del usuario antes de avanzar al Paso 6 |
| **Protocolo si algo no cuadra** | Si los tests no cubren una regla, volver a revisarlos. Cada test debe referenciar un BR-NNN. |

---

## Objetivo

El objetivo principal de este paso es traducir cada regla de negocio definida en el paso anterior en al menos una prueba de aceptación ejecutable. Estas pruebas deben utilizar el formato estandarizado *Given/When/Then* (Dado/Cuando/Entonces) para asegurar que el comportamiento del sistema esté alineado de manera precisa con los requerimientos del negocio, proporcionando criterios de éxito claros, medibles y verificables.

## Contexto

**Prerrequisito:** El Paso 4 (Business Rules / Reglas de Negocio) debe estar COMPLETADO. Las reglas de negocio aprobadas son la materia prima de este paso.
**Impacto:** El trabajo realizado aquí alimenta directamente el Paso 6 (Implementación) como guía de desarrollo y el Paso 7 (Verificación) como criterio de aceptación final. Sin pruebas de aceptación sólidas, no hay forma de validar que la implementación sea correcta.

## Reglas Críticas




4. **Gate Humano Obligatorio:** Presenta los tests al usuario para revisión. El usuario debe confirmar que los criterios de aceptación capturan correctamente el comportamiento esperado.
5. **Trazabilidad estricta:** Cada test DEBE referenciar una regla de negocio por ID (ej. linked_rule: BR-001). Tests sin trazabilidad son inválidos.

1. **Cobertura Total (1:1 o más):** Cada regla de negocio (`BR-XXX`) DEBE tener al menos una prueba de aceptación asociada (`TST-ACC-XXX`). No pueden existir reglas huérfanas sin pruebas.
2. **Naturaleza Ejecutable:** Las pruebas deben ser diseñadas de forma que sean EJECUTABLES. Esto significa que pueden ser automatizadas mediante un script (ej. pytest) o pueden ser ejecutadas por un humano, pero en ambos casos los criterios de aprobación/falla (pass/fail) deben ser inequívocos.
3. **Formato Obligatorio (Given/When/Then):**
   - **Given (Dado):** Establece las precondiciones, el estado inicial del sistema o los datos de entrada.
   - **When (Cuando):** Define la acción, el evento o la función que se ejecuta.
   - **Then (Entonces):** Describe el resultado esperado, los cambios de estado o la salida del sistema.
4. **Casos Negativos (Negative Testing):** Es obligatorio incluir pruebas negativas donde sea relevante. Define explícitamente qué es lo que DEBERÍA fallar, lanzar excepciones o ser rechazado por el sistema.
5. **Trazabilidad Contractual:** Cada prueba debe referenciar de forma explícita qué regla de negocio valida y cuáles campos del contrato de datos (Data Contract) están involucrados en la prueba.

## Protocolo Detallado (Paso a Paso)

1. **Lectura y Análisis de Insumos:**
   Comienza leyendo exhaustivamente el archivo `business-rules.yml` generado en el Paso 4, así como los esquemas definidos en los contratos de datos del Paso 3.

2. **Mapeo y Generación de Pruebas:**
   Por cada regla de negocio identificada (`BR-XXX`), redacta al menos una prueba de aceptación (`TST-ACC-XXX`). Si una regla es compleja, divídela en múltiples pruebas para abordar diferentes escenarios.

3. **Redacción en Formato BDD:**
   Utiliza el formato Given/When/Then para estructurar la prueba. Es vital emplear valores concretos y realistas en la medida de lo posible, en lugar de abstracciones genéricas.
   *Ejemplo incorrecto:* "Dado un usuario válido..."
   *Ejemplo correcto:* "Dado un usuario con email 'test@empresa.com' y rol 'admin'..."

4. **Cobertura de Casos Especiales (Edge Cases):**
   Para aquellas reglas de negocio clasificadas con prioridad CRITICAL o HIGH, debes diseñar y añadir pruebas que aborden casos límite (edge cases) y condiciones de falla.

5. **Vinculación con Data Contracts:**
   Para las pruebas que involucren validación de datos o persistencia, referencia el esquema específico y los campos del contrato de datos que están siendo validados.

6. **Clasificación de la Prueba:**
   Determina y etiqueta cada prueba según su viabilidad de ejecución:
   - **Automated:** Puede ser ejecutada por un framework de pruebas (ej. pytest, Jest).
   - **Manual:** Requiere juicio humano o configuración externa compleja.

7. **Consolidación del Artefacto:**
   Escribe todas las pruebas estructuradas en el archivo correspondiente utilizando la plantilla definida para las pruebas de aceptación.

## Artefacto de Salida

El resultado de este paso debe ser almacenado en:
`initiative/increments/<SLUG>/acceptance-tests.yml` (Asegúrate de utilizar la plantilla oficial de IEF).

## Criterios de Completitud

- Existe un 100% de cobertura de las reglas de negocio (todas las reglas tienen al menos una prueba).
- El 100% de las pruebas utilizan el formato Given/When/Then.
- Cada prueba cuenta con un criterio claro e inequívoco de éxito/falla.
- El archivo `acceptance-tests.yml` ha sido generado correctamente y validado estructuralmente.

## Errores Comunes a Evitar

- **Reglas Olvidadas:** Dejar reglas de negocio sin pruebas asociadas.
- **Aserciones Vagas:** Escribir expectativas como "el sistema debería funcionar correctamente" o "el resultado debe ser válido". Deben ser aserciones medibles.
- **Pruebas Inejecutables:** Redactar pruebas tan abstractas que un humano no sabría cómo probarlas o un script no podría implementarlas.
- **Ignorar el Camino Triste (Sad Path):** Olvidar redactar pruebas para los casos en los que la entrada es inválida o el sistema debe fallar con gracia.

## Ejemplo Concreto

```yaml
- id: TST-ACC-001
  linked_rule: BR-001
  scenario: "Pedido con descuento aplicado correctamente"
  given: "Un pedido con subtotal $10,000 y un cupón válido del 10% de descuento (campo 'discount_rate')"
  when: "Se calcula el total del pedido mediante el servicio de facturación"
  then: "El total resultante es $9,000 y el estado del pedido es 'PROCESADO'"
  type: automated
  status: DRAFT
```
