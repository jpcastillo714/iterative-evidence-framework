# 🔄 Iterative Evidence Framework (IEF) — Spec Kit Bundle V3

> **Define, inspecciona, verifica y construye — en ciclos empíricos con cualquier agente de IA.**

Un bundle de [Spec Kit](https://github.com/github/spec-kit) que extiende el flujo original con ciclos de 7 pasos empíricos (`build`), ciclos de exploración ligeros (`exploration`), verificación como evidencia, soporte multi-incremento, human gates y soporte multipropósito.

---

## ¿Qué hay de nuevo en IEF V3?

| Característica | Descripción |
|---|---|
| **Multi-Incremento** | Soporta trabajar en múltiples incrementos paralelos mediante subcarpetas (ej. `001_nombre/`). |
| **Dos Tipos de Ciclo** | `build` (7 pasos para desarrollo robusto) y `exploration` (3+1 pasos para análisis). |
| **Human Gates** | Pasos críticos en ciclos `build` (1, 4 y 5) ahora requieren aprobación humana explícita. |
| **Lightweight Rollback** | Nuevo comando `/speckit.ief.rewind` permite retroceder a un paso anterior si se descubre un error, marcando el progreso como `NEEDS_REVISION`. |
| **State V3** | Nuevo esquema en `state.yml` (ACTIVE, PAUSED, BLOCKED, COMPLETED, ABANDONED). |

---

## 🔁 Los Ciclos de Trabajo

### Ciclo Build (7 Pasos)
Orientado al desarrollo y puesta en producción de funcionalidades robustas.
1. Charter (Human Gate)
2. Inspección Empírica
3. Contratos de Datos
4. Reglas de Negocio (Human Gate)
5. Tests de Aceptación (Human Gate)
6. Implementación
7. Verificación

### Ciclo Exploration (3+1 Pasos)
Orientado a investigar datos y generar hallazgos antes de construir.
1. Objetivo
2. Análisis
2b. Contrato de Datos (Opcional)
3. Hallazgos

---

## ⚡ Inicio Rápido

### 1. Inicializar un proyecto
```bash
/speckit.ief.init --preset generic
```

### 2. Iniciar un incremento
```bash
# Para análisis previo:
/speckit.ief.explore

# Para construcción formal:
/speckit.ief.charter
```

### 3. Ejecutar y avanzar
El agente ejecutará cada paso y actualizará `state.yml`. Para avanzar manualmente:
```bash
/speckit.ief.next
```
O usar los comandos específicos de cada paso (ej. `/speckit.ief.inspect`).

### 4. Pausar y Retroceder
```bash
/speckit.ief.pause   # Pausa el incremento actual
/speckit.ief.rewind  # Retrocede a un paso anterior si algo falla
```

---

## 🎭 Presets

| Preset | Uso |
|--------|-----|
| `generic` | Cualquier proyecto de software o propósito general. |
| `engineering` | Pipelines, ETL, dashboards (énfasis en datos). |
| `academic` | Tesis, papers, experimentos (énfasis en hipótesis). |
| `astro-mlops` | Detección de anomalías sobre telemetría de instrumentación. Extiende `academic` con trazabilidad MLOps y herramientas ejecutables. |

---

## 🔭 Preset `astro-mlops`

Para memorias y proyectos que monitorean la salud de equipos a partir de su telemetría
(astronómica, industrial o mecatrónica). Hereda la numeración `00_admin/` … `08_presentaciones/`
del preset `academic`, así que **un proyecto `academic` existente lo adopta sin mover archivos**.

Lo que añade sobre `academic`:

| Capa | Qué aporta |
|---|---|
| **Contrato de telemetría** | Cada canal declara su `clase` (`medicion`, `consigna`, `comando`, `ambiente`, `derivada`, `descartada`), unidad, rango válido y centinelas. El contrato es ejecutable, no descriptivo. |
| **Reglas del detector** | Abstención fuera del dominio de validez, no mezclar regímenes, umbral calibrado sobre nominal, confirmación k-de-n. |
| **Criterios operacionales** | Falsas alarmas por noche, cobertura evaluable, lead time y severidad mínima detectable, acordados **antes** de ver resultados. |
| **Evidencia trazable** | `CLM → CRT → TST → VRN → EVI`, con enlace al `run_id` de MLflow y al commit de git. |
| **Scaffold MLOps** | `params.yaml`, `dvc.yaml`, `conf/config.yaml` (Hydra) y una CI que traduce las Human Gates a condición de merge. |

### Herramientas ejecutables

```bash
# El contrato de datos como test, no como documento
python core/scripts/validate_data_contract.py --contract data-contract.yml --data datos.parquet

# Ground truth fabricado cuando no hay historial de fallas etiquetado
python core/scripts/inject_faults.py bench --data episodios.parquet --column residuo --out benchmark/

# Evaluación por eventos, con falsas alarmas por noche y lead time
python core/scripts/eval_anomaly.py --scores scores.parquet --labels benchmark/injections.yml

# Cualquier cifra citable nace de un run registrado
python core/scripts/evidence_run.py --test TST-ACC-007 -- python pipelines/evaluar.py
```

Documentación de fondo:
[`core/docs/anomaly_detection_evaluation_protocol.md`](core/docs/anomaly_detection_evaluation_protocol.md) ·
[`core/docs/mlops_traceability_spec.md`](core/docs/mlops_traceability_spec.md) ·
[`docs/astro-mlops-adopcion.md`](docs/astro-mlops-adopcion.md)

---

## 🤖 Compatibilidad con Agentes

Total compatibilidad con GitHub Copilot, Antigravity, y Claude mediante `AGENTS.md` y `SKILL.md`.

---

## 📄 Licencia

MIT
