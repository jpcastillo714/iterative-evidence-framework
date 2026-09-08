"""Lo que el proyecto aprende de fuera.

Todo el ciclo de vida de las reglas daba por hecho que una verdad del dominio se
DESCUBRE trabajando. Pero la mitad de lo que cambia un proyecto no se descubre: llega.
Una reunion donde el proveedor de los datos dice que el instrumento se recalibro. Un
correo que retira un permiso. Un documento que contradice el charter.

Eso no era una regla —nadie lo dedujo— ni una tarea, y no tenia donde ir: o se enterraba
en `worklog.md` sin id ni forma de citarlo, o se convertia en `RUL-`, que exige un
incremento entero para registrar algo que ya es cierto. El rol `admin` («actas de
reunion») era solo una carpeta que el motor no leia.

Lo caro nunca fue perder el acta. Es que una reunion invalide tres afirmaciones y las
tres sigan vigentes seis meses despues porque nadie volvio a mirarlas. Por eso lo que
importa de esto no es el registro: es que `doctor` no calle mientras la deuda siga
abierta.
"""

from __future__ import annotations

import yaml

from conftest import correr

REGLA = {"rules": [{
    "id": "RUL-001-001",
    "statement": "La cadencia de 20 s es la unica disponible",
    "rationale": "Es lo que dice la documentacion nominal del PLC",
    "applies_to": "telemetria.cadencia",
    "scope": "project",
    "status": "proposed",
}]}


def _proyecto(tmp_path, con_regla=True):
    d = tmp_path / "proj"
    d.mkdir(parents=True, exist_ok=True)
    correr("--mode", "init", "--project-dir", str(d), "--preset", "research",
           "--layout", "flat", "--initiative-name", "M")
    correr("--mode", "new-increment", "--project-dir", str(d),
           "--type", "exploration", "--name", "EDA")
    if con_regla:
        (d / "initiative" / "increments" / "001_eda" / "rules.yml").write_text(
            yaml.safe_dump(REGLA, sort_keys=False, allow_unicode=True), encoding="utf-8")
        correr("--mode", "merge-increment", "--project-dir", str(d), "--by", "JP")
    return d


def _con_incremento_build(tmp_path):
    """Las reglas viven en el paso 4, y ese paso solo existe en el ciclo `build`."""
    d = tmp_path / "proj"
    d.mkdir(parents=True, exist_ok=True)
    correr("--mode", "init", "--project-dir", str(d), "--preset", "research",
           "--layout", "flat", "--initiative-name", "M")
    correr("--mode", "new-increment", "--project-dir", str(d),
           "--type", "build", "--name", "Pipeline")
    return d, d / "initiative" / "increments" / "001_pipeline"


def _entradas(d):
    f = d / "initiative" / "specs" / "inputs.yml"
    if not f.exists():
        return []
    return (yaml.safe_load(f.read_text(encoding="utf-8")) or {}).get("inputs") or []


def _registrar(d, *extra):
    return correr("--mode", "record-input", "--project-dir", str(d),
                  "--source", "Reunion con ESO (Paranal)", "--kind", "meeting",
                  "--date", "2026-09-02",
                  "--summary", "Existe telemetria a 1 Hz que no se archiva", *extra)


# ─── El registro ─────────────────────────────────────────────────────────────

def test_una_entrada_queda_registrada_con_su_procedencia(tmp_path):
    """Sin saber quien lo dijo y cuando, un hecho no es evidencia de nada."""
    d = _proyecto(tmp_path, con_regla=False)
    r = _registrar(d)
    assert r.returncode == 0, r.stdout + r.stderr

    e = _entradas(d)[0]
    assert e["id"] == "EXT-001"
    assert e["date"] == "2026-09-02"
    assert "ESO" in e["source"]
    assert e["kind"] == "meeting"


