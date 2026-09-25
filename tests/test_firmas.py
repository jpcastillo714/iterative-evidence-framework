"""Una firma dice «aprobe ESTO» (ADR-001).

Hasta 0.14.0 una compuerta guardaba quien firmo y cuando, pero no que. Reproducido: un
proceso sin terminal firmaba a nombre de otra persona, el artefacto cambiaba despues y
`check-gates` respondia que todo estaba aprobado. Y `approve-step --increment X` firmaba
el incremento enfocado, no X.

Estos tests fijan lo que se decidio en
docs/decisiones/ADR-001-firma-humana-ligada-al-contenido.md.
"""

from __future__ import annotations

import pytest

from conftest import BUNDLE, CORE, cargar_modulo, correr, escribir_state, leer_state

CHARTER = BUNDLE / "core" / "templates" / "charter-template.md"


def _proyecto(tmp_path, nombre="alfa"):
    """Un proyecto con un incremento `prototype` cuyo paso 1 (con compuerta) esta COMPLETED."""
    d = tmp_path / "proj"
    d.mkdir(exist_ok=True)
    r = correr("--mode", "init", "--project-dir", str(d), "--preset", "generic",
               "--initiative-name", "P")
    assert r.returncode == 0, r.stderr
    _abrir(d, nombre)
    return d


def _abrir(d, nombre):
    r = correr("--mode", "new-increment", "--project-dir", str(d), "--type", "prototype",
               "--name", nombre)
    assert r.returncode == 0, r.stderr
    slug = leer_state(d)["focus"]
    (d / "initiative" / "increments" / slug / "charter.md").write_text(
        CHARTER.read_text(encoding="utf-8"), encoding="utf-8")
    r = correr("--mode", "complete-step", "--project-dir", str(d), "--increment", slug)
    assert r.returncode == 0, r.stdout + r.stderr
    return slug


def _charter(d, slug="001_alfa"):
    return d / "initiative" / "increments" / slug / "charter.md"


def _firmar(d, *extra):
    return correr("--mode", "approve-step", "--project-dir", str(d), "--by", "Ana", *extra)


# ─── La huella ───────────────────────────────────────────────────────────────

def test_la_firma_guarda_la_huella_y_el_canal(tmp_path):
    d = _proyecto(tmp_path)
    r = _firmar(d)
    assert r.returncode == 0, r.stderr
    firma = leer_state(d)["increments"][0]["approvals"]["1_charter"]
    assert firma["artifact_sha256"].startswith("sha256:")
    assert firma["artifact"] == "initiative/increments/001_alfa/charter.md"
    assert firma["approved_via"] == "declared", "sin terminal, la firma es declarada"


def test_un_artefacto_que_cambia_despues_de_firmado_vence_la_firma(tmp_path):
    """La reproduccion del ADR: antes, check-gates respondia [OK]."""
    d = _proyecto(tmp_path)
    _firmar(d)
    with open(_charter(d), "a", encoding="utf-8") as f:
        f.write("\nCriterio de exito: CUALQUIER resultado sirve.\n")

    r = correr("--mode", "check-gates", "--project-dir", str(d))
    assert r.returncode == 1, r.stdout
    assert "001_alfa" in r.stdout and "paso 1" in r.stdout
    assert "cambio despues de la firma" in r.stdout
    assert "--increment 001_alfa --step 1" in r.stdout, "debe decir como resolverlo"

    r = correr("--mode", "doctor", "--project-dir", str(d))
    assert r.returncode == 1
    assert "aprobacion vencida" in r.stdout


def test_advance_no_pasa_sobre_una_firma_vencida(tmp_path):
    d = _proyecto(tmp_path)
    _firmar(d)
    with open(_charter(d), "a", encoding="utf-8") as f:
        f.write("\notra cosa\n")
    r = correr("--mode", "advance", "--project-dir", str(d))
    assert r.returncode != 0
    assert "vencida" in r.stderr
    assert leer_state(d)["increments"][0]["current_step"] == "1"


