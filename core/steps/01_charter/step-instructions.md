# Instrucciones del Paso 1: Charter (Acta de Constitución)

## Cabecera del Paso

| Campo | Valor |
|-------|-------|
| **Paso** | 1 — Charter |
| **Tipo de Incremento** | `build` |
| **Inputs obligatorios** | `initiative/state.yml`, hallazgos de exploraciones previas (si existen) |
| **Output** | `initiative/charter.md` |
| **Human Gate** | ✅ Sí — REQUIERE aprobación del usuario antes de avanzar al Paso 2 |
| **Protocolo si algo no cuadra** | Este paso define el alcance. Un charter incorrecto invalida todo lo demás. |

---

## Objetivo

El objetivo de este paso es crear el "Charter" (Acta de Constitución) de la iniciativa. Este es el documento fundacional que define de manera inequívoca el **POR QUÉ** estamos realizando este trabajo y el **QUÉ** esperamos lograr. Como agente de IA, tu responsabilidad es establecer una base sólida de información que guíe todas las decisiones posteriores en el desarrollo. El Charter proporciona un marco de referencia centralizado para evitar desviaciones del alcance y asegurar el alineamiento continuo con los objetivos de negocio.

## Contexto

Este es el primer paso metodológico del Iterative Evidence Framework (IEF). Se activa de inmediato cuando el usuario invoca comandos como `/speckit.ief.init` o `/speckit.ief.charter`. Como punto de partida de toda la iniciativa, no existen prerrequisitos formales de pasos anteriores. Sin embargo, tu trabajo en este paso alimentará directamente todos los pasos subsecuentes, especialmente el Paso 2 (Inspección Empírica).

## Reglas Críticas

Al ejecutar este paso, debes adherirte estrictamente a las siguientes reglas inquebrantables:

1. **Política Anti-Alucinación Cero Tolerancia:** Si no conoces un dato (por ejemplo, quiénes son los stakeholders, cuáles son las métricas exactas o las restricciones técnicas), debes marcarlo explícitamente como `PENDING` (Pendiente). **Nunca, bajo ninguna circunstancia, inventes, asumas o deduzcas stakeholders, métricas, plazos o restricciones.**
2. **Naturaleza Viva del Documento:** El Charter es un documento VIVO (Living Document). Esto significa que está diseñado para evolucionar. No necesitas que sea perfecto en la primera iteración; su propósito es reflejar el conocimiento actual y actualizarse conforme se descubra nueva información en los pasos posteriores (como en la Inspección Empírica).
3. **Seguridad contra Sobreescritura (Non-overwrite safety):** Si el archivo `charter.md` ya existe en el directorio destino, **DEBES LEERLO PRIMERO**. No debes sobreescribirlo a ciegas. Si existe, tu tarea es proponer enmiendas, añadir la nueva información proporcionada por el usuario o actualizar variables pendientes, manteniendo el historial y la integridad del documento original.

## Protocolo Detallado (Paso a Paso)

Sigue estas instrucciones secuenciales para construir el Charter utilizando la plantilla estándar del marco. Debes completar las 7 secciones canónicas del documento:

1. **Propósito (Purpose):**
   * Extrae el objetivo principal a partir de la solicitud inicial del usuario, notas de reuniones (si las hay en `initiative/sources/`) o un brief del proyecto.
   * Sé específico. Evita descripciones vagas como "Mejorar el sistema". Prefiere: "Migrar el sistema de autenticación de v1 a v2 para soportar SSO, reduciendo la fricción de inicio de sesión".

2. **Contexto (Context):**
   * Describe el estado actual de las cosas.
   * Pregúntate y responde: ¿Qué existe hoy? ¿Qué problema estamos resolviendo? ¿Qué proceso, sistema o flujo está roto, es ineficiente o necesita modernizarse?
   * Basado en la información provista, redacta un resumen del dolor o la necesidad que justifica la iniciativa.

3. **Resultados Esperados (Outcome):**
   * Define cómo se ve el éxito.
   * Utiliza criterios medibles siempre que la información lo permita (ej. "Reducir el tiempo de carga en un 20%").
   * Si no hay métricas cuantitativas disponibles, define resultados cualitativos observables (ej. "Los usuarios pueden exportar reportes en formato PDF sin errores de timeout").

4. **Interesados (Stakeholders):**
   * Lista quiénes se preocupan por esta iniciativa. ¿Quiénes son los usuarios finales? ¿Quién revisará o aprobará el trabajo?
   * **RECUERDA:** No inventes personas ni roles. Si el usuario no menciona stakeholders, escribe `PENDING: Identificar stakeholders clave`.

5. **Restricciones (Constraints):**
   * Documenta los límites del proyecto: técnicos (ej. "Debe estar escrito en Python 3.11"), de tiempo (ej. "Debe completarse para el Q3"), de presupuesto o regulatorios (ej. "Debe cumplir con GDPR").
   * Si no tienes información sobre restricciones, marca la sección con `PENDING: Restricciones por definir`.

6. **Variables Pendientes (Pending Variables):**
   * Esta es la sección más crítica para evitar alucinaciones. Crea una lista EXPLICITA de las incógnitas del proyecto.
   * Enumera todas las preguntas que necesitan respuesta, los datos que faltan, y las decisiones que aún no se han tomado.
   * Ejemplo: "1. ¿Cuál es el formato exacto del archivo de entrada? 2. ¿Quién proveerá las credenciales de la API?"

7. **Procedencia (Provenance):**
   * Registra los metadatos de creación del documento.
   * Incluye: autor (tu identificador como IA o el nombre del usuario), fecha de creación, versión del marco de trabajo (IEF V2), y las fuentes de información utilizadas (ej. "Input directo del usuario y notas de la reunión del 12 de octubre").

## Artefacto de Salida

* **Ruta de archivo:** `initiative/charter.md`
* **Plantilla a utilizar:** Debes utilizar la estructura definida en `core/steps/01_charter/template.md`. Si no puedes acceder a la plantilla, asegúrate de crear el documento en formato Markdown incluyendo las 7 secciones detalladas en el Protocolo.

## Criterios de Completitud

Antes de dar por finalizado este paso, verifica que se cumplan las siguientes condiciones:
* [ ] El documento `charter.md` ha sido creado en el directorio correcto o actualizado apropiadamente si ya existía.
* [ ] Las 7 secciones canónicas están presentes en el documento.
* [ ] No existen datos fabricados, inventados o asumidos.
* [ ] Cualquier información faltante está explícitamente listada en la sección de Variables Pendientes o marcada como `PENDING` en su respectiva sección.

## Errores Comunes a Evitar

* **Inventar Stakeholders:** Poner "Juan Pérez, Gerente de TI" o "Equipo de Desarrollo" asumiendo que existen, sin evidencia en los inputs del usuario.
* **Establecer métricas sin datos:** Escribir "El sistema mejorará en un 50%" cuando el usuario no dio ningún número.
* **Saltarse las Variables Pendientes:** Dejar la lista de incógnitas vacía asumiendo que el contexto provisto es 100% completo, lo cual casi nunca es cierto en esta fase inicial.
* **Sobreescribir trabajo previo:** Ignorar un `charter.md` preexistente y borrar todo el contexto acumulado anteriormente.