def test_sin_fuente_o_sin_resumen_se_rechaza(tmp_path):
    d = _proyecto(tmp_path, con_regla=False)
    sin_fuente = correr("--mode", "record-input", "--project-dir", str(d),
                        "--summary", "algo")
    sin_resumen = correr("--mode", "record-input", "--project-dir", str(d),
                         "--source", "alguien")
    assert sin_fuente.returncode != 0 and "--source" in sin_fuente.stderr
    assert sin_resumen.returncode != 0 and "--summary" in sin_resumen.stderr


def test_el_acta_se_enlaza_en_vez_de_copiarse(tmp_path):
    """El documento sigue viviendo donde vive; la entrada solo lo apunta."""
    d = _proyecto(tmp_path, con_regla=False)
    _registrar(d, "--file", "00_admin/MINUTA_ESO.md,00_admin/correo.eml")
    assert _entradas(d)[0]["artifacts"] == ["00_admin/MINUTA_ESO.md", "00_admin/correo.eml"]


def test_las_entradas_se_numeran_solas(tmp_path):
    d = _proyecto(tmp_path, con_regla=False)
    _registrar(d)
    _registrar(d)
    assert [e["id"] for e in _entradas(d)] == ["EXT-001", "EXT-002"]


def test_un_kind_inventado_se_rechaza(tmp_path):
    d = _proyecto(tmp_path, con_regla=False)
    r = _registrar(d, "--kind", "telepatia")
    assert r.returncode != 0
    assert "meeting" in r.stderr


def test_queda_en_el_historial(tmp_path):
    d = _proyecto(tmp_path, con_regla=False)
    _registrar(d)
    estado = yaml.safe_load((d / "initiative" / "state.yml").read_text(encoding="utf-8"))
    assert any(h.get("action") == "RECORD_INPUT" for h in estado["history"])


# ─── La deuda que abre, que es el motivo de todo esto ────────────────────────

def test_no_se_puede_invalidar_una_regla_que_no_existe(tmp_path):
    d = _proyecto(tmp_path)
    r = _registrar(d, "--invalidates", "RUL-999-999")
    assert r.returncode != 0
    assert "RUL-001-001" in r.stderr, "tiene que decir cuales SI existen"


def test_registrar_no_toca_la_regla_que_pone_en_duda(tmp_path):
    """Anotar un hecho es gratis; cambiar lo que gobierna el proyecto lleva firma."""
    d = _proyecto(tmp_path)
    _registrar(d, "--invalidates", "RUL-001-001")

    reglas = yaml.safe_load(
        (d / "initiative" / "specs" / "rules.yml").read_text(encoding="utf-8"))["rules"]
    assert reglas[0]["status"] == "active", (
        "una entrada abre la deuda; no decide por el usuario"
    )


def test_doctor_no_deja_olvidar_la_deuda(tmp_path):
    """El fallo caro: la reunion tumba una afirmacion y esa sigue rigiendo medio ano."""
    d = _proyecto(tmp_path)
    _registrar(d, "--invalidates", "RUL-001-001")

    r = correr("--mode", "doctor", "--project-dir", str(d))
    assert r.returncode != 0, "es un problema, no un aviso"
    assert "EXT-001" in r.stdout and "RUL-001-001" in r.stdout
    assert "supersedes" in r.stdout, "tiene que decir COMO se cierra"


def test_doctor_calla_cuando_la_deuda_se_resuelve(tmp_path):
    d = _proyecto(tmp_path)
    _registrar(d, "--invalidates", "RUL-001-001")

    correr("--mode", "new-increment", "--project-dir", str(d),
           "--type", "exploration", "--name", "Cadencia real")
    (d / "initiative" / "increments" / "002_cadencia_real" / "rules.yml").write_text(
        yaml.safe_dump({"rules": [{
            "id": "RUL-002-001",
            "statement": "Existe telemetria a 1 Hz, pero hay que pedirla",
            "rationale": "Confirmado por ESO el 2026-09-02",
            "applies_to": "telemetria.cadencia",
            "scope": "project", "status": "proposed",
            "supersedes": "RUL-001-001", "evidence": ["EXT-001"],
        }]}, sort_keys=False, allow_unicode=True), encoding="utf-8")
    correr("--mode", "merge-increment", "--project-dir", str(d), "--by", "JP")

    assert correr("--mode", "doctor", "--project-dir", str(d)).returncode == 0


