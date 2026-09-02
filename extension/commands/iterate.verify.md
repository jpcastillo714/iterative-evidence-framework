---
name: "speckit-ief-verify"
description: "Verifica el Charter, evalúa el contrato de verificación y genera evidencias (F1.1)"
compatibility: "Requires spec-kit project structure with .specify/ directory"
metadata:
  author: "github-spec-kit"
  source: "extension/commands/iterate.verify.md"
---

# Command Specification: /iterate.verify

## Overview
El comando `/iterate.verify` ejecuta el protocolo de **Verification as Evidence** sobre la iniciativa actual. Inspecciona el `initiative/charter.md`, evalúa el contrato de verificación y genera evidencias empíricas.

## Target Output Artifacts
- `initiative/verification/verification-contract.yml`
- `initiative/verification/verification-summary.md`
- `initiative/verification/runs/VRN-XXX/`

## Protocol Rules & Behavior

1. **Validación de Existencia del Charter**:
   - Verificar la existencia física de `initiative/charter.md`. Si no existe, fallar inmediatamente con error explícito.

2. **Validación de Secciones Obligatorias y Formato de ID**:
   - Verificar que `initiative/charter.md` contenga las 5 secciones requeridas: Propósito, Contexto, Resultado Esperado, Restricciones y Procedencia.
   - Comprobar que el `Initiative ID` cumpla con el formato canónico (e.g. `INI-XXX`).

3. **Detección de Placeholders y Procedencia**:
   - Detectar cualquier placeholder no declarado en el documento.
   - Comprobar que el bloque de procedencia contenga autor, fecha de creación y herramienta originaria.

4. **Registro de Test Definitions (`TST-XXX`) y Runs (`VRN-XXX`)**:
   - Para cada regla de verificación del Charter, registrar un `TST-XXX`.
   - Ejecutar la comprobación empírica y registrar la corrida `VRN-XXX` correspondiente en `initiative/verification/runs/VRN-XXX/` conteniendo `command.txt`, `metadata.yml`, `stdout.txt`, `stderr.txt`, `result.yml` y `artifacts.yml`.

5. **Generación de Resumen de Verificación**:
   - Generar `initiative/verification/verification-summary.md` consolidando los resultados de todas las corridas `VRN-XXX`.

6. **Bloqueo del Gate de Gobierno**:
   - Evaluar `suite_status` (`passed`, `incomplete`, `failed`).
   - Si cualquier verificación obligatoria no cumple la regla o se encuentra bloqueada, establecer `suite_status: incomplete` o `failed` y bloquear el avance del gate en el workflow.
