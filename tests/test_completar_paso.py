"""`--mode complete-step`: la unica forma legitima de dar un paso por terminado.

Existia un hueco entre dos reglas del framework. `state.yml` no se edita a mano, pero
el motor no ofrecia ninguna forma de marcar un paso como COMPLETED, asi que las
instrucciones de los comandos decian «marcalo en state.yml». Una regla que la
herramienta obliga a incumplir no se sostiene, y encima dejaba al agente editando a
mano el archivo mas delicado del proyecto.

El modo se anadio y no se probo. Esto lo cubre: sin tests, la garantia que da —que un
paso no se marca terminado si su artefacto no esta— es una promesa sin respaldo.
"""

from __future__ import annotations

import yaml

from conftest import correr


def _proyecto(tmp_path, tipo="build"):
    d = tmp_path / "proj"
    d.mkdir(exist_ok=True)
    r = correr("--mode", "init", "--project-dir", str(d), "--preset", "generic",
               "--layout", "flat", "--initiative-name", "P")
    assert r.returncode == 0, r.stderr
    r = correr("--mode", "new-increment", "--project-dir", str(d),
               "--type", tipo, "--name", "Ingesta")
    assert r.returncode == 0, r.stderr
    return d


def _estado(d):
    return yaml.safe_load((d / "initiative" / "state.yml").read_text(encoding="utf-8"))


def _pasos(d):
    return _estado(d)["increments"][0]["steps"]


def _dir_inc(d):
    return d / "initiative" / "increments" / "001_ingesta"


def test_se_niega_si_el_artefacto_no_existe(tmp_path):
    """Es la garantia entera del modo: marcar COMPLETED un paso cuyo artefacto no
    esta convierte el estado en una ficcion, y todo el ciclo posterior confia en el."""
    d = _proyecto(tmp_path)
    r = correr("--mode", "complete-step", "--project-dir", str(d))
    assert r.returncode != 0
    assert "1" in r.stderr
    assert "IN_PROGRESS" in str(_pasos(d).values()) or _pasos(d)["1_charter"] != "COMPLETED"


def test_marca_el_paso_cuando_el_artefacto_esta(tmp_path):
    d = _proyecto(tmp_path)
    (_dir_inc(d) / "charter.md").write_text("# Charter\n\nContenido suficiente.\n",
                                            encoding="utf-8")
    r = correr("--mode", "complete-step", "--project-dir", str(d))
    assert r.returncode == 0, r.stdout + r.stderr
    assert _pasos(d)["1_charter"] == "COMPLETED"


def test_avisa_de_que_el_paso_lleva_compuerta(tmp_path):
    """Completar no es aprobar. Si el motor no lo dice aqui, el agente cree que ya esta."""
    d = _proyecto(tmp_path)
    (_dir_inc(d) / "charter.md").write_text("# Charter\n\nContenido suficiente.\n",
                                            encoding="utf-8")
    r = correr("--mode", "complete-step", "--project-dir", str(d))
    assert "compuerta" in r.stdout
    assert "approve-step" in r.stdout, "tiene que decir COMO se aprueba, no solo que hace falta"


def test_no_degrada_un_paso_ya_aprobado(tmp_path):
    """Volver de APPROVED a COMPLETED borraria una firma humana sin dejar rastro."""
    d = _proyecto(tmp_path)
    (_dir_inc(d) / "charter.md").write_text("# Charter\n\nContenido suficiente.\n",
                                            encoding="utf-8")
    correr("--mode", "complete-step", "--project-dir", str(d))
    correr("--mode", "approve-step", "--project-dir", str(d), "--by", "JP")
    assert _pasos(d)["1_charter"] == "APPROVED"

    r = correr("--mode", "complete-step", "--project-dir", str(d), "--step", "1")
    assert r.returncode != 0
    assert _pasos(d)["1_charter"] == "APPROVED", "la aprobacion no se pierde"


def test_queda_en_el_historial(tmp_path):
    """Sin rastro, «quien dio esto por terminado» no tiene respuesta."""
    d = _proyecto(tmp_path)
    (_dir_inc(d) / "charter.md").write_text("# Charter\n\nContenido suficiente.\n",
                                            encoding="utf-8")
    correr("--mode", "complete-step", "--project-dir", str(d))
    assert any(h.get("action") == "COMPLETE_STEP" for h in _estado(d)["history"])


def test_un_paso_inexistente_se_rechaza(tmp_path):
    d = _proyecto(tmp_path)
    r = correr("--mode", "complete-step", "--project-dir", str(d), "--step", "99")
    assert r.returncode != 0
    assert "99" in r.stderr


def test_el_ciclo_task_tambien_lo_usa(tmp_path):
    """El ciclo mas corto no tiene compuertas: el aviso debe ser el otro."""
    d = _proyecto(tmp_path, tipo="task")
    (d / "initiative" / "increments" / "001_ingesta" / "task.md").write_text(
        "# Tarea\n\nQue se pide y como se comprueba.\n", encoding="utf-8")
    r = correr("--mode", "complete-step", "--project-dir", str(d))
    assert r.returncode == 0, r.stdout + r.stderr
    assert "advance" in r.stdout
    assert "compuerta" not in r.stdout
