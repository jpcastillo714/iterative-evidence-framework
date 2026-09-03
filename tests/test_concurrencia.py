"""Varios frentes de trabajo a la vez, sin pisarse.

El caos que estos tests previenen es real y silencioso: antes, activar un segundo
incremento robaba el puntero `active_increment` sin decir nada, y a partir de ahi
`advance`, `approve-step` y `rewind` caian sobre un incremento distinto del que creias
estar trabajando. Nada fallaba; simplemente avanzabas el equivocado.
"""

from __future__ import annotations

import yaml

from conftest import correr


def _init(tmp_path, preset="product", layout="flat"):
    d = tmp_path / "proj"
    d.mkdir(exist_ok=True)
    r = correr("--mode", "init", "--project-dir", str(d), "--preset", preset,
               "--layout", layout, "--initiative-name", "P")
    assert r.returncode == 0, r.stdout + r.stderr
    return d


def _nuevo(d, tipo, nombre):
    r = correr("--mode", "new-increment", "--project-dir", str(d),
               "--type", tipo, "--name", nombre)
    assert r.returncode == 0, r.stdout + r.stderr
    return r


def _estado(d):
    return yaml.safe_load((d / "initiative" / "state.yml").read_text(encoding="utf-8"))


# ─── Foco frente a ACTIVE ────────────────────────────────────────────────────

def test_pueden_convivir_varios_activos_con_un_solo_foco(tmp_path):
    d = _init(tmp_path)
    _nuevo(d, "build", "Ingesta")
    _nuevo(d, "prototype", "Panel")

    st = _estado(d)
    activos = [i for i in st["increments"] if i["status"] == "ACTIVE"]
    assert len(activos) == 2, "dos frentes abiertos deben poder coexistir"
    assert st["focus"] == "002_panel", "el foco es uno solo, el ultimo abierto"


def test_activar_otro_incremento_no_roba_el_foco(tmp_path):
    """La regresion principal de este rediseno."""
    d = _init(tmp_path)
    _nuevo(d, "build", "Uno")
    _nuevo(d, "prototype", "Dos")          # el foco queda en 002

    r = correr("--mode", "set-status", "--project-dir", str(d),
               "--increment", "001_uno", "--status", "ACTIVE")
    assert r.returncode == 0
    assert _estado(d)["focus"] == "002_dos", "ACTIVE no debe mover el foco por su cuenta"
    assert "--mode focus" in r.stdout, "y debe decir como moverlo si es lo que querias"


def test_con_focus_explicito_si_se_mueve(tmp_path):
    d = _init(tmp_path)
    _nuevo(d, "build", "Uno")
    _nuevo(d, "prototype", "Dos")

    correr("--mode", "set-status", "--project-dir", str(d),
           "--increment", "001_uno", "--status", "ACTIVE", "--focus")
    assert _estado(d)["focus"] == "001_uno"


def test_los_comandos_sin_increment_operan_sobre_el_foco(tmp_path):
    d = _init(tmp_path)
    _nuevo(d, "build", "Uno")
    _nuevo(d, "build", "Dos")             # foco -> 002

    r = correr("--mode", "status", "--project-dir", str(d), "--json")
    assert yaml.safe_load(r.stdout)["focus"] == "002_dos"


def test_al_cerrar_el_foco_se_propone_un_sucesor(tmp_path):
    """Antes quedaba en None y el siguiente comando fallaba con 'no encontrado'."""
    d = _init(tmp_path)
    _nuevo(d, "build", "Uno")
    _nuevo(d, "build", "Dos")             # foco -> 002

    correr("--mode", "set-status", "--project-dir", str(d),
           "--increment", "002_dos", "--status", "ABANDONED", "--reason", "descartado")
    assert _estado(d)["focus"] == "001_uno"


def test_el_limite_de_frentes_avisa_pero_no_bloquea(tmp_path):
    d = _init(tmp_path)
    for i in range(4):
        r = _nuevo(d, "build", f"Frente {i}")
    assert "limite blando" in r.stdout
    assert len([i for i in _estado(d)["increments"] if i["status"] == "ACTIVE"]) == 4


# ─── Bloqueos ────────────────────────────────────────────────────────────────

def test_bloqueo_externo_guarda_tipo_motivo_y_fecha(tmp_path):
    """El caso real: dependo de que otro equipo me pase datos."""
    d = _init(tmp_path)
    _nuevo(d, "build", "Ingesta")

    r = correr("--mode", "set-status", "--project-dir", str(d),
               "--increment", "001_ingesta", "--status", "BLOCKED",
               "--blocked-kind", "external", "--reason", "esperando extracto de BI",
               "--expected", "2099-01-01")
    assert r.returncode == 0

    bloqueo = _estado(d)["increments"][0]["blocked"]
    assert bloqueo["kind"] == "external"
    assert bloqueo["reason"] == "esperando extracto de BI"
    assert bloqueo["expected"] == "2099-01-01"
    assert bloqueo["since"], "sin fecha de inicio no se puede saber cuanto lleva esperando"


def test_bloqueo_por_incremento_inexistente_se_rechaza(tmp_path):
    d = _init(tmp_path)
    _nuevo(d, "build", "Uno")
    r = correr("--mode", "set-status", "--project-dir", str(d),
               "--increment", "001_uno", "--status", "BLOCKED",
               "--blocked-kind", "increment", "--blocked-on", "999_fantasma",
               "--reason", "x")
    assert r.returncode != 0
    assert "no existe" in r.stderr and "external" in r.stderr


