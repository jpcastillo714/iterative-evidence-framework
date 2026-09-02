# Paso 6: Implementación (Implementation)

## Cabecera del Paso

| Campo | Valor |
|-------|-------|
| **Paso** | 6 — Implementación |
| **Tipo de Incremento** | `build` |
| **Inputs obligatorios** | `initiative/increments/<SLUG>/data-contract.yml`, `business-rules.yml`, `acceptance-tests.yml` |
| **Output** | Código en `src/` y tests en `tests/` |
| **Human Gate** | ❌ No |
| **Protocolo si algo no cuadra** | Ver sección "Protocolo de Retroceso Ligero" más abajo. |

---

## Objetivo

El objetivo de este paso es escribir el código fuente real que da vida a la solución diseñada. La implementación debe ceñirse estrictamente al plan, respetando sin desviaciones los contratos de datos (Data Contracts), las reglas de negocio (Business Rules) y las pruebas de aceptación (Acceptance Tests) previamente definidos.

## Contexto

**Prerrequisito:** El Paso 5 (Pruebas de Aceptación) debe estar COMPLETADO. Este es el momento donde finalmente se escribe código de producción.
**Nota Importante:** A diferencia de otros pasos del Iterative Evidence Framework (IEF), NO existe una plantilla estándar de artefacto (YAML o Markdown) para este paso. El producto o salida de este paso es el código fuente escrito directamente en los directorios correspondientes del proyecto (ej. `src/`, `tests/`).

## Reglas Críticas

1. **Respeto Absoluto a los Contratos de Datos:** El código DEBE honrar los contratos de datos establecidos en el Paso 3. Si el contrato indica que un campo es anulable (nullable), el código debe manejar los nulos adecuadamente. Si indica un tipo específico o límite, la validación debe reflejarlo.
2. **Implementación Trazable de Reglas de Negocio:** El código DEBE implementar explícitamente las reglas de negocio. Cada regla (`BR-XXX`) debe ser trazable dentro de la base de código. Esto puede lograrse mediante comentarios en funciones clave, nombres de funciones autodescriptivos o un archivo de mapeo.
3. **Pruebas Continuas (Test As You Go):** Ejecuta las pruebas de aceptación y unitarias a medida que desarrollas. No postergues la ejecución de pruebas hasta la fase de verificación. El desarrollo debe ser guiado por las pruebas.
4. **Adherencia a Convenciones:** Sigue estrictamente las convenciones existentes del proyecto (reglas de linting, formateo de código, nomenclatura de variables, arquitectura de carpetas).
5. **Cero Sobre-Ingeniería (No Over-engineering):** Implementa exactamente lo que dice la especificación, nada más. No añadas características especulativas ni abstracciones innecesarias que no estén justificadas por las reglas de negocio actuales.
6. **Manejo de Archivos Temporales:** Cualquier archivo de prueba, script rápido o datos de descarte debe colocarse en la carpeta `scratch/`, NUNCA en el directorio fuente (`src/`).

## Protocolo Detallado (Paso a Paso)

1. **Revisión Integral de Especificaciones:**
   Antes de escribir una sola línea de código, lee nuevamente los Data Contracts (Paso 3), las Business Rules (Paso 4) y los Acceptance Tests (Paso 5). Tenlos abiertos como referencia constante.

2. **Planificación Arquitectónica Ligera:**
   Planifica mentalmente o en un archivo temporal cómo se estructurará la implementación: determina qué módulos, clases y funciones son necesarios para satisfacer las pruebas.

3. **Desarrollo del Código Fuente:**
   Escribe el código de producción en el directorio fuente (ej. `src/` o la estructura que el proyecto utilice). Asegúrate de que el código sea limpio, legible y documentado.

4. **Desarrollo de Pruebas Unitarias:**
   En paralelo a la escritura del código fuente, escribe las pruebas unitarias correspondientes en el directorio `tests/`. Las pruebas unitarias deben validar la lógica a nivel de componentes aislados.

