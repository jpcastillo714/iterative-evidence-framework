# Paso 7: Verificación (Verification)

## Cabecera del Paso

| Campo | Valor |
|-------|-------|
| **Paso** | 7 — Verificación |
| **Tipo de Incremento** | `build` |
| **Inputs obligatorios** | Todos los artefactos del incremento + código implementado |
| **Output** | `initiative/increments/<SLUG>/increment-report.md` |
| **Human Gate** | ❌ No |
| **Protocolo si algo no cuadra** | Si la verificación falla, activar retroceso al paso correspondiente. |

---

## Objetivo

El objetivo de este paso es validar de forma definitiva que todo el trabajo del incremento funciona correctamente, generar aprendizajes (learnings) de la ejecución y preparar el entorno para el siguiente ciclo iterativo.

## Contexto

**Prerrequisito:** El Paso 6 (Implementación) debe estar COMPLETADO.
Este es el **PASO FINAL** de cada incremento dentro del Iterative Evidence Framework (IEF). Tras la conclusión exitosa de este paso, el ciclo actual se cierra y el sistema está listo para comenzar un nuevo incremento desde el Paso 1.

## Reglas Críticas




5. **Integración con Charter Global:** Revisar si los hallazgos de este incremento deben propagarse al charter global (`initiative/charter.md`). Si el incremento build generó conocimiento nuevo sobre los datos, considerar si se necesita actualizar el charter con esa información.
6. **Cierre Oficial:** Actualizar `initiative/increments/index.yml` con el estado COMPLETED.

1. **Verificación Dual Obligatoria:** La validación debe constar de dos partes innegociables:
   - *Verificación Automatizada:* Ejecución del script `verify_frame.py` y paso exitoso de todas las pruebas automatizadas de aceptación y unitarias.
   - *Revisión Semántica:* Revisión subjetiva/cualitativa (por parte del agente o de un humano) para asegurar que el valor de negocio esperado realmente se entregó.
2. **Generación de Aprendizajes (Learnings):** El reporte del incremento (`increment-report.md`) DEBE incluir una sección detallada de aprendizajes: qué salió bien, qué falló, y qué prácticas deben cambiarse en el próximo ciclo.
3. **Actualización de Índices:** El archivo central `increments/index.yml` debe ser actualizado obligatoriamente para reflejar la culminación del incremento actual.
4. **Cierre de Estado:** El archivo `state.yml` de la iteración debe actualizarse para marcar absolutamente todos los pasos como completados.

## Protocolo Detallado (Paso a Paso)

1. **Ejecución de Verificación Estructural:**
   Corre la herramienta automatizada del framework para validar la estructura:
   `python core/scripts/verify_frame.py --mode verify-step --step 7`

2. **Ejecución de Pruebas de Software:**
   Ejecuta la suite de pruebas completa del proyecto para asegurar que no hay regresiones y que el nuevo código funciona:
   `pytest tests/ -v` (o el comando equivalente según el stack tecnológico).

3. **Análisis de Resultados (Automated):**
   Revisa los resultados de las pruebas. ¿Están pasando todas? ¿Aparecieron regresiones inesperadas en áreas del código que no debían ser afectadas? Si hay fallos, el incremento no puede ser verificado y se debe volver a la implementación.

4. **Revisión Semántica (Semantic Review):**
   Evalúa el resultado general del incremento: ¿El código y los artefactos generados resuelven realmente el problema original planteado en el Charter (Paso 1)? ¿El output tiene sentido funcional y de negocio?

5. **Redacción del Reporte de Incremento:**
   Crea y redacta el archivo `increment-report.md` utilizando la plantilla oficial. Este documento debe contener obligatoriamente las siguientes secciones:
   - **Resumen del incremento:** Breve descripción de lo logrado.
   - **Resultados de tests:** Resumen de la ejecución automatizada.
   - **Hallazgos relevantes:** Decisiones arquitectónicas, descubrimientos técnicos.
   - **Learnings:** Reflexión crítica sobre qué funcionó, qué no funcionó y cómo mejorar.
   - **Recomendaciones para el próximo ciclo:** Siguientes pasos tácticos.

6. **Actualización del Índice Global:**
   Modifica el archivo `increments/index.yml`. Establece el estado del incremento actual a `COMPLETED`, añade un resumen de los aprendizajes y lista los `artifacts_produced` (artefactos producidos).

7. **Cierre del Estado del Incremento:**
   Actualiza el archivo `state.yml` del incremento. Marca todos los pasos (incluyendo este Paso 7) como `COMPLETED`. Marca el estado general del incremento como finalizado.

8. **Preparación para el Siguiente Ciclo:**
   Si existe planificación para un siguiente incremento, prepara o inicializa el `state.yml` para el nuevo ciclo, dejando el entorno listo para comenzar.

## Artefacto de Salida

- `initiative/increments/<SLUG>/increment-report.md` (Asegúrate de usar la plantilla correspondiente).
- `increments/index.yml` actualizado.
- `state.yml` actualizado y cerrado.

## Criterios de Completitud

- El 100% de las pruebas automatizadas (unitarias y de aceptación) pasan exitosamente.
- El archivo `increment-report.md` ha sido generado e incluye una sección sustancial de aprendizajes (learnings).
- El archivo `index.yml` global ha sido actualizado con el estado correcto y la metadata del incremento.
- El archivo `state.yml` refleja el cierre total del ciclo.

## Errores Comunes a Evitar

- **Omitir la Sección de Aprendizajes:** Llenar el reporte pero dejar vacía o escribir obviedades en la sección de "Learnings".
- **Olvidar el Índice:** Terminar el trabajo pero no actualizar el `index.yml`, dejando el estado global del proyecto desincronizado.
- **Falta de Limpieza de Estado:** No actualizar el `state.yml` para indicar el cierre, lo que confunde a los agentes en futuras ejecuciones.
- **Aprobar con Pruebas Rotas:** Dar por válido el incremento a pesar de que hay pruebas fallando.

## Nota Crítica sobre la Ciclicidad

Los aprendizajes (learnings) extraídos y documentados en este incremento actual **DEBEN** alimentar directamente la redacción del Charter y la planificación del próximo incremento. Este es el principal mecanismo de retroalimentación y mejora continua (Kaizen) del Iterative Evidence Framework (IEF). Sin aprendizajes iterativos, el framework pierde su propósito.