def test_volver_a_firmar_un_paso_vencido_conserva_las_dos_firmas(tmp_path):
    d = _proyecto(tmp_path)
    _firmar(d)
    primera = leer_state(d)["increments"][0]["approvals"]["1_charter"]["artifact_sha256"]
    with open(_charter(d), "a", encoding="utf-8") as f:
        f.write("\nrevisado\n")

    r = _firmar(d, "--increment", "001_alfa", "--step", "1")
    assert r.returncode == 0, r.stderr
    assert "nueva firma" in r.stdout
    assert correr("--mode", "check-gates", "--project-dir", str(d)).returncode == 0

    firmas = [h for h in leer_state(d)["history"] if h["action"] == "APPROVE_STEP"]
    assert len(firmas) == 2, "el historial conserva ambas"
    assert firmas[1]["resign"] is True
    assert firmas[1]["previous_sha256"] == primera
    assert firmas[1]["artifact_sha256"] != primera


def test_una_firma_vigente_no_se_vuelve_a_firmar(tmp_path):
    d = _proyecto(tmp_path)
    _firmar(d)
    r = _firmar(d, "--step", "1")
    assert r.returncode != 0
    assert "vigente" in r.stderr


def test_cambiar_solo_los_fines_de_linea_no_vence_la_firma(tmp_path):
    """Clonar en otro sistema operativo convierte LF y CRLF: eso no es cambiar el contenido."""
    d = _proyecto(tmp_path)
    _firmar(d)
    ruta = _charter(d)
    datos = ruta.read_bytes().replace(b"\r\n", b"\n")
    ruta.write_bytes(datos.replace(b"\n", b"\r\n"))
    assert correr("--mode", "check-gates", "--project-dir", str(d)).returncode == 0


def test_status_json_informa_el_estado_de_la_firma(tmp_path):
    import json
    d = _proyecto(tmp_path)
    _firmar(d)
    paso = lambda: json.loads(correr("--mode", "status", "--json", "--project-dir",
                                     str(d)).stdout)["increments"][0]["steps"][0]
    assert paso()["signature"] == "vigente"
    with open(_charter(d), "a", encoding="utf-8") as f:
        f.write("x")
    assert paso()["signature"] == "vencida"


# ─── Firmas anteriores a 0.15.0 ──────────────────────────────────────────────

def test_una_firma_sin_huella_sigue_valiendo_y_doctor_la_identifica(tmp_path):
    """Compatibilidad (ADR-002): las firmas de 0.14.0 no se invalidan."""
    d = _proyecto(tmp_path)
    _firmar(d)
    state = leer_state(d)
    firma = state["increments"][0]["approvals"]["1_charter"]
    for campo in ("artifact_sha256", "approved_via", "artifact"):
        firma.pop(campo)
    escribir_state(d, state)

    r = correr("--mode", "check-gates", "--project-dir", str(d))
    assert r.returncode == 0, r.stdout
    assert "sin huella" in r.stdout
    r = correr("--mode", "doctor", "--project-dir", str(d))
    assert r.returncode == 0, r.stdout
    assert "sin huella" in r.stdout


def test_una_firma_sin_huella_se_puede_certificar_volviendo_a_firmar(tmp_path):
    d = _proyecto(tmp_path)
    _firmar(d)
    state = leer_state(d)
    state["increments"][0]["approvals"]["1_charter"].pop("artifact_sha256")
    escribir_state(d, state)
    r = _firmar(d, "--step", "1")
    assert r.returncode == 0, r.stderr
    assert "artifact_sha256" in leer_state(d)["increments"][0]["approvals"]["1_charter"]


# ─── El canal ────────────────────────────────────────────────────────────────

def test_doctor_resume_las_firmas_declaradas(tmp_path):
    d = _proyecto(tmp_path)
    _firmar(d)
    r = correr("--mode", "doctor", "--project-dir", str(d))
    assert r.returncode == 0, r.stdout
    assert "1 firma(s) declaradas" in r.stdout
    assert "gate-policy" in r.stdout, "debe decir como exigir la firma interactiva"


