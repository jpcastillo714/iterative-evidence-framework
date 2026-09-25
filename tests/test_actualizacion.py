"""Actualizar el bundle no rompe los proyectos que ya lo usan (ADR-002).

Cada archivo `tests/fixtures/proyecto-<version>.yml` es un proyecto escrito por esa
version del motor, tal como la dejaba (incluido un AGENTS.md que en esas versiones armaba
un agente a mano). Aqui se materializa en un directorio temporal y se comprueba que el
motor actual lo lee, lo diagnostica, y lo migra sin perder nada.

Cada version publicada agrega su fixture. Ver
docs/decisiones/ADR-002-compatibilidad-entre-versiones.md.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from conftest import BUNDLE, CORE, cargar_modulo, correr, escribir_state, leer_state

FIXTURES = sorted((BUNDLE / "tests" / "fixtures").glob("proyecto-*.yml"))


def _version_motor() -> str:
    doc = yaml.safe_load((BUNDLE / "bundle.yml").read_text(encoding="utf-8"))
    return doc["bundle"]["version"]


def _materializar(fixture: Path, destino: Path) -> dict:
    doc = yaml.safe_load(fixture.read_text(encoding="utf-8"))
    for d in doc["dirs"]:
        (destino / d).mkdir(parents=True, exist_ok=True)
    for rel, texto in doc["files"].items():
        ruta = destino / rel
        ruta.parent.mkdir(parents=True, exist_ok=True)
        ruta.write_bytes(texto.encode("utf-8"))
    return doc


def _foto(d: Path) -> dict:
    return {p.relative_to(d).as_posix(): p.read_bytes()
            for p in sorted(d.rglob("*")) if p.is_file()}


@pytest.fixture(params=FIXTURES, ids=lambda p: p.stem)
def viejo(request, tmp_path):
    d = tmp_path / "proj"
    doc = _materializar(request.param, d)
    return d, doc


def test_hay_al_menos_un_proyecto_de_una_version_anterior():
    assert FIXTURES, "sin fixtures no hay forma de saber si actualizar rompe algo"


# ─── Leer ────────────────────────────────────────────────────────────────────

def test_el_motor_actual_lee_el_proyecto_y_avisa_de_la_actualizacion(viejo):
    d, doc = viejo
    r = correr("--mode", "status", "--project-dir", str(d))
    assert r.returncode == 0, r.stderr
    assert "--mode upgrade-notes" in r.stderr, "el aviso va por stderr, en una linea"
    assert doc["ief_version"] in r.stderr and _version_motor() in r.stderr


def test_status_json_trae_el_bloque_upgrade_para_los_agentes(viejo):
    d, doc = viejo
    r = correr("--mode", "status", "--json", "--project-dir", str(d))
    assert r.returncode == 0, r.stderr
    salida = json.loads(r.stdout)                  # stdout sigue siendo JSON puro
    assert salida["ief_version"] == doc["ief_version"]
    assert salida["engine_version"] == _version_motor()
    up = salida["upgrade"]
    assert up and up["from"] == doc["ief_version"] and up["to"] == _version_motor()
    assert up["changes"], "si cambio la version, algo tiene que explicarse"
    assert all(c.get("que_hacer") for c in up["changes"])


def test_doctor_informa_la_actualizacion_sin_fallar(viejo):
    d, doc = viejo
    r = correr("--mode", "doctor", "--project-dir", str(d))
    assert r.returncode == 0, r.stdout
    assert "upgrade-notes" in r.stdout and "migrate" in r.stdout


def test_upgrade_notes_dice_que_cambio_y_que_hacer(viejo):
    d, _ = viejo
    r = correr("--mode", "upgrade-notes", "--project-dir", str(d))
    assert r.returncode == 0, r.stderr
    assert "que cambia" in r.stdout and "que hacer" in r.stdout
    assert "--mode migrate" in r.stdout


# ─── Migrar ──────────────────────────────────────────────────────────────────

def test_migrate_sin_yes_no_escribe_nada(viejo):
    d, _ = viejo
    antes = _foto(d)
    r = correr("--mode", "migrate", "--project-dir", str(d))
    assert r.returncode == 0, r.stderr
    assert "Simulacion" in r.stdout
    assert _foto(d) == antes


def test_migrate_respalda_actualiza_y_no_toca_lo_ajeno(viejo):
    d, doc = viejo
    agents_viejo = doc["files"].get("AGENTS.md")
    r = correr("--mode", "migrate", "--yes", "--project-dir", str(d))
    assert r.returncode == 0, r.stderr

    v = doc["ief_version"]
    assert (d / "initiative" / ("state.yml.bak-%s" % v)).exists()
    assert leer_state(d)["ief_version"] == _version_motor()
    assert any(h["action"] == "MIGRATE" for h in leer_state(d)["history"])

    agents = (d / "AGENTS.md").read_bytes().decode("utf-8")
    assert agents.startswith("<!-- IEF:INICIO v%s" % _version_motor())
    if agents_viejo is not None:
        assert (d / ("AGENTS.md.bak-%s" % v)).read_bytes().decode("utf-8") == agents_viejo
        assert agents.endswith(agents_viejo), "lo que el proyecto escribio queda intacto"


def test_migrate_es_idempotente(viejo):
    d, _ = viejo
    correr("--mode", "migrate", "--yes", "--project-dir", str(d))
    antes = _foto(d)
    r = correr("--mode", "migrate", "--yes", "--project-dir", str(d))
    assert r.returncode == 0, r.stderr
    assert "al dia" in r.stdout
    assert _foto(d) == antes


def test_despues_de_migrar_el_proyecto_funciona_y_no_hay_avisos_de_version(viejo):
    d, _ = viejo
    correr("--mode", "migrate", "--yes", "--project-dir", str(d))
    for args in (("--mode", "status"), ("--mode", "check-gates")):
        r = correr(*args, "--project-dir", str(d))
        assert r.returncode == 0, (args, r.stdout, r.stderr)
        assert "upgrade-notes" not in r.stderr
    r = correr("--mode", "doctor", "--project-dir", str(d))
    assert r.returncode == 0, r.stdout
    assert "upgrade-notes" not in r.stdout and "seccion del motor" not in r.stdout
    r = correr("--mode", "log", "--project-dir", str(d), "--message", "sigue vivo")
    assert r.returncode == 0, r.stderr


# ─── Un motor viejo no escribe sobre un proyecto nuevo ───────────────────────

def test_un_motor_mas_viejo_se_niega_a_escribir(tmp_path):
    d = tmp_path / "proj"
    d.mkdir()
    correr("--mode", "init", "--project-dir", str(d), "--initiative-name", "P")
    state = leer_state(d)
    state["ief_version"] = "99.0.0"
    escribir_state(d, state)
    antes = (d / "initiative" / "state.yml").read_bytes()

    r = correr("--mode", "new-increment", "--project-dir", str(d), "--name", "x")
    assert r.returncode != 0
    assert "99.0.0" in r.stderr and "Actualiza el bundle" in r.stderr
    assert (d / "initiative" / "state.yml").read_bytes() == antes

    r = correr("--mode", "status", "--project-dir", str(d))
    assert r.returncode == 0, "leer si se puede"
    assert "Aviso" in r.stderr
    assert correr("--mode", "doctor", "--project-dir", str(d)).returncode != 0
    assert correr("--mode", "migrate", "--yes", "--project-dir", str(d)).returncode != 0


# ─── La seccion del motor en AGENTS.md ───────────────────────────────────────

def test_init_escribe_la_seccion_del_motor(tmp_path):
    d = tmp_path / "proj"
    d.mkdir()
    correr("--mode", "init", "--project-dir", str(d), "--preset", "research",
           "--initiative-name", "Memoria")
    texto = (d / "AGENTS.md").read_text(encoding="utf-8")
    assert texto.startswith("<!-- IEF:INICIO v%s" % _version_motor())
    assert texto.rstrip().endswith("<!-- IEF:FIN -->")
    assert "Memoria" in texto and "research" in texto
    assert "{{" not in texto, "no quedan marcadores de plantilla sin reemplazar"
    assert "upgrade" in texto, "la primera regla es revisar si el proyecto esta al dia"


def test_init_sobre_un_agents_existente_no_borra_nada(tmp_path):
    d = tmp_path / "proj"
    d.mkdir()
    propio = "# Reglas del equipo\r\n\r\n* No se suben datos al repo.\r\n"
    (d / "AGENTS.md").write_bytes(propio.encode("utf-8"))
    correr("--mode", "init", "--project-dir", str(d), "--initiative-name", "P")
    datos = (d / "AGENTS.md").read_bytes().decode("utf-8")
    assert datos.endswith(propio), "el texto propio sigue ahi, byte a byte"
    assert datos.startswith("<!-- IEF:INICIO")


def test_migrate_reemplaza_solo_lo_que_esta_entre_los_marcadores(tmp_path):
    d = tmp_path / "proj"
    d.mkdir()
    correr("--mode", "init", "--project-dir", str(d), "--initiative-name", "P")
    antes_txt = "Nota del proyecto, arriba.\r\n\r\n"
    despues_txt = "\r\n## Reglas propias\r\n\r\n* Una regla.\r\n"
    bloque_viejo = ("<!-- IEF:INICIO v0.14.9 — generado por verify_frame.py; no editar "
                    "dentro -->\r\ncontenido viejo\r\n<!-- IEF:FIN -->")
    (d / "AGENTS.md").write_bytes((antes_txt + bloque_viejo + despues_txt).encode("utf-8"))

    r = correr("--mode", "doctor", "--project-dir", str(d))
    assert "0.14.9" in r.stdout, "doctor avisa que la seccion es vieja"

    r = correr("--mode", "migrate", "--yes", "--project-dir", str(d))
    assert r.returncode == 0, r.stderr
    datos = (d / "AGENTS.md").read_bytes().decode("utf-8")
    assert datos.startswith(antes_txt) and datos.endswith(despues_txt)
    assert "contenido viejo" not in datos
    assert "IEF:INICIO v%s" % _version_motor() in datos


def test_doctor_avisa_si_falta_agents_o_su_seccion(tmp_path):
    d = tmp_path / "proj"
    d.mkdir()
    correr("--mode", "init", "--project-dir", str(d), "--initiative-name", "P")
    (d / "AGENTS.md").unlink()
    assert "no hay AGENTS.md" in correr("--mode", "doctor", "--project-dir", str(d)).stdout
    (d / "AGENTS.md").write_text("# a mano\n", encoding="utf-8")
    assert "seccion del motor" in correr("--mode", "doctor", "--project-dir", str(d)).stdout


# ─── El registro de cambios ──────────────────────────────────────────────────

@pytest.fixture
def motor():
    return cargar_modulo(CORE / "verify_frame.py", "verify_frame_cambios")


def test_cada_version_tiene_su_changelog_y_su_bloque_de_cambios(motor):
    assert motor.validar_cambios() == []
    assert motor.validar_changelog() == []
    versiones = {str(b["version"]) for b in motor.cargar_cambios()}
    assert _version_motor() in versiones


def test_cada_fixture_es_de_una_version_con_registro(motor):
    versiones = {str(b["version"]) for b in motor.cargar_cambios()}
    for f in FIXTURES:
        v = yaml.safe_load(f.read_text(encoding="utf-8"))["ief_version"]
        assert v in versiones, f"{f.name}: {v} no esta en core/cambios.yml"


def test_retirar_algo_sin_anunciarlo_antes_no_pasa_la_validacion(motor, monkeypatch):
    """La politica de ADR-002, hecha cumplir: nada se retira sin aviso previo."""
    bloques = [
        {"version": _version_motor(), "cambios": [{
            "id": "CHG-X-01", "tipo": "retirado", "afecta": ["flag"],
            "que_cambia": "se quita --foo", "que_hacer": "usa --bar", "migracion": None,
        }]},
    ]
    monkeypatch.setattr(motor, "cargar_cambios", lambda: bloques)
    errores = motor.validar_cambios()
    assert any("sin haberlo anunciado" in e for e in errores), errores


def test_un_cambio_sin_que_hacer_no_pasa_la_validacion(motor, monkeypatch):
    bloques = [{"version": _version_motor(), "cambios": [{
        "id": "CHG-X-01", "tipo": "añadido", "afecta": ["modo"], "que_cambia": "algo",
        "migracion": "no-existe",
    }]}]
    monkeypatch.setattr(motor, "cargar_cambios", lambda: bloques)
    errores = motor.validar_cambios()
    assert any("que_hacer" in e for e in errores)
    assert any("no-existe" in e for e in errores), "una migracion citada tiene que existir"


def test_los_modos_que_escriben_existen(motor):
    """Si se renombra un modo y no se actualiza la lista, la guardia deja de protegerlo."""
    import subprocess, sys
    ayuda = subprocess.run([sys.executable, str(CORE / "verify_frame.py"), "--help"],
                           capture_output=True, text=True).stdout
    for modo in motor.MODOS_QUE_ESCRIBEN:
        assert modo in ayuda, modo