def test_la_dependencia_circular_se_detecta(tmp_path):
    """A bloquea B bloquea A: ninguno se desbloquearia nunca."""
    d = _init(tmp_path)
    _nuevo(d, "build", "Uno")
    _nuevo(d, "build", "Dos")

    correr("--mode", "set-status", "--project-dir", str(d), "--increment", "002_dos",
           "--status", "BLOCKED", "--blocked-kind", "increment",
           "--blocked-on", "001_uno", "--reason", "necesita el esquema")
    r = correr("--mode", "set-status", "--project-dir", str(d), "--increment", "001_uno",
               "--status", "BLOCKED", "--blocked-kind", "increment",
               "--blocked-on", "002_dos", "--reason", "circular")
    assert r.returncode != 0
    assert "circular" in r.stderr


def test_al_cerrar_el_bloqueante_avisa_a_quien_esperaba(tmp_path):
    d = _init(tmp_path)
    _nuevo(d, "build", "Base")
    _nuevo(d, "build", "Encima")

    correr("--mode", "set-status", "--project-dir", str(d), "--increment", "002_encima",
           "--status", "BLOCKED", "--blocked-kind", "increment",
           "--blocked-on", "001_base", "--reason", "necesita el esquema")
    r = correr("--mode", "set-status", "--project-dir", str(d), "--increment", "001_base",
               "--status", "COMPLETED")
    assert "002_encima" in r.stdout, "debe avisar de quien estaba esperando"
    # Pero no lo desbloquea solo: reanudar es una decision humana.
    assert _estado(d)["increments"][1]["status"] == "BLOCKED"


def test_paused_y_blocked_son_estados_distintos(tmp_path):
    """PAUSED es voluntario; BLOCKED es forzado. Solo uno depende de un tercero."""
    d = _init(tmp_path)
    _nuevo(d, "build", "Uno")

    correr("--mode", "set-status", "--project-dir", str(d), "--increment", "001_uno",
           "--status", "PAUSED", "--reason", "cambio la prioridad")
    inc = _estado(d)["increments"][0]
    assert inc["paused"]["reason"] == "cambio la prioridad"
    assert "blocked" not in inc

    correr("--mode", "set-status", "--project-dir", str(d), "--increment", "001_uno",
           "--status", "BLOCKED", "--blocked-kind", "decision", "--reason", "falta decidir")
    inc = _estado(d)["increments"][0]
    assert "paused" not in inc, "los dos estados no pueden coexistir"
    assert inc["blocked"]["kind"] == "decision"


def test_pausar_sin_motivo_se_rechaza(tmp_path):
    d = _init(tmp_path)
    _nuevo(d, "build", "Uno")
    r = correr("--mode", "set-status", "--project-dir", str(d),
               "--increment", "001_uno", "--status", "PAUSED")
    assert r.returncode != 0, "dentro de un mes nadie recuerda por que se pauso"


# ─── doctor ──────────────────────────────────────────────────────────────────

def test_doctor_sin_hallazgos_sale_limpio(tmp_path):
    d = _init(tmp_path)
    _nuevo(d, "build", "Uno")
    r = correr("--mode", "doctor", "--project-dir", str(d))
    assert r.returncode == 0
    assert "Sin hallazgos" in r.stdout


def test_doctor_detecta_el_proyecto_detenido(tmp_path):
    """Cada bloqueo se decide por separado; que no quede ninguno vivo no se ve."""
    d = _init(tmp_path)
    _nuevo(d, "build", "Uno")
    correr("--mode", "set-status", "--project-dir", str(d), "--increment", "001_uno",
           "--status", "BLOCKED", "--blocked-kind", "external", "--reason", "x")
    r = correr("--mode", "doctor", "--project-dir", str(d))
    assert r.returncode != 0
    assert "detenidos" in r.stdout


def test_doctor_avisa_de_completed_sin_promover(tmp_path):
    d = _init(tmp_path)
    _nuevo(d, "build", "Uno")
    correr("--mode", "set-status", "--project-dir", str(d), "--increment", "001_uno",
           "--status", "COMPLETED")
    r = correr("--mode", "doctor", "--project-dir", str(d))
    assert "merge-increment" in r.stdout


def test_doctor_avisa_de_compuerta_sin_aprobar(tmp_path):
    d = _init(tmp_path)
    _nuevo(d, "build", "Uno")
    st = _estado(d)
    st["increments"][0]["steps"]["1_charter"] = "COMPLETED"
    (d / "initiative" / "state.yml").write_text(
        yaml.safe_dump(st, sort_keys=False, allow_unicode=True), encoding="utf-8"
    )
    r = correr("--mode", "doctor", "--project-dir", str(d))
    assert r.returncode != 0
    assert "sin aprobar" in r.stdout


# ─── Base de reglas ──────────────────────────────────────────────────────────

def test_el_incremento_anota_contra_que_reglas_se_abrio(tmp_path):
    d = _init(tmp_path)
    _nuevo(d, "build", "Uno")
    assert "rules_base" in _estado(d)["increments"][0]


def test_reanudar_avisa_si_las_reglas_cambiaron(tmp_path):
    """Un incremento pausado dos meses despierta en otro mundo y nadie se lo dice."""
    d = _init(tmp_path)
    _nuevo(d, "build", "Uno")
    _nuevo(d, "build", "Dos")

    # El proyecto adquiere reglas mientras 001 estaba parado.
    (d / "initiative" / "specs" / "rules.yml").write_text(
        "rules:\n  - id: RUL-002-001\n    statement: Algo nuevo\n    status: active\n",
        encoding="utf-8",
    )
    r = correr("--mode", "focus", "--project-dir", str(d), "--increment", "001_uno")
    assert "reglas del proyecto cambiaron" in r.stdout
    assert "RUL-002-001" in r.stdout
