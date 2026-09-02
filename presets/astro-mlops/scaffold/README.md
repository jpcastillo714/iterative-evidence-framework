# Scaffold del preset `astro-mlops`

Plantillas de arranque para la capa MLOps del proyecto. **No se despliegan
automáticamente**: cópialas cuando el incremento correspondiente las necesite, y borra las
etapas que no uses. Un `dvc.yaml` con etapas fantasma es peor que no tenerlo.

| Archivo | Destino en el proyecto | Cuándo copiarlo |
|---|---|---|
| `params.yaml` | raíz | Al empezar el primer incremento `build` con pipeline. |
| `dvc.yaml` | raíz | Cuando existan al menos dos etapas encadenadas. |
| `conf/config.yaml` | `04_codigo/conf/` | Al primer experimento con hiperparámetros. |
| `ci/ief-verify.yml` | `.github/workflows/` | Cuando el repo esté en GitHub y haya tests. |

## Orden sugerido

1. `params.yaml` primero, aunque todavía no haya DVC: obliga a sacar los números del código.
2. `conf/config.yaml` al montar MLflow, con backend local `file:./06_resultados/experimentos/mlruns`.
3. `dvc.yaml` cuando la consolidación de datos ya sea estable.
4. `ci/ief-verify.yml` al final: sin tests que correr, la CI solo genera ruido rojo.

## Nota sobre rutas

Las etapas de `dvc.yaml` invocan los scripts del bundle como `core/scripts/...`. Si el
bundle no está copiado dentro del proyecto, reemplaza ese prefijo por la ruta a tu
instalación del bundle o expón los scripts vía una variable de entorno.
