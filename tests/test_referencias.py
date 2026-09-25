"""Toda decisión de diseño se justifica con una referencia que existe.

`docs/REFERENCIAS.md` es la bibliografía del bundle; `docs/decisiones/ADR-*.md`, las
decisiones que se apoyan en ella. Estos tests hacen cumplir tres cosas:

1. Una cita `[@clave]` en cualquier documento apunta a una entrada que existe.
2. Cada entrada dice qué es (revisada por pares, preprint...), dónde está, cuándo se
   verificó y qué hallazgo concreto se usa de ella, con su ubicación en el trabajo.
3. Cada decisión tiene las secciones que permiten juzgarla, incluida la que dice hasta
   dónde llega la evidencia, y cita al menos una referencia en su evidencia.

Es la garantía 4 del framework (trazabilidad) aplicada al propio framework: una
decisión que no dice de dónde viene no se puede revisar, solo creer.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from conftest import BUNDLE

REFERENCIAS = BUNDLE / "docs" / "REFERENCIAS.md"
DECISIONES = BUNDLE / "docs" / "decisiones"

IGNORAR = {".git", "__pycache__", ".pytest_cache", "node_modules", ".venv",
           ".claude", "worktrees"}

CITA = re.compile(r"\[@([a-z0-9][a-z0-9-]*)\]")
ENTRADA = re.compile(r"^### \[@([a-z0-9][a-z0-9-]*)\]\s*$", re.M)
ESTADOS_REF = {"revisado por pares", "preprint", "ensayo", "norma", "documentación técnica"}
ESTADOS_ADR = re.compile(r"^(Propuesta|Aceptada|Rechazada|Reemplazada por ADR-\d{3})\b")
SECCIONES_ADR = ["Estado", "Contexto", "Decisión", "Evidencia",
                 "Límites de la evidencia", "Alternativas descartadas", "Cómo se verifica"]


def _entradas() -> dict:
    """{clave: texto de la entrada}, en el orden del archivo."""
    texto = REFERENCIAS.read_text(encoding="utf-8")
    marcas = list(ENTRADA.finditer(texto))
    entradas = {}
    for i, m in enumerate(marcas):
        fin = marcas[i + 1].start() if i + 1 < len(marcas) else len(texto)
        # Una entrada termina donde empieza otra, o en el siguiente título de nivel 2.
        cuerpo = texto[m.end():fin]
        corte = re.search(r"^## ", cuerpo, re.M)
        entradas[m.group(1)] = cuerpo[: corte.start()] if corte else cuerpo
    return entradas


def _sin_codigo(texto: str) -> str:
    """Quita bloques y fragmentos de código: un `[@clave]` de ejemplo no es una cita."""
    texto = re.sub(r"^```.*?^```", "", texto, flags=re.M | re.S)
    return re.sub(r"`[^`\n]*`", "", texto)


def _citas(ruta: Path) -> list:
    return CITA.findall(_sin_codigo(ruta.read_text(encoding="utf-8", errors="ignore")))


def _documentos():
    for ruta in BUNDLE.rglob("*.md"):
        if any(p in ruta.parts for p in IGNORAR) or ruta == REFERENCIAS:
            continue
        yield ruta


def _adrs():
    return sorted(DECISIONES.glob("ADR-*.md"))


def _secciones(texto: str) -> dict:
    """{título de sección de nivel 2: cuerpo}."""
    partes = re.split(r"^## (.+?)\s*$", texto, flags=re.M)
    return {partes[i].strip(): partes[i + 1] for i in range(1, len(partes) - 1, 2)}


# ─── La bibliografía ─────────────────────────────────────────────────────────

def test_la_bibliografia_existe_y_no_esta_vacia():
    assert REFERENCIAS.exists(), "falta docs/REFERENCIAS.md"
    assert _entradas(), "docs/REFERENCIAS.md no tiene entradas `### [@clave]`"


def test_no_hay_claves_repetidas():
    texto = REFERENCIAS.read_text(encoding="utf-8")
    claves = ENTRADA.findall(texto)
    repetidas = sorted({c for c in claves if claves.count(c) > 1})
    assert not repetidas, f"claves repetidas en REFERENCIAS.md: {repetidas}"


@pytest.mark.parametrize("clave", sorted(_entradas()) if REFERENCIAS.exists() else [])
def test_cada_entrada_dice_que_es_donde_esta_y_que_se_usa(clave):
    cuerpo = _entradas()[clave]
    faltan = [c for c in ("**Cita:**", "**Enlace:**", "**Estado:**",
                          "**Verificado:**", "**Hallazgos que se usan:**")
              if c not in cuerpo]
    assert not faltan, f"[@{clave}] no tiene: {faltan}"

    enlace = re.search(r"\*\*Enlace:\*\*\s*(\S+)", cuerpo).group(1)
    assert enlace.startswith("https://"), f"[@{clave}] enlace no es https: {enlace}"

    estado = re.search(r"\*\*Estado:\*\*\s*([^.\n(]+)", cuerpo).group(1).strip().lower()
    assert estado in ESTADOS_REF, (
        f"[@{clave}] estado `{estado}`; válidos: {sorted(ESTADOS_REF)}. "
        "Un preprint se declara como tal: no es lo mismo que un trabajo revisado."
    )

    assert re.search(r"\*\*Verificado:\*\*\s*\d{4}-\d{2}-\d{2}", cuerpo), (
        f"[@{clave}] sin fecha de verificación AAAA-MM-DD"
    )

    # Cada hallazgo dice dónde está en el trabajo: una cita sin ubicación no se revisa.
    hallazgos = cuerpo.split("**Hallazgos que se usan:**", 1)[1]
    items = re.findall(r"^\s*- (.+)$", hallazgos, re.M)
    assert items, f"[@{clave}] no lista ningún hallazgo"
    sin_ubicacion = [h for h in items if not re.match(r"\(.+?\)", h)]
    assert not sin_ubicacion, (
        f"[@{clave}] hallazgos sin ubicación entre paréntesis al inicio "
        f"(sección, tabla, página): {sin_ubicacion}"
    )


def test_toda_cita_apunta_a_una_entrada_que_existe():
    conocidas = set(_entradas())
    rotas = []
    for doc in _documentos():
        for clave in _citas(doc):
            if clave not in conocidas:
                rotas.append(f"{doc.relative_to(BUNDLE)}: [@{clave}]")
    assert not rotas, f"citas a referencias que no existen: {rotas}"


def test_ninguna_entrada_queda_sin_citar():
    """Una referencia que ningún documento usa es decoración: o se cita, o se quita."""
    citadas = set()
    for doc in _documentos():
        citadas |= set(_citas(doc))
    huerfanas = sorted(set(_entradas()) - citadas)
    assert not huerfanas, f"referencias que nadie cita: {huerfanas}"


# ─── Las decisiones ──────────────────────────────────────────────────────────

def test_hay_un_indice_de_decisiones():
    assert (DECISIONES / "README.md").exists(), "falta docs/decisiones/README.md"


@pytest.mark.parametrize("adr", _adrs(), ids=lambda p: p.stem)
def test_cada_decision_tiene_las_secciones_que_permiten_juzgarla(adr):
    texto = adr.read_text(encoding="utf-8")
    secciones = _secciones(texto)
    faltan = [s for s in SECCIONES_ADR if s not in secciones]
    assert not faltan, f"{adr.name} no tiene las secciones: {faltan}"

    estado = secciones["Estado"].strip()
    assert ESTADOS_ADR.match(estado), (
        f"{adr.name}: estado `{estado.splitlines()[0] if estado else ''}`. "
        "Válidos: Propuesta, Aceptada, Rechazada, Reemplazada por ADR-NNN."
    )

    assert CITA.search(_sin_codigo(secciones["Evidencia"])), (
        f"{adr.name}: la sección Evidencia no cita ninguna referencia `[@clave]`"
    )
    assert secciones["Límites de la evidencia"].strip(), (
        f"{adr.name}: una decisión que no dice hasta dónde llega su evidencia la exagera"
    )


@pytest.mark.parametrize("adr", _adrs(), ids=lambda p: p.stem)
def test_cada_decision_figura_en_el_indice(adr):
    indice = (DECISIONES / "README.md").read_text(encoding="utf-8")
    assert adr.name in indice, f"{adr.name} no figura en docs/decisiones/README.md"
