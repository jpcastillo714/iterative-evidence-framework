"""El motor de estado, ejercitado como lo usa un agente: por linea de comandos.

Cada test corre `verify_frame.py` de verdad sobre un proyecto temporal y comprueba
el codigo de salida y el estado resultante. Un test que no puede fallar no es un test.
"""

from __future__ import annotations

import yaml

from conftest import correr, leer_state, escribir_state, marcar_paso, sembrar_artefactos


# ─── init ────────────────────────────────────────────────────────────────────

def test_init_crea_estado_y_directorios(tmp_path):
    r = correr("--mode", "init", "--project-dir", str(tmp_path), "--preset", "research",
               "--layout", "numbered", "--initiative-name", "Tesis")
    assert r.returncode == 0, r.stderr
    state = leer_state(tmp_path)
    assert state["initiative"]["preset"] == "research"
    assert state["initiative"]["layout"] == "numbered"
    assert state["increments"] == []
    assert state["focus"] is None
    # Las rutas salen del LAYOUT, no del preset: es lo que permite que el mismo
    # preset se use con carpetas numeradas o planas segun lo que pida el proyecto.
    assert (tmp_path / "00_admin").is_dir()
    assert (tmp_path / "07_documento").is_dir()


def test_el_mismo_preset_con_el_otro_layout_da_otras_rutas(tmp_path):
    r = correr("--mode", "init", "--project-dir", str(tmp_path), "--preset", "research",
               "--layout", "flat", "--initiative-name", "Tesis")
    assert r.returncode == 0, r.stderr
    assert (tmp_path / "admin").is_dir() and (tmp_path / "docs").is_dir()
    assert not (tmp_path / "00_admin").exists()


def test_init_crea_la_constitucion(tmp_path):
    correr("--mode", "init", "--project-dir", str(tmp_path), "--preset", "generic",
           "--initiative-name", "P")
    assert (tmp_path / "initiative" / "specs" / "constitution.md").exists()


def test_init_no_pisa_un_estado_existente(tmp_path):
    correr("--mode", "init", "--project-dir", str(tmp_path))
    r = correr("--mode", "init", "--project-dir", str(tmp_path))
    assert r.returncode != 0
    assert "force-overwrite" in r.stderr


def test_init_con_preset_inexistente_falla(tmp_path):
    r = correr("--mode", "init", "--project-dir", str(tmp_path), "--preset", "inventado")
    assert r.returncode == 2
    assert "no existe el preset" in r.stderr


# ─── Avance por el ciclo ─────────────────────────────────────────────────────

def test_no_avanza_desde_un_paso_sin_terminar(proyecto):
    r = correr("--mode", "advance", "--project-dir", str(proyecto))
    assert r.returncode != 0
    assert "IN_PROGRESS" in r.stderr


def test_no_avanza_desde_una_compuerta_solo_completada(proyecto):
    """La compuerta humana como condicion mecanica, no como recordatorio."""
    marcar_paso(proyecto, "1_charter", "COMPLETED")
    r = correr("--mode", "advance", "--project-dir", str(proyecto))
    assert r.returncode != 0
    assert "aprobacion" in r.stderr


def test_avanza_tras_aprobar(proyecto):
    marcar_paso(proyecto, "1_charter", "COMPLETED")
    assert correr("--mode", "approve-step", "--project-dir", str(proyecto),
                  "--by", "tester").returncode == 0
    r = correr("--mode", "advance", "--project-dir", str(proyecto))
    assert r.returncode == 0
    state = leer_state(proyecto)
    assert state["increments"][0]["current_step"] == "2"
    assert state["increments"][0]["steps"]["2_empirical_inspection"] == "IN_PROGRESS"


def test_la_aprobacion_queda_registrada_con_autor_y_fecha(proyecto):
    marcar_paso(proyecto, "1_charter", "COMPLETED")
    correr("--mode", "approve-step", "--project-dir", str(proyecto), "--by", "tester")
    inc = leer_state(proyecto)["increments"][0]
    assert inc["approvals"]["1_charter"]["approved_by"] == "tester"
    assert inc["approvals"]["1_charter"]["approved_at"].endswith("+00:00"), "timestamp UTC explicito"


def test_no_se_aprueba_un_paso_sin_compuerta(proyecto):
    marcar_paso(proyecto, "1_charter", "APPROVED")
    correr("--mode", "advance", "--project-dir", str(proyecto))
    marcar_paso(proyecto, "2_empirical_inspection", "COMPLETED")
    r = correr("--mode", "approve-step", "--project-dir", str(proyecto))
    assert r.returncode != 0
    assert "no tiene compuerta" in r.stderr


