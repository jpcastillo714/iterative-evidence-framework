"""El preset es la fuente de verdad del ciclo: si esto falla, el motor obedece a otra cosa.

Estos tests importan `ief_preset` de verdad. La suite anterior construia diccionarios a
mano y verificaba ese mismo diccionario, por lo que no podia detectar ningun defecto del
codigo — de hecho no detecto el desajuste de clave que bloqueaba el paso 2.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from conftest import BUNDLE, correr


# ─── Carga y herencia ────────────────────────────────────────────────────────

def test_todos_los_presets_cargan(preset_mod):
    ids = preset_mod.presets_disponibles(BUNDLE)
    assert set(ids) >= {"generic", "research", "product", "analysis", "modeling"}
    for pid in ids:
        base = "generic" if preset_mod.es_mixin(pid, BUNDLE) else None
        preset_mod.cargar_preset(pid, BUNDLE, base_para_mixin=base)   # no debe lanzar


def test_la_herencia_encadena_en_orden(preset_mod):
    p = preset_mod.cargar_preset("research", BUNDLE)
    assert p.cadena == ["generic", "research"]


def test_el_hijo_hereda_los_pasos_del_padre(preset_mod):
    generico = preset_mod.cargar_preset("generic", BUNDLE)
    investig = preset_mod.cargar_preset("research", BUNDLE)
    assert [s.clave for s in investig.pasos("build")] == [s.clave for s in generico.pasos("build")]


def test_rename_cambia_la_etiqueta_pero_no_la_clave(preset_mod):
    p = preset_mod.cargar_preset("research", BUNDLE)
    paso = p.ciclo("build").por_clave("4_rules")
    assert paso is not None
    assert paso.nombre == "Reglas del Modelo"
    assert paso.ref == "4"
    assert paso.artefacto == "rules.yml"


def test_preset_inexistente_da_error_claro(preset_mod):
    with pytest.raises(preset_mod.ErrorDePreset, match="no existe el preset"):
        preset_mod.cargar_preset("no-existe", BUNDLE)


# ─── Los tres ciclos ─────────────────────────────────────────────────────────

def test_todo_preset_ofrece_la_escala_completa_de_ciclos(preset_mod):
    """El rigor es una propiedad del trabajo, no del proyecto.

    Antes `mvp` era un preset, lo que obligaba a elegir "soy un proyecto MVP" de una vez
    y para siempre. Ahora cualquier proyecto elige por incremento, y la escala llega
    hasta abajo: `task` para codigo pequeno, y `--mode log` para lo que ni siquiera es
    un incremento.
    """
    for pid in ("generic", "research", "product", "analysis"):
        p = preset_mod.cargar_preset(pid, BUNDLE)
        assert set(p.tipos_de_ciclo()) == {"build", "exploration", "prototype", "task"}, pid


def test_el_ciclo_prototype_recorta_y_lo_declara(preset_mod):
    p = preset_mod.cargar_preset("generic", BUNDLE)
    assert [s.ref for s in p.pasos("prototype")] == ["1", "2", "3", "4"]
    assert [s.ref for s in p.pasos("prototype") if s.human_gate] == ["1"]
    # Los pasos que se saltan NO estan, en vez de fingirse completados.
    claves = {s.clave for s in p.pasos("prototype")}
    assert "3_data_contracts" not in claves
    assert "4_rules" not in claves


# ─── Composicion: mixins ─────────────────────────────────────────────────────

def test_el_mixin_solo_falla_con_un_mensaje_que_ensena_a_usarlo(preset_mod):
    with pytest.raises(preset_mod.ErrorDePreset, match="es un mixin"):
        preset_mod.cargar_preset("modeling", BUNDLE)


@pytest.mark.parametrize("base", ["analysis", "product", "research"])
def test_el_mixin_modeling_se_compone_con_cualquier_base(preset_mod, tmp_path, base):
    """El motivo del rediseno: "ML dentro de engineering O dentro de data-science".

    Con herencia simple hacia falta un preset por combinacion. Como mixin, `modeling`
    inyecta su paso en cualquier base sin redeclarar el ciclo.
    """
    dp = BUNDLE / "presets" / "_test_composicion"
    dp.mkdir(exist_ok=True)
    try:
        (dp / "preset.yml").write_text(
            f"id: _test_composicion\nname: T\nextends: [{base}, modeling]\n", encoding="utf-8"
        )
        p = preset_mod.cargar_preset("_test_composicion", BUNDLE)
        refs = [s.ref for s in p.pasos("build")]
        assert "6b" in refs, f"el mixin no inyecto su paso sobre {base}"
        assert refs.index("6b") == refs.index("6") + 1, "6b debe ir justo despues de 6"
        paso = p.ciclo("build").por_ref("6b")
        assert paso.human_gate and paso.artefacto == "model-card.md"
        assert {"modelos", "experimentos", "config"} <= set(p.roles)
    finally:
        import shutil
        shutil.rmtree(dp, ignore_errors=True)


# ─── Personalizacion de ciclos ───────────────────────────────────────────────

def _escribir_preset(dir_presets: Path, pid: str, doc: dict) -> None:
    d = dir_presets / pid
    d.mkdir(parents=True, exist_ok=True)
    (d / "preset.yml").write_text(
        yaml.safe_dump(doc, sort_keys=False, allow_unicode=True), encoding="utf-8"
    )


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
    _escribir_preset(bundle_falso / "presets", "hijo", {
        "id": "hijo", "extends": "base",
        "cycles": {"build": {"human_gates": ["3_c"]}},
    })
    p = preset_mod.cargar_preset("hijo", bundle_falso)
    assert {s.clave: s.human_gate for s in p.pasos("build")} == {
        "1_a": False, "2_b": False, "3_c": True
    }


def test_insert_after_no_obliga_a_redeclarar_el_ciclo(preset_mod, bundle_falso):
    """La operacion que hace posible que un mixin exista."""
    _escribir_preset(bundle_falso / "presets", "conmixin", {
        "id": "conmixin", "extends": "base",
        "cycles": {"build": {"insert_after": {"2_b": [
            {"key": "2b_extra", "ref": "2b", "name": "Extra", "artifact": "x.md"}
        ]}}},
    })
    p = preset_mod.cargar_preset("conmixin", bundle_falso)
    assert [s.ref for s in p.pasos("build")] == ["1", "2", "2b", "3"]


def test_insert_before_coloca_antes(preset_mod, bundle_falso):
    _escribir_preset(bundle_falso / "presets", "antes", {
        "id": "antes", "extends": "base",
        "cycles": {"build": {"insert_before": {"1_a": [
            {"key": "0_pre", "ref": "0", "name": "Pre", "artifact": "p.md"}
        ]}}},
    })
    p = preset_mod.cargar_preset("antes", bundle_falso)
    assert [s.ref for s in p.pasos("build")] == ["0", "1", "2", "3"]


def test_remove_quita_pasos(preset_mod, bundle_falso):
    _escribir_preset(bundle_falso / "presets", "corto", {
        "id": "corto", "extends": "base",
        "cycles": {"build": {"remove": ["2_b"]}},
    })
    p = preset_mod.cargar_preset("corto", bundle_falso)
    assert [s.ref for s in p.pasos("build")] == ["1", "3"]


def test_las_operaciones_sobre_pasos_inexistentes_fallan_temprano(preset_mod, bundle_falso):
    for op, valor in (
        ("rename", {"99_no": "X"}),
        ("human_gates", ["99_no"]),
        ("remove", ["99_no"]),
    ):
        _escribir_preset(bundle_falso / "presets", f"malo_{op}", {
            "id": f"malo_{op}", "extends": "base", "cycles": {"build": {op: valor}},
        })
        with pytest.raises(preset_mod.ErrorDePreset, match="inexistentes"):
            preset_mod.cargar_preset(f"malo_{op}", bundle_falso)


def test_insert_con_ancla_inexistente_falla(preset_mod, bundle_falso):
    _escribir_preset(bundle_falso / "presets", "malancla", {
        "id": "malancla", "extends": "base",
        "cycles": {"build": {"insert_after": {"99_no": [{"key": "x", "ref": "x"}]}}},
    })
    with pytest.raises(preset_mod.ErrorDePreset, match="ancla en un paso inexistente"):
        preset_mod.cargar_preset("malancla", bundle_falso)


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
    r = correr("--mode", "check-bundle")
    assert r.returncode == 0, r.stdout + r.stderr


def test_las_claves_de_paso_son_las_mismas_en_todo_el_repo():
    """Regresion doble.

    `2_inspection`: `verify_frame.py` usaba esa clave y todo lo demas
    `2_empirical_inspection`, lo que impedia avanzar del paso 2 para siempre.
    `4_business_rules`: al renombrarlo a `4_rules` habia cuatro sitios que tocar.
    """
    aqui = Path(__file__).resolve()
    huerfanas = []
    for ruta in list(BUNDLE.rglob("*.py")) + list(BUNDLE.rglob("*.yml")) + list(BUNDLE.rglob("*.md")):
        if any(p in ruta.parts for p in (".git", "__pycache__", "scratch")):
            continue
        if ruta.resolve() == aqui:
            continue
        texto = ruta.read_text(encoding="utf-8", errors="ignore")
        if "2_inspection" in texto.replace("2_empirical_inspection", ""):
            huerfanas.append(f"{ruta.relative_to(BUNDLE)}: 2_inspection")
        if "business_rules" in texto or "business-rules" in texto:
            huerfanas.append(f"{ruta.relative_to(BUNDLE)}: business-rules")
    assert not huerfanas, f"claves divergentes: {huerfanas}"
