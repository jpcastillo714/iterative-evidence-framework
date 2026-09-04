"""El bundle tiene que ser instalable por spec-kit de verdad.

Durante meses este bundle declaro `schema_version: "3.1"` y `speckit_version: ">=0.16.0"`.
Ninguna de las dos cifras existia: spec-kit acepta exactamente `"1.0"` y va por la serie
1.0.x. `specify bundle install` habria rechazado el manifiesto entero antes de copiar un
solo archivo, y nada en el repositorio lo notaba, porque todas las comprobaciones eran
nuestras contra nosotros mismos.

Este archivo es la unica parte de la suite que mira hacia AFUERA. Las constantes de abajo
estan copiadas del codigo de spec-kit, no inventadas; cada una dice de que archivo sale
para poder re-verificarla:

    src/specify_cli/bundler/models/manifest.py   -> el manifiesto del bundle
    src/specify_cli/extensions/__init__.py       -> el manifiesto de la extension

Se copian a proposito en lugar de descargarlas: un test que necesita red falla los dias
que GitHub tose y se acaba desactivando. Cuando spec-kit publique un esquema nuevo, estos
tests fallaran diciendo exactamente que cambio — que es justo lo que queremos que pase.
"""

from __future__ import annotations

import re

import pytest
import yaml

from conftest import BUNDLE

# ─── Copiado de spec-kit v1.0.4 ──────────────────────────────────────────────

# manifest.py: SUPPORTED_SCHEMA_VERSIONS / COMPONENT_KINDS / PRESET_STRATEGIES
BUNDLE_SCHEMA_VERSIONS = {"1.0"}
COMPONENT_KINDS = ("extensions", "presets", "steps", "workflows")
PRESET_STRATEGIES = {"replace", "prepend", "append", "wrap"}
BUNDLE_ID_PATTERN = re.compile(r"^[a-z0-9](?:[a-z0-9._-]*[a-z0-9])?$")
# structural_errors(): campos sin los cuales el manifiesto no resuelve.
BUNDLE_REQUERIDOS = ("id", "name", "version", "role", "description", "author", "license")

# extensions/__init__.py: ExtensionManifest
EXT_SCHEMA_VERSION = "1.0"
EXT_REQUERIDOS_RAIZ = ("schema_version", "extension", "requires", "provides")
EXT_REQUERIDOS_META = ("id", "name", "version", "description")
EXT_ID_PATTERN = re.compile(r"^[a-z0-9-]+$")
VALID_EFFECTS = {"read-only", "read-write"}
EXT_COMMAND_PATTERN = re.compile(r"^speckit\.([a-z0-9-]+)\.[a-z0-9.-]+$")

SEMVER = re.compile(r"^\d+\.\d+\.\d+")