def test_el_ciclo_completo_llega_al_paso_7(proyecto):
    """Regresion del bug que dejaba el ciclo trabado en el paso 2 para siempre."""
    sembrar_artefactos(proyecto)
    claves = ["1_charter", "2_empirical_inspection", "3_data_contracts", "4_rules",
              "5_acceptance_tests", "6_implementation"]
    for clave in claves:
        marcar_paso(proyecto, clave, "COMPLETED")
        correr("--mode", "approve-step", "--project-dir", str(proyecto), "--by", "t")
        r = correr("--mode", "advance", "--project-dir", str(proyecto))
        assert r.returncode == 0, f"atascado en {clave}: {r.stderr}"
    assert leer_state(proyecto)["increments"][0]["current_step"] == "7"


# ─── Compuertas para CI ──────────────────────────────────────────────────────

def test_check_gates_falla_si_una_compuerta_quedo_sin_aprobar(proyecto):
    marcar_paso(proyecto, "1_charter", "COMPLETED")
    r = correr("--mode", "check-gates", "--project-dir", str(proyecto))
    assert r.returncode == 1
    assert "sin APPROVED" in r.stdout


def test_check_gates_pasa_con_todo_aprobado(proyecto):
    marcar_paso(proyecto, "1_charter", "APPROVED")
    r = correr("--mode", "check-gates", "--project-dir", str(proyecto))
    assert r.returncode == 0


def test_check_gates_no_castiga_pasos_aun_en_curso(proyecto):
    """Un paso PENDING no es una compuerta violada: es trabajo no empezado."""
    r = correr("--mode", "check-gates", "--project-dir", str(proyecto))
    assert r.returncode == 0


# ─── verify-step ─────────────────────────────────────────────────────────────

def test_verify_step_detecta_artefacto_ausente(proyecto):
    (proyecto / "initiative" / "increments" / "001_demo" / "charter.md").unlink()
    r = correr("--mode", "verify-step", "--project-dir", str(proyecto), "--step", "1")
    assert r.returncode != 0
    assert "charter.md existe" in r.stdout


def test_verify_step_detecta_test_huerfano(proyecto):
    sembrar_artefactos(proyecto)
    inc = proyecto / "initiative" / "increments" / "001_demo"
    inc.joinpath("acceptance-tests.yml").write_text(yaml.safe_dump({
        "tests": [{"test_id": "TST-ACC-009", "linked_rule": "BR-404",
                   "given": "g", "when": "w", "then": "t"}]
    }), encoding="utf-8")
    r = correr("--mode", "verify-step", "--project-dir", str(proyecto), "--step", "5")
    assert r.returncode != 0
    assert "TST-ACC-009" in r.stdout


def test_verify_step_detecta_compuerta_sin_aprobar(proyecto):
    marcar_paso(proyecto, "1_charter", "COMPLETED")
    r = correr("--mode", "verify-step", "--project-dir", str(proyecto), "--step", "1")
    assert r.returncode != 0
    assert "requiere APPROVED" in r.stdout


# ─── rewind ──────────────────────────────────────────────────────────────────

def test_rewind_exige_razon(proyecto):
    r = correr("--mode", "rewind", "--project-dir", str(proyecto), "--to-step", "1")
    assert r.returncode != 0
    assert "reason" in r.stderr


def test_rewind_marca_los_pasos_y_revoca_la_aprobacion(proyecto):
    marcar_paso(proyecto, "1_charter", "COMPLETED")
    correr("--mode", "approve-step", "--project-dir", str(proyecto), "--by", "t")
    correr("--mode", "advance", "--project-dir", str(proyecto))
    marcar_paso(proyecto, "2_empirical_inspection", "COMPLETED")
    correr("--mode", "advance", "--project-dir", str(proyecto))

    r = correr("--mode", "rewind", "--project-dir", str(proyecto),
               "--to-step", "1", "--reason", "el contrato no cuadra con los datos")
    assert r.returncode == 0
    inc = leer_state(proyecto)["increments"][0]
    assert inc["current_step"] == "1"
    assert inc["steps"]["1_charter"] == "NEEDS_REVISION"
    assert "1_charter" not in inc.get("approvals", {}), "la aprobacion previa debe revocarse"


def test_no_se_puede_rewind_hacia_adelante(proyecto):
    r = correr("--mode", "rewind", "--project-dir", str(proyecto),
               "--to-step", "5", "--reason", "x")
    assert r.returncode != 0


# ─── merge-increment ─────────────────────────────────────────────────────────

def test_merge_rechaza_compuertas_sin_aprobar(proyecto):
    sembrar_artefactos(proyecto)
    marcar_paso(proyecto, "1_charter", "COMPLETED")
    r = correr("--mode", "merge-increment", "--project-dir", str(proyecto),
               "--increment", "001_demo")
    assert r.returncode != 0
    assert "compuertas sin aprobar" in r.stderr


