# Paso 1: Qué se pide y cómo se comprueba

| Campo | Valor |
|-------|-------|
| **Ciclo** | `task` (2 pasos, sin compuertas) |
| **Output** | `initiative/increments/<SLUG>/task.md` |
| **Human Gate** | ❌ No |

## Cuándo estás en el ciclo correcto

`task` es para trabajo que **es código de verdad pero no arrastra decisiones**: añadir
un filtro, arreglar un cálculo, exponer un campo que ya existe.

La escala completa, de menos a más:

| | Para qué |
|---|---|
| `--mode log` | No es un incremento. Un gráfico, un documento, un arreglo de diez minutos. |
| `task` | Código pequeño. Nadie hereda decisiones nuevas. |
| `prototype` | Descubrir si algo vale la pena. Hay una hipótesis que puede fallar. |
| `build` | Tiene que aguantar. Otros dependerán de ello. |

**Cómo elegir:** no por tamaño, por consecuencia. ¿Alguien va a citar un número que
salga de aquí? ¿Alguien más va a mantener esto? ¿Cambia una regla del proyecto? Si las
tres son «no», `task` o `log` bastan.

## Protocolo

1. Escribir `task.md` con la plantilla. Media página.
2. Si el criterio se puede automatizar, escribir el test ahora, antes del código.
3. `--mode complete-step` y `--mode advance`.
4. Hacer el trabajo.
5. Cerrar con `increment-report.md`: qué se hizo, si el criterio se cumple, y **qué
   quedó pendiente**.

## Reglas críticas

1. **Si aparece una decisión que otros heredan, cambia de ciclo.** Una definición nueva
   («qué cuenta como activo»), un supuesto sobre los datos, o una regla del dominio no
   caben en un `task`: no tiene compuerta donde aprobarlas, y acabarían vigentes sin que
   nadie las haya mirado. Cierra el `task` y abre un `prototype` o un `build`.

2. **«Qué NO se toca» no es relleno.** Es lo que impide que media tarde se vuelvan tres
   días. Escríbelo aunque parezca obvio.

3. **Un `task` sin criterio comprobable es un encargo, no una tarea.** Si no puedes
   decir cómo se sabrá que está terminado, todavía no está claro qué se pide.

4. **No promuevas reglas desde un `task`.** No pasó por contrato de datos ni por
   compuerta. Si descubriste algo que merece ser regla del proyecto, anótalo y llévalo
   a un `build`.
