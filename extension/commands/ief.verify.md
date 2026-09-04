---
name: "ief.verify"
description: "Paso 7: Verificacion (build)"
step_number: 7
---

# Paso 7: Verificacion (`/speckit.ief.verify`)

Ejecutar los criterios del Paso 5 y redactar el reporte del incremento.

## Rutas

El motor resuelve la ruta del artefacto desde el preset. **No inventes subcarpetas**:
el artefacto de este paso va exactamente en

```
initiative/increments/<SLUG>/increment-report.md
```

Consultala siempre con `python core/scripts/verify_frame.py --mode status --json`.

## Protocolo

1. Comprobar que el paso anterior este `COMPLETED` y, si tiene compuerta, `APPROVED`.
2. Escribir el artefacto en la ruta de arriba, partiendo de la plantilla que el
   preset declara para este paso.
3. Verificar antes de cerrar:
   ```bash
   python core/scripts/verify_frame.py --mode verify-step --step 7
   ```
4. Cerrar el paso con el motor (verifica el artefacto antes de darlo por hecho):
   `python core/scripts/verify_frame.py --mode complete-step`
5. Avanzar:
   ```bash
   python core/scripts/verify_frame.py --mode advance
   ```

## Ejecutar los criterios, no describirlos

```bash
python core/scripts/compile_acceptance_tests.py --increment <SLUG>
pytest tests/generated -v
```

Un `failed` admite tres lecturas y hay que elegir una explicitamente:

- **fallo de ejecucion** -> arreglar el codigo o el entorno y volver a ejecutar;
- **hipotesis rechazada** -> es un resultado; va al informe y puede motivar
  `/speckit.ief.rewind` al Paso 4;
- **verificacion bloqueada** -> falta un prerrequisito; se marca `status: blocked`
  con su bloqueo declarado, no como fallido.

## Cierre del incremento

```bash
python core/scripts/verify_frame.py --mode check-gates
python core/scripts/verify_frame.py --mode set-status --increment <SLUG> --status COMPLETED
python core/scripts/verify_frame.py --mode merge-increment --increment <SLUG> --dry-run
python core/scripts/verify_frame.py --mode merge-increment --increment <SLUG>
```

El `merge` promueve las reglas del incremento a `initiative/specs/`, que es la
especificacion **viva** del proyecto. Sin ese paso, cada incremento acumula su propia
copia y nadie sabe cual es la regla vigente.
