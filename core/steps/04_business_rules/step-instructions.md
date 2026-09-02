# Instrucciones del Paso 4: Reglas de Negocio (Business Rules)

## Cabecera del Paso

| Campo | Valor |
|-------|-------|
| **Paso** | 4 — Reglas de Negocio |
| **Tipo de Incremento** | `build` |
| **Inputs obligatorios** | `initiative/increments/<SLUG>/data-contract.yml`, `initiative/charter.md` |
| **Output** | `initiative/increments/<SLUG>/business-rules.yml` |
| **Human Gate** | ✅ Sí — REQUIERE aprobación del usuario antes de avanzar al Paso 5 |
| **Protocolo si algo no cuadra** | Si la implementación revela que una regla es infactible, este paso se marca como NEEDS_REVISION. |

---

## Objetivo

El objetivo de este paso es extraer, clasificar y formalizar cada componente de lógica funcional en un registro trazable de **Reglas de Negocio**. El propósito de este registro es actuar como la "fuente de la verdad" del comportamiento del sistema, traduciendo requisitos difusos, notas de reuniones y estructuras de datos implícitas en un conjunto exhaustivo de reglas discretas y verificables. Esto evitará las regresiones funcionales y garantizará que el software construido refleje exactamente las necesidades del negocio.

## Contexto

Este paso consolida el conocimiento comportamental del sistema.
* **Prerrequisito:** Los Pasos 2 (Inspección Empírica) y 3 (Contratos de Datos) deben estar COMPLETADOS.
* **Fuentes de Información:** Debes apoyarte intensamente en el *Charter* (Paso 1), el reporte de inspección (Paso 2), las transcripciones de reuniones (en `initiative/sources/`), los contratos de datos (Paso 3) y el análisis del código existente.
* **Relación con otros pasos:** Las reglas generadas en este registro son la entrada directa y principal para el Paso 5 (Pruebas de Aceptación). Cada regla se convertirá eventualmente en uno o más casos de prueba automatizados.

## Reglas Críticas




5. **Gate Humano CRÍTICO:** Después de generar las reglas de negocio, DEBES presentarlas al usuario para revisión. NO avances al Paso 5 hasta recibir aprobación explícita. Las reglas de negocio son la fuente de verdad del comportamiento del sistema — un error aquí se propaga a tests e implementación.
6. **Anti-Apresuramiento:** Cada regla debe ser atómica, comprobable y trazable. Si no puedes citar la fuente de una regla, márcala como DRAFT.

El éxito de este paso depende del cumplimiento de los siguientes principios rectores:

1. **Identificadores Únicos y Trazabilidad:** Cada regla registrada DEBE poseer un ID alfanumérico único e inmutable (ej. `BR-001`, `BR-002`, `REG-AUTH-05`) y una cita explícita a la fuente de donde se extrajo (ej. "Mencionado por el cliente en la transcripción de la reunión del 05/10, minuto 14:20" o "Derivado de la validación descubierta en el archivo src/auth.py").
2. **Atomicidad de las Reglas:** La regla de oro es: **Una regla = Un comportamiento comprobable**. Si una regla contiene condiciones de ramificación mediante conjunciones complejas como "Y", "O", "EXCEPTO QUE", probablemente deba dividirse. Las reglas deben ser atómicas para que las pruebas asociadas sean precisas y aislables.
3. **Priorización Rigurosa:** Las reglas no tienen el mismo peso. Deben clasificarse usando una escala estándar:
   * `CRITICAL`: Si esta regla falla, el sistema es inservible o se producen pérdidas financieras/riesgos de seguridad graves.
   * `HIGH`: Flujo principal del negocio afectado, pero existen alternativas manuales o "workarounds".
   * `MEDIUM`: Reglas de mejora de UX, validaciones secundarias o casos extremos comunes.
   * `LOW`: Comportamientos cosméticos o validaciones marginales.