def manifiesto_dict():
    return yaml.safe_load((BUNDLE / "bundle.yml").read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def manifiesto():
    return yaml.safe_load((BUNDLE / "bundle.yml").read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def extension():
    return yaml.safe_load((BUNDLE / "extension" / "extension.yml").read_text(encoding="utf-8"))


# ─── bundle.yml ──────────────────────────────────────────────────────────────

def test_el_schema_version_del_bundle_es_uno_que_speckit_acepta(manifiesto):
    v = str(manifiesto.get("schema_version"))
    assert v in BUNDLE_SCHEMA_VERSIONS, (
        "spec-kit compara contra %s y aborta con cualquier otro valor; aqui pone %r"
        % (sorted(BUNDLE_SCHEMA_VERSIONS), v)
    )


def test_el_bundle_declara_todos_los_campos_obligatorios(manifiesto):
    meta = manifiesto.get("bundle") or {}
    faltan = [c for c in BUNDLE_REQUERIDOS if not str(meta.get(c) or "").strip()]
    assert not faltan, "bundle.%s vacio o ausente" % ", bundle.".join(faltan)


def test_el_id_del_bundle_es_un_slug_seguro(manifiesto):
    """Se interpola en el nombre del .zip: un separador de ruta seria traversal."""
    bid = (manifiesto.get("bundle") or {}).get("id", "")
    assert BUNDLE_ID_PATTERN.match(bid), "bundle.id %r no es un slug" % bid


def test_la_version_del_bundle_es_semver(manifiesto):
    v = str((manifiesto.get("bundle") or {}).get("version", ""))
    assert SEMVER.match(v), "bundle.version %r no es semver" % v


def test_el_bundle_no_declara_presets_de_speckit():
    """Nuestros «presets» NO son presets de spec-kit. Es un error de categoria.

    Un preset de spec-kit es un paquete que reemplaza plantillas de comando
    (speckit.specify, speckit.plan...). Un preset del IEF define el ciclo de trabajo:
    que pasos hay, cuales llevan compuerta, que artefacto produce cada uno. Comparten
    la palabra y nada mas.

    Medido con la CLI real: `specify preset add --dev presets/generic` responde
    `Validation Error: Missing required field: schema_version`. Declararlos bajo
    `provides.presets` era prometer una instalacion que falla siempre.
    """
    presets = ((manifiesto_dict().get("provides") or {}).get("presets")) or []
    assert not presets, (
        "provides.presets deberia estar vacio: lo que hay en presets/ son ciclos del "
        "IEF, no presets de spec-kit. Van bajo `provides.cycles`. Declarados: %s"
        % [p.get("id") for p in presets]
    )


def test_los_ciclos_del_ief_estan_declarados_y_existen_en_disco():
    ciclos = ((manifiesto_dict().get("provides") or {}).get("cycles")) or []
    assert ciclos, "el bundle no declara ningun ciclo"
    for c in ciclos:
        assert (BUNDLE / "presets" / c["id"] / "preset.yml").is_file(), (
            "el ciclo %s no existe en disco" % c.get("id")
        )
    en_disco = {d.name for d in (BUNDLE / "presets").iterdir() if d.is_dir()}
    assert {c["id"] for c in ciclos} == en_disco, (
        "bundle.yml declara %s pero en disco hay %s"
        % (sorted(c["id"] for c in ciclos), sorted(en_disco))
    )


def test_las_extensiones_vienen_fijadas(manifiesto):
    for e in ((manifiesto.get("provides") or {}).get("extensions")) or []:
        assert SEMVER.match(str(e.get("version") or "")), (
            "extension %s sin version semver" % e.get("id")
        )


def test_lo_que_speckit_no_sabe_instalar_esta_marcado_como_nuestro(manifiesto):
    """`tools`, `catalogs` y `cycles` no son tipos de componente de spec-kit.

    No es un error tenerlos —los usa nuestra propia higiene— pero SI lo seria creer
    que spec-kit los instala. Los ignora en silencio: si algun dia el motor o los
    catalogos tuvieran que llegar por ahi, no llegarian. Viajan dentro de la
    extension, y este test existe para que nadie lo olvide.
    """
    PROPIAS = {"tools", "catalogs", "cycles"}
    ajenas = set((manifiesto.get("provides") or {})) - set(COMPONENT_KINDS)
    assert ajenas <= PROPIAS, (
        "provides.%s no es un tipo de componente de spec-kit y no esta documentado "
        "como clave propia" % ", provides.".join(sorted(ajenas - PROPIAS))
    )


def test_la_puerta_de_version_apunta_a_una_serie_que_existe(manifiesto):
    req = str((manifiesto.get("requires") or {}).get("speckit_version") or "")
    assert req, "sin requires.speckit_version no hay puerta de version"
    assert not req.startswith(">=0."), (
        "%r apunta a una serie 0.x: spec-kit va por 1.0.x y esa cifra no se "
        "corresponde con ninguna version publicada" % req
    )


# ─── extension.yml ───────────────────────────────────────────────────────────

def test_el_schema_version_de_la_extension_es_exacto(extension):
    """Aqui la comparacion es de igualdad, no de pertenencia: no hay margen."""
    v = str(extension.get("schema_version"))
    assert v == EXT_SCHEMA_VERSION, (
        "el cargador exige exactamente %r y aqui pone %r" % (EXT_SCHEMA_VERSION, v)
    )


def test_la_extension_trae_las_cuatro_secciones_de_raiz(extension):
    faltan = [c for c in EXT_REQUERIDOS_RAIZ if c not in extension]
    assert not faltan, "faltan secciones: %s" % ", ".join(faltan)


def test_los_metadatos_de_la_extension_son_cadenas(extension):
    """Un `version: 1.0` sin comillas es un float y revienta el validador."""
    meta = extension.get("extension") or {}
    for campo in EXT_REQUERIDOS_META:
        assert campo in meta, "falta extension.%s" % campo
        assert isinstance(meta[campo], str), (
            "extension.%s es %s, no una cadena (¿faltan comillas en el YAML?)"
            % (campo, type(meta[campo]).__name__)
        )
    assert EXT_ID_PATTERN.match(meta["id"]), "extension.id %r invalido" % meta["id"]
    assert SEMVER.match(meta["version"]), "extension.version %r no es semver" % meta["version"]
    if "effect" in meta:
        assert meta["effect"] in VALID_EFFECTS


def test_cada_comando_vive_en_el_espacio_de_nombres_de_la_extension(extension):
    """Un nombre fuera de `speckit.<id>.<algo>` hace fallar la instalacion entera."""
    ident = (extension.get("extension") or {})["id"]
    comandos = ((extension.get("provides") or {}).get("commands")) or []
    assert comandos, "la extension no declara comandos"
    for c in comandos:
        nombre = c.get("name", "")
        m = EXT_COMMAND_PATTERN.match(nombre)
        assert m, "el comando %r no sigue 'speckit.<extension>.<comando>'" % nombre
        assert m.group(1) == ident, (
            "el comando %r usa el espacio %r, pero la extension se llama %r"
            % (nombre, m.group(1), ident)
        )


def test_cada_comando_apunta_a_un_archivo_que_existe(extension):
    for c in ((extension.get("provides") or {}).get("commands")) or []:
        ruta = BUNDLE / "extension" / c.get("file", "")
        assert ruta.is_file(), "%s declara %s y ese archivo no esta" % (c.get("name"), c.get("file"))


# ─── Los dos manifiestos entre si ────────────────────────────────────────────

def test_los_dos_manifiestos_van_a_la_par(manifiesto, extension):
    """La version que el bundle fija para la extension y la que la extension dice
    de si misma tienen que coincidir: si divergen, `bundle update` reinstala una
    version que no es la que hay en disco."""
    del_bundle = next(
        (e.get("version") for e in ((manifiesto.get("provides") or {}).get("extensions") or [])
         if e.get("id") == (extension.get("extension") or {}).get("id")), None)
    propia = (extension.get("extension") or {}).get("version")
    assert del_bundle == propia, (
        "bundle.yml fija la extension en %r y extension.yml dice %r" % (del_bundle, propia)
    )


def test_los_dos_manifiestos_piden_la_misma_serie_de_speckit(manifiesto, extension):
    a = (manifiesto.get("requires") or {}).get("speckit_version")
    b = (extension.get("requires") or {}).get("speckit_version")
    assert a == b, "el bundle pide %r y la extension %r" % (a, b)


# ─── Que el motor y la superficie de comandos no se separen ──────────────────

# Modos internos de verificacion: los ejecuta el CI y los tests, no una persona
# desde un comando. El resto SI necesita puerta de entrada.
MODOS_INTERNOS = {"check-gates", "check-preset", "check-bundle", "check-steps"}


def _modos_del_motor() -> set:
    import subprocess
    import sys
    r = subprocess.run(
        [sys.executable, str(BUNDLE / "core" / "scripts" / "verify_frame.py"), "--help"],
        capture_output=True, text=True,
    )
    m = re.search(r"--mode \{([^}]+)\}", r.stdout)
    assert m, "no se pudo leer la lista de modos de --help"
    return {x.strip() for x in m.group(1).split(",")}


def test_todo_modo_de_usuario_tiene_un_comando_que_lo_invoque():
    """Cuatro modos vivieron sin comando y nadie lo noto.

    `adopt`, `log`, `explain` y `draft-report` se anadieron al motor y quedaron
    inalcanzables desde la extension: existian, estaban probados, y ningun agente
    que usara la superficie de comandos podia llegar a ellos. Una funcion sin
    puerta de entrada es una funcion que no existe para quien la necesita.
    """
    invocados = set()
    for ruta in (BUNDLE / "extension" / "commands").glob("*.md"):
        invocados |= set(re.findall(r"--mode\s+([a-z-]+)", ruta.read_text(encoding="utf-8")))

    huerfanos = sorted(_modos_del_motor() - MODOS_INTERNOS - invocados)
    assert not huerfanos, (
        "estos modos no los invoca ningun comando de extension/commands/: %s" % huerfanos
    )


def test_no_hay_comandos_que_invoquen_modos_inexistentes():
    """El fallo simetrico: un comando que llama a un modo que se renombro o borro."""
    modos = _modos_del_motor()
    rotos = []
    for ruta in (BUNDLE / "extension" / "commands").glob("*.md"):
        for modo in re.findall(r"--mode\s+([a-z-]+)", ruta.read_text(encoding="utf-8")):
            if modo not in modos:
                rotos.append("%s -> --mode %s" % (ruta.name, modo))
    assert not rotos, "comandos que invocan modos que el motor no tiene: %s" % rotos


def test_cada_comando_declarado_apunta_a_un_archivo_y_al_reves():
    """Un .md que nadie declara no se instala: es documentacion muerta."""
    ext = yaml.safe_load((BUNDLE / "extension" / "extension.yml").read_text(encoding="utf-8"))
    declarados = {c["file"].split("/")[-1]
                  for c in ((ext.get("provides") or {}).get("commands") or [])}
    en_disco = {p.name for p in (BUNDLE / "extension" / "commands").glob("*.md")}
    assert not (en_disco - declarados), (
        "archivos de comando que extension.yml no declara: %s" % sorted(en_disco - declarados)
    )
    assert not (declarados - en_disco), (
        "comandos declarados sin archivo: %s" % sorted(declarados - en_disco)
    )
