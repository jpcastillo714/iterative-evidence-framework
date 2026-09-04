"""Los niveles ligeros, adopcion y trazabilidad de reglas.

El framework tenia un hueco por abajo: entre "nada" y un ciclo de 4 pasos con compuerta
no habia nada, asi que el trabajo pequeno —un grafico, un arreglo— o se quedaba fuera
del registro o se le montaba una ceremonia que nadie sostiene. Un framework demasiado
pesado no se usa mal: se deja de usar.

Y tenia otro por el lado: solo servia para proyectos que nacian con el.
"""

from __future__ import annotations

import yaml

from conftest import correr


def _init(tmp_path, preset="generic", layout="flat"):
    d = tmp_path / "proj"
    d.mkdir(exist_ok=True)
    r = correr("--mode", "init", "--project-dir", str(d), "--preset", preset,
               "--layout", layout, "--initiative-name", "P")
    assert r.returncode == 0, r.stdout + r.stderr
    return d


def _estado(d):
    return yaml.safe_load((d / "initiative" / "state.yml").read_text(encoding="utf-8"))


# ─── Nivel 0: log ────────────────────────────────────────────────────────────

def test_log_registra_sin_crear_incremento(tmp_path):
    d = _init(tmp_path)
    r = correr("--mode", "log", "--project-dir", str(d),
               "--message", "grafico de margen para el comite",
               "--output", "reports/figures/margen.png",
               "--from", "notebooks/03.ipynb")
    assert r.returncode == 0, r.stderr

    texto = (d / "initiative" / "worklog.md").read_text(encoding="utf-8")
    assert "grafico de margen para el comite" in texto
    assert "reports/figures/margen.png" in texto
    assert "notebooks/03.ipynb" in texto
    assert _estado(d)["increments"] == [], "log no debe crear incrementos"


def test_el_worklog_explica_cuando_dejar_de_usarlo(tmp_path):
    """Si no dice cuando algo deja de ser una linea, acaba siendo el vertedero."""
    d = _init(tmp_path)
    correr("--mode", "log", "--project-dir", str(d), "--message", "x")
    texto = (d / "initiative" / "worklog.md").read_text(encoding="utf-8")
    assert "incremento" in texto.lower()


def test_log_sin_mensaje_se_rechaza(tmp_path):
    d = _init(tmp_path)
    r = correr("--mode", "log", "--project-dir", str(d))
    assert r.returncode != 0


def test_log_queda_en_el_historial(tmp_path):
    d = _init(tmp_path)
    correr("--mode", "log", "--project-dir", str(d), "--message", "algo")
    assert any(h.get("action") == "LOG" for h in _estado(d)["history"])


# ─── Nivel 1: ciclo task ─────────────────────────────────────────────────────

def test_el_ciclo_task_existe_y_es_corto(preset_mod):
    from conftest import BUNDLE
    p = preset_mod.cargar_preset("generic", BUNDLE)
    assert "task" in p.tipos_de_ciclo()
    pasos = p.pasos("task")
    assert len(pasos) == 2
    assert not any(x.human_gate for x in pasos), (
        "un task no lleva compuertas: si hace falta aprobar algo, no era un task"
    )


def test_la_escala_de_ciclos_es_monotona(preset_mod):
    """log < task < prototype < build, en pasos y en compuertas."""
    from conftest import BUNDLE
    p = preset_mod.cargar_preset("generic", BUNDLE)
    pasos = {c: len(p.pasos(c)) for c in ("task", "prototype", "build")}
    gates = {c: sum(1 for x in p.pasos(c) if x.human_gate) for c in ("task", "prototype", "build")}
    assert pasos["task"] < pasos["prototype"] < pasos["build"]
    assert gates["task"] < gates["prototype"] < gates["build"]


def test_se_puede_abrir_un_incremento_task(tmp_path):
    d = _init(tmp_path)
    r = correr("--mode", "new-increment", "--project-dir", str(d),
               "--type", "task", "--name", "Filtro por categoria")
    assert r.returncode == 0, r.stderr
    assert _estado(d)["increments"][0]["type"] == "task"


# ─── Adopcion de un proyecto existente ───────────────────────────────────────

def _proyecto_a_medias(tmp_path):
    d = tmp_path / "existente"
    for sub in ("notebooks", "datos_crudos", "salidas", "src", "cosas_raras"):
        (d / sub).mkdir(parents=True)
    return d


def test_adopt_reconoce_las_carpetas_que_ya_hay(tmp_path):
    d = _proyecto_a_medias(tmp_path)
    r = correr("--mode", "adopt", "--project-dir", str(d), "--preset", "analysis")
    assert r.returncode == 0, r.stderr
    for esperado in ("datos_crudos", "notebooks", "salidas"):
        assert esperado in r.stdout


def test_adopt_sin_yes_no_toca_nada(tmp_path):
    d = _proyecto_a_medias(tmp_path)
    antes = sorted(x.name for x in d.iterdir())
    correr("--mode", "adopt", "--project-dir", str(d), "--preset", "analysis")
    assert sorted(x.name for x in d.iterdir()) == antes
    assert not (d / "initiative").exists()


