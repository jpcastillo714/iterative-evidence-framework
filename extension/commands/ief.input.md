---
name: "ief.input"
description: "Registra algo que el proyecto aprendió de fuera: una reunión, un correo, un documento"
---

# Entrada externa (`/speckit.ief.input`)

## Propósito

Anotar un hecho que **llegó de fuera** y que el proyecto tiene que asumir.

## Por qué existe

Todo el ciclo de vida de las reglas da por hecho que una verdad del dominio se
**descubre trabajando**: nace en un incremento, se propone en un paso, se promueve con
firma. Esa es la aportación del IEF y sigue siendo correcta.

Pero la mitad de lo que cambia un proyecto no se descubre: **llega**. Una reunión donde
el proveedor de los datos dice que el instrumento se recalibró. Un correo que retira un
permiso. Un documento que contradice un supuesto del charter.

Eso no es una regla —nadie lo dedujo— ni es una tarea. Antes no tenía dónde ir: o se
enterraba en `worklog.md`, sin id y sin poder citarse, o se convertía en `RUL-`, que
exige un incremento entero para registrar algo que ya es cierto.

## Uso

```bash
python core/scripts/verify_frame.py --mode record-input \
    --source "Reunión con ESO (Paranal)" \
    --kind meeting \
    --date 2026-09-02 \
    --summary "Existe telemetría a 1 Hz en un buffer que no se archiva" \
    --file "00_admin/MINUTA_REUNION_ESO_2026-09-02.md" \
    --invalidates RUL-001-003
```

`--source` y `--summary` son obligatorios: **sin saber quién lo dijo y qué dijo, un hecho
no es evidencia de nada.** Los tipos válidos son `meeting`, `document`, `dataset`,
`decision` y `correspondence`.

El acta **no se copia, se enlaza**. Sigue viviendo donde vive.

## Lo importante: la deuda que abre

`--invalidates` es la razón de que esto exista. Lo caro nunca fue perder un acta — es que
una reunión tumbe tres afirmaciones del proyecto y **las tres sigan vigentes seis meses
después**, porque nadie volvió a abrir la carpeta.

Registrar una entrada **no toca ninguna regla**:

```
  Declara que invalida RUL-001-003, pero NO las ha tocado.
  Anotar un hecho es gratis; cambiar lo que gobierna el proyecto lleva
  firma. `doctor` te lo recordara hasta que alguien decida.
```

Y `doctor` lo trata como **problema, no como aviso**, mientras la regla siga activa:

```
FAIL  EXT-001 (2026-09-02) dice que invalida RUL-001-003, y RUL-001-003 sigue
      activa. Reemplazala con una regla que declare `supersedes: RUL-001-003`,
      o retira esa linea de la entrada si al mirarla no era para tanto
```

Se cierra de una de dos formas, y **las dos son decisión de una persona**: una regla nueva
que la reemplace, o retirar el `invalidates` porque al mirarlo no era para tanto.

## Citarla como evidencia

Una entrada se cita igual que un test:

```yaml
- id: RUL-002-001
  statement: "Existe telemetría a 1 Hz, pero hay que pedirla"
  evidence: [EXT-001]
  supersedes: RUL-001-003
```

«El instrumento se recalibró en marzo» no se demuestra con un `assert`: se demuestra con
quién lo dijo y cuándo. El motor comprueba que la entrada citada exista, igual que hace
con los tests.

## Verla después

```bash
python core/scripts/verify_frame.py --mode explain --input EXT-001
```

Muestra qué dijo, de dónde vino, qué puso en duda **y si eso sigue pendiente**, y qué
reglas acabaron apoyándose en ella.
