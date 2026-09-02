#!/usr/bin/env python3
"""
IEF V3 · Cargador de presets.

Por que existe
--------------
Hasta la version 0.4.0 el ciclo de trabajo (que pasos hay, en que orden, cuales
requieren aprobacion humana y donde vive cada artefacto) estaba escrito a mano
dentro de `verify_frame.py`. Los archivos `preset.yml` declaraban `step_aliases`,
`human_gates`, `templates` y `directory-convention.yml`, pero ningun codigo los
leia: eran documentacion.

El resultado era que un preset solo podia cambiar nombres en el papel, nunca el
proceso. Este modulo convierte el preset en la fuente unica de verdad del ciclo:
el motor pregunta, el preset responde.

Herencia
--------
Un preset declara `extends: <id>` y hereda todo lo que no redefine. La cadena se
resuelve hasta un preset sin padre (`extends: null`), y se detectan los ciclos.

Tres formas de personalizar un ciclo, de menos a mas invasiva:

    rename:        {clave_de_paso: "Nuevo nombre"}   solo cambia la etiqueta
    human_gates:   [clave_de_paso, ...]              redefine que pasos se aprueban
    steps:         [ {...}, {...} ]                  reemplaza el ciclo completo

Uso
---
    from ief_preset import cargar_preset

    preset = cargar_preset("academic", bundle_dir)
    for paso in preset.pasos("build"):
        print(paso.ref, paso.nombre, paso.artefacto, paso.human_gate)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import yaml
except ImportError:  # pragma: no cover
    raise SystemExit("ERROR: falta PyYAML (pip install pyyaml)")


PRESET_POR_DEFECTO = "generic"


class ErrorDePreset(Exception):
    """El preset no existe, esta mal formado o su herencia es circular."""


# ─── Modelo ──────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class Paso:
    """Un paso del ciclo. `ref` es el identificador corto que usa el usuario."""

    ref: str                       # "1", "2b", "7"
    clave: str                     # "1_charter"  (la clave en state.yml)
    nombre: str                    # "Charter" / "Hipótesis y Alcance"
    artefacto: Optional[str]       # "charter.md" o None si el paso no produce archivo
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
        for p in self.pasos:
            if p.ref == str(ref):
                return p
        return None

    def por_clave(self, clave: str) -> Optional[Paso]:
        for p in self.pasos:
            if p.clave == clave:
                return p
        return None


@dataclass
class Preset:
    id: str
    nombre: str
    descripcion: str
    ciclos: Dict[str, Ciclo]
    rutas: Dict[str, str]
    directorios: List[Dict[str, str]] = field(default_factory=list)
    invariantes: List[Dict[str, str]] = field(default_factory=list)
    herramientas: Dict[str, Any] = field(default_factory=dict)
    cadena: List[str] = field(default_factory=list)   # ["generic", "academic", ...]

    # ── Consulta del ciclo ───────────────────────────────────────────────────

    def tipos_de_ciclo(self) -> List[str]:
        return sorted(self.ciclos)

    def ciclo(self, tipo: str) -> Ciclo:
        if tipo not in self.ciclos:
            disponibles = ", ".join(self.tipos_de_ciclo())
            raise ErrorDePreset(
                f"el preset `{self.id}` no define el ciclo `{tipo}` (tiene: {disponibles})"
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


# ─── Carga y herencia ────────────────────────────────────────────────────────

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


def _cadena_de_herencia(preset_id: str, dir_presets: Path) -> List[Dict[str, Any]]:
    """Del ancestro mas lejano al preset pedido. Detecta ciclos y padres ausentes."""
    cadena: List[Dict[str, Any]] = []
    vistos: List[str] = []
    actual: Optional[str] = preset_id

    while actual:
        if actual in vistos:
            ruta = " -> ".join(vistos + [actual])
            raise ErrorDePreset(f"herencia circular de presets: {ruta}")
        vistos.append(actual)

        path = dir_presets / actual / "preset.yml"
        if not path.exists():
            if len(vistos) == 1:
                disponibles = sorted(p.name for p in dir_presets.iterdir() if p.is_dir())
                raise ErrorDePreset(
                    f"no existe el preset `{actual}`. Disponibles: {', '.join(disponibles)}"
                )
            raise ErrorDePreset(
                f"el preset `{vistos[-2]}` extiende `{actual}`, que no existe en {dir_presets}"
            )

        doc = _leer_yaml(path)
        doc["_dir"] = str(path.parent)
        cadena.append(doc)
        actual = doc.get("extends")

    cadena.reverse()
    return cadena


def _paso_desde_dict(d: Dict[str, Any], indice: int) -> Paso:
    clave = d.get("key") or d.get("clave")
    if not clave:
        raise ErrorDePreset(f"el paso #{indice + 1} no declara `key`")
    ref = str(d.get("ref") or clave.split("_", 1)[0])
    return Paso(
        ref=ref,
        clave=str(clave),
        nombre=str(d.get("name") or d.get("nombre") or clave),
        artefacto=d.get("artifact") or d.get("artefacto"),
        human_gate=bool(d.get("human_gate", False)),
        plantilla=d.get("template") or d.get("plantilla"),
        instrucciones=d.get("instructions") or d.get("instrucciones"),
    )


def _fusionar_ciclos(
    heredado: Dict[str, Ciclo], doc: Dict[str, Any]
) -> Dict[str, Ciclo]:
    """Aplica sobre lo heredado las tres formas de personalizacion del preset hijo."""
    ciclos = {k: Ciclo(nombre=v.nombre, pasos=list(v.pasos)) for k, v in heredado.items()}

    for tipo, cfg in (doc.get("cycles") or {}).items():
        if not isinstance(cfg, dict):
            raise ErrorDePreset(f"`cycles.{tipo}` debe ser un mapeo")

        base = ciclos.get(tipo)
        nombre = cfg.get("name") or (base.nombre if base else tipo)

        # 1. Reemplazo completo del ciclo.
        if cfg.get("steps"):
            pasos = [_paso_desde_dict(d, i) for i, d in enumerate(cfg["steps"])]
        elif base:
            pasos = list(base.pasos)
        else:
            raise ErrorDePreset(
                f"el ciclo `{tipo}` no existe en los presets padre y no declara `steps`"
            )

        # 2. Renombrado de etiquetas.
        renombres = cfg.get("rename") or {}
        if renombres:
            claves = {p.clave for p in pasos} | {p.ref for p in pasos}
            desconocidas = [k for k in renombres if k not in claves]
            if desconocidas:
                raise ErrorDePreset(
                    f"`cycles.{tipo}.rename` menciona pasos inexistentes: {desconocidas}"
                )
            pasos = [
                Paso(**{**p.__dict__, "nombre": renombres.get(p.clave, renombres.get(p.ref, p.nombre))})
                for p in pasos
            ]

        # 3. Redefinicion de compuertas humanas.
        if "human_gates" in cfg:
            gates = {str(g) for g in (cfg.get("human_gates") or [])}
            claves = {p.clave for p in pasos} | {p.ref for p in pasos}
            desconocidas = [g for g in gates if g not in claves]
            if desconocidas:
                raise ErrorDePreset(
                    f"`cycles.{tipo}.human_gates` menciona pasos inexistentes: {desconocidas}"
                )
            pasos = [
                Paso(**{**p.__dict__, "human_gate": (p.clave in gates or p.ref in gates)})
                for p in pasos
            ]

        # 4. Plantillas por paso (mapa clave -> ruta), atajo comodo.
        plantillas = cfg.get("templates") or {}
        if plantillas:
            pasos = [
                Paso(**{**p.__dict__, "plantilla": plantillas.get(p.clave, p.plantilla)})
                for p in pasos
            ]

        ciclos[tipo] = Ciclo(nombre=nombre, pasos=pasos)

    return ciclos


def _validar(preset: Preset) -> None:
    """Un preset mal formado debe fallar al cargarse, no a mitad de un incremento."""
    if not preset.ciclos:
        raise ErrorDePreset(f"el preset `{preset.id}` no define ningun ciclo")

    if "increment_dir" not in preset.rutas:
        raise ErrorDePreset(f"el preset `{preset.id}` no define `paths.increment_dir`")
    if "{slug}" not in preset.rutas["increment_dir"]:
        raise ErrorDePreset("`paths.increment_dir` debe contener el marcador {slug}")

    for tipo, ciclo in preset.ciclos.items():
        if not ciclo.pasos:
            raise ErrorDePreset(f"el ciclo `{tipo}` de `{preset.id}` no tiene pasos")

        refs = [p.ref for p in ciclo.pasos]
        if len(refs) != len(set(refs)):
            dup = sorted({r for r in refs if refs.count(r) > 1})
            raise ErrorDePreset(f"refs duplicadas en el ciclo `{tipo}`: {dup}")

        claves = [p.clave for p in ciclo.pasos]
        if len(claves) != len(set(claves)):
            dup = sorted({c for c in claves if claves.count(c) > 1})
            raise ErrorDePreset(f"claves duplicadas en el ciclo `{tipo}`: {dup}")

        artefactos = [p.artefacto for p in ciclo.pasos if p.artefacto]
        if len(artefactos) != len(set(artefactos)):
            dup = sorted({a for a in artefactos if artefactos.count(a) > 1})
            raise ErrorDePreset(
                f"dos pasos del ciclo `{tipo}` reclaman el mismo artefacto: {dup}. "
                "Cada artefacto tiene una ruta unica."
            )


def cargar_preset(preset_id: Optional[str], bundle_dir: Path) -> Preset:
    """Resuelve un preset y su cadena de herencia. Lanza ErrorDePreset si no es valido."""
    preset_id = preset_id or PRESET_POR_DEFECTO
    dir_presets = Path(bundle_dir) / "presets"
    if not dir_presets.exists():
        raise ErrorDePreset(f"no existe el directorio de presets: {dir_presets}")

    cadena = _cadena_de_herencia(preset_id, dir_presets)

    ciclos: Dict[str, Ciclo] = {}
    rutas: Dict[str, str] = {}
    directorios: List[Dict[str, str]] = []
    invariantes: List[Dict[str, str]] = []
    herramientas: Dict[str, Any] = {}
    nombre = preset_id
    descripcion = ""

    for doc in cadena:
        ciclos = _fusionar_ciclos(ciclos, doc)
        rutas.update(doc.get("paths") or {})
        herramientas.update(doc.get("tooling") or {})
        if doc.get("invariants"):
            invariantes = list(doc["invariants"])
        if doc.get("name"):
            nombre = doc["name"]
        if doc.get("description"):
            descripcion = doc["description"]

        # La convencion de directorios vive junto al preset que la declara.
        conv = Path(doc["_dir"]) / "directory-convention.yml"
        if conv.exists():
            directorios = (_leer_yaml(conv).get("directories") or [])

    preset = Preset(
        id=preset_id,
        nombre=nombre,
        descripcion=descripcion,
        ciclos=ciclos,
        rutas=rutas,
        directorios=directorios,
        invariantes=invariantes,
        herramientas=herramientas,
        cadena=[d.get("id", "?") for d in cadena],
    )
    _validar(preset)
    return preset


def presets_disponibles(bundle_dir: Path) -> List[str]:
    dir_presets = Path(bundle_dir) / "presets"
    if not dir_presets.exists():
        return []
    return sorted(p.name for p in dir_presets.iterdir() if (p / "preset.yml").exists())
