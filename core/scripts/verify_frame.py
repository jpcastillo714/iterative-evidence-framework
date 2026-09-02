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
import json
import os
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
    Paso,
    Preset,
    cargar_preset,
    presets_disponibles,
)

INCREMENT_STATUS = ["ACTIVE", "PAUSED", "BLOCKED", "COMPLETED", "MERGED", "ABANDONED"]
STEP_STATUS = ["PENDING", "IN_PROGRESS", "COMPLETED", "APPROVED", "NEEDS_REVISION"]

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


def get_increment(
    state: Dict[str, Any], slug: Optional[str]
) -> Tuple[Optional[Dict[str, Any]], Optional[int]]:
    objetivo = slug or state.get("active_increment")
    for idx, inc in enumerate(state.get("increments", [])):
        if inc.get("slug") == objetivo or inc.get("id") == objetivo:
            return inc, idx
    return None, None


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
    """Valida la estructura de un data-contract.yml en cualquiera de sus tres formas."""
    canales = data.get("canales") or data.get("channels")
    if canales:
        if not isinstance(canales, dict) or not canales:
            return False, "telemetria"

        def _tiene_clase(nodo: Any) -> bool:
            if not isinstance(nodo, dict):
                return False
            return "clase" in nodo or any(_tiene_clase(v) for v in nodo.values())

        return any(_tiene_clase(v) for v in canales.values()), "telemetria"

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


def _validar_business_rules(data: Dict[str, Any]) -> List[Tuple[str, str, bool]]:
    rules = data.get("rules") or []
    ok = bool(rules)
    for r in rules:
        if not str(r.get("id", "")).startswith("BR-") or not r.get("description"):
            ok = False
        if str(r.get("priority", "")).lower() not in PRIORIDADES:
            ok = False
        if str(r.get("status", "")).lower() not in ESTADOS_REGLA:
            ok = False
    ids = [r.get("id") for r in rules if r.get("id")]
    return [
        ("Estructura", "business-rules.yml estructura valida", ok),
        ("Estructura", "business-rules.yml IDs unicos", len(ids) == len(set(ids))),
    ]


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

    br_path = dir_inc / "business-rules.yml"
    if br_path.exists():
        with open(br_path, "r", encoding="utf-8") as f:
            br = yaml.safe_load(f) or {}
        br_ids = {r.get("id") for r in (br.get("rules") or []) if r.get("id")}
        huerfanos = [_tid(t) for t in tests if t.get("linked_rule") not in br_ids]
        res.append(
            ("Trazabilidad", f"cada TST apunta a un BR existente{'' if not huerfanos else f' (huerfanos: {huerfanos})'}", not huerfanos)
        )
        cubiertas = {t.get("linked_rule") for t in tests}
        sin_test = sorted(br_ids - cubiertas)
        if sin_test:
            print(f"  [!] Reglas de negocio sin ningun test: {', '.join(sin_test)}")
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
    elif paso.artefacto == "business-rules.yml":
        res += _validar_business_rules(data)
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

