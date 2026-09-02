"""Utilidades compartidas por la suite del bundle."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import pytest
import yaml

BUNDLE = Path(__file__).resolve().parent.parent
CORE = BUNDLE / "core" / "scripts"
VERIFY = CORE / "verify_frame.py"
COMPILE = CORE / "compile_acceptance_tests.py"


def cargar_modulo(ruta: Path, nombre: Optional[str] = None):
    """Importa un script por ruta, para poder testear sus funciones directamente."""
    nombre = nombre or ruta.stem
    spec = importlib.util.spec_from_file_location(nombre, ruta)
    modulo = importlib.util.module_from_spec(spec)
    sys.modules[nombre] = modulo
    if str(ruta.parent) not in sys.path:
        sys.path.insert(0, str(ruta.parent))
    spec.loader.exec_module(modulo)
    return modulo


@pytest.fixture(scope="session")
def preset_mod():
    return cargar_modulo(CORE / "ief_preset.py")


def correr(*args: str, cwd: Optional[Path] = None) -> subprocess.CompletedProcess:
    """Ejecuta verify_frame.py como lo haria el usuario y devuelve el proceso."""
    return subprocess.run(
        [sys.executable, str(VERIFY), *args],
        cwd=str(cwd) if cwd else None,
        capture_output=True,
        text=True,
        timeout=120,
    )


def compilar(*args: str, cwd: Optional[Path] = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(COMPILE), *args],
        cwd=str(cwd) if cwd else None,
        capture_output=True,
        text=True,
        timeout=120,
    )


def leer_state(project: Path) -> Dict[str, Any]:
    return yaml.safe_load((project / "initiative" / "state.yml").read_text(encoding="utf-8"))


def escribir_state(project: Path, state: Dict[str, Any]) -> None:
    (project / "initiative" / "state.yml").write_text(
        yaml.safe_dump(state, sort_keys=False, allow_unicode=True), encoding="utf-8"
    )


def marcar_paso(project: Path, clave: str, estado: str) -> None:
    state = leer_state(project)
    state["increments"][0].setdefault("steps", {})[clave] = estado
    escribir_state(project, state)


@pytest.fixture
def proyecto(tmp_path: Path):
    """Un proyecto IEF recien inicializado con un incremento build activo."""
    r = correr("--mode", "init", "--project-dir", str(tmp_path),
               "--preset", "generic", "--initiative-name", "Proyecto de prueba")
    assert r.returncode == 0, r.stderr

    state = leer_state(tmp_path)
    state["active_increment"] = "001_demo"
    state["increments"] = [{
        "id": "001", "slug": "001_demo", "name": "Demo",
        "type": "build", "status": "ACTIVE", "current_step": "1",
        "steps": {"1_charter": "IN_PROGRESS"},
    }]
    escribir_state(tmp_path, state)

    inc = tmp_path / "initiative" / "increments" / "001_demo"
    inc.mkdir(parents=True, exist_ok=True)
    (inc / "charter.md").write_text("# Charter\nObjetivo de prueba.\n", encoding="utf-8")
    return tmp_path


def sembrar_artefactos(project: Path) -> None:
    """Artefactos minimos y coherentes para los pasos 2 a 7."""
    inc = project / "initiative" / "increments" / "001_demo"
    (inc / "inspection-report.md").write_text("# Inspeccion\n", encoding="utf-8")
    (inc / "increment-report.md").write_text("# Reporte\n", encoding="utf-8")
    (inc / "data-contract.yml").write_text(yaml.safe_dump({
        "schemas": [{"name": "t", "fields": [{"name": "ts", "type": "datetime"}]}]
    }), encoding="utf-8")
    (inc / "business-rules.yml").write_text(yaml.safe_dump({
        "rules": [{"id": "BR-001", "description": "Regla de prueba",
                   "priority": "high", "status": "approved"}]
    }), encoding="utf-8")
    (inc / "acceptance-tests.yml").write_text(yaml.safe_dump({
        "tests": [{"test_id": "TST-ACC-001", "linked_rule": "BR-001",
                   "given": "g", "when": "w", "then": "t"}]
    }), encoding="utf-8")
