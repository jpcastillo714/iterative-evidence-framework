---
name: "ief.adopt"
description: "Adopta el IEF en un proyecto que ya existe, sin mover un solo archivo"
---

# Adoptar (`/speckit.ief.adopt`)

## Propósito

Empezar a usar el IEF en un proyecto **que ya lleva meses en marcha**, respetando la
estructura de carpetas que ya tiene.

## Por qué existe

`--mode init` da por hecho un proyecto que nace con el framework: crea `data/raw/`,
`notebooks/`, `reports/`. En un proyecto empezado eso construye una estructura
**paralela** a la que ya hay — acabas con `datos_crudos/` y `data/raw/`, y ninguna de las
dos es la buena.

Pedirle a un proyecto que renombre sus carpetas para entrar al framework es pedirle que
reorganice su trabajo para complacer a una herramienta. `adopt` invierte la dirección:
**descubre las rutas en vez de imponerlas**.

## Uso

```bash
# 1. Propone. No escribe nada.
python core/scripts/verify_frame.py --mode adopt --preset analysis

# 2. Si la propuesta cuadra, se aplica.
python core/scripts/verify_frame.py --mode adopt --preset analysis --yes
```

## Qué verás

```
  Carpetas reconocidas:
    datos_crudos             -> datos_raw
    notebooks                -> exploracion
    salidas                  -> resultados

  Reconocidas, pero el preset `analysis` no usa esos roles:
    documentacion            -> documento

  Carpetas que no supe clasificar (se dejan como estan, intactas):
    cosas_raras
```

Las tres listas importan, y la tercera es la que más: **lo que no se entiende se dice, no
se ignora**. Una herramienta que calla lo que no supo clasificar te deja creyendo que lo
revisó todo.

## Qué hace y qué no

- **No mueve, renombra ni borra ningún archivo.** Nunca, ni con `--yes`.
- Guarda el mapa rol→ruta en `initiative.role_paths`, que **tiene prioridad sobre el
  layout**. A partir de ahí el motor escribe en las carpetas del proyecto, no en las suyas.
- Solo crea las carpetas de roles que el preset necesita y no existen.
- Se niega a ejecutarse si el proyecto ya tiene `state.yml`: para eso está `init`.