5. **Ejecución y Corrección Iterativa:**
   Ejecuta las pruebas de aceptación automatizadas para verificar que cada regla de negocio es satisfecha. Si una prueba falla, corrige el código fuente inmediatamente.

6. **Documentación de Desviaciones (Excepcional):**
   Si por razones técnicas insalvables debes desviarte de la especificación original, documenta claramente la desviación, su justificación y el impacto esperado. Esto debe ser una excepción, no la regla.

7. **Actualización de Estado:**
   Una vez que todas las pruebas (unitarias y de aceptación) pasen exitosamente, actualiza el archivo `state.yml` para marcar el paso de implementación como COMPLETADO.



## ⚠️ Protocolo de Retroceso Ligero

Si durante la implementación descubres que una especificación anterior es incorrecta o infactible:

### ¿Cuándo activar el retroceso?
- El modelo matemático/algorítmico es infactible con las reglas definidas
- Los datos reales no coinciden con el contrato de datos
- Una regla de negocio es contradictoria o imposible de implementar
- Los tests de aceptación no son verificables con la implementación actual

### ¿Qué hacer?
1. **DETENTE**. No sigas parcheando código a ciegas.
2. **Identifica** qué paso anterior contiene el error:
   - ¿Datos incorrectos? → Volver al Paso 2 (Inspección) o Paso 3 (Contratos)
   - ¿Regla incorrecta? → Volver al Paso 4 (Business Rules)
   - ¿Test mal definido? → Volver al Paso 5 (Acceptance Tests)
3. **Informa al usuario**: "He detectado que [descripción del problema]. Necesito volver al Paso X para corregir [artefacto]."
4. **Actualiza state.yml**:
   - Marca el paso actual (6) como `NEEDS_REVISION`
   - Marca el paso destino como `NEEDS_REVISION`
   - Actualiza `current_step` al paso destino
   - Registra en `history`: `{ step: 6, action: "REWIND", target_step: X, reason: "..." }`
5. **Corrige** el artefacto del paso anterior.
6. **Re-avanza** desde ese paso, revisando los artefactos intermedios.

### ¿Qué NO hacer?
- No intentes parchar el código sin corregir la especificación
- No ignores discrepancias esperando que se resuelvan solas
- No acumules más de 3-5 intentos de fix sin retroceder formalmente

## Artefacto de Salida

Código fuente funcional y verificado en `src/` (o equivalente) y pruebas en `tests/`. No hay archivo de plantilla para este paso.

## Criterios de Completitud

- Todas las pruebas de aceptación y unitarias pasan sin errores.
- El código respeta rigurosamente los esquemas y tipos de los contratos de datos.
- La cobertura de pruebas unitarias es adecuada y cubre al menos los caminos principales y críticos.
- El código se adhiere a los estándares de linting y formateo del proyecto.

## Errores Comunes a Evitar

- **Sobre-ingeniería:** Construir sistemas genéricos hiper-complejos para resolver un problema simple detallado en la especificación.
- **Ignorar Contratos de Datos:** No validar tipos de datos, no manejar valores nulos (null/None) o ignorar las restricciones de longitud u obligatoriedad.
- **Contaminación del Directorio:** Dejar archivos de prueba sueltos (`test_rapido.py`) en la raíz del proyecto o en `src/`.
- **Desarrollo Ciego:** Escribir todo el código y dejar las pruebas para el final.

## Directiva Especial

**Atención Agentes de IA:** Este es el punto exacto donde existe la mayor tentación de "apresurarse a programar" (rush to code). ¡RESISTE ESTA TENTACIÓN! Lee exhaustivamente las especificaciones antes de codificar. Sigue el contrato al pie de la letra. Codifica iterativamente y prueba a cada paso. Tu valor aquí no es escribir código rápido, es escribir código verificablemente correcto.
