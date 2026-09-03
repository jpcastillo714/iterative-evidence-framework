# Instrucciones del Paso 2: Inspección Empírica (Empirical Inspection)

## Cabecera del Paso

| Campo | Valor |
|-------|-------|
| **Paso** | 2 — Inspección Empírica |
| **Tipo de Incremento** | `build` |
| **Inputs obligatorios** | `initiative/charter.md`, datos y sistemas reales del proyecto |
| **Output** | `initiative/increments/<SLUG>/inspection-report.md` |
| **Human Gate** | ❌ No — Confirmación ligera |
| **Protocolo si algo no cuadra** | Si la inspección revela que el charter es incorrecto, marcar Paso 1 como NEEDS_REVISION. |

---

## Objetivo

El objetivo principal de este paso es examinar **datos reales, documentos reales y código real**. Esta es la fase MÁS IMPORTANTE del Iterative Evidence Framework (IEF), ya que obliga al agente a confrontar las suposiciones teóricas con la realidad técnica antes de escribir una sola línea de código de implementación. Tu labor es actuar como un auditor técnico: debes observar sin prejuicios y documentar estrictamente lo que REALMENTE VES, no lo que crees que deberías ver.

## Contexto

Este paso se ejecuta después de haber completado la fase inicial de definición.
* **Prerrequisito:** El Paso 1 (Charter) debe estar COMPLETADO.
* **Relación con otros pasos:** Los descubrimientos realizados y documentados en este paso son la materia prima que alimentará directamente el Paso 3 (Contratos de Datos) y el Paso 4 (Reglas). Sin una inspección empírica rigurosa, los contratos y las reglas estarán basados en alucinaciones, lo que inevitablemente causará fallos en las etapas de pruebas e implementación.

## Reglas Críticas

Al realizar la inspección empírica, tu comportamiento debe regirse por las siguientes directrices inflexibles:

1. **Nunca inventes datos:** Si se te pide inspeccionar un archivo o una tabla de base de datos y no tienes acceso, o el archivo no existe, dilo explícitamente. No inventes esquemas, no asumas estructuras de JSON ni fabriques columnas de bases de datos. La ausencia de información es un hallazgo válido que debe ser documentado.
2. **La Realidad supera a la Documentación (Reality trumps documentation):** Si la documentación oficial, las notas de reuniones, o incluso el *Charter* dicen que el campo "fecha_nacimiento" es de tipo `Date`, pero tu inspección revela que la base de datos almacena cadenas de texto `String` (ej. "12/05/1990"), la realidad técnica es la que manda. Debes documentar esta discrepancia y actualizar el *Charter* para reflejar este descubrimiento.
3. **El tamaño de la muestra importa (Sample size matters):** No te conformes con mirar la primera fila de un CSV o el primer objeto de un JSON. Siempre que sea posible y tu ventana de contexto lo permita, inspecciona al menos de 3 a 5 muestras representativas de cada conjunto de datos para descubrir inconsistencias, campos nulos y anomalías estructurales.

4. **Confirmación Ligera:** Al terminar, muestra un resumen de los hallazgos al usuario. Si no hay objeciones, avanza.
5. **Integración de Exploración:** Revisa si existen hallazgos de incrementos de exploración previos que sean relevantes para esta inspección empírica.




## Protocolo Detallado (Paso a Paso)

Para llevar a cabo una inspección sistemática y exhaustiva, sigue este flujo de trabajo:

1. **Identificar Fuentes de Datos:**
   * Lee el archivo `initiative/charter.md` creado en el Paso 1.
   * Identifica y extrae todas las fuentes de datos mencionadas implícita o explícitamente (ej. bases de datos, APIs de terceros, archivos de configuración, reportes en CSV, logs del sistema).

2. **Acceder y Examinar:**
   * Utiliza tus herramientas de sistema (ej. lectura de archivos, consultas de bases de datos si están habilitadas, llamadas a APIs de desarrollo) para acceder físicamente a cada una de estas fuentes.

3. **Documentar Estructuras de Datos:**
   * Para cada fuente de datos accedida, debes registrar rigurosamente:
     * **Formato:** (ej. JSON, Parquet, CSV, PostgreSQL).
     * **Esquema/Estructura:** Lista de columnas, llaves o propiedades.
     * **Conteo:** Número aproximado de filas o registros (si es relevante y obtenible).
     * **Tipos de Datos Reales:** Lo que observaste (ej. un `Integer` que a veces llega como `Float`).
     * **Tasa de Nulos (Null rates):** ¿Qué campos vienen vacíos frecuentemente?
     * **Casos Extremos (Edge cases):** Anomalías descubiertas (ej. "el campo 'email' a veces contiene el string 'no-aplica' en lugar de un correo válido").

4. **Revisar Código Existente (Si aplica):**
   * Si la iniciativa implica modificar un sistema existente, examina los repositorios de código.
   * Identifica patrones de diseño utilizados.
   * Detecta y documenta deuda técnica relevante que pueda afectar la implementación futura.

5. **Revisar Documentación y Especificaciones:**
   * Lee cualquier archivo en `initiative/sources/` (ej. transcripciones, manuales, PDFs).
   * Extrae requisitos clave, lógica de negocio embebida en textos y terminología específica del dominio del negocio.

6. **Triangulación y Actualización del Charter:**
   * Cruza la información obtenida (la realidad empírica) con lo documentado en el *Charter* (las suposiciones iniciales).
   * Si descubres discrepancias materiales, proponer/ejecutar una actualización en `initiative/charter.md` para reflejar la realidad del sistema.

7. **Consolidar el Reporte:**
   * Redacta todos tus hallazgos en el documento final de inspección.

## Artefacto de Salida

* **Ruta de archivo:** `initiative/increments/<SLUG>/inspection-report.md` (donde `NNN` es el identificador del incremento actual, ej. `001`).
* **Formato:** Debes utilizar la plantilla definida para el reporte de inspección. El documento debe estar estructurado lógicamente, separando análisis de datos, revisión de código y hallazgos documentales.

## Criterios de Completitud

La inspección empírica se considera terminada y exitosa cuando:
* [ ] Se ha intentado acceder e inspeccionar absolutamente todas las fuentes de datos listadas en el Charter.
* [ ] Cada hallazgo incluye detalles técnicos precisos (tipos reales, formatos, anomalías).
* [ ] Las discrepancias entre teoría y práctica están claramente documentadas.
* [ ] Los casos extremos y las inconsistencias de los datos están listados.
* [ ] Si la realidad difiere del Charter original, este último ha sido actualizado o se ha dejado una nota clara de discrepancia.

## Errores Comunes a Evitar

* **Asumir tipos de datos:** Leer un esquema en un documento Word y asumir que el JSON de respuesta de la API es idéntico, sin hacer una llamada HTTP de prueba.
* **Ignorar casos límite:** Mirar un solo registro "feliz" (happy path) e ignorar los registros que contienen nulos o errores de formato, lo que explotará en producción.
* **Síndrome del espectador:** Ver que la base de datos es radicalmente distinta a lo planeado en el Charter, y simplemente seguir adelante sin documentar la alerta crítica ni actualizar los documentos base.
