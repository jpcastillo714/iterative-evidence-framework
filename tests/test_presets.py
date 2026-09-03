"""El preset es la fuente de verdad del ciclo: si esto falla, el motor obedece a otra cosa.

Estos tests importan `ief_preset` de verdad. La suite anterior construia diccionarios
a mano y verificaba ese mismo diccionario, por lo que no podia detectar ningun defecto
del codigo — de hecho no detecto el desajuste de clave que bloqueaba el paso 2.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from conftest import BUNDLE, correr


# ─── Carga y herencia ────────────────────────────────────────────────────────

def test_todos_los_presets_cargan(preset_mod):
    ids = preset_mod.presets_disponibles(BUNDLE)
    assert set(ids) >= {"generic", "engineering", "data-science", "ml", "mvp", "academic"}
    for pid in ids:
        preset_mod.cargar_preset(pid, BUNDLE)   # no debe lanzar


def test_la_herencia_encadena_en_orden(preset_mod):
    p = preset_mod.cargar_preset("academic", BUNDLE)
    assert p.cadena == ["generic", "academic"]


def test_el_hijo_hereda_los_pasos_del_padre(preset_mod):
    generico = preset_mod.cargar_preset("generic", BUNDLE)
    academico = preset_mod.cargar_preset("academic", BUNDLE)
    assert [s.clave for s in academico.pasos("build")] == [s.clave for s in generico.pasos("build")]


def test_rename_cambia_la_etiqueta_pero_no_la_clave(preset_mod):
    p = preset_mod.cargar_preset("engineering", BUNDLE)
    paso = p.ciclo("build").por_clave("2_empirical_inspection")
    assert paso is not None
    assert paso.nombre == "Perfilado de Fuentes"
    assert paso.ref == "2"


def test_el_preset_ml_agrega_un_paso_con_compuerta(preset_mod):
    """Un preset puede extender el ciclo, no solo renombrarlo."""
    p = preset_mod.cargar_preset("ml", BUNDLE)
    refs = [s.ref for s in p.pasos("build")]
    assert refs == ["1", "2", "3", "4", "5", "6", "6b", "7"]
    paso = p.ciclo("build").por_ref("6b")
    assert paso.human_gate is True
    assert paso.artefacto == "model-card.md"


def test_el_preset_mvp_recorta_el_ciclo(preset_mod):
    """Y puede acortarlo: 4 pasos y una sola compuerta, declarado."""
    p = preset_mod.cargar_preset("mvp", BUNDLE)
    assert [s.ref for s in p.pasos("build")] == ["1", "2", "3", "4"]
    assert [s.ref for s in p.pasos("build") if s.human_gate] == ["1"]


def test_preset_inexistente_da_error_claro(preset_mod):
    with pytest.raises(preset_mod.ErrorDePreset, match="no existe el preset"):
        preset_mod.cargar_preset("no-existe", BUNDLE)


# ─── Las tres formas de flexibilidad ─────────────────────────────────────────

def _escribir_preset(dir_presets: Path, pid: str, doc: dict) -> None:
    d = dir_presets / pid
    d.mkdir(parents=True, exist_ok=True)
    (d / "preset.yml").write_text(yaml.safe_dump(doc, sort_keys=False, allow_unicode=True), encoding="utf-8")


@pytest.fixture
def bundle_falso(tmp_path: Path) -> Path:
    """Un bundle minimo para probar la personalizacion sin tocar el real."""
    dp = tmp_path / "presets"
    _escribir_preset(dp, "base", {
        "id": "base", "name": "Base", "extends": None,
        "paths": {"increment_dir": "initiative/increments/{slug}"},
        "cycles": {"build": {"steps": [
            {"key": "1_a", "ref": "1", "name": "A", "artifact": "a.md", "human_gate": True},
            {"key": "2_b", "ref": "2", "name": "B", "artifact": "b.md", "human_gate": False},
            {"key": "3_c", "ref": "3", "name": "C", "artifact": "c.md", "human_gate": False},
        ]}},
    })
    return tmp_path


def test_un_preset_puede_mover_la_compuerta(preset_mod, bundle_falso):
    """Antes esto era imposible: las compuertas estaban fijas en el codigo."""
    _escribir_preset(bundle_falso / "presets", "hijo", {
        "id": "hijo", "extends": "base",
        "cycles": {"build": {"human_gates": ["3_c"]}},
    })
    p = preset_mod.cargar_preset("hijo", bundle_falso)
    gates = {s.clave: s.human_gate for s in p.pasos("build")}
    assert gates == {"1_a": False, "2_b": False, "3_c": True}


def test_un_preset_puede_quitar_y_agregar_pasos(preset_mod, bundle_falso):
    """La flexibilidad estructural que motivo todo este refactor."""
    _escribir_preset(bundle_falso / "presets", "corto", {
        "id": "corto", "extends": "base",
        "cycles": {"build": {"steps": [
            {"key": "1_a", "ref": "1", "name": "A", "artifact": "a.md", "human_gate": True},
            {"key": "9_z", "ref": "9", "name": "Paso nuevo", "artifact": "z.md", "human_gate": False},
        ]}},
    })
    p = preset_mod.cargar_preset("corto", bundle_falso)
    assert [s.ref for s in p.pasos("build")] == ["1", "9"]


def test_rename_de_un_paso_inexistente_falla_temprano(preset_mod, bundle_falso):
    _escribir_preset(bundle_falso / "presets", "malo", {
        "id": "malo", "extends": "base",
        "cycles": {"build": {"rename": {"99_no_existe": "X"}}},
    })
    with pytest.raises(preset_mod.ErrorDePreset, match="pasos inexistentes"):
        preset_mod.cargar_preset("malo", bundle_falso)


def test_la_herencia_circular_se_detecta(preset_mod, bundle_falso):
    _escribir_preset(bundle_falso / "presets", "a", {"id": "a", "extends": "b"})
    _escribir_preset(bundle_falso / "presets", "b", {"id": "b", "extends": "a"})
    with pytest.raises(preset_mod.ErrorDePreset, match="circular"):
        preset_mod.cargar_preset("a", bundle_falso)


def test_dos_pasos_no_pueden_reclamar_el_mismo_artefacto(preset_mod, bundle_falso):
    """Un artefacto, una ruta. Es la regla que el bundle violaba en tres capas."""
    _escribir_preset(bundle_falso / "presets", "choque", {
        "id": "choque", "extends": None,
        "paths": {"increment_dir": "initiative/increments/{slug}"},
        "cycles": {"build": {"steps": [
            {"key": "1_a", "ref": "1", "name": "A", "artifact": "mismo.md"},
            {"key": "2_b", "ref": "2", "name": "B", "artifact": "mismo.md"},
        ]}},
    })
    with pytest.raises(preset_mod.ErrorDePreset, match="mismo artefacto"):
        preset_mod.cargar_preset("choque", bundle_falso)


# ─── Coherencia con el bundle real ───────────────────────────────────────────

def test_las_rutas_que_prometen_los_presets_existen():
    r = correr("--mode", "check-preset")
    assert r.returncode == 0, r.stdout + r.stderr


def test_cada_paso_tiene_sus_archivos_de_apoyo():
    r = correr("--mode", "check-steps")
    assert r.returncode == 0, r.stdout + r.stderr


def test_el_nucleo_no_contiene_codigo_de_dominio():
    """core/scripts es una lista cerrada: solo el motor. Cualquier otro script
    es codigo de dominio y su sitio es presets/<id>/scripts/."""
    r = correr("--mode", "check-bundle")
    assert r.returncode == 0, r.stdout + r.stderr


def test_la_clave_del_paso_2_es_la_misma_en_todo_el_repo():
    """Regresion: `verify_frame.py` usaba `2_inspection` y todo lo demas
    `2_empirical_inspection`, lo que impedia avanzar del paso 2."""
    aqui = Path(__file__).resolve()
    apariciones = []
    for ruta in list(BUNDLE.rglob("*.py")) + list(BUNDLE.rglob("*.yml")) + list(BUNDLE.rglob("*.md")):
        if any(p in ruta.parts for p in ("docs", ".git", "__pycache__", "scratch")):
            continue
        if ruta.resolve() == aqui:      # este archivo nombra la clave para explicarla
            continue
        texto = ruta.read_text(encoding="utf-8", errors="ignore")
        if "2_inspection" in texto.replace("2_empirical_inspection", ""):
            apariciones.append(str(ruta.relative_to(BUNDLE)))
    assert not apariciones, f"clave de paso divergente en: {apariciones}"