def cmd_init(project_dir: Path, preset_id: str, nombre: str, force: bool) -> None:
    try:
        preset = cargar_preset(preset_id, BUNDLE_DIR)
    except ErrorDePreset as exc:
        fallar(str(exc), 2)

    state_file = ruta_state(project_dir)
    if state_file.exists() and not force:
        fallar(f"ya existe {state_file}. Usa --force-overwrite para reemplazarlo.")

    creados = []
    for d in preset.directorios:
        destino = project_dir / d["path"]
        if not destino.exists():
            destino.mkdir(parents=True, exist_ok=True)
            creados.append(d["path"])
    (project_dir / preset.dir_incremento("").rstrip("/")).mkdir(parents=True, exist_ok=True)
    (project_dir / preset.rutas.get("specs_dir", "initiative/specs")).mkdir(parents=True, exist_ok=True)

    state = {
        "schema_version": "3.1",
        "initiative": {
            "id": nombre.upper().replace(" ", "-")[:24],
            "name": nombre,
            "preset": preset.id,
            "created_at": ahora(),
        },
        "active_increment": None,
        "increments": [],
        "history": [],
    }
    record_history(state, "INIT", {"preset": preset.id, "cadena": preset.cadena})
    save_state(state, state_file)

    print(f"\n[INIT] IEF V3 inicializado con preset `{preset.id}`")
    print(f"       herencia   : {' -> '.join(preset.cadena)}")
    print(f"       ciclos     : {', '.join(preset.tipos_de_ciclo())}")
    for tipo in preset.tipos_de_ciclo():
        pasos = preset.pasos(tipo)
        gates = [p.ref for p in pasos if p.human_gate]
        print(f"         {tipo:<12} {len(pasos)} pasos, compuertas en {gates or 'ninguna'}")
    print(f"       directorios: {len(creados)} creado(s)")
    print(f"\nSiguiente: crear un incremento con /speckit.ief.charter o /speckit.ief.explore")


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
            "active_increment": state.get("active_increment"),
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
    activo = state.get("active_increment")
    print()
    print(f"  IEF V3 — {ini.get('name', 'sin nombre')}")
    print(f"  preset {preset.id} ({' -> '.join(preset.cadena)}) · schema {state.get('schema_version', '?')}")
    print("  " + "─" * 68)

    if not state.get("increments"):
        print("  (sin incrementos todavia)")

    for inc in state.get("increments", []):
        slug = inc.get("slug", inc.get("id", "?"))
        tipo = inc.get("type", "build")
        estado = inc.get("status", "PENDING")
        marca = "*" if slug == activo else " "
        print(f"\n  {marca} {slug}  ({tipo})  {INCREMENT_ICONS.get(estado, '[?]')} {estado}")

        if tipo not in preset.ciclos:
            print(f"      [!] el preset `{preset.id}` no define el ciclo `{tipo}`")
            continue

        for p in preset.pasos(tipo):
            s = (inc.get("steps") or {}).get(p.clave, "PENDING")
            aqui = "<--" if str(inc.get("current_step")) == p.ref else ""
            gate = " (compuerta)" if p.human_gate else ""
            print(f"      {STEP_ICONS.get(s, '?')} {p.ref:>2}. {p.nombre:<26} {s:<15}{gate} {aqui}")

        if estado == "PAUSED" and inc.get("paused_reason"):
            print(f"      razon: {inc['paused_reason']}")
        if estado == "BLOCKED" and inc.get("blocked_by"):
            print(f"      bloqueado por: {inc['blocked_by']}")
    print()
    print("  leyenda: o COMPLETED  * APPROVED  ~ IN_PROGRESS  . PENDING  ! NEEDS_REVISION")
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
        obligatorios = ["schema_version", "initiative", "active_increment", "increments"]
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
        try:
            p = cargar_preset(pid, BUNDLE_DIR)
        except ErrorDePreset as exc:
            print(f"  FAIL  {pid}: {exc}")
            fallidos += 1
            continue

        print(f"  PASS  {pid}  ({' -> '.join(p.cadena)})")
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


def cmd_set_status(
    project_dir: Path, slug: Optional[str], status: str, reason: Optional[str], blocked_by: Optional[str]
) -> None:
    state, state_file = load_state(project_dir)
    if not state:
        fallar("no existe initiative/state.yml")
    if status not in INCREMENT_STATUS:
        fallar(f"estado invalido. Validos: {', '.join(INCREMENT_STATUS)}")

    inc, idx = get_increment(state, slug)
    if not inc:
        fallar(f"incremento no encontrado: {slug}")
    slug_real = inc.get("slug", inc.get("id"))

    if status == "PAUSED":
        if not reason:
            fallar("--reason es obligatorio para PAUSED")
        inc["paused_reason"] = reason
        inc["paused_at_step"] = inc.get("current_step")
    elif status == "BLOCKED":
        if not reason or not blocked_by:
            fallar("--reason y --blocked-by son obligatorios para BLOCKED")
        inc["blocked_reason"] = reason
        inc["blocked_by"] = blocked_by
    elif status == "ACTIVE":
        for k in ("paused_reason", "paused_at_step", "blocked_reason", "blocked_by"):
            inc.pop(k, None)
        state["active_increment"] = slug_real
    elif status in {"COMPLETED", "MERGED", "ABANDONED"}:
        inc["closed_at"] = ahora()
        if state.get("active_increment") == slug_real:
            state["active_increment"] = None

    inc["status"] = status
    state["increments"][idx] = inc
    record_history(state, "SET_STATUS", {"increment": slug_real, "status": status, "reason": reason})
    save_state(state, state_file)
    print(f"[STATUS] {slug_real} -> {status}")


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


