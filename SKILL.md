---
name: iterative-evidence-framework
description: >
  Iterative Evidence Framework (IEF) V3 — a dual-cycle methodology (build & exploration) 
  for software and data projects with AI agents. Supports multi-increment state tracking,
  human gates for critical steps, and a lightweight rollback protocol.
---

# Iterative Evidence Framework (IEF) V3

El **Iterative Evidence Framework (IEF) V3** es una metodología ágil diseñada para guiar el desarrollo de proyectos operados por agentes de IA. V3 introduce soporte multi-incremento, ciclos diferenciados (Build y Exploration), Human Gates, y un protocolo de rollback ligero (Rewind).

## Dos Tipos de Ciclo

### 1. Ciclo "Build" (7 Pasos)
Para construir funcionalidades robustas y verificables.
1. **Charter:** Definición de objetivos y alcance. *(Requiere aprobación humana)*
2. **Empirical Inspection:** Inspección de sistemas o datos reales.
3. **Data Contracts:** Formalización de entradas/salidas.
4. **Business Rules:** Lógica pura de dominio. *(Requiere aprobación humana)*
5. **Acceptance Tests:** Pruebas automatizadas. *(Requiere aprobación humana)*
6. **Implementation:** Código.
7. **Verification:** Ejecución y reporte.

### 2. Ciclo "Exploration" (3+1 Pasos)
Para investigar, prototipar y aprender antes de construir.
1. **Objective:** Pregunta de investigación o análisis.
2. **Analysis:** Exploración de datos, scripts, notebooks.
- **2b. Data Contract (Opcional):** Formalización si aplica.
3. **Findings:** Reporte de hallazgos (que alimentará un futuro Charter).

## Multi-Incremento y Estado (`state.yml`)

El agente coordina el trabajo leyendo y actualizando `state.yml` (esquema V3).
- **Increments:** Múltiples iteraciones conviven en carpetas slug (ej. `initiative/increments/001_nombre/`).
- **Increment States:** `ACTIVE`, `PAUSED`, `BLOCKED`, `COMPLETED`, `ABANDONED`.
- **Step States:** `PENDING`, `IN_PROGRESS`, `COMPLETED`, `APPROVED` (human gates), `NEEDS_REVISION` (rollback).

## Protocolo de Rollback (Rewind)

Si durante la implementación o verificación se descubre una regla infactible o datos incorrectos, NO parchar el código. Usar `/speckit.ief.rewind` para regresar a los pasos 3 o 4, marcar intermedios como `NEEDS_REVISION`, y reconstruir correctamente.

## Comandos Principales

- `/speckit.ief.init`: Inicializa el proyecto.
- `/speckit.ief.charter`: Inicia/continúa un incremento `build`.
- `/speckit.ief.explore`: Inicia/continúa un incremento `exploration`.
- `/speckit.ief.pause`: Pausa el incremento activo.
- `/speckit.ief.rewind`: Retroceso ligero a un paso anterior.
- `/speckit.ief.status`: Estado de todos los incrementos.
- `/speckit.ief.next`: Avanza al siguiente paso del incremento activo.
- `/speckit.ief.evidence`: Ejecuta un test y emite su evidencia (`VRN-*` + enlace MLflow).

## Presets

`generic` · `engineering` · `academic` · **`astro-mlops`**

`astro-mlops` extiende `academic` para detección de anomalías sobre telemetría de
instrumentación: contratos de telemetría ejecutables, reglas de detector con dominio de
validez, criterios operacionales (falsas alarmas por noche, cobertura, lead time) y
trazabilidad `CLM → CRT → TST → VRN → run de MLflow`. Herramientas en `core/scripts/`:
`validate_data_contract.py`, `inject_faults.py`, `eval_anomaly.py`, `evidence_run.py`.
Protocolo de evaluación en `core/docs/anomaly_detection_evaluation_protocol.md`.

*(Los comandos individuales `/speckit.ief.inspect`, `contracts`, `rules`, `tests`, `implement`, `verify` siguen disponibles para el ciclo build).*

## Reglas Clave (Core Rules)
1. **Anti-Alucinación:** Marcar faltantes como `PENDING`, no inventar.
2. **Human Gates:** No avanzar de un paso que requiera aprobación (1, 4, 5 de build) sin confirmación explícita del usuario (`APPROVED`).
3. **Zero Clutter:** Todo en su carpeta slug correspondiente. Nada de basura en la raíz.
