# Instrucciones: Paso 02b - Data Contract (Exploration, Opcional)

| Campo | Valor |
|-------|-------|
| **Inputs** | Artefactos de análisis (paso 2) |
| **Output** | `data-contract.yml` |
| **Human Gate** | NO |
| **Aplica a** | exploration |

## Propósito
ESTE PASO ES OPCIONAL. Solo se ejecuta si el análisis previo reveló estructuras de datos o respuestas (APIs, bases de datos) que necesiten ser formalizadas mediante un esquema estructurado.

## Protocolo
1. Si decides crear un contrato de datos, se reusa exactamente la misma plantilla y formato que el ciclo build (Paso 3).
2. Refiérete a la plantilla principal de contratos de datos del ciclo build: `core/steps/03_data_contracts/template.yml`.
3. Crea y rellena `data-contract.yml` dentro del directorio de tu incremento actual.

## Criterios de Calidad
- El contrato debe ser sintácticamente válido (YAML puro).
- Debe describir las entidades encontradas en la inspección/análisis empírico (tipos de datos, nulabilidad, restricciones).
