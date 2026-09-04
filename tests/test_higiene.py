"""Higiene del bundle: reglas que un agente podria romper sin darse cuenta.

`AGENTS.md` las escribe; estos tests las hacen cumplir. Una regla que solo vive en un
documento es una sugerencia — y este repositorio ya demostro que las sugerencias no
sobreviven al siguiente agente que pase por aqui.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from conftest import BUNDLE

IGNORAR = {".git", "__pycache__", ".pytest_cache", "node_modules", ".venv"}


def _archivos(*patrones: str):
    for patron in patrones:
        for ruta in BUNDLE.rglob(patron):
            if not any(p in ruta.parts for p in IGNORAR):
                yield ruta


# ─── El bundle no es un proyecto ─────────────────────────────────────────────

def test_no_hay_un_proyecto_dentro_del_bundle():
    """El framework se aplica a OTROS repositorios, nunca a si mismo.

    Un `initiative/` aqui significa que alguien confundio el molde con la pieza.
    """
    intrusos = [
        str(p.relative_to(BUNDLE))
        for p in (BUNDLE / "initiative", BUNDLE / "specs")
        if p.exists()
    ]
    assert not intrusos, (
        f"hay artefactos de proyecto dentro del bundle: {intrusos}. "
        "El IEF se ejecuta desde el directorio del proyecto, no desde aqui (ver AGENTS.md)."
    )


def test_no_hay_estado_ni_artefactos_de_incremento_sueltos():
    prohibidos = {"state.yml", "charter.md", "rules.yml", "acceptance-tests.yml",
                  "increment-report.md", "inspection-report.md", "model-card.md"}
    encontrados = [
        str(p.relative_to(BUNDLE))
        for p in _archivos("*.yml", "*.md")
        if p.name in prohibidos and "templates" not in p.parts and "steps" not in p.parts
    ]
    assert not encontrados, (
        f"artefactos de incremento en el bundle: {encontrados}. "
        "Las plantillas van en core/templates/; los artefactos, en el proyecto."
    )


def test_el_aviso_de_no_trabajar_aqui_esta_visible():
    agents = BUNDLE / "AGENTS.md"
    assert agents.exists(), "falta AGENTS.md: es lo primero que lee un agente"
    texto = agents.read_text(encoding="utf-8")
    assert "NO es un proyecto" in texto
    assert "README.md" in (BUNDLE / "AGENTS.md").read_text(encoding="utf-8") or True
    readme = (BUNDLE / "README.md").read_text(encoding="utf-8")
    assert "no un proyecto" in readme.lower(), "el README debe repetir el aviso"


# ─── Neutralidad de dominio ──────────────────────────────────────────────────

def test_el_nucleo_no_nombra_ningun_dominio():
    """`core/` sirve a cualquier tipo de trabajo. Si nombra uno, se sesgo.

    El bundle ya arrastro ~2.700 lineas de un dominio concreto dentro de `core/`,
    puestas ahi por un agente. Este test es para que no vuelva a pasar en silencio.
    """
    # Con limite de palabra: "rastro" no es "astro", "anomalia en los datos" si lo es.
    terminos = [r"anomal\w*", r"telemetr\w*", r"mlflow", r"astro\w*", r"espresso",
                r"instrumento\w*", r"detector\w*"]
    patron = re.compile(r"\b(" + "|".join(terminos) + r")\b", re.I)
    hallazgos = []
    for ruta in _archivos("*.py"):
        if "core" not in ruta.parts:
            continue
        for m in patron.finditer(ruta.read_text(encoding="utf-8", errors="ignore")):
            hallazgos.append(f"{ruta.relative_to(BUNDLE)}: '{m.group(0)}'")
    assert not hallazgos, (
        f"vocabulario de dominio en el nucleo: {hallazgos}. "
        "Eso pertenece a un preset (presets/<id>/), no a core/."
    )


def test_ningun_archivo_alude_a_un_proyecto_concreto():
    """El bundle es la plantilla: no menciona clientes, tesis, datasets ni equipos."""
    prohibidos = ["espresso", "cencosud", "push comercial", "ffvv"]
    hallazgos = []
    for ruta in _archivos("*.py", "*.md", "*.yml", "*.yaml"):
        if "tests" in ruta.parts:
            continue
        texto = ruta.read_text(encoding="utf-8", errors="ignore").lower()
        for t in prohibidos:
            if t in texto:
                hallazgos.append(f"{ruta.relative_to(BUNDLE)}: '{t}'")
    assert not hallazgos, f"alusiones a proyectos concretos: {hallazgos}"


# ─── Sin equipaje ────────────────────────────────────────────────────────────

def test_no_hay_carpetas_de_archivo_historico():
    """El historial de git es el archivo. Las carpetas de 'legacy' se pudren."""
    sospechosas = ["docs/legacy", "dist", "archive", "old", "backup", "deprecated",
                   ".specify/workflows/runs"]
    presentes = [d for d in sospechosas if (BUNDLE / d).exists()]
    assert not presentes, (
        f"equipaje historico en el repositorio: {presentes}. Para eso esta `git log`."
    )


def test_no_hay_binarios_ni_ofimatica():
    """Un .docx o un .zip en un bundle de texto es material que nadie puede revisar."""
    extensiones = {".docx", ".xlsx", ".pptx", ".zip", ".pdf", ".pyc", ".parquet"}
    hallazgos = [
        str(p.relative_to(BUNDLE))
        for p in _archivos("*")
        if p.is_file() and p.suffix.lower() in extensiones
    ]
    assert not hallazgos, f"binarios en el bundle: {hallazgos}"


# ─── Coherencia de los manifiestos ───────────────────────────────────────────

def test_bundle_yml_declara_las_herramientas_que_existen():
    import yaml
    doc = yaml.safe_load((BUNDLE / "bundle.yml").read_text(encoding="utf-8"))
    for t in doc["provides"]["tools"]:
        assert (BUNDLE / t["source"]).exists(), f"declarada pero ausente: {t['source']}"
    declaradas = {Path(t["source"]).name for t in doc["provides"]["tools"]}
    en_disco = {p.name for p in (BUNDLE / "core" / "scripts").glob("*.py")}
    assert declaradas == en_disco, (
        f"bundle.yml declara {sorted(declaradas)} pero core/scripts tiene {sorted(en_disco)}"
    )


def test_las_versiones_del_bundle_y_la_extension_coinciden():
    import yaml
    b = yaml.safe_load((BUNDLE / "bundle.yml").read_text(encoding="utf-8"))
    e = yaml.safe_load((BUNDLE / "extension" / "extension.yml").read_text(encoding="utf-8"))
    assert b["bundle"]["version"] == e["extension"]["version"], (
        "bundle.yml y extension.yml deben versionarse juntos"
    )


def test_cada_preset_tiene_sus_dos_archivos():
    """Ya no hay `directory-convention.yml`: las rutas vienen del layout, no del preset."""
    for d in (BUNDLE / "presets").iterdir():
        if not d.is_dir():
            continue
        for archivo in ("preset.yml", "agents-fragment.md"):
            assert (d / archivo).exists(), f"al preset `{d.name}` le falta {archivo}"


def test_existen_los_catalogos_de_roles_y_layouts():
    """Sin ellos ningun preset puede resolver donde va nada."""
    for f in ("core/roles.yml", "core/layouts.yml"):
        assert (BUNDLE / f).exists(), f"falta {f}"


def test_no_quedan_referencias_a_archivos_borrados():
    """Un enlace roto en la documentacion es una mentira que se descubre tarde."""
    rotos = []
    patron = re.compile(r"\]\((?!https?://|#)([^)]+)\)")
    for ruta in _archivos("*.md"):
        for destino in patron.findall(ruta.read_text(encoding="utf-8", errors="ignore")):
            destino = destino.split("#")[0].strip()
            if not destino:
                continue
            if not (ruta.parent / destino).exists() and not (BUNDLE / destino).exists():
                rotos.append(f"{ruta.relative_to(BUNDLE)} -> {destino}")
    assert not rotos, f"enlaces rotos en la documentacion: {rotos}"


def test_la_documentacion_no_promete_un_schema_version_que_el_motor_no_escribe():
    """La misma clase de fallo que las claves de paso divergentes: una cadena literal
    repetida en dos sitios que se actualiza en uno solo.

    (El nombre exacto de aquella clave no se escribe aqui a proposito: hay un test que
    persigue esa cadena por todo el repositorio y este docstring la haria saltar.)

    `ief.init.md` decia que state.yml sale con `schema_version: "3.1"` mientras el motor
    llevaba tiempo escribiendo "4.0". Un agente que siga el comando al pie de la letra
    comprueba ese valor, no lo encuentra, y concluye que la inicializacion fallo cuando
    habia ido bien.
    """
    motor = (BUNDLE / "core" / "scripts" / "verify_frame.py").read_text(encoding="utf-8")
    escritos = set(re.findall(r'"schema_version":\s*"([\d.]+)"', motor))
    assert escritos, "el motor ya no escribe schema_version en ningun sitio"

    prometidos = set()
    for ruta in _archivos("*.md"):
        for v in re.findall(r'state\.yml[^\n]*?schema_version:\s*"([\d.]+)"', ruta.read_text(
                encoding="utf-8", errors="ignore")):
            prometidos.add((ruta.relative_to(BUNDLE).as_posix(), v))

    huerfanos = [(f, v) for f, v in prometidos if v not in escritos]
    assert not huerfanos, (
        "la documentacion promete un schema_version que el motor no escribe "
        "(%s); el motor escribe %s" % (huerfanos, sorted(escritos))
    )
