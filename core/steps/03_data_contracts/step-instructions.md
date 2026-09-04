# Instrucciones del Paso 3: Contratos de Datos (Data Contracts)

## Cabecera del Paso

| Campo | Valor |
|-------|-------|
| **Paso** | 3 — Contratos de Datos |
| **Tipo de Incremento** | `build` |
| **Inputs obligatorios** | `initiative/increments/<SLUG>/inspection-report.md` |
| **Output** | `initiative/increments/<SLUG>/data-contract.yml` |
| **Human Gate** | ❌ No — Confirmación ligera |
| **Protocolo si algo no cuadra** | Si la implementación revela errores en el contrato, este paso se marca como NEEDS_REVISION. |

---

> **NOTA DE RETROCESO:** Si durante la implementación (Paso 6) se descubre que el contrato de datos es incorrecto, este paso será marcado como NEEDS_REVISION y deberás volver aquí para corregirlo.

## Objetivo

El objetivo de este paso es derivar esquemas de datos formales, rigurosos y legibles por máquina a partir de la inspección empírica realizada previamente. Un Contrato de Datos es una garantía formal entre sistemas (o entre componentes) sobre la estructura, el tipo y la calidad de los datos que van a intercambiar. Tu trabajo es traducir las observaciones descriptivas (textuales) de la realidad técnica en especificaciones precisas (esquemas) que guiarán el desarrollo, la validación y las pruebas automatizadas.

## Contexto

Este paso consolida la comprensión técnica de los modelos de información del sistema.
* **Prerrequisito:** El Paso 2 (Inspección Empírica) debe estar completamente FINALIZADO. No puedes redactar contratos sin haber visto los datos reales.
* **Relación con otros pasos:** Los contratos generados aquí serán la columna vertebral de las validaciones en el Paso 5 (Pruebas de Aceptación) y determinarán las estructuras de código a implementar en el Paso 6.

## Reglas Críticas

Para asegurar que los contratos de datos sean útiles y no meras ficciones, debes cumplir las siguientes reglas:

1. **Trazabilidad Absoluta:** Cada campo, propiedad o columna descrita en el contrato de datos DEBE tener una referencia rastreable a una observación documentada en el reporte de inspección del Paso 2. No se permiten atributos "huérfanos".
2. **Tipado Basado en la Realidad, no en la Teoría:** Debes usar los tipos reales observados empíricamente, no los tipos que "deberían" ser lógicamente. Por ejemplo, si un campo representa una fecha pero el sistema actual lo transmite como un string con formato `DD-MM-YYYY`, el contrato debe declarar explícitamente que es un `string` acompañado de una regla de formato `date-time`.
3. **Manejo Estricto de la Nulidad:** Los campos opcionales o que pueden contener valores nulos deben estar marcados explícitamente (ej. `nullable: true` o `required: false`). Si en la inspección viste al menos un registro nulo en un campo, este no puede ser requerido.
4. **Validaciones Incorporadas:** Un contrato no es solo una lista de tipos; debe incluir reglas de validación inherentes al modelo, tales como rangos numéricos (ej. `min: 0`), enumeraciones finitas (ej. `enum: [ACTIVO, INACTIVO]`), formatos de cadena (ej. expresiones regulares para emails) e integridad referencial.

## Protocolo Detallado (Paso a Paso)

Sigue este proceso meticuloso para construir el artefacto de contratos de datos:

1. **Revisión de la Evidencia Base:**
   * Abre y lee detenidamente el archivo `initiative/increments/<SLUG>/inspection-report.md` generado en el Paso 2.
   * Identifica todas las entidades de datos discretas (ej. Usuario, Orden, Transacción, Configuración) descubiertas durante la inspección.

2. **Creación de Entradas de Esquema:**
   * Por cada entidad de datos identificada, crea una entrada de esquema principal en tu contrato.

3. **Especificación a Nivel de Campo:**
   * Itera sobre cada atributo/campo de la entidad y define lo siguiente:
     * **Nombre:** El nombre técnico exacto del campo.
     * **Tipo:** El tipo primitivo (string, integer, boolean, object, array, etc.).
     * **Nulabilidad (Nullable):** ¿Puede ser nulo u omitido?
     * **Restricciones (Constraints):** Longitud máxima/mínima, patrones regex, rangos, etc.
     * **Descripción:** Una breve explicación semántica de qué representa el dato.
     * **Referencia de Origen (Source reference):** Una cita breve que apunte a dónde se observó (ej. "Visto en la tabla dbo.users").

4. **Reglas de Validación Inter-entidades (Cross-entity rules):**
   * Añade validaciones que involucren dependencias entre campos o entidades, como claves foráneas o verificaciones de consistencia. (Ejemplo: "El campo `fecha_fin` debe ser cronológicamente posterior a `fecha_inicio`").

5. **Validación contra Muestra Real (Si es posible):**
   * Si tienes acceso a un fragmento real de los datos (como un JSON de respuesta de prueba), contrasta mentalmente el contrato redactado contra la muestra para asegurar que pasaría la validación.

6. **Redacción del Artefacto:**
   * Transcribe toda esta especificación al archivo YAML destino utilizando la sintaxis requerida (usualmente compatible con estándares como OpenAPI Schema, JSON Schema, o el dialecto propio del marco IEF).

## Artefacto de Salida

* **Ruta de archivo:** `initiative/increments/<SLUG>/data-contract.yml` (sustituye `NNN` por el incremento correspondiente, ej. `001`).
* **Formato:** Debes utilizar la estructura de plantilla predefinida para contratos de datos, asegurándote de que el formato YAML sea válido, correctamente indentado y legible.

## Criterios de Completitud

Antes de considerar concluido este paso, verifica:
* [ ] Se han definido contratos para todas las entidades de datos clave descubiertas en el reporte de inspección.
* [ ] Cada campo define claramente su tipo, estado de nulabilidad y su procedencia/evidencia.
* [ ] Se han incluido reglas de validación básicas (formatos, rangos, enums) donde aplique.
* [ ] El documento YAML resultante tiene sintaxis válida y puede ser parseado por herramientas automatizadas.

## Errores Comunes a Evitar

* **Inventar campos no observados:** Añadir campos como `created_at` o `updated_at` simplemente porque es una "buena práctica", sin que hayan aparecido en la inspección de la base de datos real.
* **Corregir tipos prematuramente:** Intentar arreglar un mal diseño de base de datos en el contrato (ej. declarar un campo como `integer` en el contrato cuando la base de datos actual lo retorna como `string`). El contrato refleja la realidad de integración actual, no un mundo ideal.
* **Olvidar la nulabilidad:** Asumir que todos los campos son obligatorios por defecto, lo que provocará fallos en los parsers de validación durante las pruebas de integración en sistemas donde los datos suelen ser sucios o incompletos.