def test_merge_promueve_a_la_especificacion_viva(proyecto):
    """Cierra el problema de origen: reglas duplicadas sin fuente unica de verdad."""
    sembrar_artefactos(proyecto)
    for clave in ("1_charter", "4_rules", "5_acceptance_tests"):
        marcar_paso(proyecto, clave, "APPROVED")
    r = correr("--mode", "merge-increment", "--project-dir", str(proyecto),
               "--increment", "001_demo")
    assert r.returncode == 0, r.stderr

    specs = proyecto / "initiative" / "specs" / "rules.yml"
    assert specs.exists()
    doc = yaml.safe_load(specs.read_text(encoding="utf-8"))
    assert doc["rules"][0]["id"] == "RUL-001-001"
    assert doc["rules"][0]["_origen"]["increment"] == "001_demo", "cada regla lleva su procedencia"
    assert leer_state(proyecto)["increments"][0]["status"] == "MERGED"


def test_merge_dry_run_no_escribe(proyecto):
    sembrar_artefactos(proyecto)
    for clave in ("1_charter", "4_rules", "5_acceptance_tests"):
        marcar_paso(proyecto, clave, "APPROVED")
    correr("--mode", "merge-increment", "--project-dir", str(proyecto),
           "--increment", "001_demo", "--dry-run")
    assert not (proyecto / "initiative" / "specs" / "rules.yml").exists()
    assert leer_state(proyecto)["increments"][0]["status"] == "ACTIVE"


def test_merge_de_un_segundo_incremento_actualiza_la_regla(proyecto):
    sembrar_artefactos(proyecto)
    for clave in ("1_charter", "4_rules", "5_acceptance_tests"):
        marcar_paso(proyecto, clave, "APPROVED")
    correr("--mode", "merge-increment", "--project-dir", str(proyecto), "--increment", "001_demo")

    state = leer_state(proyecto)
    state["increments"].append({
        "id": "002", "slug": "002_ajuste", "name": "Ajuste", "type": "build",
        "status": "ACTIVE", "current_step": "7",
        "steps": {"1_charter": "APPROVED", "4_rules": "APPROVED",
                  "5_acceptance_tests": "APPROVED"},
    })
    escribir_state(proyecto, state)
    d2 = proyecto / "initiative" / "increments" / "002_ajuste"
    d2.mkdir(parents=True)
    (d2 / "rules.yml").write_text(yaml.safe_dump({"rules": [
        {"id": "RUL-001-001", "description": "Regla CORREGIDA", "priority": "critical", "status": "approved"},
        {"id": "RUL-001-002", "description": "Regla nueva", "priority": "low", "status": "draft"},
    ]}), encoding="utf-8")

    r = correr("--mode", "merge-increment", "--project-dir", str(proyecto), "--increment", "002_ajuste")
    assert r.returncode == 0, r.stderr
    doc = yaml.safe_load((proyecto / "initiative" / "specs" / "rules.yml").read_text(encoding="utf-8"))
    reglas = {r["id"]: r for r in doc["rules"]}
    assert reglas["RUL-001-001"]["description"] == "Regla CORREGIDA"
    assert reglas["RUL-001-001"]["_origen"]["increment"] == "002_ajuste"
    assert "RUL-001-002" in reglas


# ─── Robustez del estado ─────────────────────────────────────────────────────

def test_status_json_es_consumible_por_ci(proyecto):
    import json
    r = correr("--mode", "status", "--project-dir", str(proyecto), "--json")
    assert r.returncode == 0
    doc = json.loads(r.stdout)
    assert doc["preset"] == "generic"
    assert doc["increments"][0]["steps"][0]["human_gate"] is True


def test_estado_invalido_es_rechazado(proyecto):
    r = correr("--mode", "set-status", "--project-dir", str(proyecto),
               "--increment", "001_demo", "--status", "INVENTADO")
    assert r.returncode != 0


def test_pausar_exige_razon(proyecto):
    r = correr("--mode", "set-status", "--project-dir", str(proyecto),
               "--increment", "001_demo", "--status", "PAUSED")
    assert r.returncode != 0


def test_state_yml_no_queda_corrupto_tras_muchas_escrituras(proyecto):
    """La escritura es atomica: se escribe a un temporal y se reemplaza."""
    for _ in range(10):
        correr("--mode", "set-status", "--project-dir", str(proyecto),
               "--increment", "001_demo", "--status", "ACTIVE")
    state = leer_state(proyecto)
    assert state["increments"][0]["status"] == "ACTIVE"
    tmp = list((proyecto / "initiative").glob(".state-*.tmp"))
    assert not tmp, f"quedaron temporales sin limpiar: {tmp}"
