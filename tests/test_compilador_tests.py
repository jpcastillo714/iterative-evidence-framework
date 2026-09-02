"""El compilador que cierra la brecha entre `acceptance-tests.yml` y pytest.

Antes, un criterio podia declarar `status: passing` sin que nadie hubiera ejecutado
nada. La regla que estos tests fijan: un criterio sin forma de verificarse FALLA;
no se aprueba por omision.
"""

from __future__ import annotations

import json
import subprocess
import sys

import yaml

from conftest import compilar, correr, leer_state, escribir_state


def _poner_tests(proyecto, tests):
    inc = proyecto / "initiative" / "increments" / "001_demo"
    inc.mkdir(parents=True, exist_ok=True)
    (inc / "acceptance-tests.yml").write_text(
        yaml.safe_dump({"tests": tests}, sort_keys=False, allow_unicode=True), encoding="utf-8"
    )


def _pytest(proyecto):
    return subprocess.run(
        [sys.executable, "-m", "pytest", "tests/generated", "-p", "no:cacheprovider", "-q"],
        cwd=str(proyecto), capture_output=True, text=True, timeout=180,
    )


def test_un_criterio_sin_verify_falla_no_se_aprueba_solo(proyecto):
    _poner_tests(proyecto, [{
        "test_id": "TST-ACC-001", "linked_rule": "BR-001",
        "given": "el sistema", "when": "pasa algo", "then": "el operador queda conforme",
    }])
    assert compilar("--project-dir", str(proyecto), "--increment", "001_demo").returncode == 0
    r = _pytest(proyecto)
    assert r.returncode != 0
    assert "1 failed" in r.stdout
    assert "es prosa, no un criterio verificable" in r.stdout


def test_un_criterio_bloqueado_se_salta_con_su_razon(proyecto):
    _poner_tests(proyecto, [{
        "test_id": "TST-ACC-002", "linked_rule": "BR-001",
        "given": "g", "when": "w", "then": "t",
        "status": "blocked", "blocked_reason": "falta la bitacora de mantenimiento",
    }])
    compilar("--project-dir", str(proyecto), "--increment", "001_demo")
    r = _pytest(proyecto)
    assert r.returncode == 0
    assert "1 skipped" in r.stdout


def test_un_criterio_con_metrica_mide_de_verdad(proyecto):
    (proyecto / "resultados").mkdir(exist_ok=True)
    (proyecto / "resultados" / "eval.json").write_text(
        json.dumps({"por_evento": {"recall": 0.42}}), encoding="utf-8"
    )
    _poner_tests(proyecto, [
        {"test_id": "TST-ACC-010", "linked_rule": "BR-001", "given": "g", "when": "w", "then": "t",
         "verify": {"kind": "metric", "report": "resultados/eval.json",
                    "path": "por_evento.recall", "op": ">=", "value": 0.80}},
        {"test_id": "TST-ACC-011", "linked_rule": "BR-001", "given": "g", "when": "w", "then": "t",
         "verify": {"kind": "metric", "report": "resultados/eval.json",
                    "path": "por_evento.recall", "op": ">=", "value": 0.30}},
    ])
    compilar("--project-dir", str(proyecto), "--increment", "001_demo")
    r = _pytest(proyecto)
    assert "1 failed" in r.stdout and "1 passed" in r.stdout, r.stdout


def test_una_metrica_sin_reporte_falla_con_mensaje_util(proyecto):
    _poner_tests(proyecto, [{
        "test_id": "TST-ACC-012", "linked_rule": "BR-001", "given": "g", "when": "w", "then": "t",
        "verify": {"kind": "metric", "report": "no/existe.json",
                   "path": "a.b", "op": ">=", "value": 1},
    }])
    compilar("--project-dir", str(proyecto), "--increment", "001_demo")
    r = _pytest(proyecto)
    assert r.returncode != 0
    assert "Ejecuta el pipeline" in r.stdout


def test_un_criterio_de_comando_ejecuta_el_comando(proyecto):
    _poner_tests(proyecto, [
        {"test_id": "TST-ACC-020", "linked_rule": "BR-001", "given": "g", "when": "w", "then": "t",
         "verify": {"kind": "command", "run": f'"{sys.executable}" -c "import sys; sys.exit(0)"'}},
        {"test_id": "TST-ACC-021", "linked_rule": "BR-001", "given": "g", "when": "w", "then": "t",
         "verify": {"kind": "command", "run": f'"{sys.executable}" -c "import sys; sys.exit(3)"'}},
    ])
    compilar("--project-dir", str(proyecto), "--increment", "001_demo")
    r = _pytest(proyecto)
    assert "1 failed" in r.stdout and "1 passed" in r.stdout, r.stdout


def test_la_trazabilidad_queda_como_marcas_de_pytest(proyecto):
    _poner_tests(proyecto, [{
        "test_id": "TST-ACC-030", "linked_rule": "BR-007", "given": "g", "when": "w", "then": "t",
        "verify": {"kind": "command", "run": f'"{sys.executable}" -c "pass"'},
    }])
    compilar("--project-dir", str(proyecto), "--increment", "001_demo")
    generado = (proyecto / "tests" / "generated" / "test_acceptance_001_demo.py").read_text(encoding="utf-8")
    assert "@pytest.mark.tst_acc_030" in generado
    assert "@pytest.mark.br_007" in generado
    assert "BR-007" in generado, "la regla enlazada queda en la docstring"


def test_check_detecta_que_el_yaml_cambio(proyecto):
    _poner_tests(proyecto, [{
        "test_id": "TST-ACC-040", "linked_rule": "BR-001", "given": "g", "when": "w", "then": "t",
        "verify": {"kind": "metric", "report": "r.json", "path": "a", "op": ">=", "value": 1},
    }])
    compilar("--project-dir", str(proyecto), "--increment", "001_demo")
    assert compilar("--project-dir", str(proyecto), "--increment", "001_demo", "--check").returncode == 0

    _poner_tests(proyecto, [{
        "test_id": "TST-ACC-040", "linked_rule": "BR-001", "given": "g", "when": "w", "then": "t",
        "verify": {"kind": "metric", "report": "r.json", "path": "a", "op": ">=", "value": 999},
    }])
    r = compilar("--project-dir", str(proyecto), "--increment", "001_demo", "--check")
    assert r.returncode == 1
    assert "desactualizado" in r.stderr


def test_sin_acceptance_tests_no_compila(proyecto):
    r = compilar("--project-dir", str(proyecto), "--increment", "001_demo")
    assert r.returncode == 2
    assert "Paso 5" in r.stderr
