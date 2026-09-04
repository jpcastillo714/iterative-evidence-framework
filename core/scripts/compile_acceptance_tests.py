#!/usr/bin/env python3
"""
IEF · Compilador de tests de aceptacion.

Que resuelve
------------
El Paso 5 produce `acceptance-tests.yml`: criterios en prosa `given / when / then`
con un campo `status` que hasta ahora se actualizaba a mano. Nada conectaba ese
documento con codigo que se ejecutara, asi que un test podia decir `passing` sin que
nadie hubiera corrido nada. Es la brecha que el diagnostico llamo "el abismo entre
YAML declarativo y Python ejecutable".

Este compilador traduce el YAML a un archivo pytest real. Cada criterio se convierte
en una funcion de test que:

  - lleva el `test_id`, la regla enlazada y el given/when/then en su docstring,
  - queda marcada con `@pytest.mark.ief` y `@pytest.mark.<test_id>`,
  - ejecuta el `verify` declarado si existe, o FALLA como `not_implemented` si no.

Un criterio sin forma de verificarse no pasa: falla ruidosamente. Esa es la regla.
Un `status: blocked` con `blocked_reason` se traduce en `pytest.skip`, que es la
unica manera honesta de decir "esto no se puede medir todavia".

Formas de `verify` soportadas
-----------------------------
    verify:
      kind: command                 # ejecuta un comando; exito = exit code esperado
      run: "python pipelines/evaluar.py"
      expected_exit_code: 0

    verify:
      kind: python                  # llama a una funcion importable que devuelve bool
      callable: "mi_paquete.checks:umbral_calibrado_sobre_nominal"

    verify:
      kind: metric                  # compara una metrica de un JSON contra un umbral
      report: "06_resultados/experimentos/evaluacion.json"
      path: "por_evento.recall"     # ruta con puntos dentro del JSON
      op: ">="                      # >= > <= < == !=
      value: 0.80

Uso
---
    python core/scripts/compile_acceptance_tests.py --project-dir . \\
        --increment 003_deteccion --out tests/generated/

    pytest tests/generated/ -v
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

SCRIPT_DIR = Path(__file__).parent.resolve()
BUNDLE_DIR = SCRIPT_DIR.parent.parent
sys.path.insert(0, str(SCRIPT_DIR))

from ief_preset import ErrorDePreset, cargar_preset  # noqa: E402

OPERADORES = {">=", ">", "<=", "<", "==", "!="}


def _slug_py(texto: str) -> str:
    """Convierte TST-ACC-007 en un nombre de funcion valido y estable."""
    limpio = re.sub(r"[^0-9a-zA-Z]+", "_", str(texto)).strip("_").lower()
    return limpio or "sin_id"


def _tid(t: Dict[str, Any]) -> str:
    return str(t.get("test_id") or t.get("id") or "")


def _lit(valor: Any) -> str:
    return repr(valor)


def _docstring(t: Dict[str, Any]) -> str:
    partes = [
        f"{_tid(t)} — {t.get('scenario') or t.get('name') or 'criterio de aceptacion'}",
        "",
        f"Regla enlazada : {t.get('linked_rule') or 'SIN ENLACE'}",
    ]
    for etiqueta, clave in (("Dado", "given"), ("Cuando", "when"), ("Entonces", "then")):
        if t.get(clave):
            partes.append(f"{etiqueta:<15}: {t[clave]}")
    for clave, etiqueta in (("claim", "Afirmacion"), ("criterion", "Criterio")):
        if t.get(clave):
            partes.append(f"{etiqueta:<15}: {t[clave]}")
    return "\n    ".join(partes)


# ─── Generacion del cuerpo de cada test ──────────────────────────────────────

def _cuerpo_command(v: Dict[str, Any]) -> List[str]:
    cmd = v.get("run") or v.get("command")
    if not cmd:
        return ["    pytest.fail('verify.kind=command sin `run`')"]
    esperado = int(v.get("expected_exit_code", 0))
    return [
        f"    proc = subprocess.run({_lit(cmd)}, shell=True, cwd=str(PROJECT_DIR),",
        "                          capture_output=True, text=True)",
        f"    assert proc.returncode == {esperado}, (",
        f"        f'exit {{proc.returncode}} (esperado {esperado})\\n'",
        "        f'stdout: {proc.stdout[-2000:]}\\nstderr: {proc.stderr[-2000:]}')",
    ]


def _cuerpo_python(v: Dict[str, Any]) -> List[str]:
    ref = v.get("callable") or v.get("funcion")
    if not ref or ":" not in str(ref):
        return ["    pytest.fail('verify.kind=python requiere `callable: modulo:funcion`')"]
    modulo, funcion = str(ref).split(":", 1)
    return [
        "    import importlib",
        f"    mod = importlib.import_module({_lit(modulo)})",
        f"    fn = getattr(mod, {_lit(funcion)})",
        "    resultado = fn()",
        f"    assert resultado, f'{ref} devolvio {{resultado!r}}, se esperaba un valor verdadero'",
    ]


def _cuerpo_metric(v: Dict[str, Any]) -> List[str]:
    reporte, ruta, op, valor = v.get("report"), v.get("path"), v.get("op"), v.get("value")
    if not reporte or not ruta or op not in OPERADORES or valor is None:
        return [
            "    pytest.fail('verify.kind=metric requiere `report`, `path`, "
            f"`op` en {sorted(OPERADORES)} y `value`')"
        ]
    return [
        f"    destino = PROJECT_DIR / {_lit(reporte)}",
        "    if not destino.exists():",
        f"        pytest.fail(f'no existe el reporte {{destino}}. "
        "Ejecuta el pipeline antes de verificar este criterio.')",
        "    doc = json.loads(destino.read_text(encoding='utf-8'))",
        f"    obtenido = _buscar(doc, {_lit(ruta)})",
        f"    assert obtenido is not None, 'la metrica {ruta} no esta en el reporte'",
        f"    assert obtenido {op} {_lit(valor)}, (",
        f"        f'{ruta} = {{obtenido}}, se exigia {op} {valor}')",
    ]


def _cuerpo(t: Dict[str, Any]) -> List[str]:
    estado = str(t.get("status", "")).lower()
    if estado == "blocked":
        razon = t.get("blocked_reason") or t.get("bloqueo") or "sin razon declarada"
        return [f"    pytest.skip({_lit(f'BLOQUEADO: {razon}')})"]

    v = t.get("verify") or t.get("verificacion")
    if not v or not isinstance(v, dict):
        return [
            "    pytest.fail(",
            f"        '{_tid(t)} no declara `verify`: es prosa, no un criterio verificable.\\n'",
            "        'Agrega un bloque verify (kind: command | python | metric) "
            "o marca el test como status: blocked con su razon.')",
        ]

    kind = str(v.get("kind") or v.get("tipo") or "").lower()
    if kind == "command":
        return _cuerpo_command(v)
    if kind == "python":
        return _cuerpo_python(v)
    if kind == "metric":
        return _cuerpo_metric(v)
    return [f"    pytest.fail({_lit(f'verify.kind desconocido: {kind!r}')})"]


# ─── Ensamblado del archivo ──────────────────────────────────────────────────

CABECERA = '''"""
ARCHIVO GENERADO — no editar a mano.

