# AGENTS.md: Reglas y Contexto del Proyecto (IEF)

## 1. Proyecto
* **Nombre:** {{INITIATIVE_NAME}}
* **ID:** {{INITIATIVE_ID}}
* **Preset:** {{PRESET_NAME}}

## 2. IEF Core Rules (Reglas Centrales)
Al operar en este proyecto, todos los agentes deben adherirse estrictamente a las siguientes reglas:

* **Anti-Basura (Zero Clutter):** Prohibido dejar archivos sueltos en la raíz del proyecto. Todos los archivos, scripts de prueba o artefactos deben ubicarse en su directorio semántico correspondiente.
* **Piensa Lento (Plan → Execute → Validate):** Nunca te saltes pasos. Primero planifica tu aproximación, luego ejecuta la tarea, y finalmente valida los resultados de forma rigurosa.
* **Anti-Alucinación:** Bajo ninguna circunstancia inventes datos, variables, reglas de negocio o esquemas. Si falta información o es desconocida, márcala explícitamente como `PENDING` y solicita aclaración.
* **Protocolo de Pasos (Step Protocol):** 
  1. Lee el archivo `state.yml` para determinar el paso actual.
  2. Carga *únicamente* las instrucciones del paso actual.
  3. Ejecuta el trabajo requerido.
  4. Actualiza `state.yml` al finalizar, reflejando el progreso (ej. de `IN_PROGRESS` a `COMPLETED`).
* **Reglas de Aprobación (Human Gates):** Los pasos 1 (Charter), 4 (Business Rules), y 5 (Acceptance Tests) en el ciclo build requieren aprobación explícita. "When a human gate step is completed, present the artifact to the user and wait for APPROVAL. Do NOT advance automatically."
* **Rollback Ligero:** "When implementation reveals a specification error, mark affected steps as NEEDS_REVISION and rewind current_step."

## 3. Tipos de Incremento y Estados
* **Tipos:**
  - `build`: 7 pasos (1_charter, 2_empirical_inspection, 3_data_contracts, 4_business_rules, 5_acceptance_tests, 6_implementation, 7_verification).
  - `exploration`: 3-4 pasos (1_objective, 2_analysis, 2b_data_contract opcional, 3_findings).
* **Estados de Incremento:** ACTIVE, PAUSED, BLOCKED, COMPLETED, ABANDONED.
* **Estados de Paso:** PENDING, IN_PROGRESS, COMPLETED, APPROVED, NEEDS_REVISION.

## 4. Reglas Específicas del Contexto (Preset)
{{PRESET_FRAGMENT}}

## 5. Gestión del Estado (state.yml)
El progreso de este proyecto se gestiona mediante el archivo `state.yml` de la iniciativa. 
* **Lectura:** Siempre verifica la llave del incremento activo, su tipo y el `current_step`.
* **Actualización:** Cambia los estados de `PENDING` a `IN_PROGRESS` cuando comiences un paso, a `COMPLETED` cuando lo termines. Si requiere aprobación, espera que pase a `APPROVED`.
* **Historial:** Registra los cambios de estado en la sección `history`.

## 6. Referencia de Comandos IEF
Puedes usar los siguientes comandos (o prompts) para interactuar con el flujo de trabajo:
* `/speckit.ief.init`: Inicializar una nueva iniciativa.
* `/speckit.ief.status`: Mostrar el estado actual del incremento.
* `/speckit.ief.next`: Avanzar al siguiente paso lógico según el `state.yml`.
