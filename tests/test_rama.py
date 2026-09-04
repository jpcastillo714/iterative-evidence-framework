"""La rama declarada frente a la rama real.

`--branch` guardaba un nombre en state.yml que nadie comprobaba nunca. El fallo que eso
permite es silencioso y caro: avanzas pasos y firmas compuertas del incremento 003 con
el arbol de trabajo en la rama de 001. Nada falla — el estado dice una cosa y el codigo
del disco dice otra, y eso no se descubre hasta que alguien mira un diff que no cuadra.

Es aviso, no error: el motor no sabe por que estas donde estas, y bloquear el avance
convertiria una ayuda en un estorbo. Pero callarlo es peor.
"""

from __future__ import annotations

import shutil
import subprocess

import pytest
import yaml

from conftest import correr

pytestmark = pytest.mark.skipif(shutil.which("git") is None, reason="no hay git")


def _repo(tmp_path, rama="main"):
    d = tmp_path / "proj"
    d.mkdir()
    subprocess.run(["git", "init", "-q", "-b", rama, str(d)], check=True)
    # La identidad va explicita: un runner de CI limpio no tiene user.name ni
    # user.email configurados y `git commit` falla con codigo 128.
    subprocess.run(
        ["git", "-C", str(d),
         "-c", "user.name=test", "-c", "user.email=test@example.invalid",
         "commit", "-q", "--allow-empty", "-m", "x"],
        check=True, capture_output=True,
    )
    r = correr("--mode", "init", "--project-dir", str(d), "--preset", "generic",
               "--layout", "flat", "--initiative-name", "P")
    assert r.returncode == 0, r.stderr
    return d


def _estado(d):
    return yaml.safe_load((d / "initiative" / "state.yml").read_text(encoding="utf-8"))


def test_avisa_cuando_estas_en_otra_rama(tmp_path):
    d = _repo(tmp_path)
    correr("--mode", "new-increment", "--project-dir", str(d), "--type", "task",
           "--name", "F", "--branch", "inc/001-f")
    r = correr("--mode", "advance", "--project-dir", str(d))
    assert "inc/001-f" in r.stdout and "main" in r.stdout, (
        "el aviso tiene que nombrar las dos ramas para que se entienda que pasa"
    )


def test_no_avisa_cuando_la_rama_cuadra(tmp_path):
    d = _repo(tmp_path)
    correr("--mode", "new-increment", "--project-dir", str(d), "--type", "task",
           "--name", "F", "--branch", "main")
    r = correr("--mode", "advance", "--project-dir", str(d))
    assert "declara la rama" not in r.stdout


def test_no_avisa_si_el_incremento_no_declaro_rama(tmp_path):
    """Un incremento sin `--branch` no prometio nada: avisarle seria ruido."""
    d = _repo(tmp_path)
    correr("--mode", "new-increment", "--project-dir", str(d), "--type", "task", "--name", "F")
    r = correr("--mode", "advance", "--project-dir", str(d))
    assert "declara la rama" not in r.stdout


def test_fuera_de_un_repositorio_git_no_estorba(tmp_path):
    """Que el proyecto no use git es normal, no un error."""
    d = tmp_path / "sin_git"
    d.mkdir()
    correr("--mode", "init", "--project-dir", str(d), "--preset", "generic",
           "--layout", "flat", "--initiative-name", "P")
    correr("--mode", "new-increment", "--project-dir", str(d), "--type", "task",
           "--name", "F", "--branch", "inc/001-f")
    r = correr("--mode", "advance", "--project-dir", str(d))
    assert "declara la rama" not in r.stdout
    assert "Traceback" not in r.stderr


def test_doctor_lo_ve(tmp_path):
    d = _repo(tmp_path)
    correr("--mode", "new-increment", "--project-dir", str(d), "--type", "task",
           "--name", "F", "--branch", "inc/001-f")
    r = correr("--mode", "doctor", "--project-dir", str(d))
    assert "inc/001-f" in r.stdout


def test_la_rama_se_corrige_sin_abrir_otro_incremento(tmp_path):
    """El nombre de una rama cambia en la vida real; el estado debe poder seguirle."""
    d = _repo(tmp_path)
    correr("--mode", "new-increment", "--project-dir", str(d), "--type", "task",
           "--name", "F", "--branch", "inc/001-f")
    r = correr("--mode", "set-status", "--project-dir", str(d),
               "--increment", "001_f", "--branch", "main")
    assert r.returncode == 0, r.stderr

    inc = _estado(d)["increments"][0]
    assert inc["branch"] == "main"
    assert inc["status"] == "ACTIVE", "corregir la rama no debe tocar el estado"

    assert "inc/001-f" not in correr("--mode", "doctor", "--project-dir", str(d)).stdout


def test_set_status_sin_estado_ni_rama_se_rechaza(tmp_path):
    d = _repo(tmp_path)
    correr("--mode", "new-increment", "--project-dir", str(d), "--type", "task", "--name", "F")
    r = correr("--mode", "set-status", "--project-dir", str(d), "--increment", "001_f")
    assert r.returncode != 0
