# Reportes generados por agentes — material histórico, no fuente de verdad

Los archivos de esta carpeta fueron escritos por agentes de IA durante el desarrollo
del bundle. Se conservan como registro, **no como especificación ni como evidencia**.

## Por qué están aquí y no en `docs/`

Al auditarlos en septiembre de 2026 se comprobó que varios contienen afirmaciones
que no se sostienen contra el código:

- **`DIAGNOSTICO_ARQUITECTURA_SPEC_KIT_IEF.md`** cita un bloque de código atribuido a
  `verify_frame.py` líneas 142–172, con una función `verify_yaml_artifact()`. Esa
  función **no existe en ninguna versión del repositorio**, y esas líneas contenían
  el dibujo del tablero de `cmd_status`. El `state.yml` que presenta como "estructura
  actual", con la clave `current_increment`, tampoco existió nunca aquí.

  El diagnóstico *general* del documento (duplicación de especificaciones, verificación
  superficial, brecha entre YAML y Python) resultó coincidir con problemas reales
  verificados de forma independiente. Pero sus **citas son reconstrucciones, no
  transcripciones**, y su "hoja de ruta de 5 fases" es una propuesta de un agente, no
  un plan acordado. No debe usarse como lista de tareas sin verificar cada punto.

- **`tests/results.json`** (retirado del repo) afirmaba 12 pruebas superadas, entre
  ellas una que aseveraba `extension.yml schema_version == '1.0'`. El archivo real
  declara `'3.0'`: era un resultado congelado presentado como estado actual.

- Los informes `phase-*.md`, `f1.1-*.md` y `bundle-lifecycle-*.md` describen fases de
  un plan (`plan.docx`) que ya no gobierna el diseño del bundle.

## Regla

Si necesitas saber cómo se comporta el framework, **ejecútalo**:

```bash
python core/scripts/verify_frame.py --mode check-preset
python core/scripts/verify_frame.py --mode check-bundle
python -m pytest tests/ -q
```

Un documento que describe el comportamiento es una hipótesis. La ejecución es el dato.
Es, literalmente, el principio que este framework intenta imponer sobre los proyectos
que gestiona; conviene aplicárselo a sí mismo.
