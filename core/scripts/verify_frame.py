#!/usr/bin/env python3
"""
Iterative Evidence Framework (IEF) V3 — Motor de estado y verificacion.

Que hace
--------
Es la unica pieza que puede modificar `initiative/state.yml`. Gestiona el avance
entre pasos, las compuertas humanas, el retroceso y la promocion de un incremento
a la especificacion viva del proyecto.

Que cambio respecto de 0.4.0
----------------------------
El ciclo (que pasos hay, en que orden, cuales llevan compuerta humana y donde vive
cada artefacto) ya NO esta escrito en este archivo: sale de `presets/<id>/preset.yml`.
Este motor pregunta, el preset responde. Un preset puede ahora quitar pasos, agregar
pasos o mover una compuerta sin tocar una linea de Python.

Modos
-----
    init             crea la estructura del proyecto y state.yml segun el preset
    status           tablero de incrementos (--json para consumo automatico)
    verify-step      verifica el artefacto y la compuerta de un paso
    check-gates      falla si algun paso con compuerta quedo sin aprobar  (CI)
    check-preset     valida que el preset este bien formado
    check-bundle     valida la estructura del bundle
    advance          avanza al siguiente paso del incremento activo
    approve-step     marca un paso con compuerta como APPROVED
    set-status       cambia el estado de un incremento
    rewind           retrocede a un paso anterior
    merge-increment  promueve los artefactos del incremento a initiative/specs/
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml

SCRIPT_DIR = Path(__file__).parent.resolve()
BUNDLE_DIR = SCRIPT_DIR.parent.parent
sys.path.insert(0, str(SCRIPT_DIR))

from ief_preset import (  # noqa: E402
    ErrorDePreset,
    Layout,
    Paso,
    Preset,
    cargar_layout,
    cargar_preset,
    cargar_roles,
    es_mixin,
    layouts_disponibles,
    presets_disponibles,
)

INCREMENT_STATUS = ["ACTIVE", "PAUSED", "BLOCKED", "COMPLETED", "MERGED", "ABANDONED"]
STEP_STATUS = ["PENDING", "IN_PROGRESS", "COMPLETED", "APPROVED", "NEEDS_REVISION"]

# PAUSED es voluntario (tu decidiste parar); BLOCKED es forzado (algo externo frena).
# Se confunden porque ambos son "no estoy trabajando en esto", pero solo uno depende
# de que otra cosa se resuelva, y solo uno se puede diagnosticar.
TIPOS_DE_BLOQUEO = ["increment", "external", "decision"]

ABIERTOS = {"ACTIVE", "PAUSED", "BLOCKED"}
CERRADOS = {"COMPLETED", "MERGED", "ABANDONED"}

MAX_ACTIVOS_POR_DEFECTO = 3      # limite blando: avisa, no bloquea
DIAS_BLOQUEO_RANCIO = 30

INCREMENT_ICONS = {
    "ACTIVE": "[~]", "PAUSED": "[||]", "BLOCKED": "[X]",
    "COMPLETED": "[OK]", "MERGED": "[>>]", "ABANDONED": "[--]",
}
STEP_ICONS = {
    "COMPLETED": "o", "APPROVED": "*", "IN_PROGRESS": "~",
    "PENDING": ".", "NEEDS_REVISION": "!",
}


def ahora() -> str:
    """Timestamp UTC con zona explicita. Todo el rastro de evidencia usa el mismo reloj."""
    return datetime.now(timezone.utc).isoformat()


def fallar(mensaje: str, codigo: int = 1) -> None:
    print(f"ERROR: {mensaje}", file=sys.stderr)
    sys.exit(codigo)


# ─── Estado ──────────────────────────────────────────────────────────────────

def ruta_state(project_dir: Path) -> Path:
    return project_dir / "initiative" / "state.yml"


def load_state(project_dir: Path) -> Tuple[Optional[Dict[str, Any]], Path]:
    path = ruta_state(project_dir)
    if not path.exists():
        return None, path
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as exc:
        fallar(f"state.yml ilegible: {exc}")
    if not isinstance(data, dict):
        fallar("state.yml no es un mapeo YAML")
    return data, path


def save_state(state: Dict[str, Any], state_file: Path) -> None:
    """Escritura atomica: un fallo a mitad de camino no deja el estado corrupto."""
    state["updated_at"] = ahora()
    state_file.parent.mkdir(parents=True, exist_ok=True)

    tmp = None
    try:
        with tempfile.NamedTemporaryFile(
            "w", encoding="utf-8", dir=state_file.parent,
            prefix=".state-", suffix=".tmp", delete=False,
        ) as f:
            tmp = Path(f.name)
            yaml.safe_dump(state, f, sort_keys=False, allow_unicode=True, default_flow_style=False)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, state_file)
        tmp = None
    finally:
        if tmp and tmp.exists():
            tmp.unlink()

    print(f"[STATE] {state_file}", flush=True)


def record_history(state: Dict[str, Any], action: str, details: Dict[str, Any]) -> None:
    entry = {"action": action, "timestamp": ahora()}
    entry.update(details)
    state.setdefault("history", []).append(entry)


def get_focus(state: Dict[str, Any]) -> Optional[str]:
    """A que incremento apuntan los comandos que no llevan `--increment`.

    Es distinto de `status: ACTIVE`. Varios incrementos pueden estar ACTIVE a la vez
    (varios frentes abiertos); el FOCO es uno solo. Antes ambas ideas vivian en el
    mismo campo `active_increment`, y activar un segundo incremento robaba el puntero
    en silencio: seguias trabajando creyendo estar en uno y los comandos —advance,
    approve-step, rewind— caian sobre otro.
    """
    return state.get("focus") or state.get("active_increment")


def set_focus(state: Dict[str, Any], slug: Optional[str]) -> None:
    state["focus"] = slug
    state.pop("active_increment", None)     # el campo viejo no sobrevive a la escritura


def get_increment(
    state: Dict[str, Any], slug: Optional[str]
) -> Tuple[Optional[Dict[str, Any]], Optional[int]]:
    objetivo = slug or get_focus(state)
    for idx, inc in enumerate(state.get("increments", [])):
        if inc.get("slug") == objetivo or inc.get("id") == objetivo:
            return inc, idx
    return None, None


def incrementos_activos(state: Dict[str, Any]) -> List[Dict[str, Any]]:
    return [i for i in state.get("increments", []) if i.get("status") == "ACTIVE"]


def sugerir_foco(state: Dict[str, Any]) -> Optional[str]:
    """Al cerrar el incremento enfocado, proponer el siguiente en vez de dejar None."""
    for estados in (("ACTIVE",), tuple(ABIERTOS)):
        for inc in state.get("increments", []):
            if inc.get("status") in estados:
                return inc.get("slug")
    return None


def dias_desde(iso: Optional[str]) -> Optional[int]:
    if not iso:
        return None
    try:
        t = datetime.fromisoformat(str(iso))
    except (TypeError, ValueError):
        return None
    if t.tzinfo is None:
        t = t.replace(tzinfo=timezone.utc)
    return (datetime.now(timezone.utc) - t).days


# ─── Base de reglas: contra que se construyo el incremento ───────────────────

def ruta_reglas(project_dir: Path, preset: Preset) -> Path:
    return project_dir / preset.rutas.get("specs_dir", "initiative/specs") / "rules.yml"


def hash_reglas(project_dir: Path, preset: Preset) -> Optional[str]:
    """Huella de la especificacion viva en este instante.

    Se anota al abrir un incremento. Si al reanudarlo la huella cambio, las reglas del
    proyecto avanzaron mientras trabajabas en otro frente y el charter puede haber
    quedado obsoleto. Sin esto, un incremento pausado dos meses despierta en otro
    mundo y nadie se lo dice.
    """
    ruta = ruta_reglas(project_dir, preset)
    if not ruta.exists():
        # Sentinela explicito en vez de None: "todavia no habia reglas" es un estado
        # tan comparable como cualquier otro. Con None, un incremento abierto antes
        # de que existiera la primera regla nunca se enteraba de que ya existen.
        return "sha256:sin-reglas"
    return "sha256:" + hashlib.sha256(ruta.read_bytes()).hexdigest()[:16]


def reglas_vigentes(project_dir: Path, preset: Preset) -> Dict[str, Dict[str, Any]]:
    ruta = ruta_reglas(project_dir, preset)
    if not ruta.exists():
        return {}
    with open(ruta, "r", encoding="utf-8") as f:
        doc = yaml.safe_load(f) or {}
    return {r["id"]: r for r in (doc.get("rules") or []) if r.get("id")}


def avisar_si_cambiaron_las_reglas(
    project_dir: Path, preset: Preset, inc: Dict[str, Any]
) -> None:
    if "rules_base" not in inc:
        return                                  # incremento anterior al campo
    base = inc.get("rules_base")
    actual = hash_reglas(project_dir, preset)
    if base == actual:
        return
    ajenas = [
        r for r in reglas_vigentes(project_dir, preset).values()
        if (r.get("_origen") or {}).get("increment") != inc.get("slug")
    ]
    print()
    print("  [!] Las reglas del proyecto cambiaron desde que abriste este incremento.")
    for r in ajenas[:6]:
        marca = "~" if r.get("status") == "superseded" else "+"
        print("        %s %-14s %s" % (marca, r.get("id"), str(r.get("statement", ""))[:52]))
    if len(ajenas) > 6:
        print("        ... y %d mas" % (len(ajenas) - 6))
    print("      Revisa charter.md y data-contract.yml antes de seguir.")
    print()


def preset_de(state: Dict[str, Any]) -> Preset:
    pid = (state.get("initiative") or {}).get("preset") or "generic"
    try:
        return cargar_preset(pid, BUNDLE_DIR)
    except ErrorDePreset as exc:
        fallar(str(exc), 2)


def paso_actual(preset: Preset, inc: Dict[str, Any]) -> Paso:
    tipo = inc.get("type", "build")
    try:
        ciclo = preset.ciclo(tipo)
    except ErrorDePreset as exc:
        fallar(str(exc))
    ref = str(inc.get("current_step") or ciclo.refs[0])
    paso = ciclo.por_ref(ref)
    if paso is None:
        fallar(
            f"el paso `{ref}` no existe en el ciclo `{tipo}` del preset `{preset.id}` "
            f"(pasos: {', '.join(ciclo.refs)})"
        )
    return paso


# ─── Validacion de artefactos ────────────────────────────────────────────────

PRIORIDADES = {"critical", "high", "medium", "low"}
ESTADOS_REGLA = {"draft", "validated", "approved", "deprecated", "active", "pending"}


def _tid(t: Dict[str, Any]) -> str:
    return str(t.get("test_id") or t.get("id") or "")


def validate_data_contract_shape(data: Dict[str, Any]) -> Tuple[bool, str]:
    """Valida la estructura de un data-contract.yml en sus dos formas.

    - `schemas[].fields[]`  forma de la plantilla del Paso 3
    - `sources[].columns[]` forma clasica orientada a sistemas de origen

    Un preset puede definir su propia forma; entonces le corresponde aportar su
    propio validador. El nucleo solo conoce las formas genericas.
    """
    if data.get("schemas"):
        for s in data["schemas"]:
            if not isinstance(s, dict) or not s.get("name") or not s.get("fields"):
                return False, "schemas"
            for c in s["fields"]:
                if not isinstance(c, dict) or not c.get("name") or not c.get("type"):
                    return False, "schemas"
        return True, "schemas"

    sources = data.get("sources")
    if not sources:
        return False, "vacio"
    for s in sources:
        if not isinstance(s, dict) or not s.get("name") or not s.get("columns") or not s.get("format"):
            return False, "sources"
        for c in s["columns"]:
            if not isinstance(c, dict) or not c.get("name") or not c.get("type"):
                return False, "sources"
    return True, "sources"


def _validar_rules(data: Dict[str, Any]) -> List[Tuple[str, str, bool]]:
    """Una regla es normativa y verificable, y trae su justificacion dentro.

    `rationale` no es adorno: es lo que antes seria una bitacora de decisiones aparte,
    y como artefacto separado se desincroniza. Dentro de la regla no puede.
    """
    reglas = data.get("rules") or []
    ok = bool(reglas)
    sin_rationale = []
    ambitos_malos = []
    estados_malos = []

    for r in reglas:
        rid = str(r.get("id", ""))
        if not rid.startswith("RUL-") or not r.get("statement"):
            ok = False
        if not r.get("rationale"):
            sin_rationale.append(rid or "(sin id)")
        if r.get("scope") not in (None, "increment", "project"):
            ambitos_malos.append(rid)
        if r.get("status") not in (None, "proposed", "active", "superseded", "rejected"):
            estados_malos.append(rid)

    ids = [r.get("id") for r in reglas if r.get("id")]
    res = [
        ("Estructura", "rules.yml: cada regla tiene id RUL-* y statement", ok),
        ("Estructura", "rules.yml: IDs unicos", len(ids) == len(set(ids))),
    ]
    if ambitos_malos:
        res.append(("Estructura", "scope invalido en %s" % ambitos_malos, False))
    if estados_malos:
        res.append(("Estructura", "status invalido en %s" % estados_malos, False))
    if sin_rationale:
        # Aviso, no fallo: forzar una justificacion produce justificaciones vacias.
        print("  [!] Reglas sin `rationale` (por que existe la regla): %s"
              % ", ".join(sin_rationale))
    return res


def _validar_acceptance_tests(
    data: Dict[str, Any], dir_inc: Path
) -> List[Tuple[str, str, bool]]:
    tests = data.get("tests") or []
    ok = bool(tests)
    for t in tests:
        if not _tid(t).startswith("TST-") or not t.get("linked_rule"):
            ok = False
        if not (t.get("given") and t.get("when") and t.get("then")):
            ok = False
    ids = [_tid(t) for t in tests if _tid(t)]
    res = [
        ("Estructura", "acceptance-tests.yml estructura valida", ok),
        ("Estructura", "acceptance-tests.yml IDs unicos", len(ids) == len(set(ids))),
    ]

    br_path = dir_inc / "rules.yml"
    if br_path.exists():
        with open(br_path, "r", encoding="utf-8") as f:
            br = yaml.safe_load(f) or {}
        br_ids = {r.get("id") for r in (br.get("rules") or []) if r.get("id")}
        huerfanos = [_tid(t) for t in tests if t.get("linked_rule") not in br_ids]
        detalle = "" if not huerfanos else " (huerfanos: %s)" % huerfanos
        res.append(
            ("Trazabilidad", "cada TST apunta a una regla existente" + detalle, not huerfanos)
        )
        cubiertas = {t.get("linked_rule") for t in tests}
        sin_test = sorted(br_ids - cubiertas)
        if sin_test:
            print("  [!] Reglas sin ningun test: %s" % ", ".join(sin_test))
    return res


def verificar_artefacto(
    preset: Preset, slug: str, paso: Paso, project_dir: Path
) -> List[Tuple[str, str, bool]]:
    """Comprueba existencia, sintaxis y estructura del artefacto de un paso."""
    if not paso.artefacto:
        return [("Artefacto", f"el paso {paso.ref} no produce artefacto", True)]

    dir_inc = project_dir / preset.dir_incremento(slug)
    art = dir_inc / paso.artefacto
    if not art.exists():
        return [("Artefacto", f"{paso.artefacto} existe", False)]

    res: List[Tuple[str, str, bool]] = [("Artefacto", f"{paso.artefacto} existe", True)]
    if not paso.artefacto.endswith((".yml", ".yaml")):
        return res

    try:
        with open(art, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
    except yaml.YAMLError:
        res.append(("Artefacto", f"{paso.artefacto} es YAML valido", False))
        return res
    res.append(("Artefacto", f"{paso.artefacto} es YAML valido", True))

    if paso.artefacto == "data-contract.yml":
        ok, forma = validate_data_contract_shape(data)
        res.append(("Estructura", f"data-contract.yml estructura valida ({forma})", ok))
    elif paso.artefacto == "rules.yml":
        res += _validar_rules(data)
    elif paso.artefacto == "acceptance-tests.yml":
        res += _validar_acceptance_tests(data, dir_inc)
    return res


def verificar_compuerta(inc: Dict[str, Any], paso: Paso) -> List[Tuple[str, str, bool]]:
    """La compuerta humana como condicion mecanica, no como recordatorio."""
    if not paso.human_gate:
        return []
    estado = (inc.get("steps") or {}).get(paso.clave, "PENDING")
    if estado == "APPROVED":
        return [("Compuerta", f"paso {paso.ref} aprobado por el usuario", True)]
    if estado in {"PENDING", "IN_PROGRESS", "NEEDS_REVISION"}:
        return [("Compuerta", f"paso {paso.ref} aun no terminado ({estado})", True)]
    return [
        ("Compuerta", f"paso {paso.ref} esta {estado} pero requiere APPROVED del usuario", False)
    ]


# ─── Modos ───────────────────────────────────────────────────────────────────

def cmd_init(
    project_dir: Path, preset_id: str, layout_id: str, nombre: str, force: bool
) -> None:
    try:
        preset = cargar_preset(preset_id, BUNDLE_DIR)
        layout = cargar_layout(layout_id, BUNDLE_DIR)
    except ErrorDePreset as exc:
        fallar(str(exc), 2)

    state_file = ruta_state(project_dir)
    if state_file.exists() and not force:
        fallar("ya existe %s. Usa --force-overwrite para reemplazarlo." % state_file)

    catalogo = cargar_roles(BUNDLE_DIR)
    creados = []
    for d in preset.directorios(layout, catalogo):
        destino = project_dir / d["path"]
        if not destino.exists():
            destino.mkdir(parents=True, exist_ok=True)
            creados.append((d["path"], d["role"]))

    dir_specs = project_dir / preset.rutas.get("specs_dir", "initiative/specs")
    dir_specs.mkdir(parents=True, exist_ok=True)
    (project_dir / preset.dir_incremento("").rstrip("/")).mkdir(parents=True, exist_ok=True)

    # La constitucion: los principios bajo los que se trabaja, escritos una vez. Es la
    # capa de arriba abajo (como en spec-kit); las reglas que promueven los incrementos
    # son la de abajo arriba. Son cosas distintas y conviven.
    plantilla = BUNDLE_DIR / "core" / "templates" / "constitution-template.md"
    destino_const = dir_specs / "constitution.md"
    if plantilla.exists() and not destino_const.exists():
        texto = plantilla.read_text(encoding="utf-8")
        texto = texto.replace("{{PROYECTO}}", nombre).replace("{{FECHA}}", ahora()[:10])
        destino_const.write_text(texto, encoding="utf-8")

    ident = re.sub(r"[^A-Z0-9-]", "", nombre.upper().replace(" ", "-"))[:24]
    state = {
        "schema_version": "4.0",
        "initiative": {
            "id": ident or "PROYECTO",
            "name": nombre,
            "preset": preset.id,
            "layout": layout.id,
            "created_at": ahora(),
        },
        "focus": None,
        "max_active": MAX_ACTIVOS_POR_DEFECTO,
        "increments": [],
        "history": [],
    }
    record_history(state, "INIT", {
        "preset": preset.id, "layout": layout.id, "cadena": preset.cadena,
    })
    save_state(state, state_file)

    print()
    print("[INIT] %s" % nombre)
    print("       preset : %s  (%s)" % (preset.id, " -> ".join(preset.cadena)))
    print("       layout : %s  (%s)" % (layout.id, layout.nombre))
    print("       ciclos : %s" % ", ".join(preset.tipos_de_ciclo()))
    for tipo in preset.tipos_de_ciclo():
        pasos = preset.pasos(tipo)
        gates = [x.ref for x in pasos if x.human_gate]
        print("          %-12s %d pasos, compuertas en %s"
              % (tipo, len(pasos), gates or "ninguna"))
    print()
    print("       %d directorio(s) creado(s):" % len(creados))
    for ruta, rol in creados:
        print("          %-26s %s" % (ruta, rol))
    if destino_const.exists():
        print()
        print("       constitucion: %s" % destino_const.relative_to(project_dir))
        print("       Escribela antes del primer incremento: son los principios bajo los")
        print("       que trabajaras, y las reglas que descubras viviran debajo.")
    print()
    print("Siguiente: --mode new-increment --type build|exploration|prototype --name '...'")


def cmd_new_increment(
    project_dir: Path, tipo: str, nombre: str, rama: Optional[str]
) -> None:
    """Abre un frente de trabajo y anota contra que reglas se construye."""
    state, state_file = load_state(project_dir)
    if not state:
        fallar("no existe initiative/state.yml. Ejecuta --mode init primero.")
    preset = preset_de(state)

    if tipo not in preset.ciclos:
        fallar("el preset `%s` no define el ciclo `%s` (tiene: %s)"
               % (preset.id, tipo, ", ".join(preset.tipos_de_ciclo())))

    activos = incrementos_activos(state)
    limite = int(state.get("max_active") or MAX_ACTIVOS_POR_DEFECTO)
    if len(activos) >= limite:
        # Limite blando: avisa, no bloquea. Cuantos frentes puedes sostener a la vez
        # lo sabes tu, no el motor; pero conviene que la decision sea consciente.
        print()
        print("  [!] Ya tienes %d incremento(s) ACTIVE: %s"
              % (len(activos), ", ".join(i.get("slug", "?") for i in activos)))
        print("      El limite blando de este proyecto es %d. Mas frentes suele ser"
              % limite)
        print("      dispersion, no productividad. Sigo adelante: es tu decision.")
        print()

    numeros = [int(i["id"]) for i in state.get("increments", [])
               if str(i.get("id", "")).isdigit()]
    nuevo_id = "%03d" % ((max(numeros) + 1) if numeros else 1)
    corto = re.sub(r"[^a-z0-9]+", "_", nombre.lower()).strip("_")[:40] or "sin_nombre"
    slug = "%s_%s" % (nuevo_id, corto)

    ciclo = preset.ciclo(tipo)
    pasos = {p.clave: "PENDING" for p in ciclo.pasos}
    pasos[ciclo.pasos[0].clave] = "IN_PROGRESS"
    inc = {
        "id": nuevo_id,
        "slug": slug,
        "name": nombre,
        "type": tipo,
        "status": "ACTIVE",
        "current_step": ciclo.refs[0],
        "steps": pasos,
        "branch": rama,
        "rules_base": hash_reglas(project_dir, preset),
        "opened_at": ahora(),
    }

    (project_dir / preset.dir_incremento(slug)).mkdir(parents=True, exist_ok=True)
    state.setdefault("increments", []).append(inc)
    set_focus(state, slug)
    record_history(state, "NEW_INCREMENT", {"increment": slug, "type": tipo})
    save_state(state, state_file)

    print()
    print("[NUEVO] %s  (%s)" % (slug, tipo))
    print("        directorio : %s" % preset.dir_incremento(slug))
    print("        foco       -> %s" % slug)
    print("        paso %s: %s" % (ciclo.pasos[0].ref, ciclo.pasos[0].nombre))
    if ciclo.pasos[0].plantilla:
        print("        plantilla  : %s" % ciclo.pasos[0].plantilla)


def cmd_focus(project_dir: Path, slug: Optional[str]) -> None:
    """Cambia a que incremento apuntan los comandos sin `--increment`."""
    state, state_file = load_state(project_dir)
    if not state:
        fallar("no existe initiative/state.yml")
    preset = preset_de(state)

    if not slug:
        actual = get_focus(state)
        print()
        print("  foco actual: %s" % (actual or "(ninguno)"))
        abiertos = [i for i in state.get("increments", []) if i.get("status") in ABIERTOS]
        if abiertos:
            print("  incrementos abiertos:")
            for i in abiertos:
                marca = "*" if i.get("slug") == actual else " "
                print("    %s %-34s %s" % (marca, i.get("slug"), i.get("status")))
        print()
        return

    inc, _ = get_increment(state, slug)
    if not inc:
        fallar("incremento no encontrado: %s" % slug)
    if inc.get("status") in CERRADOS:
        fallar("%s esta %s: no puede recibir el foco" % (inc.get("slug"), inc.get("status")))

    set_focus(state, inc.get("slug"))
    record_history(state, "FOCUS", {"increment": inc.get("slug")})
    save_state(state, state_file)
    print("[FOCO] -> %s" % inc.get("slug"))
    avisar_si_cambiaron_las_reglas(project_dir, preset, inc)


def cmd_status(project_dir: Path, como_json: bool) -> None:
    state, _ = load_state(project_dir)
    if not state:
        fallar("no existe initiative/state.yml. Ejecuta --mode init primero.")
    preset = preset_de(state)

    if como_json:
        salida = {
            "schema_version": state.get("schema_version"),
            "preset": preset.id,
            "preset_chain": preset.cadena,
            "layout": (state.get("initiative") or {}).get("layout"),
            "focus": get_focus(state),
            "max_active": state.get("max_active", MAX_ACTIVOS_POR_DEFECTO),
            "increments": [],
        }
        for inc in state.get("increments", []):
            tipo = inc.get("type", "build")
            pasos = preset.pasos(tipo) if tipo in preset.ciclos else []
            salida["increments"].append({
                "slug": inc.get("slug"),
                "type": tipo,
                "status": inc.get("status"),
                "current_step": inc.get("current_step"),
                "branch": inc.get("branch"),
                "blocked": inc.get("blocked"),
                "paused": inc.get("paused"),
                "rules_base": inc.get("rules_base"),
                "steps": [
                    {
                        "ref": p.ref, "key": p.clave, "name": p.nombre,
                        "human_gate": p.human_gate,
                        "status": (inc.get("steps") or {}).get(p.clave, "PENDING"),
                    }
                    for p in pasos
                ],
            })
        print(json.dumps(salida, indent=2, ensure_ascii=False))
        return

    ini = state.get("initiative", {})
    foco = get_focus(state)
    activos = incrementos_activos(state)
    limite = int(state.get("max_active") or MAX_ACTIVOS_POR_DEFECTO)

    print()
    print("  IEF — %s" % ini.get("name", "sin nombre"))
    print("  preset %s (%s) · layout %s · schema %s"
          % (preset.id, " -> ".join(preset.cadena),
             ini.get("layout", "?"), state.get("schema_version", "?")))
    print("  foco: %s" % (foco or "(ninguno)"))
    if len(activos) > limite:
        print("  [!] %d incrementos ACTIVE (limite blando %d)" % (len(activos), limite))
    print("  " + "-" * 68)

    if not state.get("increments"):
        print("  (sin incrementos todavia)")

    for inc in state.get("increments", []):
        slug = inc.get("slug", inc.get("id", "?"))
        tipo = inc.get("type", "build")
        estado = inc.get("status", "PENDING")
        marca = "*" if slug == foco else " "
        rama = "  [%s]" % inc.get("branch") if inc.get("branch") else ""
        print()
        print("  %s %s  (%s)  %s %s%s"
              % (marca, slug, tipo, INCREMENT_ICONS.get(estado, "[?]"), estado, rama))

        if tipo not in preset.ciclos:
            print("      [!] el preset `%s` no define el ciclo `%s`" % (preset.id, tipo))
            continue

        for p in preset.pasos(tipo):
            st = (inc.get("steps") or {}).get(p.clave, "PENDING")
            aqui = "<--" if str(inc.get("current_step")) == p.ref else ""
            gate = " (compuerta)" if p.human_gate else ""
            print("      %s %2s. %-28s %-15s%s %s"
                  % (STEP_ICONS.get(st, "?"), p.ref, p.nombre, st, gate, aqui))

        pausa = inc.get("paused") or {}
        if pausa:
            dias = dias_desde(pausa.get("since"))
            extra = " (%d dias)" % dias if dias is not None else ""
            print("      pausado%s: %s" % (extra, pausa.get("reason")))

        bloqueo = inc.get("blocked") or {}
        if bloqueo:
            dias = dias_desde(bloqueo.get("since"))
            espera = " · esperando %d dia(s)" % dias if dias is not None else ""
            destino = bloqueo.get("on") or "(externo)"
            print("      bloqueado [%s] por %s%s" % (bloqueo.get("kind"), destino, espera))
            print("        %s" % bloqueo.get("reason"))
            if bloqueo.get("expected"):
                print("        fecha esperada: %s" % bloqueo["expected"])

    print()
    print("  leyenda: o COMPLETED  * APPROVED  ~ IN_PROGRESS  . PENDING  ! NEEDS_REVISION")
    print("           el * de la izquierda marca el incremento con el FOCO")
    print()


def cmd_verify_step(project_dir: Path, ref: Optional[str], slug: Optional[str]) -> None:
    state, _ = load_state(project_dir)
    if not state:
        fallar("no existe initiative/state.yml")
    preset = preset_de(state)

    inc, _ = get_increment(state, slug)
    if not inc:
        fallar(f"incremento no encontrado: {slug or state.get('active_increment')}")

    slug_real = inc.get("slug", inc.get("id"))
    tipo = inc.get("type", "build")
    paso = preset.ciclo(tipo).por_ref(str(ref)) if ref else paso_actual(preset, inc)
    if paso is None:
        fallar(f"paso `{ref}` invalido para el ciclo `{tipo}`")

    print(f"\n[VERIFY] {slug_real} · paso {paso.ref}: {paso.nombre}")

    resultados = verificar_artefacto(preset, slug_real, paso, project_dir)
    resultados += verificar_compuerta(inc, paso)

    if paso.ref == preset.ciclo(tipo).refs[0]:
        obligatorios = ["schema_version", "initiative", "increments"]
        resultados.append(
            ("Estado", "state.yml tiene los campos obligatorios",
             all(k in state for k in obligatorios))
        )

    fallidos = 0
    print()
    for cat, nombre, ok in resultados:
        print(f"  {'PASS' if ok else 'FAIL'}  [{cat}] {nombre}")
        fallidos += (not ok)
    print()
    if fallidos:
        fallar(f"{fallidos} verificacion(es) fallida(s) en el paso {paso.ref}")
    print(f"[OK] paso {paso.ref} verificado")


def cmd_check_gates(project_dir: Path) -> None:
    """Compuertas humanas como condicion de merge. Es lo que llama la CI."""
    state, _ = load_state(project_dir)
    if not state:
        fallar("no existe initiative/state.yml")
    preset = preset_de(state)

    print("[CHECK] Compuertas humanas de todos los incrementos\n")
    problemas: List[str] = []
    revisados = 0

    for inc in state.get("increments", []):
        slug = inc.get("slug", inc.get("id", "?"))
        tipo = inc.get("type", "build")
        if inc.get("status") in {"ABANDONED"}:
            continue
        if tipo not in preset.ciclos:
            problemas.append(f"{slug}: el preset no define el ciclo `{tipo}`")
            continue

        for p in preset.pasos(tipo):
            if not p.human_gate:
                continue
            revisados += 1
            estado = (inc.get("steps") or {}).get(p.clave, "PENDING")
            if estado == "APPROVED":
                print(f"  PASS  {slug} · paso {p.ref} ({p.nombre}) APPROVED")
            elif estado in {"PENDING", "IN_PROGRESS", "NEEDS_REVISION"}:
                print(f"  ....  {slug} · paso {p.ref} ({p.nombre}) aun en curso ({estado})")
            else:
                print(f"  FAIL  {slug} · paso {p.ref} ({p.nombre}) esta {estado} sin APPROVED")
                problemas.append(f"{slug} paso {p.ref} ({p.nombre}): {estado} sin aprobacion")

    print(f"\n{revisados} compuerta(s) revisada(s), {len(problemas)} sin aprobar")
    if problemas:
        print("\nUn paso con compuerta no puede integrarse sin aprobacion explicita:")
        for p in problemas:
            print(f"  - {p}")
        sys.exit(1)
    print("[OK] todas las compuertas alcanzadas estan aprobadas")


def cmd_check_preset(preset_id: Optional[str]) -> None:
    ids = [preset_id] if preset_id else presets_disponibles(BUNDLE_DIR)
    print(f"[CHECK] Presets: {', '.join(ids)}\n")
    fallidos = 0

    for pid in ids:
        # Un mixin no se sostiene solo: se valida componiendolo con el preset base.
        mixin = es_mixin(pid, BUNDLE_DIR)
        try:
            p = cargar_preset(pid, BUNDLE_DIR, base_para_mixin="generic" if mixin else None)
        except ErrorDePreset as exc:
            print(f"  FAIL  {pid}: {exc}")
            fallidos += 1
            continue

        etiqueta = " [mixin, validado sobre generic]" if mixin else ""
        print(f"  PASS  {pid}  ({' -> '.join(p.cadena)}){etiqueta}")
        for tipo in p.tipos_de_ciclo():
            pasos = p.pasos(tipo)
            gates = [x.ref for x in pasos if x.human_gate]
            print(f"          {tipo:<12} {len(pasos)} pasos · compuertas {gates or '[]'}")

        # Las rutas que el preset promete deben existir en el bundle.
        for tipo in p.tipos_de_ciclo():
            for paso in p.pasos(tipo):
                for etiqueta, ruta in (("plantilla", paso.plantilla), ("instrucciones", paso.instrucciones)):
                    if ruta and not (BUNDLE_DIR / ruta).exists():
                        print(f"  FAIL  {pid} · paso {paso.ref}: {etiqueta} inexistente: {ruta}")
                        fallidos += 1
        for nombre, cfg in (p.herramientas or {}).items():
            ruta = cfg.get("script") if isinstance(cfg, dict) else None
            if ruta and not (BUNDLE_DIR / ruta).exists():
                print(f"  FAIL  {pid} · herramienta {nombre}: script inexistente: {ruta}")
                fallidos += 1

    print()
    if fallidos:
        fallar(f"{fallidos} problema(s) en los presets")
    print("[OK] todos los presets son validos y sus rutas existen")


def cmd_advance(project_dir: Path) -> None:
    state, state_file = load_state(project_dir)
    if not state:
        fallar("no existe initiative/state.yml")
    preset = preset_de(state)

    inc, idx = get_increment(state, None)
    if not inc:
        fallar("no hay incremento activo")

    tipo = inc.get("type", "build")
    ciclo = preset.ciclo(tipo)
    paso = paso_actual(preset, inc)
    pasos = inc.setdefault("steps", {})
    estado = pasos.get(paso.clave, "PENDING")

    if paso.human_gate and estado == "COMPLETED":
        fallar(
            f"el paso {paso.ref} ({paso.nombre}) requiere aprobacion del usuario.\n"
            f"       Ejecuta: verify_frame.py --mode approve-step"
        )
    if estado not in {"COMPLETED", "APPROVED"}:
        fallar(
            f"no se puede avanzar: el paso {paso.ref} ({paso.nombre}) esta {estado}. "
            f"Debe estar COMPLETED{' y APPROVED' if paso.human_gate else ''}."
        )

    i = ciclo.refs.index(paso.ref)
    if i + 1 >= len(ciclo.refs):
        print(f"[FIN] {inc.get('slug')} llego al ultimo paso del ciclo `{tipo}`.")
        print("      Cierra el incremento con --mode set-status --status COMPLETED")
        return

    siguiente = ciclo.pasos[i + 1]
    inc["current_step"] = siguiente.ref
    pasos[siguiente.clave] = "IN_PROGRESS"
    state["increments"][idx] = inc
    record_history(state, "ADVANCE_STEP", {
        "increment": inc.get("slug"), "from_step": paso.ref, "to_step": siguiente.ref,
    })
    save_state(state, state_file)
    print(f"[ADVANCE] paso {siguiente.ref}: {siguiente.nombre}")
    if siguiente.human_gate:
        print("          este paso requiere aprobacion humana al terminarlo")
    if siguiente.plantilla:
        print(f"          plantilla: {siguiente.plantilla}")
    ruta = preset.ruta_artefacto(inc.get("slug", ""), siguiente)
    if ruta:
        print(f"          artefacto: {ruta}")


def cmd_approve_step(project_dir: Path, actor: Optional[str]) -> None:
    state, state_file = load_state(project_dir)
    if not state:
        fallar("no existe initiative/state.yml")
    preset = preset_de(state)

    inc, idx = get_increment(state, None)
    if not inc:
        fallar("no hay incremento activo")

    paso = paso_actual(preset, inc)
    if not paso.human_gate:
        fallar(f"el paso {paso.ref} ({paso.nombre}) no tiene compuerta humana")

    pasos = inc.setdefault("steps", {})
    if pasos.get(paso.clave) != "COMPLETED":
        fallar(
            f"el paso debe estar COMPLETED antes de aprobarse "
            f"(ahora: {pasos.get(paso.clave, 'PENDING')})"
        )

    pasos[paso.clave] = "APPROVED"
    inc.setdefault("approvals", {})[paso.clave] = {
        "approved_at": ahora(),
        "approved_by": actor or os.environ.get("USER") or os.environ.get("USERNAME") or "desconocido",
    }
    state["increments"][idx] = inc
    record_history(state, "APPROVE_STEP", {
        "increment": inc.get("slug"), "step": paso.ref, "by": inc["approvals"][paso.clave]["approved_by"],
    })
    save_state(state, state_file)
    print(f"[APPROVED] paso {paso.ref}: {paso.nombre}")


def _ciclo_de_dependencias(
    state: Dict[str, Any], desde: str, hacia: Optional[str]
) -> Optional[List[str]]:
    """Detecta A bloquea B bloquea A: ninguno se desbloquearia nunca."""
    por_slug = {i.get("slug"): i for i in state.get("increments", [])}
    camino = [desde]
    actual = hacia
    while actual:
        camino.append(actual)
        if actual == desde:
            return camino
        bloqueo = (por_slug.get(actual) or {}).get("blocked") or {}
        actual = bloqueo.get("on") if bloqueo.get("kind") == "increment" else None
        if len(camino) > len(por_slug) + 1:
            break
    return None


def cmd_set_status(
    project_dir: Path, slug: Optional[str], status: str, reason: Optional[str],
    blocked_kind: Optional[str], blocked_on: Optional[str], expected: Optional[str],
    mover_foco: bool,
) -> None:
    state, state_file = load_state(project_dir)
    if not state:
        fallar("no existe initiative/state.yml")
    if status not in INCREMENT_STATUS:
        fallar("estado invalido. Validos: %s" % ", ".join(INCREMENT_STATUS))
    preset = preset_de(state)

    inc, idx = get_increment(state, slug)
    if not inc:
        fallar("incremento no encontrado: %s" % slug)
    slug_real = inc.get("slug", inc.get("id"))

    if status == "PAUSED":
        # Voluntario: tu decidiste parar. No depende de nadie mas.
        if not reason:
            fallar("--reason es obligatorio para PAUSED: dentro de un mes no te acordaras")
        inc["paused"] = {
            "reason": reason, "at_step": inc.get("current_step"), "since": ahora(),
        }
        inc.pop("blocked", None)

    elif status == "BLOCKED":
        # Forzado: algo externo frena. El motor necesita saber QUE, para avisarte
        # cuando se resuelva y para detectar dependencias imposibles.
        if not reason:
            fallar("--reason es obligatorio para BLOCKED")
        kind = blocked_kind or "external"
        if kind not in TIPOS_DE_BLOQUEO:
            fallar("--blocked-kind invalido. Validos: %s" % ", ".join(TIPOS_DE_BLOQUEO))

        if kind == "increment":
            if not blocked_on:
                fallar("--blocked-on es obligatorio con --blocked-kind increment")
            objetivo, _ = get_increment(state, blocked_on)
            if not objetivo:
                fallar("el incremento bloqueante `%s` no existe. Si esperas a alguien "
                       "de fuera, usa --blocked-kind external." % blocked_on)
            ciclo = _ciclo_de_dependencias(state, slug_real, objetivo.get("slug"))
            if ciclo:
                fallar("dependencia circular entre incrementos: %s\n"
                       "       Ninguno de los dos podria desbloquearse nunca."
                       % " -> ".join(ciclo))
        inc["blocked"] = {
            "kind": kind, "on": blocked_on, "reason": reason,
            "since": ahora(), "expected": expected,
        }
        inc.pop("paused", None)

    elif status == "ACTIVE":
        inc.pop("paused", None)
        inc.pop("blocked", None)
        # Antes esta rama robaba el foco en silencio: activabas un segundo frente y
        # los comandos sin --increment pasaban a caer sobre el sin avisar.
        if mover_foco:
            set_focus(state, slug_real)
        elif get_focus(state) != slug_real:
            print("  [i] %s queda ACTIVE, pero el foco sigue en %s."
                  % (slug_real, get_focus(state) or "(ninguno)"))
            print("      Para moverlo: --mode focus --increment %s" % slug_real)

    elif status in CERRADOS:
        inc["closed_at"] = ahora()
        if get_focus(state) == slug_real:
            set_focus(state, None)
            inc["status"] = status
            siguiente = sugerir_foco(state)
            if siguiente:
                set_focus(state, siguiente)
                print("  [i] el foco pasa a %s" % siguiente)

    inc["status"] = status
    state["increments"][idx] = inc
    record_history(state, "SET_STATUS", {
        "increment": slug_real, "status": status, "reason": reason,
    })
    save_state(state, state_file)
    print("[STATUS] %s -> %s" % (slug_real, status))

    if status == "ACTIVE":
        avisar_si_cambiaron_las_reglas(project_dir, preset, inc)

    if status in CERRADOS:
        # Nunca desbloquea solo: avisa, y reanudar es decision tuya.
        for otro in state.get("increments", []):
            bloqueo = otro.get("blocked") or {}
            if bloqueo.get("kind") == "increment" and bloqueo.get("on") in (slug_real, inc.get("id")):
                print("  [i] %s estaba bloqueado por este. Para reanudarlo:"
                      % otro.get("slug"))
                print("      --mode set-status --increment %s --status ACTIVE --focus"
                      % otro.get("slug"))


def cmd_rewind(project_dir: Path, to_ref: str, reason: Optional[str]) -> None:
    if not reason:
        fallar("--reason es obligatorio: el retroceso queda en el historial")

    state, state_file = load_state(project_dir)
    if not state:
        fallar("no existe initiative/state.yml")
    preset = preset_de(state)

    inc, idx = get_increment(state, None)
    if not inc:
        fallar("no hay incremento activo")

    tipo = inc.get("type", "build")
    ciclo = preset.ciclo(tipo)
    actual = paso_actual(preset, inc)
    destino = ciclo.por_ref(str(to_ref))
    if destino is None:
        fallar(f"paso `{to_ref}` invalido (pasos: {', '.join(ciclo.refs)})")

    i_actual = ciclo.refs.index(actual.ref)
    i_destino = ciclo.refs.index(destino.ref)
    if i_destino >= i_actual:
        fallar("solo se puede retroceder a un paso anterior")

    pasos = inc.setdefault("steps", {})
    tocados = []
    for p in ciclo.pasos[i_destino : i_actual + 1]:
        pasos[p.clave] = "NEEDS_REVISION"
        inc.get("approvals", {}).pop(p.clave, None)
        tocados.append(p.ref)

    inc["current_step"] = destino.ref
    state["increments"][idx] = inc
    record_history(state, "REWIND", {
        "increment": inc.get("slug"), "from_step": actual.ref,
        "to_step": destino.ref, "reason": reason, "steps_marked": tocados,
    })
    save_state(state, state_file)
    print(f"[REWIND] {actual.ref} -> {destino.ref}: {destino.nombre}")
    print(f"         marcados NEEDS_REVISION: {', '.join(tocados)}")
    print(f"         razon: {reason}")
    if destino.human_gate:
        print("         este paso vuelve a requerir aprobacion humana")


def cmd_merge_increment(
    project_dir: Path, slug: Optional[str], dry_run: bool
) -> None:
    """Promueve las reglas del incremento a la especificacion viva del proyecto.

    Es la direccion que distingue al IEF de spec-kit: alli la constitucion se escribe
    de arriba abajo antes de empezar; aqui las reglas se DESCUBREN trabajando y suben.

    Y es donde estaba el agujero: promover sin detectar conflictos deja que dos
    incrementos contradictorios convivan en silencio, que es exactamente el problema
    de "cambiaste el archivo y no veo el cambio".
    """
    state, state_file = load_state(project_dir)
    if not state:
        fallar("no existe initiative/state.yml")
    preset = preset_de(state)

    inc, idx = get_increment(state, slug)
    if not inc:
        fallar("incremento no encontrado: %s" % (slug or get_focus(state)))
    slug_real = inc.get("slug", inc.get("id"))
    tipo = inc.get("type", "build")

    if inc.get("status") not in {"COMPLETED", "ACTIVE"}:
        fallar("el incremento esta %s; solo se promueve uno COMPLETED o ACTIVE"
               % inc.get("status"))

    pendientes = [
        p.ref for p in preset.pasos(tipo)
        if p.human_gate and (inc.get("steps") or {}).get(p.clave) != "APPROVED"
    ]
    if pendientes:
        fallar("no se promueve un incremento con compuertas sin aprobar: pasos %s"
               % ", ".join(pendientes))

    dir_inc = project_dir / preset.dir_incremento(slug_real)
    dir_specs = project_dir / preset.rutas.get("specs_dir", "initiative/specs")
    dir_specs.mkdir(parents=True, exist_ok=True)
    resumen: List[str] = []

    origen = dir_inc / "rules.yml"
    if origen.exists():
        with open(origen, "r", encoding="utf-8") as f:
            propuestas = (yaml.safe_load(f) or {}).get("rules") or []
        vigentes = reglas_vigentes(project_dir, preset)

        # ── Deteccion de conflictos ─────────────────────────────────────────
        # Choca una regla nueva con una vigente si ambas gobiernan lo mismo
        # (`applies_to`) y la nueva no declara a cual reemplaza.
        conflictos: List[str] = []
        for r in propuestas:
            rid = r.get("id")
            if not rid:
                continue
            supersede = r.get("supersedes")
            ambito = r.get("applies_to")
            for vid, vigente in vigentes.items():
                if vigente.get("status") == "superseded" or vid == rid:
                    continue
                mismo_ambito = ambito and vigente.get("applies_to") == ambito
                if mismo_ambito and supersede != vid:
                    conflictos.append(
                        "%s gobierna `%s`, que ya rige %s. Declara "
                        "`supersedes: %s` si la reemplaza." % (rid, ambito, vid, vid)
                    )
            if supersede and supersede not in vigentes:
                conflictos.append(
                    "%s declara `supersedes: %s`, que no existe en la especificacion viva"
                    % (rid, supersede)
                )

        if conflictos:
            print("[CONFLICTO] La promocion se detiene. Sin esto, dos reglas")
            print("            contradictorias convivirian sin que nadie lo notara.\n")
            for c in conflictos:
                print("  - %s" % c)
            print("\nResuelvelo declarando `supersedes` en la regla que manda, o")
            print("retrocede con --mode rewind si la nueva regla estaba mal planteada.")
            sys.exit(1)

        # ── Promocion ───────────────────────────────────────────────────────
        agregadas, superadas = 0, 0
        for r in propuestas:
            rid = r.get("id")
            if not rid:
                continue
            anterior = r.get("supersedes")
            if anterior and anterior in vigentes:
                # La superada NO se borra: queda con puntero a la que la reemplaza.
                # Borrarla perderia por que el proyecto penso lo contrario un dia.
                vigentes[anterior] = {
                    **vigentes[anterior],
                    "status": "superseded",
                    "superseded_by": rid,
                    "superseded_at": ahora(),
                }
                superadas += 1
            vigentes[rid] = {
                **r,
                "scope": "project",
                "status": r.get("status") if r.get("status") == "rejected" else "active",
                "_origen": {"increment": slug_real, "merged_at": ahora()},
            }
            agregadas += 1

        doc = {
            "schema_version": "2.0",
            "kind": "living_rules",
            "updated_at": ahora(),
            "rules": [vigentes[k] for k in sorted(vigentes)],
        }
        if not dry_run:
            with open(ruta_reglas(project_dir, preset), "w", encoding="utf-8") as f:
                yaml.safe_dump(doc, f, sort_keys=False, allow_unicode=True)
        resumen.append("rules.yml: +%d promovidas, ~%d superadas, %d vigentes"
                       % (agregadas, superadas, len(vigentes)))

    for nombre in ("data-contract.yml", "acceptance-tests.yml"):
        src = dir_inc / nombre
        if not src.exists():
            continue
        if not dry_run:
            shutil.copy2(src, dir_specs / nombre)
        resumen.append("%s: promovido desde %s" % (nombre, slug_real))

    if not resumen:
        fallar("el incremento %s no tiene artefactos promovibles" % slug_real)

    print("[MERGE] %s -> %s" % (slug_real, dir_specs.relative_to(project_dir)))
    for linea in resumen:
        print("        %s" % linea)

    if dry_run:
        print("\n[DRY-RUN] no se escribio nada. Quita --dry-run para aplicar.")
        return

    inc["status"] = "MERGED"
    inc["merged_at"] = ahora()
    if get_focus(state) == slug_real:
        set_focus(state, sugerir_foco(state))
    state["increments"][idx] = inc
    record_history(state, "MERGE_INCREMENT", {"increment": slug_real, "changes": resumen})
    save_state(state, state_file)
    print("\n[OK] %s marcado MERGED. La especificacion viva esta actualizada." % slug_real)


def cmd_doctor(project_dir: Path) -> None:
    """Diagnostico: en que estado real esta esto.

    Existe porque el caos de varios frentes abiertos no se ve en `status`, que muestra
    lo que hay pero no lo que esta mal: una dependencia imposible, un bloqueo de hace
    tres meses que nadie mira, o reglas terminadas que nunca se promovieron.
    """
    state, _ = load_state(project_dir)
    if not state:
        fallar("no existe initiative/state.yml")
    preset = preset_de(state)

    problemas: List[str] = []
    avisos: List[str] = []
    incs = state.get("increments", [])

    # 1. Dependencias circulares.
    for inc in incs:
        bloqueo = inc.get("blocked") or {}
        if bloqueo.get("kind") == "increment":
            ciclo = _ciclo_de_dependencias(state, inc.get("slug"), bloqueo.get("on"))
            if ciclo:
                problemas.append("dependencia circular: %s" % " -> ".join(ciclo))
            elif not any(o.get("slug") == bloqueo.get("on") for o in incs):
                problemas.append("%s esta bloqueado por `%s`, que no existe"
                                 % (inc.get("slug"), bloqueo.get("on")))

    # 2. Bloqueos vencidos o rancios.
    for inc in incs:
        bloqueo = inc.get("blocked") or {}
        if not bloqueo:
            continue
        dias = dias_desde(bloqueo.get("since"))
        if bloqueo.get("expected") and str(bloqueo["expected"]) < ahora()[:10]:
            avisos.append("%s: la fecha esperada (%s) ya paso"
                          % (inc.get("slug"), bloqueo["expected"]))
        elif dias is not None and dias > DIAS_BLOQUEO_RANCIO:
            avisos.append("%s lleva %d dias bloqueado. Sigue vivo o se abandona?"
                          % (inc.get("slug"), dias))

    # 3. Base de reglas obsoleta.
    actual = hash_reglas(project_dir, preset)
    for inc in incs:
        if inc.get("status") in ABIERTOS and inc.get("rules_base") and actual:
            if inc["rules_base"] != actual:
                avisos.append("%s se construyo sobre reglas que ya cambiaron; "
                              "revisa su charter" % inc.get("slug"))

    # 4. Demasiados frentes.
    activos = incrementos_activos(state)
    limite = int(state.get("max_active") or MAX_ACTIVOS_POR_DEFECTO)
    if len(activos) > limite:
        avisos.append("%d incrementos ACTIVE (limite blando %d): %s"
                      % (len(activos), limite,
                         ", ".join(i.get("slug", "?") for i in activos)))

    # 5. Terminados sin promover.
    for inc in incs:
        if inc.get("status") == "COMPLETED":
            avisos.append("%s esta COMPLETED pero sus reglas no se han promovido "
                          "(--mode merge-increment)" % inc.get("slug"))

    # 6. Compuertas terminadas sin aprobar.
    for inc in incs:
        tipo = inc.get("type", "build")
        if inc.get("status") in CERRADOS or tipo not in preset.ciclos:
            continue
        for p in preset.pasos(tipo):
            if p.human_gate and (inc.get("steps") or {}).get(p.clave) == "COMPLETED":
                problemas.append("%s paso %s (%s): COMPLETED sin aprobar"
                                 % (inc.get("slug"), p.ref, p.nombre))

    # 7. Sin foco habiendo trabajo abierto.
    if not get_focus(state) and any(i.get("status") in ABIERTOS for i in incs):
        avisos.append("hay incrementos abiertos y ningun foco: --mode focus --increment <slug>")

    # 8. Todo detenido. Ningun frente puede avanzar y es facil no darse cuenta
    #    cuando cada bloqueo se decidio por separado y con semanas de diferencia.
    abiertos = [i for i in incs if i.get("status") in ABIERTOS]
    if abiertos and not activos:
        problemas.append(
            "los %d incremento(s) abiertos estan detenidos (pausados o bloqueados): "
            "el proyecto no puede avanzar en ningun frente" % len(abiertos)
        )

    print("\n[DOCTOR] %s\n" % (state.get("initiative", {}).get("name", "proyecto")))
    if not problemas and not avisos:
        print("  Sin hallazgos. %d incremento(s), %d activo(s)." % (len(incs), len(activos)))
        print()
        return
    for x in problemas:
        print("  FAIL  %s" % x)
    for x in avisos:
        print("  WARN  %s" % x)
    print("\n%d problema(s), %d aviso(s)" % (len(problemas), len(avisos)))
    print()
    if problemas:
        sys.exit(1)


def cmd_check_bundle() -> None:
    print("[CHECK] Estructura del bundle\n")
    resultados: List[Tuple[str, bool]] = []

    for f in ("bundle.yml", "README.md", "SKILL.md", "requirements.txt"):
        resultados.append((f"raiz: {f}", (BUNDLE_DIR / f).exists()))
    resultados.append(("extension/extension.yml", (BUNDLE_DIR / "extension" / "extension.yml").exists()))
    resultados.append(("core/scripts/ief_preset.py", (BUNDLE_DIR / "core/scripts/ief_preset.py").exists()))
    resultados.append(("hay al menos un preset", bool(presets_disponibles(BUNDLE_DIR))))

    # El nucleo es una lista cerrada. Cualquier otro script en core/scripts/ es
    # codigo de dominio que se colo: su sitio es presets/<id>/scripts/.
    MODULOS_DEL_NUCLEO = {"verify_frame", "ief_preset", "compile_acceptance_tests"}
    intrusos = sorted(
        p.name for p in (BUNDLE_DIR / "core" / "scripts").glob("*.py")
        if p.stem not in MODULOS_DEL_NUCLEO
    )
    resultados.append((
        "core/scripts solo contiene el motor"
        + (f" (intrusos: {intrusos}; su sitio es presets/<id>/scripts/)" if intrusos else ""),
        not intrusos,
    ))

    # Cada comando declarado en extension.yml debe existir.
    ext = BUNDLE_DIR / "extension" / "extension.yml"
    if ext.exists():
        with open(ext, "r", encoding="utf-8") as f:
            doc = yaml.safe_load(f) or {}
        faltan = [
            c.get("file") for c in ((doc.get("provides") or {}).get("commands") or [])
            if c.get("file") and not (BUNDLE_DIR / "extension" / c["file"]).exists()
        ]
        resultados.append((f"comandos declarados existen{f' (faltan: {faltan})' if faltan else ''}", not faltan))

    fallidos = 0
    for nombre, ok in resultados:
        print(f"  {'PASS' if ok else 'FAIL'}  {nombre}")
        fallidos += (not ok)
    print()
    if fallidos:
        fallar(f"{fallidos} problema(s) en la estructura del bundle")
    print("[OK] estructura del bundle correcta")


def cmd_check_steps() -> None:
    """Cada paso declarado por cada preset debe tener sus archivos en el bundle."""
    print("[CHECK] Archivos de apoyo de cada paso\n")
    fallidos, revisados = 0, 0

    for pid in presets_disponibles(BUNDLE_DIR):
        try:
            preset = cargar_preset(
                pid, BUNDLE_DIR,
                base_para_mixin="generic" if es_mixin(pid, BUNDLE_DIR) else None,
            )
        except ErrorDePreset as exc:
            print(f"  FAIL  preset {pid}: {exc}")
            fallidos += 1
            continue
        for tipo in preset.tipos_de_ciclo():
            for paso in preset.pasos(tipo):
                revisados += 1
                for etiqueta, ruta in (("instrucciones", paso.instrucciones), ("plantilla", paso.plantilla)):
                    if ruta and not (BUNDLE_DIR / ruta).exists():
                        print(f"  FAIL  {pid}/{tipo}/{paso.ref}: falta {etiqueta} {ruta}")
                        fallidos += 1

    print(f"\n{revisados} paso(s) revisado(s) en {len(presets_disponibles(BUNDLE_DIR))} preset(s)")
    if fallidos:
        fallar(f"{fallidos} archivo(s) de apoyo faltante(s)")
    print("[OK] todos los pasos tienen sus instrucciones y plantillas")


# ─── CLI ─────────────────────────────────────────────────────────────────────

def main() -> None:
    p = argparse.ArgumentParser(description="IEF V3 — motor de estado y verificacion")
    p.add_argument("--mode", required=True, choices=[
        "init", "new-increment", "status", "focus", "doctor",
        "verify-step", "check-gates", "check-preset", "check-bundle", "check-steps",
        "advance", "approve-step", "set-status", "rewind", "merge-increment",
    ])
    p.add_argument("--project-dir", default=os.getcwd())
    p.add_argument("--preset", help="id del preset (modo init / check-preset)")
    p.add_argument("--layout", help="como se nombran las carpetas: flat | numbered")
    p.add_argument("--initiative-name", default="Nueva Iniciativa")
    p.add_argument("--type", dest="tipo", default="build",
                   help="ciclo del incremento: build | exploration | prototype")
    p.add_argument("--name", help="nombre del incremento (modo new-increment)")
    p.add_argument("--branch", help="rama git asociada al incremento")
    p.add_argument("--step", help="ref del paso (1, 2b, 7...)")
    p.add_argument("--increment", help="slug del incremento")
    p.add_argument("--status", help="nuevo estado del incremento")
    p.add_argument("--reason")
    p.add_argument("--blocked-kind", choices=TIPOS_DE_BLOQUEO,
                   help="que tipo de espera: otro incremento, algo externo, o una decision")
    p.add_argument("--blocked-on", help="slug del incremento bloqueante")
    p.add_argument("--expected", help="fecha esperada de desbloqueo (YYYY-MM-DD)")
    p.add_argument("--focus", dest="mover_foco", action="store_true",
                   help="al reactivar, mover tambien el foco a este incremento")
    p.add_argument("--to-step")
    p.add_argument("--by", help="quien aprueba (modo approve-step)")
    p.add_argument("--json", action="store_true", help="salida JSON (modo status)")
    p.add_argument("--dry-run", action="store_true", help="no escribe (modo merge-increment)")
    p.add_argument("--force-overwrite", action="store_true")
    args = p.parse_args()

    proj = Path(args.project_dir)

    if args.mode == "init":
        cmd_init(proj, args.preset or "generic", args.layout or "flat",
                 args.initiative_name, args.force_overwrite)
    elif args.mode == "new-increment":
        if not args.name:
            fallar("--name es obligatorio para new-increment")
        cmd_new_increment(proj, args.tipo, args.name, args.branch)
    elif args.mode == "focus":
        cmd_focus(proj, args.increment)
    elif args.mode == "doctor":
        cmd_doctor(proj)
    elif args.mode == "status":
        cmd_status(proj, args.json)
    elif args.mode == "verify-step":
        cmd_verify_step(proj, args.step, args.increment)
    elif args.mode == "check-gates":
        cmd_check_gates(proj)
    elif args.mode == "check-preset":
        cmd_check_preset(args.preset)
    elif args.mode == "check-bundle":
        cmd_check_bundle()
    elif args.mode == "check-steps":
        cmd_check_steps()
    elif args.mode == "advance":
        cmd_advance(proj)
    elif args.mode == "approve-step":
        cmd_approve_step(proj, args.by)
    elif args.mode == "set-status":
        if not args.status:
            fallar("--status es obligatorio")
        cmd_set_status(proj, args.increment, args.status, args.reason,
                       args.blocked_kind, args.blocked_on, args.expected,
                       args.mover_foco)
    elif args.mode == "rewind":
        cmd_rewind(proj, args.to_step, args.reason)
    elif args.mode == "merge-increment":
        cmd_merge_increment(proj, args.increment, args.dry_run)


if __name__ == "__main__":
    main()
