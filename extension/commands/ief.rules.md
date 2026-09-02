---
name: "ief.rules"
description: "Paso 4: Reglas de Negocio (build)"
step_number: 4
---

# Paso 4: Reglas de Negocio (`/speckit.ief.rules`)

## Protocolo
1. Verificar que Paso 3 esté `COMPLETED`.
2. Crear/actualizar `initiative/increments/<SLUG>/04_business_rules/`.
3. Extraer reglas, transformaciones o lógica core a un documento estructurado.
4. Asignar IDs a las reglas (ej. BR-001).
5. **Human Gate**: Pedir aprobación al usuario.
6. Si aprueba, marcar como `APPROVED`.

## Si el preset es `astro-mlops`

- Partir de `core/steps/04_business_rules/template.detector.yml`.
- Aquí se decide **qué es una anomalía y cuándo el sistema tiene derecho a hablar**, no qué
  modelo se usa. El modelo concreto es decisión del Paso 6.
- Reglas que no pueden faltar: solo canales `medicion`/`derivada` alimentan al detector;
  abstención fuera del dominio de validez; umbral calibrado sobre nominal con cuantil
  declarado; confirmación k-de-n; y prohibición explícita de ajustar el umbral a posteriori.
- Las decisiones abiertas (un modelo por unidad o compartido, definición operacional de
  anomalía) se listan en `decisiones_pendientes` y se resuelven **en el gate**.
