"""Dos fallos de `rewind` que encontro un agente leyendo el codigo fuente.

1. `--increment` se aceptaba y se ignoraba: el retroceso caia SIEMPRE sobre el foco.
   Escribir `--increment 002` retrocedia el 001 sin decir nada. La misma clase de fallo
   que ya aparecio dos veces aqui: algo que parece funcionar y no funciona.

2. El barrido era invisible. Retroceder al paso 2 marca 2, 2b y 3 — y eso esta bien: el
   trabajo posterior se apoyaba en lo que ahora se revisa. Lo que estaba mal es el
   silencio. Un agente tuvo que leer `cmd_rewind` para descubrirlo, y de no haberlo
   hecho habria roto un proyecto real.

Por eso aqui no se prueba que el barrido desaparezca —seria empeorar el framework— sino
que se anuncie.
"""

from __future__ import annotations

import yaml

from conftest import correr


def _dos_frentes(tmp_path):
    d = tmp_path / "proj"
    d.mkdir(parents=True, exist_ok=True)
    correr("--mode", "init", "--project-dir", str(d), "--preset", "research",
           "--layout", "flat", "--initiative-name", "M")
    for nombre in ("Primero", "Segundo"):
        correr("--mode", "new-increment", "--project-dir", str(d),
               "--type", "exploration", "--name", nombre)
    # Ambos con trabajo hecho hasta el paso 2.
    for slug in ("001_primero", "002_segundo"):
        dir_inc = d / "initiative" / "increments" / slug
        (dir_inc / "objective.md").write_text("# O\n", encoding="utf-8")
        (dir_inc / "analysis.md").write_text("# A\n", encoding="utf-8")
        correr("--mode", "focus", "--project-dir", str(d), "--increment", slug)
        for ref in ("1", "2"):
            correr("--mode", "complete-step", "--project-dir", str(d), "--step", ref)
            correr("--mode", "advance", "--project-dir", str(d))
    return d


def _pasos(d, slug):
    doc = yaml.safe_load((d / "initiative" / "state.yml").read_text(encoding="utf-8"))
    return next(i for i in doc["increments"] if i["slug"] == slug)["steps"]


def test_increment_deja_de_ignorarse(tmp_path):
    """El foco esta en 002; el retroceso pedido es sobre 001."""
    d = _dos_frentes(tmp_path)
    correr("--mode", "focus", "--project-dir", str(d), "--increment", "002_segundo")

    r = correr("--mode", "rewind", "--project-dir", str(d),
               "--increment", "001_primero", "--to-step", "1",
               "--reason", "hay que replantear la pregunta")
    assert r.returncode == 0, r.stdout + r.stderr

    assert _pasos(d, "001_primero")["1_objective"] == "NEEDS_REVISION", (
        "el retroceso tenia que caer sobre el incremento pedido"
    )
    assert _pasos(d, "002_segundo")["1_objective"] != "NEEDS_REVISION", (
        "y no sobre el que tenia el foco"
    )


def test_sin_increment_sigue_cayendo_sobre_el_foco(tmp_path):
    """El comportamiento por defecto no cambia: sin `--increment`, manda el foco."""
    d = _dos_frentes(tmp_path)
    correr("--mode", "focus", "--project-dir", str(d), "--increment", "002_segundo")
    correr("--mode", "rewind", "--project-dir", str(d), "--to-step", "1",
           "--reason", "x")
    assert _pasos(d, "002_segundo")["1_objective"] == "NEEDS_REVISION"
    assert _pasos(d, "001_primero")["1_objective"] != "NEEDS_REVISION"


def test_un_incremento_inexistente_se_rechaza(tmp_path):
    d = _dos_frentes(tmp_path)
    r = correr("--mode", "rewind", "--project-dir", str(d),
               "--increment", "009_fantasma", "--to-step", "1", "--reason", "x")
    assert r.returncode != 0
    assert "009_fantasma" in r.stderr


def test_el_barrido_se_anuncia_antes_de_hacerlo(tmp_path):
    """Descubrirlo despues es una sorpresa cara; hubo que leer el codigo para saberlo."""
    d = _dos_frentes(tmp_path)
    r = correr("--mode", "rewind", "--project-dir", str(d), "--increment", "001_primero",
               "--to-step", "1", "--reason", "replantear")
    assert "1_objective" in r.stdout or "Pregunta" in r.stdout
    assert "2" in r.stdout
    assert "NEEDS_REVISION" in r.stdout
    assert "se apoyaba" in r.stdout, "tiene que decir POR QUE arrastra, no solo que arrastra"


def test_el_barrido_sigue_arrastrando_lo_posterior(tmp_path):
    """No se cambia la semantica: dar por bueno el trabajo posterior seria peor."""
    d = _dos_frentes(tmp_path)
    correr("--mode", "rewind", "--project-dir", str(d), "--increment", "001_primero",
           "--to-step", "1", "--reason", "replantear")
    pasos = _pasos(d, "001_primero")
    assert pasos["1_objective"] == "NEEDS_REVISION"
    assert pasos["2_analysis"] == "NEEDS_REVISION"


def test_el_anuncio_nombra_todos_los_pasos_que_arrastra(tmp_path):
    """No basta con decir «arrastra varios»: hay que poder ver cuales, antes de aceptar.

    El motor ya listaba los pasos marcados, pero DESPUES de marcarlos y sin decir por
    que. Un resumen a toro pasado no evita la sorpresa que costo un proyecto.
    """
    d = _dos_frentes(tmp_path)
    r = correr("--mode", "rewind", "--project-dir", str(d), "--increment", "001_primero",
               "--to-step", "1", "--reason", "replantear")
    for ref in ("1", "2"):
        assert ref in r.stdout
    # El estado del que vienen, no solo el al que van: «COMPLETED -> NEEDS_REVISION»
    # dice cuanto trabajo se esta reabriendo.
    assert "COMPLETED" in r.stdout


def test_rewind_sin_motivo_se_rechaza(tmp_path):
    d = _dos_frentes(tmp_path)
    r = correr("--mode", "rewind", "--project-dir", str(d), "--to-step", "1")
    assert r.returncode != 0
