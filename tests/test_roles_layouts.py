"""Roles y layouts: la estructura de carpetas es un eje aparte del preset.

Sale de un ejercicio concreto: un estudiante de memoria, un ingeniero de datos, un
cientifico de datos, un equipo de MVP y un investigador de ML acumulan casi las mismas
cosas. Lo que cambia entre ellos es el vocabulario y la ceremonia, no las carpetas.

Por eso el catalogo de roles es unico, el layout se elige por proyecto, y ningun preset
declara rutas.
"""

from __future__ import annotations

import pytest
import yaml

from conftest import BUNDLE, correr


# ─── El catalogo ─────────────────────────────────────────────────────────────

def test_los_dos_layouts_cubren_todos_los_roles(preset_mod):
    """Cambiar de layout no puede quitarle al proyecto un sitio donde guardar algo."""
    roles = set(preset_mod.cargar_roles(BUNDLE))
    for lid in preset_mod.layouts_disponibles(BUNDLE):
        layout = preset_mod.cargar_layout(lid, BUNDLE)
        faltan = roles - set(layout.rutas)
        assert not faltan, f"el layout `{lid}` no define ruta para: {sorted(faltan)}"


def test_ningun_layout_asigna_dos_roles_a_la_misma_ruta(preset_mod):
    for lid in preset_mod.layouts_disponibles(BUNDLE):
        rutas = preset_mod.cargar_layout(lid, BUNDLE).rutas
        vistas = {}
        for rol, ruta in rutas.items():
            assert ruta not in vistas, (
                f"layout `{lid}`: `{ruta}` la reclaman {vistas.get(ruta)} y {rol}"
            )
            vistas[ruta] = rol


def test_avances_y_documento_son_roles_distintos(preset_mod):
    """Muchos reportes cortos y un entregable largo son necesidades distintas.

    Mezclarlos en una sola carpeta hace que ninguno de los dos se encuentre cuando
    se busca: no tienen la misma cadencia ni la misma audiencia.
    """
    roles = preset_mod.cargar_roles(BUNDLE)
    assert "avances" in roles and "documento" in roles
    for lid in preset_mod.layouts_disponibles(BUNDLE):
        rutas = preset_mod.cargar_layout(lid, BUNDLE).rutas
        assert rutas["avances"] != rutas["documento"], lid


def test_el_rol_onboarding_existe(preset_mod):
    """Material de entrada: para quien llega nuevo, o para el yo de dentro de un ano."""
    assert "onboarding" in preset_mod.cargar_roles(BUNDLE)


def test_ningun_preset_declara_rutas_de_carpeta():
    """Las rutas salen del layout. Un preset que las declare rompe el eje."""
    culpables = []
    for d in (BUNDLE / "presets").iterdir():
        if not (d / "preset.yml").exists():
            continue
        doc = yaml.safe_load((d / "preset.yml").read_text(encoding="utf-8")) or {}
        for clave in ("directories", "directory_convention"):
            if doc.get(clave):
                culpables.append(f"{d.name}: {clave}")
        if (d / "directory-convention.yml").exists():
            culpables.append(f"{d.name}: directory-convention.yml")
    assert not culpables, (
        f"presets con rutas propias: {culpables}. Las rutas vienen del layout."
    )


# ─── Herencia aditiva de roles ───────────────────────────────────────────────

def test_los_roles_se_acumulan_por_la_cadena(preset_mod):
    """Antes la convencion del hijo pisaba entera la del padre.

    Por eso cada preset tenia que redeclarar la lista completa de carpetas solo para
    anadir una. Ahora se suman.
    """
    generico = set(preset_mod.cargar_preset("generic", BUNDLE).roles)
    investig = set(preset_mod.cargar_preset("research", BUNDLE).roles)
    assert generico < investig, "research debe heredar los roles de generic y sumar los suyos"
    assert {"referencias", "documento", "presentaciones", "avances"} <= investig


def test_initiative_esta_siempre_aunque_nadie_lo_declare(preset_mod):
    for pid in ("generic", "research", "product", "analysis"):
        assert "initiative" in preset_mod.cargar_preset(pid, BUNDLE).roles, pid


def test_un_rol_desconocido_falla_al_cargar(preset_mod, tmp_path):
    dp = tmp_path / "presets" / "malo"
    dp.mkdir(parents=True)
    (dp / "preset.yml").write_text(
        "id: malo\nextends: null\n"
        "paths: {increment_dir: 'i/{slug}'}\n"
        "roles: [rol_que_no_existe]\n"
        "cycles: {build: {steps: [{key: '1_a', ref: '1', name: A}]}}\n",
        encoding="utf-8",
    )
    (tmp_path / "core").mkdir()
    (tmp_path / "core" / "roles.yml").write_text(
        "roles:\n  initiative:\n    always: true\n", encoding="utf-8"
    )
    with pytest.raises(preset_mod.ErrorDePreset, match="no estan en core/roles.yml"):
        preset_mod.cargar_preset("malo", tmp_path)


# ─── Los ejes son independientes ─────────────────────────────────────────────

def test_cada_combinacion_de_preset_y_layout_funciona(tmp_path, preset_mod):
    """El mismo preset con dos layouts, y el mismo layout con dos presets."""
    combinaciones = [
        ("research", "numbered"), ("research", "flat"),
        ("analysis", "numbered"), ("product", "flat"),
    ]
    for pid, lid in combinaciones:
        destino = tmp_path / f"{pid}_{lid}"
        destino.mkdir()
        r = correr("--mode", "init", "--project-dir", str(destino),
                   "--preset", pid, "--layout", lid, "--initiative-name", "X")
        assert r.returncode == 0, r.stdout + r.stderr

        state = yaml.safe_load((destino / "initiative" / "state.yml").read_text(encoding="utf-8"))
        assert state["initiative"]["preset"] == pid
        assert state["initiative"]["layout"] == lid

        preset = preset_mod.cargar_preset(pid, BUNDLE)
        layout = preset_mod.cargar_layout(lid, BUNDLE)
        for rol in preset.roles:
            assert (destino / layout.ruta(rol)).is_dir(), f"{pid}/{lid}: falta {rol}"


def test_el_layout_numerado_usa_prefijos_y_el_plano_no(preset_mod):
    numerado = preset_mod.cargar_layout("numbered", BUNDLE)
    plano = preset_mod.cargar_layout("flat", BUNDLE)
    assert numerado.ruta("admin").startswith("00_")
    assert numerado.ruta("documento").startswith("07_")
    assert plano.ruta("codigo") == "src", "las herramientas del ecosistema esperan src/"
    # Excepcion deliberada: tests/ en la raiz en ambos, porque el descubrimiento de
    # tests es convencion del ecosistema y esconderlo rompe herramientas.
    assert numerado.ruta("tests") == plano.ruta("tests") == "tests"
