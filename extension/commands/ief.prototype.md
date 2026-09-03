---
name: "ief.prototype"
description: "Abre un incremento de ciclo corto para descubrir si algo vale la pena"
---

# Prototipo (`/speckit.ief.prototype`)

## Propósito

Abrir un frente de trabajo con **cuatro pasos y una sola compuerta**, para cuando la
pregunta es *«¿esto funciona?»* y no todavía *«esto tiene que aguantar»*.

Antes esto era un preset (`mvp`), lo que obligaba a decidir de una vez y para siempre
que el proyecto entero era «de prototipos». No tiene sentido: **el rigor es una
propiedad del trabajo, no del proyecto.** Un proyecto serio abre un incremento
`prototype` cuando explora, y uno `build` cuando construye en firme.

## El ciclo

| Paso | Nombre | Artefacto | Compuerta |
|---|---|---|---|
| 1 | Hipótesis y Criterio de Éxito | `charter.md` | ✋ |
| 2 | Cómo Sabremos Si Funciona | `acceptance-tests.yml` | |
| 3 | Construir | *(código)* | |
| 4 | Aprender y Decidir | `increment-report.md` | |

Los pasos 2, 3 y 4 del ciclo `build` (inspección, contratos, reglas) **no están**. No
se saltan fingiendo que están completados: sencillamente no forman parte de este ciclo.
El recorte es una decisión declarada, no un descuido.

## Protocolo

1. Abrir el incremento:
   ```bash
   python core/scripts/verify_frame.py --mode new-increment --type prototype --name "<qué se prueba>"
   ```
2. **Paso 1 — Hipótesis y criterio de éxito.** Antes de construir nada hay que poder
   responder: *¿qué resultado me haría abandonar esta idea?* Un prototipo sin criterio
   de descarte no es un experimento, es un compromiso disfrazado. Lleva compuerta.
3. **Paso 2 — Cómo sabremos si funciona.** Los criterios, aunque sean dos. Sin
   compuerta: aquí la velocidad importa más que la ceremonia.
4. **Paso 3 — Construir.** Lo mínimo para responder la pregunta. `scratch/` es
   desechable y nada de ahí sobrevive.
5. **Paso 4 — Aprender y decidir.** El informe dice qué se aprendió y qué se decide:
   seguir, descartar o graduar. **Anota la deuda técnica que dejas**, no la escondas.

## Al graduar un prototipo

Si funcionó, el trabajo continúa en un incremento `build` que sí pasa por inspección,
contratos y reglas. El prototipo **no se convierte** en el sistema: se usa lo aprendido
para construirlo bien.

Las reglas que descubriste en el prototipo son candidatas al paso 4 del build que venga
después.

## Reglas

- **Un prototipo que no se descarta ni se gradúa es deuda.** Si al terminar no hay una
  decisión, el paso 4 no está hecho.
- **No promuevas reglas desde un prototipo** sin haberlas pasado por un `build`: no
  tuvieron ni contrato de datos ni compuerta que las revisara.
