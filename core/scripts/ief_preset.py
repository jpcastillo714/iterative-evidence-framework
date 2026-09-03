#!/usr/bin/env python3
"""
IEF · Cargador de presets, roles y layouts.

Los tres ejes
-------------
Hasta la version 0.6.0 el preset decidia tres cosas a la vez: el ciclo de trabajo, el
vocabulario y la estructura de carpetas. Eso obligaba a inventar un preset por cada
combinacion (`ml`, `mvp`, `academic`...) y no componia: "ML dentro de engineering" o
"ML dentro de data-science" exigian presets distintos que duplicaban todo.

Los tres ejes ahora son independientes:

    LAYOUT   como se llaman las carpetas          decision del proyecto  (--layout)
    PRESET   vocabulario y ceremonia              decision del proyecto  (--preset)
    CICLO    cuanto rigor lleva ESTE trabajo      decision por incremento

Un rol es una necesidad ("un sitio para las presentaciones"); el layout la convierte
en una ruta. Un preset declara que roles usa, y los hereda de forma ADITIVA.

Herencia y composicion
----------------------
`extends` acepta un id o una lista. El grafo se linealiza con los ancestros primero y
deduplicacion, de modo que un mixin puede aportar solo lo suyo:

    extends: [analysis, modeling]

Personalizacion de un ciclo, de menos a mas invasiva:

    rename:        {clave: "Nuevo nombre"}     solo la etiqueta
    human_gates:   [clave, ...]                redefine que pasos se aprueban
    remove:        [clave, ...]                quita pasos
    insert_after:  {clave: [ {...} ]}          inserta sin redeclarar el ciclo
    insert_before: {clave: [ {...} ]}
    steps:         [ {...} ]                   reemplaza el ciclo completo
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

try:
    import yaml
except ImportError:  # pragma: no cover
    raise SystemExit("ERROR: falta PyYAML (pip install pyyaml)")


PRESET_POR_DEFECTO = "generic"
LAYOUT_POR_DEFECTO = "flat"


class ErrorDePreset(Exception):
    """El preset, rol o layout no existe, esta mal formado o su herencia es circular."""


# ─── Modelo ──────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class Paso:
    """Un paso del ciclo. `ref` es el identificador corto que escribe el usuario."""

    ref: str                       # "1", "2b", "6b", "7"
    clave: str                     # "1_charter"  (la clave en state.yml)
    nombre: str                    # "Charter" / "Hipotesis y Alcance"
    artefacto: Optional[str]       # "charter.md", o None si el paso no produce archivo
    human_gate: bool
    plantilla: Optional[str] = None
    instrucciones: Optional[str] = None

    @property
    def requiere_aprobacion(self) -> bool:
        return self.human_gate


@dataclass
class Ciclo:
    nombre: str
    pasos: List[Paso]

    @property
    def refs(self) -> List[str]:
        return [p.ref for p in self.pasos]

    def por_ref(self, ref: str) -> Optional[Paso]:
        return next((p for p in self.pasos if p.ref == str(ref)), None)

    def por_clave(self, clave: str) -> Optional[Paso]:
        return next((p for p in self.pasos if p.clave == clave), None)


@dataclass
class Layout:
    id: str
    nombre: str
    descripcion: str
    rutas: Dict[str, str]

    def ruta(self, rol: str) -> Optional[str]:
        return self.rutas.get(rol)


@dataclass
class Preset:
    id: str
    nombre: str
    descripcion: str
    abstracto: bool = False
    ciclos: Dict[str, Ciclo] = field(default_factory=dict)
    rutas: Dict[str, str] = field(default_factory=dict)
    roles: List[str] = field(default_factory=list)
    invariantes: List[Dict[str, str]] = field(default_factory=list)
    herramientas: Dict[str, Any] = field(default_factory=dict)
    cadena: List[str] = field(default_factory=list)

    # ── Ciclos ───────────────────────────────────────────────────────────────

    def tipos_de_ciclo(self) -> List[str]:
        return sorted(self.ciclos)

    def ciclo(self, tipo: str) -> Ciclo:
        if tipo not in self.ciclos:
            raise ErrorDePreset(
                f"el preset `{self.id}` no define el ciclo `{tipo}` "
                f"(tiene: {', '.join(self.tipos_de_ciclo())})"
            )
        return self.ciclos[tipo]

    def pasos(self, tipo: str) -> List[Paso]:
        return self.ciclo(tipo).pasos

    def paso(self, tipo: str, ref: str) -> Optional[Paso]:
        return self.ciclo(tipo).por_ref(ref)

    # ── Rutas ────────────────────────────────────────────────────────────────

    def dir_incremento(self, slug: str) -> str:
        return self.rutas["increment_dir"].format(slug=slug)

    def ruta_artefacto(self, slug: str, paso: Paso) -> Optional[str]:
        """Ruta unica y canonica del artefacto de un paso. None si no produce."""
        if not paso.artefacto:
            return None
        return f"{self.dir_incremento(slug)}/{paso.artefacto}"

    def directorios(self, layout: Layout, catalogo: Dict[str, Any]) -> List[Dict[str, str]]:
        """Los roles del preset resueltos a rutas concretas por el layout."""
        salida: List[Dict[str, str]] = []
        for rol in self.roles:
            ruta = layout.ruta(rol)
            if not ruta:
                raise ErrorDePreset(
                    f"el layout `{layout.id}` no define ruta para el rol `{rol}`"
                )
            salida.append({
                "role": rol,
                "path": ruta,
                "description": (catalogo.get(rol) or {}).get("description", ""),
            })
        return salida


# ─── Lectura ─────────────────────────────────────────────────────────────────

def _leer_yaml(path: Path) -> Dict[str, Any]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as exc:
        raise ErrorDePreset(f"YAML invalido en {path}: {exc}") from exc
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ErrorDePreset(f"{path} no es un mapeo YAML")
    return data


def cargar_roles(bundle_dir: Path) -> Dict[str, Any]:
    path = Path(bundle_dir) / "core" / "roles.yml"
    if not path.exists():
        raise ErrorDePreset(f"no existe el catalogo de roles: {path}")
    return _leer_yaml(path).get("roles") or {}


def layouts_disponibles(bundle_dir: Path) -> List[str]:
    path = Path(bundle_dir) / "core" / "layouts.yml"
    if not path.exists():
        return []
    return sorted((_leer_yaml(path).get("layouts") or {}))


def cargar_layout(layout_id: Optional[str], bundle_dir: Path) -> Layout:
    layout_id = layout_id or LAYOUT_POR_DEFECTO
    path = Path(bundle_dir) / "core" / "layouts.yml"
    if not path.exists():
        raise ErrorDePreset(f"no existe el catalogo de layouts: {path}")
    todos = _leer_yaml(path).get("layouts") or {}
    if layout_id not in todos:
        raise ErrorDePreset(
            f"no existe el layout `{layout_id}`. Disponibles: {', '.join(sorted(todos))}"
        )
    cfg = todos[layout_id]
    return Layout(
        id=layout_id,
        nombre=cfg.get("name", layout_id),
        descripcion=cfg.get("description", ""),
        rutas=cfg.get("paths") or {},
    )


# ─── Herencia: grafo linealizado, no cadena ──────────────────────────────────

def _padres(doc: Dict[str, Any]) -> List[str]:
    """`extends` acepta un id, una lista, o nada."""
    ext = doc.get("extends")
    if ext is None:
        return []
    if isinstance(ext, str):
        return [ext]
    if isinstance(ext, list):
        return [str(e) for e in ext if e]
    raise ErrorDePreset(
        f"`extends` debe ser un id o una lista de ids, no {type(ext).__name__}"
    )


def _linearizar(
    preset_id: str,
    dir_presets: Path,
    pila: Optional[List[str]] = None,
    vistos: Optional[Dict[str, Dict[str, Any]]] = None,
    orden: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """Ancestros primero, deduplicado, con deteccion de herencia circular."""
    pila = pila or []
    vistos = vistos if vistos is not None else {}
    orden = orden if orden is not None else []

    if preset_id in pila:
        raise ErrorDePreset(
            f"herencia circular de presets: {' -> '.join(pila + [preset_id])}"
        )
    if preset_id in vistos:
        return [vistos[k] for k in orden]

    path = dir_presets / preset_id / "preset.yml"
    if not path.exists():
        if not pila:
            disponibles = sorted(p.name for p in dir_presets.iterdir() if p.is_dir())
            raise ErrorDePreset(
                f"no existe el preset `{preset_id}`. Disponibles: {', '.join(disponibles)}"
            )
        raise ErrorDePreset(
            f"el preset `{pila[-1]}` extiende `{preset_id}`, que no existe en {dir_presets}"
        )

    doc = _leer_yaml(path)
    doc["_dir"] = str(path.parent)
    doc.setdefault("id", preset_id)

    for padre in _padres(doc):
        _linearizar(padre, dir_presets, pila + [preset_id], vistos, orden)

    vistos[preset_id] = doc
    orden.append(preset_id)
    return [vistos[k] for k in orden]


# ─── Fusion de ciclos ────────────────────────────────────────────────────────

def _paso_desde_dict(d: Dict[str, Any], contexto: str) -> Paso:
    clave = d.get("key") or d.get("clave")
    if not clave:
        raise ErrorDePreset(f"{contexto}: un paso no declara `key`")
    return Paso(
        ref=str(d.get("ref") or str(clave).split("_", 1)[0]),
        clave=str(clave),
        nombre=str(d.get("name") or d.get("nombre") or clave),
        artefacto=d.get("artifact") or d.get("artefacto"),
        human_gate=bool(d.get("human_gate", False)),
        plantilla=d.get("template") or d.get("plantilla"),
        instrucciones=d.get("instructions") or d.get("instrucciones"),
    )


def _claves_y_refs(pasos: Sequence[Paso]) -> set:
    return {p.clave for p in pasos} | {p.ref for p in pasos}


def _insertar(
    pasos: List[Paso], mapa: Dict[str, Any], despues: bool, tipo: str
) -> List[Paso]:
    """Inserta pasos junto a un ancla, para que un mixin no redeclare el ciclo."""
    donde = "insert_after" if despues else "insert_before"
    for ancla, nuevos in mapa.items():
        idx = next(
            (i for i, p in enumerate(pasos) if p.clave == ancla or p.ref == str(ancla)),
            -1,
        )
        if idx < 0:
            raise ErrorDePreset(
                f"`cycles.{tipo}.{donde}` ancla en un paso inexistente: `{ancla}`"
            )
        lote = [_paso_desde_dict(d, f"cycles.{tipo}") for d in (nuevos or [])]
        corte = idx + 1 if despues else idx
        pasos = pasos[:corte] + lote + pasos[corte:]
    return pasos


def _fusionar_ciclos(heredado: Dict[str, Ciclo], doc: Dict[str, Any]) -> Dict[str, Ciclo]:
    ciclos = {k: Ciclo(nombre=v.nombre, pasos=list(v.pasos)) for k, v in heredado.items()}

    for tipo, cfg in (doc.get("cycles") or {}).items():
        if not isinstance(cfg, dict):
            raise ErrorDePreset(f"`cycles.{tipo}` debe ser un mapeo")

        base = ciclos.get(tipo)
        nombre = cfg.get("name") or (base.nombre if base else tipo)

        # 1. Reemplazo completo del ciclo.
        if cfg.get("steps"):
            pasos = [_paso_desde_dict(d, f"cycles.{tipo}") for d in cfg["steps"]]
        elif base:
            pasos = list(base.pasos)
        else:
            raise ErrorDePreset(
                f"el ciclo `{tipo}` no existe en los presets padre y no declara `steps`"
            )

        # 2. Quitar pasos.
        if cfg.get("remove"):
            quitar = {str(k) for k in cfg["remove"]}
            desconocidas = quitar - _claves_y_refs(pasos)
            if desconocidas:
                raise ErrorDePreset(
                    f"`cycles.{tipo}.remove` menciona pasos inexistentes: {sorted(desconocidas)}"
                )
            pasos = [p for p in pasos if p.clave not in quitar and p.ref not in quitar]

        # 3. Insertar pasos junto a un ancla.
        if cfg.get("insert_before"):
            pasos = _insertar(pasos, cfg["insert_before"], despues=False, tipo=tipo)
        if cfg.get("insert_after"):
            pasos = _insertar(pasos, cfg["insert_after"], despues=True, tipo=tipo)

        # 4. Renombrar etiquetas.
        if cfg.get("rename"):
            renombres = cfg["rename"]
            desconocidas = set(renombres) - _claves_y_refs(pasos)
            if desconocidas:
                raise ErrorDePreset(
                    f"`cycles.{tipo}.rename` menciona pasos inexistentes: {sorted(desconocidas)}"
                )
            pasos = [
                replace(p, nombre=renombres.get(p.clave, renombres.get(p.ref, p.nombre)))
                for p in pasos
            ]

        # 5. Redefinir compuertas humanas.
        if "human_gates" in cfg:
            gates = {str(g) for g in (cfg.get("human_gates") or [])}
            desconocidas = gates - _claves_y_refs(pasos)
            if desconocidas:
                raise ErrorDePreset(
                    f"`cycles.{tipo}.human_gates` menciona pasos inexistentes: {sorted(desconocidas)}"
                )
            pasos = [
                replace(p, human_gate=(p.clave in gates or p.ref in gates)) for p in pasos
            ]

        # 6. Plantillas por paso (atajo comodo).
        if cfg.get("templates"):
            plantillas = cfg["templates"]
            pasos = [replace(p, plantilla=plantillas.get(p.clave, p.plantilla)) for p in pasos]

        ciclos[tipo] = Ciclo(nombre=nombre, pasos=pasos)

    return ciclos


# ─── Validacion ──────────────────────────────────────────────────────────────

def _validar(preset: Preset, catalogo: Dict[str, Any]) -> None:
    """Un preset mal formado falla al cargarse, no a mitad de un incremento."""
    if not preset.ciclos:
        raise ErrorDePreset(f"el preset `{preset.id}` no define ningun ciclo")
    if "increment_dir" not in preset.rutas:
        raise ErrorDePreset(f"el preset `{preset.id}` no define `paths.increment_dir`")
    if "{slug}" not in preset.rutas["increment_dir"]:
        raise ErrorDePreset("`paths.increment_dir` debe contener el marcador {slug}")

    desconocidos = [r for r in preset.roles if catalogo and r not in catalogo]
    if desconocidos:
        raise ErrorDePreset(
            f"el preset `{preset.id}` declara roles que no estan en core/roles.yml: "
            f"{desconocidos}"
        )

    for tipo, ciclo in preset.ciclos.items():
        if not ciclo.pasos:
            raise ErrorDePreset(f"el ciclo `{tipo}` de `{preset.id}` no tiene pasos")

        for etiqueta, valores in (
            ("refs", [p.ref for p in ciclo.pasos]),
            ("claves", [p.clave for p in ciclo.pasos]),
        ):
            if len(valores) != len(set(valores)):
                dup = sorted({v for v in valores if valores.count(v) > 1})
                raise ErrorDePreset(f"{etiqueta} duplicadas en el ciclo `{tipo}`: {dup}")

        artefactos = [p.artefacto for p in ciclo.pasos if p.artefacto]
        if len(artefactos) != len(set(artefactos)):
            dup = sorted({a for a in artefactos if artefactos.count(a) > 1})
            raise ErrorDePreset(
                f"dos pasos del ciclo `{tipo}` reclaman el mismo artefacto: {dup}. "
                "Cada artefacto tiene una ruta unica."
            )


# ─── API ─────────────────────────────────────────────────────────────────────

def cargar_preset(
    preset_id: Optional[str], bundle_dir: Path, base_para_mixin: Optional[str] = None
) -> Preset:
    """Resuelve un preset, su grafo de herencia y sus roles. Lanza ErrorDePreset.

    `base_para_mixin` permite validar un mixin componiendolo con un preset base;
    lo usa `--mode check-preset`, que necesita revisarlos todos.
    """
    preset_id = preset_id or PRESET_POR_DEFECTO
    bundle_dir = Path(bundle_dir)
    dir_presets = bundle_dir / "presets"
    if not dir_presets.exists():
        raise ErrorDePreset(f"no existe el directorio de presets: {dir_presets}")

    catalogo = cargar_roles(bundle_dir) if (bundle_dir / "core" / "roles.yml").exists() else {}

    # Un mixin no se carga solo: sus operaciones (`insert_after`, roles extra) se
    # aplican SOBRE un ciclo que aporta el preset base. Cargarlo suelto fallaria con
    # "el ciclo build no existe", que no le dice a nadie como arreglarlo.
    if es_mixin(preset_id, dir_presets.parent) and not base_para_mixin:
        raise ErrorDePreset(
            f"`{preset_id}` es un mixin: no se usa solo. Componlo con un preset base, "
            f"por ejemplo `extends: [analysis, {preset_id}]`."
        )
    if base_para_mixin:
        cadena = _linearizar(base_para_mixin, dir_presets)
        cadena += [d for d in _linearizar(preset_id, dir_presets) if d not in cadena]
    else:
        cadena = _linearizar(preset_id, dir_presets)

    ciclos: Dict[str, Ciclo] = {}
    rutas: Dict[str, str] = {}
    roles: List[str] = []
    invariantes: List[Dict[str, str]] = []
    herramientas: Dict[str, Any] = {}
    nombre, descripcion = preset_id, ""

    # Los roles marcados `always` entran primero, los declare quien los declare.
    for rol, cfg in catalogo.items():
        if isinstance(cfg, dict) and cfg.get("always") and rol not in roles:
            roles.append(rol)

    for doc in cadena:
        ciclos = _fusionar_ciclos(ciclos, doc)
        rutas.update(doc.get("paths") or {})
        herramientas.update(doc.get("tooling") or {})

        # Los roles se ACUMULAN por la cadena; no se reemplazan. Antes de 0.7.0 la
        # convencion de directorios del hijo pisaba entera la del padre, y por eso
        # cada preset tenia que redeclarar la lista completa para anadir una carpeta.
        for rol in (doc.get("roles") or []):
            if rol not in roles:
                roles.append(str(rol))
        for rol in (doc.get("roles_remove") or []):
            if rol in roles:
                roles.remove(rol)

        if doc.get("invariants"):
            invariantes = list(doc["invariants"])
        if doc.get("name"):
            nombre = doc["name"]
        if doc.get("description"):
            descripcion = doc["description"]

    preset = Preset(
        id=preset_id,
        nombre=nombre,
        abstracto=es_mixin(preset_id, dir_presets.parent),
        descripcion=descripcion,
        ciclos=ciclos,
        rutas=rutas,
        roles=roles,
        invariantes=invariantes,
        herramientas=herramientas,
        cadena=[d.get("id", "?") for d in cadena],
    )
    _validar(preset, catalogo)
    return preset


def es_mixin(preset_id: str, bundle_dir: Path) -> bool:
    """Un mixin (`abstract: true`) aporta piezas a otro preset; no se usa solo."""
    path = Path(bundle_dir) / "presets" / preset_id / "preset.yml"
    if not path.exists():
        return False
    return bool(_leer_yaml(path).get("abstract"))


def presets_disponibles(bundle_dir: Path) -> List[str]:
    dir_presets = Path(bundle_dir) / "presets"
    if not dir_presets.exists():
        return []
    return sorted(p.name for p in dir_presets.iterdir() if (p / "preset.yml").exists())
