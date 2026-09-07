"""`doctor` tiene que diagnosticar tambien el archivo del que vive.

Contra un proyecto real —una memoria de titulo empezada con una version anterior del
IEF, con dos incrementos en `status: PENDING` y tres pasos en `DONE`, ninguno de los
cuales es un valor valido— `doctor` respondio **«Sin hallazgos»**.

Miraba las relaciones entre incrementos y daba por bueno el vocabulario del estado. Pero
un estado que el motor no entiende no falla: se interpreta. Y la interpretacion pierde
trabajo en silencio, que es la peor forma de perderlo.
"""

from __future__ import annotations

import yaml

from conftest import correr


def _proyecto(tmp_path, tipo="build"):
    d = tmp_path / "proj"
    d.mkdir(parents=True, exist_ok=True)
    correr("--mode", "init", "--project-dir", str(d), "--preset", "research",
           "--layout", "flat", "--initiative-name", "M")
    correr("--mode", "new-increment", "--project-dir", str(d),
           "--type", tipo, "--name", "Ingesta")
    return d


def _tocar(d, fn):
    f = d / "initiative" / "state.yml"
    doc = yaml.safe_load(f.read_text(encoding="utf-8"))
    fn(doc)
    f.write_text(yaml.safe_dump(doc, sort_keys=False, allow_unicode=True), encoding="utf-8")


def _doctor(d):
    return correr("--mode", "doctor", "--project-dir", str(d))


def test_un_estado_de_incremento_inexistente_se_denuncia(tmp_path):
    d = _proyecto(tmp_path)
    _tocar(d, lambda doc: doc["increments"][0].update(status="PENDING"))
    r = _doctor(d)
    assert r.returncode != 0
    assert "PENDING" in r.stdout
    assert "ACTIVE" in r.stdout, "tiene que decir cuales SI son validos"


def test_un_estado_de_paso_inexistente_se_denuncia(tmp_path):
    """`DONE` venia de una version anterior y se leia como si no fuera nada."""
    d = _proyecto(tmp_path)
    _tocar(d, lambda doc: doc["increments"][0]["steps"].update({"1_charter": "DONE"}))
    r = _doctor(d)
    assert r.returncode != 0
    assert "DONE" in r.stdout


def test_una_clave_de_paso_huerfana_se_denuncia(tmp_path):
    """El fallo que mas caro sale: progreso que desaparece sin avisar.

    `4_business_rules` se renombro a `4_rules`. El motor busca la clave nueva, no la
    encuentra, y da el paso por PENDING — aunque el archivo dijera COMPLETED.
    """
    d = _proyecto(tmp_path)

    def romper(doc):
        pasos = doc["increments"][0]["steps"]
        pasos.pop("4_rules", None)
        pasos["4_business_rules"] = "COMPLETED"

    _tocar(d, romper)
    r = _doctor(d)
    assert r.returncode != 0
    assert "4_business_rules" in r.stdout
    assert "PENDING" in r.stdout, "tiene que explicar la CONSECUENCIA, no solo que sobra"


def test_un_tipo_de_ciclo_que_el_preset_no_define(tmp_path):
    d = _proyecto(tmp_path)
    _tocar(d, lambda doc: doc["increments"][0].update(type="ceremonia"))
    r = _doctor(d)
    assert r.returncode != 0
    assert "ceremonia" in r.stdout


def test_un_foco_que_apunta_a_la_nada(tmp_path):
    d = _proyecto(tmp_path)
    _tocar(d, lambda doc: doc.update(focus="004_no_existe"))
    r = _doctor(d)
    assert r.returncode != 0
    assert "004_no_existe" in r.stdout


def test_un_schema_de_otra_version_es_aviso_no_error(tmp_path):
    """Se puede seguir trabajando con el; solo hay que saberlo."""
    d = _proyecto(tmp_path)
    _tocar(d, lambda doc: doc.update(schema_version="3.0"))
    r = _doctor(d)
    assert "3.0" in r.stdout and "4.0" in r.stdout
    assert "WARN" in r.stdout


def test_un_proyecto_sano_sigue_sin_hallazgos(tmp_path):
    """La red no puede saltar sobre lo que el propio motor acaba de escribir."""
    d = _proyecto(tmp_path)
    r = _doctor(d)
    assert r.returncode == 0, r.stdout
    assert "Sin hallazgos" in r.stdout


def test_todos_los_ciclos_pasan_limpios_recien_creados(tmp_path):
    """Si `doctor` se queja de un incremento que el motor acaba de abrir, la red esta mal."""
    for tipo in ("task", "exploration", "prototype", "build"):
        d = _proyecto(tmp_path / tipo, tipo=tipo)
        r = _doctor(d)
        assert r.returncode == 0, "%s: %s" % (tipo, r.stdout)
