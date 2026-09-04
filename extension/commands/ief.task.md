---
name: "ief.task"
description: "Abre un incremento mínimo: dos pasos, ninguna compuerta"
---

# Tarea (`/speckit.ief.task`)

## Propósito

Trabajo que **es código de verdad pero no arrastra decisiones**: añadir un filtro a un
dashboard, corregir una agregación, exponer un campo que ya existe.

## Por qué existe

Entre `--mode log` (una línea) y `prototype` (cuatro pasos y una compuerta) no había
nada. Un filtro nuevo lo va a mantener alguien y merece saber qué debe hacer y cómo se
comprueba — pero no merece charter con criterio de abandono, ni contrato de datos, ni
promoción de reglas al proyecto.

## La escala completa

| Nivel | Cuándo | Coste |
|---|---|---|
| `--mode log` | Un gráfico, un documento, un arreglo de diez minutos | Una línea |
| **`task`** | **Código pequeño; nadie hereda decisiones nuevas** | **2 pasos, 0 compuertas** |
| `prototype` | Hay una hipótesis que puede fallar | 4 pasos, 1 compuerta |
| `build` | Otros dependerán de esto | 7 pasos, 3 compuertas |

## Uso

```bash
python core/scripts/verify_frame.py --mode new-increment \
    --type task --name "Filtro por categoría en el panel"
```

Dos pasos: `task.md` (qué se pide y cómo se comprueba) e `increment-report.md` (hecho).

## La alarma que lleva dentro

Si al escribir el paso 1 aparece una decisión que **otros van a heredar** —una definición
de métrica, un criterio de exclusión, una regla del dominio— eso ya **no es un `task`**.

Un `task` no tiene compuerta donde aprobar esa decisión, así que la regla acabaría
vigente sin que nadie la mirara: exactamente el fallo que el framework existe para
evitar. Ciérralo y abre un `prototype` o un `build`.