# ─── Citarla como evidencia ──────────────────────────────────────────────────

def test_una_regla_puede_apoyarse_en_una_entrada(tmp_path):
    """«El instrumento se recalibro en marzo» no se demuestra con un assert."""
    d, dir_inc = _con_incremento_build(tmp_path)
    _registrar(d)
    (dir_inc / "rules.yml").write_text(yaml.safe_dump({"rules": [{
        "id": "RUL-001-001", "statement": "Hay que pedir la telemetria a 1 Hz",
        "rationale": "Lo confirmo ESO", "applies_to": "telemetria",
        "scope": "project", "status": "proposed", "evidence": ["EXT-001"],
    }]}, sort_keys=False, allow_unicode=True), encoding="utf-8")

    r = correr("--mode", "verify-step", "--project-dir", str(d), "--step", "4")
    assert "la evidencia citada existe" in r.stdout, (
        "si la comprobacion no llego a correr, este test no prueba nada: %s" % r.stdout
    )
    assert "fantasmas" not in r.stdout, r.stdout


def test_una_evidencia_inventada_se_denuncia_aunque_no_haya_tests(tmp_path):
    """Antes esta comprobacion colgaba de que ya existiera algun test.

    Es decir: en un proyecto sin un solo test —justo donde una cita inventada pasa mas
    desapercibida— no se comprobaba nada.
    """
    d, dir_inc = _con_incremento_build(tmp_path)
    (dir_inc / "rules.yml").write_text(yaml.safe_dump({"rules": [{
        "id": "RUL-001-001", "statement": "Algo", "rationale": "Porque si",
        "applies_to": "x", "scope": "project", "status": "proposed",
        "evidence": ["EXT-042", "TST-ACC-999"],
    }]}, sort_keys=False, allow_unicode=True), encoding="utf-8")

    r = correr("--mode", "verify-step", "--project-dir", str(d), "--step", "4")
    assert "EXT-042" in r.stdout and "TST-ACC-999" in r.stdout


# ─── explain ─────────────────────────────────────────────────────────────────

def test_explain_cuenta_que_dijo_y_que_se_hizo(tmp_path):
    d = _proyecto(tmp_path)
    _registrar(d, "--invalidates", "RUL-001-001", "--file", "00_admin/MINUTA.md")

    r = correr("--mode", "explain", "--project-dir", str(d), "--input", "EXT-001")
    assert r.returncode == 0, r.stderr
    assert "ESO" in r.stdout
    assert "2026-09-02" in r.stdout
    assert "00_admin/MINUTA.md" in r.stdout
    assert "SIGUE ACTIVA" in r.stdout, "lo pendiente tiene que verse"


def test_explain_con_una_entrada_inexistente_lista_las_que_hay(tmp_path):
    d = _proyecto(tmp_path, con_regla=False)
    _registrar(d)
    r = correr("--mode", "explain", "--project-dir", str(d), "--input", "EXT-999")
    assert r.returncode != 0
    assert "EXT-001" in r.stderr


def test_explain_sigue_explicando_reglas(tmp_path):
    """La bifurcacion no puede romper lo que ya funcionaba."""
    d = _proyecto(tmp_path)
    r = correr("--mode", "explain", "--project-dir", str(d), "--rule", "RUL-001-001")
    assert r.returncode == 0
    assert "documentacion nominal" in r.stdout


def test_explain_sin_rule_ni_input_se_rechaza(tmp_path):
    d = _proyecto(tmp_path, con_regla=False)
    r = correr("--mode", "explain", "--project-dir", str(d))
    assert r.returncode != 0
    assert "--rule" in r.stderr and "--input" in r.stderr