def cmd_merge_increment(project_dir: Path, slug: Optional[str], dry_run: bool) -> None:
    """Promueve los artefactos del incremento a la especificacion viva del proyecto.

    Sin esta promocion, cada incremento acumula su propio `business-rules.yml` y
    nadie sabe cual es la regla vigente. Es el problema que este comando cierra.
    """
    state, state_file = load_state(project_dir)
    if not state:
        fallar("no existe initiative/state.yml")
    preset = preset_de(state)

    inc, idx = get_increment(state, slug)
    if not inc:
        fallar(f"incremento no encontrado: {slug or state.get('active_increment')}")
    slug_real = inc.get("slug", inc.get("id"))
    tipo = inc.get("type", "build")

    if inc.get("status") not in {"COMPLETED", "ACTIVE"}:
        fallar(f"el incremento esta {inc.get('status')}; solo se promueve un incremento COMPLETED")

    pendientes = [
        p.ref for p in preset.pasos(tipo)
        if p.human_gate and (inc.get("steps") or {}).get(p.clave) != "APPROVED"
    ]
    if pendientes:
        fallar(f"no se promueve un incremento con compuertas sin aprobar: pasos {', '.join(pendientes)}")

    dir_inc = project_dir / preset.dir_incremento(slug_real)
    dir_specs = project_dir / preset.rutas.get("specs_dir", "initiative/specs")
    dir_specs.mkdir(parents=True, exist_ok=True)

    resumen: List[str] = []

    # business-rules.yml: union por id, la version del incremento gana, con procedencia.
    origen = dir_inc / "business-rules.yml"
    if origen.exists():
        with open(origen, "r", encoding="utf-8") as f:
            nuevas = (yaml.safe_load(f) or {}).get("rules") or []
        destino = dir_specs / "business-rules.yml"
        vigentes: Dict[str, Dict[str, Any]] = {}
        if destino.exists():
            with open(destino, "r", encoding="utf-8") as f:
                for r in (yaml.safe_load(f) or {}).get("rules") or []:
                    if r.get("id"):
                        vigentes[r["id"]] = r
        agregadas, actualizadas = 0, 0
        for r in nuevas:
            rid = r.get("id")
            if not rid:
                continue
            r = {**r, "_origen": {"increment": slug_real, "merged_at": ahora()}}
            if rid in vigentes:
                actualizadas += 1
            else:
                agregadas += 1
            vigentes[rid] = r
        doc = {
            "schema_version": "1.0",
            "kind": "living_business_rules",
            "updated_at": ahora(),
            "rules": [vigentes[k] for k in sorted(vigentes)],
        }
        if not dry_run:
            with open(destino, "w", encoding="utf-8") as f:
                yaml.safe_dump(doc, f, sort_keys=False, allow_unicode=True)
        resumen.append(f"business-rules.yml: +{agregadas} nuevas, ~{actualizadas} actualizadas, {len(vigentes)} vigentes")

    # data-contract.yml y acceptance-tests.yml: copia versionada por incremento.
    for nombre in ("data-contract.yml", "acceptance-tests.yml"):
        origen = dir_inc / nombre
        if not origen.exists():
            continue
        destino = dir_specs / nombre
        if not dry_run:
            shutil.copy2(origen, destino)
        resumen.append(f"{nombre}: promovido desde {slug_real}")

    if not resumen:
        fallar(f"el incremento {slug_real} no tiene artefactos promovibles")

    print(f"[MERGE] {slug_real} -> {dir_specs.relative_to(project_dir)}")
    for linea in resumen:
        print(f"        {linea}")

    if dry_run:
        print("\n[DRY-RUN] no se escribio nada. Quita --dry-run para aplicar.")
        return

    inc["status"] = "MERGED"
    inc["merged_at"] = ahora()
    if state.get("active_increment") == slug_real:
        state["active_increment"] = None
    state["increments"][idx] = inc
    record_history(state, "MERGE_INCREMENT", {"increment": slug_real, "changes": resumen})
    save_state(state, state_file)
    print(f"\n[OK] {slug_real} marcado MERGED. La especificacion viva esta actualizada.")


