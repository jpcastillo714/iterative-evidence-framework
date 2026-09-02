---
name: "ief.tests"
description: "Paso 5: Criterios de Aceptacion (build)"
step_number: 5
---

# Paso 5: Criterios de Aceptacion (`/speckit.ief.tests`)

Escribir los criterios de aceptacion, cada uno enlazado a una regla (`linked_rule`).

## Rutas

El motor resuelve la ruta del artefacto desde el preset. **No inventes subcarpetas**:
el artefacto de este paso va exactamente en

```
initiative/increments/<SLUG>/acceptance-tests.yml
```

Consultala siempre con `python core/scripts/verify_frame.py --mode status --json`.

## Protocolo

1. Comprobar que el paso anterior este `COMPLETED` y, si tiene compuerta, `APPROVED`.
2. Escribir el artefacto en la ruta de arriba, partiendo de la plantilla que el
   preset declara para este paso.
3. Verificar antes de cerrar:
   ```bash
   python core/scripts/verify_frame.py --mode verify-step --step 5
   ```
4. Marcar el paso como `COMPLETED` en `state.yml`.

   **Compuerta humana.** Pedir aprobacion explicita al usuario y, solo si aprueba:
   ```bash
   python core/scripts/verify_frame.py --mode approve-step --by "<usuario>"
   ```
   El motor NO deja avanzar sin esto, y la CI lo comprueba con `--mode check-gates`.

5. Avanzar:
   ```bash
   python core/scripts/verify_frame.py --mode advance
   ```

## Cada criterio debe poder ejecutarse

Un `given/when/then` en prosa no es un criterio: es una intencion. Declara ademas un
bloque `verify` para que el compilador lo convierta en un test real:

```yaml
tests:
  - test_id: TST-ACC-001
    linked_rule: BR-001
    given: "el banco de fallas inyectadas"
    when: "se evalua a severidad 4 sigma"
    then: "el recall por evento supera 0.80"
    verify:
      kind: metric                                   # metric | command | python
      report: "06_resultados/experimentos/evaluacion.json"
      path: "por_evento.recall"
      op: ">="
      value: 0.80
```

Un criterio que hoy no se puede medir se marca `status: blocked` con su `blocked_reason`
y su via alternativa. **No se rebaja para que quepa el resultado disponible.**

Compilar y ejecutar:

```bash
python core/scripts/compile_acceptance_tests.py --increment <SLUG>
pytest tests/generated -v
```

## Si el preset es `astro-mlops`

El bloque `presupuesto_operacional` (falsas alarmas por noche, cobertura minima, lead
time, severidad minima detectable) **es lo que se aprueba en la compuerta**. Se acuerda
antes de ver resultados; cambiarlo despues exige `/speckit.ief.rewind`.

Si no hay historial de fallas etiquetado, construir el banco sintetico en este paso:

```bash
python presets/astro-mlops/scripts/inject_faults.py bench     --data <episodios> --column <objetivo>     --out 05_datos/benchmark_sintetico --params params.yaml
```