def test_adopt_no_duplica_las_carpetas_existentes(tmp_path):
    """El fallo que motivo este comando: acabar con datos_crudos/ Y data/raw/."""
    d = _proyecto_a_medias(tmp_path)
    r = correr("--mode", "adopt", "--project-dir", str(d), "--preset", "analysis", "--yes")
    assert r.returncode == 0, r.stderr
    assert not (d / "data" / "raw").exists(), "datos_raw ya vivia en datos_crudos/"
    assert (d / "datos_crudos").exists()

    rutas = _estado(d)["initiative"]["role_paths"]
    assert rutas["datos_raw"] == "datos_crudos"
    assert rutas["exploracion"] == "notebooks"
    assert rutas["resultados"] == "salidas"


def test_adopt_avisa_de_carpetas_que_no_entiende(tmp_path):
    d = _proyecto_a_medias(tmp_path)
    r = correr("--mode", "adopt", "--project-dir", str(d), "--preset", "analysis")
    assert "cosas_raras" in r.stdout, "lo que no se entiende se dice, no se ignora"


def test_adopt_se_niega_si_ya_hay_estado(tmp_path):
    d = _init(tmp_path)
    r = correr("--mode", "adopt", "--project-dir", str(d), "--preset", "generic")
    assert r.returncode != 0
    assert "ya usa IEF" in r.stderr


# ─── explain ─────────────────────────────────────────────────────────────────

def _con_reglas(tmp_path):
    d = _init(tmp_path, preset="product")
    specs = d / "initiative" / "specs"
    specs.mkdir(parents=True, exist_ok=True)
    (specs / "rules.yml").write_text(yaml.safe_dump({"rules": [
        {"id": "RUL-001-001", "statement": "Se descarta", "rationale": "Parecian pruebas",
         "applies_to": "pedidos", "scope": "project", "status": "superseded",
         "superseded_by": "RUL-002-001", "_origen": {"increment": "001_x"}},
        {"id": "RUL-002-001", "statement": "Se asigna a generico",
         "rationale": "Eran ventas de mostrador", "applies_to": "pedidos",
         "scope": "project", "status": "active", "supersedes": "RUL-001-001",
         "evidence": ["TST-ACC-002"], "_origen": {"increment": "002_y"}},
    ]}, sort_keys=False, allow_unicode=True), encoding="utf-8")
    return d


def test_explain_muestra_el_linaje_completo(tmp_path):
    d = _con_reglas(tmp_path)
    r = correr("--mode", "explain", "--project-dir", str(d), "--rule", "RUL-002-001")
    assert r.returncode == 0, r.stderr
    assert "mostrador" in r.stdout, "el porque tiene que estar"
    assert "reemplaza a RUL-001-001" in r.stdout
    assert "TST-ACC-002" in r.stdout


def test_explain_avisa_de_que_una_regla_ya_no_rige(tmp_path):
    d = _con_reglas(tmp_path)
    r = correr("--mode", "explain", "--project-dir", str(d), "--rule", "RUL-001-001")
    assert "ya NO rige" in r.stdout
    assert "RUL-002-001" in r.stdout


def test_explain_con_regla_inexistente_lista_las_conocidas(tmp_path):
    d = _con_reglas(tmp_path)
    r = correr("--mode", "explain", "--project-dir", str(d), "--rule", "RUL-999-999")
    assert r.returncode != 0
    assert "RUL-001-001" in r.stderr


# ─── Informe ─────────────────────────────────────────────────────────────────

def test_draft_report_trae_los_datos_y_deja_los_aprendizajes(tmp_path):
    d = _init(tmp_path)
    correr("--mode", "new-increment", "--project-dir", str(d),
           "--type", "task", "--name", "Filtro")
    r = correr("--mode", "draft-report", "--project-dir", str(d))
    assert r.returncode == 0, r.stderr

    texto = (d / "initiative" / "increments" / "001_filtro" / "increment-report.md").read_text(encoding="utf-8")
    assert "Recorrido" in texto and "task" in texto
    # Lo que la maquina no puede escribir queda como pregunta, no como hueco.
    assert "Aprendizajes" in texto
    assert "Deuda que queda" in texto
    assert "supuesto resulto falso" in texto


def test_draft_report_no_pisa_un_informe_escrito(tmp_path):
    d = _init(tmp_path)
    correr("--mode", "new-increment", "--project-dir", str(d), "--type", "task", "--name", "F")
    correr("--mode", "draft-report", "--project-dir", str(d))
    destino = d / "initiative" / "increments" / "001_f" / "increment-report.md"
    destino.write_text("# Mi informe escrito a mano\n", encoding="utf-8")
    r = correr("--mode", "draft-report", "--project-dir", str(d))
    assert r.returncode != 0
    assert destino.read_text(encoding="utf-8") == "# Mi informe escrito a mano\n"