def cmd_check_bundle() -> None:
    print("[CHECK] Estructura del bundle\n")
    resultados: List[Tuple[str, bool]] = []

    for f in ("bundle.yml", "README.md", "SKILL.md", "requirements.txt"):
        resultados.append((f"raiz: {f}", (BUNDLE_DIR / f).exists()))
    resultados.append(("extension/extension.yml", (BUNDLE_DIR / "extension" / "extension.yml").exists()))
    resultados.append(("core/scripts/ief_preset.py", (BUNDLE_DIR / "core/scripts/ief_preset.py").exists()))
    resultados.append(("hay al menos un preset", bool(presets_disponibles(BUNDLE_DIR))))

    # El nucleo no debe contener codigo de dominio: eso vive en su preset.
    dominio = [
        p.name for p in (BUNDLE_DIR / "core" / "scripts").glob("*.py")
        if p.stem in {"eval_anomaly", "inject_faults", "validate_data_contract"}
    ]
    resultados.append((f"core/scripts sin codigo de dominio{f' (encontrado: {dominio})' if dominio else ''}", not dominio))

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
            preset = cargar_preset(pid, BUNDLE_DIR)
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
        "init", "status", "verify-step", "check-gates", "check-preset",
        "check-bundle", "check-steps", "advance", "approve-step",
        "set-status", "rewind", "merge-increment",
    ])
    p.add_argument("--project-dir", default=os.getcwd())
    p.add_argument("--preset", help="id del preset (modo init / check-preset)")
    p.add_argument("--initiative-name", default="Nueva Iniciativa")
    p.add_argument("--step", help="ref del paso (1, 2b, 7...)")
    p.add_argument("--increment", help="slug del incremento")
    p.add_argument("--status", help="nuevo estado del incremento")
    p.add_argument("--reason")
    p.add_argument("--blocked-by")
    p.add_argument("--to-step")
    p.add_argument("--by", help="quien aprueba (modo approve-step)")
    p.add_argument("--json", action="store_true", help="salida JSON (modo status)")
    p.add_argument("--dry-run", action="store_true", help="no escribe (modo merge-increment)")
    p.add_argument("--force-overwrite", action="store_true")
    args = p.parse_args()

    d = Path(args.project_dir)

    if args.mode == "init":
        cmd_init(d, args.preset or "generic", args.initiative_name, args.force_overwrite)
    elif args.mode == "status":
        cmd_status(d, args.json)
    elif args.mode == "verify-step":
        cmd_verify_step(d, args.step, args.increment)
    elif args.mode == "check-gates":
        cmd_check_gates(d)
    elif args.mode == "check-preset":
        cmd_check_preset(args.preset)
    elif args.mode == "check-bundle":
        cmd_check_bundle()
    elif args.mode == "check-steps":
        cmd_check_steps()
    elif args.mode == "advance":
        cmd_advance(d)
    elif args.mode == "approve-step":
        cmd_approve_step(d, args.by)
    elif args.mode == "set-status":
        if not args.status:
            fallar("--status es obligatorio")
        cmd_set_status(d, args.increment, args.status, args.reason, args.blocked_by)
    elif args.mode == "rewind":
        if not args.to_step:
            fallar("--to-step es obligatorio")
        cmd_rewind(d, args.to_step, args.reason)
    elif args.mode == "merge-increment":
        cmd_merge_increment(d, args.increment, args.dry_run)


if __name__ == "__main__":
    main()