def test_un_proyecto_que_exige_terminal_rechaza_la_firma_declarada(tmp_path):
    d = _proyecto(tmp_path)
    r = correr("--mode", "gate-policy", "--project-dir", str(d), "--require-interactive", "on")
    assert r.returncode == 0, r.stderr
    assert leer_state(d)["initiative"]["gates"]["require_interactive"] is True

    r = _firmar(d)
    assert r.returncode != 0
    assert "terminal" in r.stderr and "No lo firmes tu" in r.stderr
    assert leer_state(d)["increments"][0]["steps"]["1_charter"] == "COMPLETED"


def test_sin_terminal_no_se_puede_dejar_de_exigir_la_firma_interactiva(tmp_path):
    """Si un programa pudiera apagarla, podria apagarla y despues firmar en nombre de otro."""
    d = _proyecto(tmp_path)
    correr("--mode", "gate-policy", "--project-dir", str(d), "--require-interactive", "on")
    r = correr("--mode", "gate-policy", "--project-dir", str(d), "--require-interactive", "off")
    assert r.returncode != 0
    assert leer_state(d)["initiative"]["gates"]["require_interactive"] is True


@pytest.fixture
def motor(monkeypatch):
    """El motor importado, para simular una terminal (un subproceso no puede tenerla)."""
    return cargar_modulo(CORE / "verify_frame.py", "verify_frame_firmas")


def test_en_una_terminal_la_firma_se_confirma_escribiendo_el_slug(tmp_path, motor, monkeypatch):
    d = _proyecto(tmp_path)
    monkeypatch.setattr(motor, "_hay_terminal", lambda: True)
    monkeypatch.setattr("builtins.input", lambda *_: "001_alfa")
    motor.cmd_approve_step(d, "Ana")
    assert leer_state(d)["increments"][0]["approvals"]["1_charter"]["approved_via"] == "interactive"


def test_en_una_terminal_un_slug_equivocado_cancela_la_firma(tmp_path, motor, monkeypatch):
    d = _proyecto(tmp_path)
    monkeypatch.setattr(motor, "_hay_terminal", lambda: True)
    monkeypatch.setattr("builtins.input", lambda *_: "si")
    with pytest.raises(SystemExit):
        motor.cmd_approve_step(d, "Ana")
    assert leer_state(d)["increments"][0]["steps"]["1_charter"] == "COMPLETED"


# ─── --increment (ESTADO 5.1) ────────────────────────────────────────────────

def test_approve_step_firma_el_incremento_pedido_y_no_el_enfocado(tmp_path):
    d = _proyecto(tmp_path)
    _abrir(d, "beta")                               # el foco queda en 002_beta
    assert leer_state(d)["focus"] == "002_beta"

    r = _firmar(d, "--increment", "001_alfa")
    assert r.returncode == 0, r.stderr
    assert "001_alfa" in r.stdout, "la salida nombra el incremento firmado"
    incs = {i["slug"]: i for i in leer_state(d)["increments"]}
    assert incs["001_alfa"]["steps"]["1_charter"] == "APPROVED"
    assert incs["002_beta"]["steps"]["1_charter"] == "COMPLETED"


def test_advance_avanza_el_incremento_pedido_y_no_el_enfocado(tmp_path):
    d = _proyecto(tmp_path)
    _firmar(d)
    _abrir(d, "beta")
    r = correr("--mode", "advance", "--project-dir", str(d), "--increment", "001_alfa")
    assert r.returncode == 0, r.stderr
    assert "001_alfa" in r.stdout
    incs = {i["slug"]: i for i in leer_state(d)["increments"]}
    assert incs["001_alfa"]["current_step"] == "2"
    assert incs["002_beta"]["current_step"] == "1"


def test_un_increment_inexistente_es_un_error_y_no_cae_sobre_el_foco(tmp_path):
    d = _proyecto(tmp_path)
    for modo in ("approve-step", "advance"):
        r = correr("--mode", modo, "--project-dir", str(d), "--increment", "009_no", "--by", "A")
        assert r.returncode != 0, modo
        assert "009_no" in r.stderr
    assert leer_state(d)["increments"][0]["steps"]["1_charter"] == "COMPLETED"