4. **Seguimiento de Estado:** El ciclo de vida de una regla debe monitorearse: de `DRAFT` (Borrador inicial), a `VALIDATED` (Confirmada empíricamente o por el usuario), a `APPROVED` (Lista para implementación) o a `DEPRECATED` (Regla obsoleta que ya no aplica).

## Protocolo Detallado (Paso a Paso)

Para construir un registro de reglas de negocio completo y sin ambigüedades, sigue estas acciones secuenciales:

1. **Recolección Sistemática de Evidencias:**
   * Revisa el `charter.md` para extraer reglas de alto nivel y restricciones.
   * Revisa el `inspection-report.md` para identificar reglas de validación implícitas en los datos reales (ej. "Los IDs de transacción observados siempre comienzan con 'TX-'").
   * Revisa cualquier archivo de texto, acta de reunión o correo en el directorio `initiative/sources/`.
   * Revisa el `data-contract.yml` generado en el Paso 3 para asociar reglas de integridad (ej. relaciones entre campos).

2. **Extracción y Redacción de Reglas:**
   * Por cada comportamiento identificado, redacta una regla clara y concisa en formato declarativo o condicional (ej. "Si un usuario tiene saldo negativo, no puede emitir nuevas órdenes de compra").

3. **Asignación de Atributos:**
   * Para cada regla redactada, asigna:
     * Un `ID` único.
     * Una `descripción` precisa.
     * El `origen` de la regla (cita/fuente).
     * El nivel de `prioridad`.
     * El `estado` inicial (generalmente `DRAFT`).

4. **Auditoría de Atomicidad:**
   * Revisa la lista completa de reglas. Si encuentras reglas del tipo "El usuario debe ser mayor de edad Y residir en el país Y tener una cuenta bancaria aprobada", divídela en `BR-101` (Validación de edad), `BR-102` (Validación de residencia) y `BR-103` (Validación de estado de cuenta bancaria).

5. **Referencia Cruzada con Contratos de Datos:**
   * Asegúrate de que los sustantivos utilizados en las descripciones de las reglas coincidan con los nombres de campos y entidades definidos formalmente en el `data-contract.yml`. Mantén un vocabulario ubicuo y coherente.

6. **Consolidación del Artefacto:**
   * Vuelca todas las reglas, correctamente formateadas y categorizadas, en el documento de salida en formato YAML.

## Artefacto de Salida

* **Ruta de archivo:** `initiative/increments/<SLUG>/business-rules.yml` (donde `NNN` es el número de incremento actual, ej. `001`).
* **Formato:** Debes emplear la plantilla predefinida y estructurar la información en un formato YAML válido, en forma de lista o diccionario de reglas indexadas por su ID.

## Criterios de Completitud

Tu labor en este paso finaliza satisfactoriamente cuando:
* [ ] Se han identificado y documentado todas las reglas deducidas de los pasos previos y las fuentes disponibles.
* [ ] Absolutamente todas las reglas tienen asignado un ID único y un origen/fuente comprobable.
* [ ] No existen reglas compuestas complejas; se ha aplicado el principio de atomicidad.
* [ ] La terminología empleada en las reglas concuerda con las entidades definidas en el paso de Contratos de Datos.

## Errores Comunes a Evitar

* **Reglas Compuestas y Monolíticas:** Escribir un párrafo completo de comportamiento como si fuera una sola regla. Esto hace imposible asociarle una prueba de aceptación unitaria simple (ej. "El sistema procesa el pago, envía un email de confirmación, descuenta el stock y actualiza el log de auditoría" -> Deben ser 4 reglas distintas).
* **Ausencia de Fuentes:** Inventar reglas que suenan lógicas pero que ningún stakeholder solicitó ni están sustentadas en el análisis empírico. El sistema solo debe hacer lo que el negocio y los datos justifican.
* **Omisión de Estados Negativos:** Enfocarse únicamente en lo que el sistema "debe hacer" (Happy path) olvidando redactar las reglas de lo que el sistema "NO debe hacer" frente a entradas inválidas o casos extremos.
