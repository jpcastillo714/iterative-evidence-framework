---
name: "speckit-ief-frame"
description: "Inicializa o actualiza el Charter de una iniciativa en initiative/charter.md (F1.1)"
compatibility: "Requires spec-kit project structure with .specify/ directory"
metadata:
  author: "github-spec-kit"
  source: "extension/commands/iterate.frame.md"
---

# Command Specification: /iterate.frame

## Overview
El comando `/iterate.frame` es el punto de entrada para encuadrar una iniciativa incierta en el Iterative Evidence Framework (IEF). Su propósito es estructurar el `initiative/charter.md` con trazabilidad estricta y sin invención de datos.

## Output File
- `initiative/charter.md`

## Protocol Rules & Behavior

1. **Recepción e Iniciación**:
   - Recibir la descripción proporcionada por el usuario para la iniciativa.
   - Si no se proporciona un nombre o descripción, solicitarla explícitamente.

2. **Creación del Directorio y Verificación de Existencia**:
   - Comprobar si `initiative/charter.md` ya existe en el espacio de trabajo.
   - Si el archivo ya existe, **NO SOBRESCRIBIR** su contenido existente sin confirmación explícita del usuario (checkpoint humano). Preservar las secciones existentes y añadir o actualizar únicamente campos complementarios.

3. **Estructura Obligatoria de `initiative/charter.md`**:
   - **Header & Initiative ID**: Asignar o verificar el ID de la iniciativa (e.g. `INI-001`).
   - **Propósito (Purpose)**: Registrar la razón fundamental de la iniciativa según la entrada real del usuario.
   - **Contexto (Context)**: Registrar el contexto de negocio/técnico expresado.
   - **Resultado Esperado (Outcome)**: Definir el resultado o meta deseada.
   - **Restricciones (Constraints)**: Registrar límites temporales, técnicos u operacionales declarados.
   - **Campos Desconocidos (PENDING)**: Si la entrada del usuario no especifica información para un campo obligatorio, marcarlo explícitamente como `PENDING`. Está **estrictamente prohibido** inventar stakeholders, requisitos, métricas o suposiciones no declaradas.
   - **Procedencia (Provenance)**: Registrar metadatos de creación/modificación:
     - `Author`: Usuario / Agente orquestador.
     - `Created At`: ISO timestamp.
     - `Tool`: `speckit.ief.frame`.

4. **Reporte de Acciones**:
   - Al finalizar, informar explícitamente al usuario la ruta del archivo creado o modificado (`initiative/charter.md`) y el Initiative ID asignado.
