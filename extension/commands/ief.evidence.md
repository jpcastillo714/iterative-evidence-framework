---
name: "ief.evidence"
description: "Registra la ejecución de un test como evidencia (VRN + enlace MLflow)"
step_number: 7
---

# Evidencia de verificación (`/speckit.ief.evidence`)

## Propósito

Ejecutar un comando y dejar su rastro completo: carpeta `VRN-*` con la evidencia cruda y,
si MLflow está disponible, el run etiquetado con las claves `ief.*`. Es el paso que convierte
"lo corrí y dio 0.87" en una cifra citable.

Complementa a `/speckit.ief.verify`: aquel decide si el incremento pasa; este produce la
evidencia sobre la que se decide.

## Precondiciones

- Existe `initiative/state.yml` con un incremento activo (o se pasa `--increment`).
- El test que se ejecuta está declarado en `acceptance-tests.yml` (Paso 5) con su `test_id`.
- Si la cifra se va a citar en el informe, el test tiene `CLM-XXX` y `CRT-XXX` asociados.

## Protocolo de ejecución

1. **Identificar el test.** Leer `acceptance-tests.yml` del incremento activo y localizar el
   `TST-ACC-XXX` que corresponde. Si no existe, detenerse: no se genera evidencia de un test
   que nadie definió ni aprobó.
2. **Resolver la trazabilidad.** Recuperar `linked_rule` (BR), criterio (CRT) y afirmación
   (CLM). Si falta alguno, avisar al usuario y continuar con `PENDING`, dejando constancia de
   que el run **no es citable** hasta completarlos.
3. **Ejecutar con el puente.**

   ```bash
   python core/scripts/evidence_run.py \
       --test TST-ACC-007 --claim CLM-003-001 --criterion CRT-003-002 \
       --name "Tasa de falsas alarmas en operacion nominal" \
       --metrics-from 06_resultados/experimentos/evaluacion.json \
       -- python 04_codigo/pipelines/evaluar.py
   ```

4. **Leer el resultado y clasificarlo.** Un `status: failed` admite tres lecturas distintas y
   hay que elegir una explícitamente:
   - **fallo de ejecución** → arreglar el código o el entorno y volver a ejecutar;
   - **hipótesis rechazada** → es un resultado; va al informe y puede motivar
     `/speckit.ief.rewind` al Paso 4;
   - **verificación bloqueada** → falta un prerrequisito; marcar el test como `blocked` con su
     bloqueo declarado, no como fallido.
5. **Actualizar el estado.** Registrar el `vrn_id` en el historial del incremento en
   `state.yml` y en el reporte del Paso 7.
6. **Informar al usuario** con el `vrn_id`, el `status`, la ruta de la evidencia y, si lo hay,
   el `run_id` de MLflow.

## Reglas

- **Nunca editar a mano un `VRN-*`.** Si algo salió mal, se ejecuta otro run. La evidencia es
  un registro histórico, no un borrador.
- **Un run por test.** Agrupar varias verificaciones en un solo comando destruye la
  trazabilidad de cuál falló.
- **Una cifra sin VRN es `PENDING`,** no un resultado, por muy segura que parezca.
- Para verificaciones negativas (donde se espera un exit code distinto de 0), usar
  `--expected-exit-code N` o `--allow-failure`.

## Postcondiciones

- Existe `initiative/increments/<SLUG>/verification/runs/VRN-*/` con los seis archivos de
  evidencia.
- `artifacts.yml` enumera los artefactos producidos y, cuando corresponde, el `run_id`.
- El historial del incremento en `state.yml` referencia el `vrn_id`.

## Referencias

- `core/docs/verification_contract_spec.md` — taxonomía de la cadena de evidencia.
- `presets/astro-mlops/docs/mlops_traceability_spec.md` — vocabulario de etiquetas y formato de citación.