Compilado desde : {origen}
Incremento      : {slug}
Generado        : {cuando}

Se regenera con:
    python core/scripts/compile_acceptance_tests.py --increment {slug}

Editar aqui es editar el reporte en vez del experimento: el proximo `compile`
borra los cambios. Si un criterio esta mal, se corrige en acceptance-tests.yml.
"""

import json
import subprocess
from pathlib import Path

import pytest

PROJECT_DIR = Path(__file__).resolve().parents[{niveles}]

pytestmark = pytest.mark.ief


def _buscar(doc, ruta):
    """Recorre un JSON anidado con una ruta con puntos: por_evento.recall"""
    nodo = doc
    for parte in str(ruta).split("."):
        if isinstance(nodo, dict) and parte in nodo:
            nodo = nodo[parte]
        else:
            return None
    return nodo
'''


def compilar(
    tests: List[Dict[str, Any]], slug: str, origen: str, niveles: int
) -> str:
    lineas = [
        CABECERA.format(
            origen=origen, slug=slug,
            cuando=datetime.now(timezone.utc).isoformat(), niveles=niveles,
        )
    ]
    vistos: Dict[str, int] = {}

    for t in tests:
        tid = _tid(t) or "SIN-ID"
        base = _slug_py(tid)
        vistos[base] = vistos.get(base, 0) + 1
        nombre = base if vistos[base] == 1 else f"{base}_{vistos[base]}"

        marcas = [f'@pytest.mark.{_slug_py(tid)}']
        if t.get("linked_rule"):
            marcas.append(f'@pytest.mark.{_slug_py(t["linked_rule"])}')

        lineas.append("")
        lineas.append("")
        lineas.extend(marcas)
        lineas.append(f"def test_{nombre}():")
        lineas.append(f'    """{_docstring(t)}"""')
        lineas.extend(_cuerpo(t))

    return "\n".join(lineas) + "\n"


def main() -> None:
    p = argparse.ArgumentParser(
        description="Compila acceptance-tests.yml a un archivo pytest ejecutable"
    )
    p.add_argument("--project-dir", default=".")
    p.add_argument("--increment", help="slug del incremento (por defecto, el activo)")
    p.add_argument("--out", default="tests/generated", help="directorio de salida")
    p.add_argument("--check", action="store_true",
                   help="no escribe; falla si el archivo generado difiere del existente")
    args = p.parse_args()

    project_dir = Path(args.project_dir).resolve()
    state_path = project_dir / "initiative" / "state.yml"
    if not state_path.exists():
        print(f"ERROR: no existe {state_path}", file=sys.stderr)
        sys.exit(2)

    state = yaml.safe_load(state_path.read_text(encoding="utf-8")) or {}
    slug = args.increment or state.get("active_increment")
    if not slug:
        print("ERROR: no hay incremento activo; pasa --increment", file=sys.stderr)
        sys.exit(2)

    try:
        preset = cargar_preset((state.get("initiative") or {}).get("preset"), BUNDLE_DIR)
    except ErrorDePreset as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(2)

    origen = project_dir / preset.dir_incremento(slug) / "acceptance-tests.yml"
    if not origen.exists():
        print(f"ERROR: no existe {origen}. El Paso 5 debe completarse primero.", file=sys.stderr)
        sys.exit(2)

    doc = yaml.safe_load(origen.read_text(encoding="utf-8")) or {}
    tests = doc.get("tests") or []
    if not tests:
        print(f"ERROR: {origen} no declara ningun test", file=sys.stderr)
        sys.exit(2)

    dir_out = project_dir / args.out
    destino = dir_out / f"test_acceptance_{_slug_py(slug)}.py"
    niveles = len(destino.relative_to(project_dir).parts) - 1

    codigo = compilar(
        tests, slug, str(origen.relative_to(project_dir)).replace("\\", "/"), niveles
    )

    sin_verify = [_tid(t) for t in tests
                  if not t.get("verify") and str(t.get("status", "")).lower() != "blocked"]
    bloqueados = [_tid(t) for t in tests if str(t.get("status", "")).lower() == "blocked"]

    if args.check:
        if not destino.exists():
            print(f"ERROR: falta {destino}. Ejecuta el compilador.", file=sys.stderr)
            sys.exit(1)
        actual = destino.read_text(encoding="utf-8")
        # La cabecera lleva la fecha de generacion: se compara el cuerpo.
        def _cuerpo_solo(txt: str) -> str:
            return txt.split('"""', 2)[-1]
        if _cuerpo_solo(actual) != _cuerpo_solo(codigo):
            print(f"ERROR: {destino} esta desactualizado respecto de {origen.name}", file=sys.stderr)
            sys.exit(1)
        print(f"[OK] {destino.name} al dia respecto de acceptance-tests.yml")
        return

    dir_out.mkdir(parents=True, exist_ok=True)
    init = dir_out / "__init__.py"
    if not init.exists():
        init.write_text("", encoding="utf-8")
    destino.write_text(codigo, encoding="utf-8")

    # Cada TST y cada BR se convierten en una marca de pytest, para poder correr
    # "todos los tests de la regla RUL-001-003" con `pytest -m br_003`. Registrarlas
    # evita el ruido de PytestUnknownMarkWarning.
    marcas = {"ief"}
    for t in tests:
        marcas.add(_slug_py(_tid(t)))
        if t.get("linked_rule"):
            marcas.add(_slug_py(t["linked_rule"]))
    conftest = "\n".join(
        ["# ARCHIVO GENERADO — registra las marcas de trazabilidad IEF.", "", "", "def pytest_configure(config):"]
        + [f'    config.addinivalue_line("markers", {_lit(m)})' for m in sorted(marcas)]
    ) + "\n"
    (dir_out / "conftest.py").write_text(conftest, encoding="utf-8")

    print(f"[COMPILE] {len(tests)} criterio(s) -> {destino.relative_to(project_dir)}")
    if bloqueados:
        print(f"          {len(bloqueados)} bloqueado(s) (se saltaran): {', '.join(bloqueados)}")
    if sin_verify:
        print(f"          {len(sin_verify)} SIN bloque `verify`, fallaran hasta declararlo:")
        for t in sin_verify:
            print(f"            - {t}")
    print(f"\nEjecutalos con:  pytest {args.out} -v")


if __name__ == "__main__":
    main()
