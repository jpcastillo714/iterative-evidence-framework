"""Promover reglas desde un ciclo que no tiene compuertas.

El ciclo de vida de las reglas empezaba de hecho en el paso 4 del ciclo `build`. Pero una
exploracion produce verdades del dominio que condicionan todo lo que venga despues, y no
tenia por donde subirlas: se quedaban como prosa en `findings.md`, sin poder citarse como
evidencia, ni entrar en deteccion de conflictos, ni marcarse como superadas.

La mecanica ya estaba —`merge-increment` lee el `rules.yml` de cualquier incremento— pero
`exploration` y `task` no tienen NINGUNA compuerta y `prototype` solo la del charter:
promover desde ellos metia reglas que gobiernan el proyecto entero sin que nadie firmara.

La correccion no anade ceremonia a la exploracion. Pone la firma donde esta la
consecuencia: explorar no obliga a nadie, promover si.
"""

from __future__ import annotations

import yaml

from conftest import correr

REGLA = {"rules": [{
    "id": "RUL-001-001",
    "statement": "nStatus se descarta: es constante 0 en los cuatro telescopios",
    "rationale": "Sin varianza no aporta informacion; medido en UT1-UT4",
    "applies_to": "telemetria_adc",
    "scope": "project",
    "status": "proposed",
}]}


def _con_reglas_propuestas(tmp_path, tipo, nombre="EDA"):
    d = tmp_path / "proj"
    d.mkdir(exist_ok=True)
    assert correr("--mode", "init", "--project-dir", str(d), "--preset", "research",
                  "--layout", "flat", "--initiative-name", "M").returncode == 0
    assert correr("--mode", "new-increment", "--project-dir", str(d),
                  "--type", tipo, "--name", nombre).returncode == 0
    estado = yaml.safe_load((d / "initiative" / "state.yml").read_text(encoding="utf-8"))
    slug = estado["increments"][0]["slug"]
    dir_inc = d / "initiative" / "increments" / slug
    dir_inc.mkdir(parents=True, exist_ok=True)
    (dir_inc / "rules.yml").write_text(
        yaml.safe_dump(REGLA, sort_keys=False, allow_unicode=True), encoding="utf-8")
    return d, slug


def _vigentes(d):
    f = d / "initiative" / "specs" / "rules.yml"
    if not f.exists():
        return []
    return (yaml.safe_load(f.read_text(encoding="utf-8")) or {}).get("rules") or []


def test_una_exploracion_no_promueve_sin_firma(tmp_path):
    """Es la garantia entera: una regla promovida rige todo el proyecto."""
    d, _ = _con_reglas_propuestas(tmp_path, "exploration")
    r = correr("--mode", "merge-increment", "--project-dir", str(d))
    assert r.returncode != 0
    assert not _vigentes(d), "no debe haber promovido nada"


def test_el_error_dice_como_conseguir_la_firma(tmp_path):
    """Un error que no dice como salir de el manda a improvisar."""
    d, slug = _con_reglas_propuestas(tmp_path, "exploration")
    err = correr("--mode", "merge-increment", "--project-dir", str(d)).stderr
    assert "--by" in err
    assert slug in err
    assert "no es aprobar" in err, (
        "tiene que decir que pedirlo no es firmarlo: es la racionalizacion "
        "por la que un agente firma en nombre del usuario"
    )


def test_con_firma_la_regla_sube_y_conserva_su_procedencia(tmp_path):
    d, slug = _con_reglas_propuestas(tmp_path, "exploration")
    r = correr("--mode", "merge-increment", "--project-dir", str(d), "--by", "JP")
    assert r.returncode == 0, r.stdout + r.stderr

    reglas = _vigentes(d)
    assert len(reglas) == 1
    assert reglas[0]["status"] == "active"
    assert (reglas[0].get("_origen") or {}).get("increment") == slug, (
        "sin procedencia, dentro de un ano nadie sabe de donde salio la regla"
    )


def test_la_firma_queda_en_el_historial(tmp_path):
    """«Quien aprobo esto» tiene que tener respuesta despues, no solo en pantalla."""
    d, _ = _con_reglas_propuestas(tmp_path, "exploration")
    correr("--mode", "merge-increment", "--project-dir", str(d), "--by", "JP")
    estado = yaml.safe_load((d / "initiative" / "state.yml").read_text(encoding="utf-8"))
    merges = [h for h in estado["history"] if h.get("action") == "MERGE_INCREMENT"]
    assert merges and merges[-1].get("approved_by") == "JP"


def test_un_build_no_pide_firma_extra(tmp_path):
    """Su paso 4 lleva compuerta: exigir otra firma seria pedir lo mismo dos veces."""
    d, slug = _con_reglas_propuestas(tmp_path, "build", nombre="Pipeline")
    estado_f = d / "initiative" / "state.yml"
    estado = yaml.safe_load(estado_f.read_text(encoding="utf-8"))
    inc = estado["increments"][0]
    for p in inc["steps"]:
        inc["steps"][p] = "APPROVED"
    estado_f.write_text(yaml.safe_dump(estado, sort_keys=False, allow_unicode=True),
                        encoding="utf-8")

    r = correr("--mode", "merge-increment", "--project-dir", str(d))
    assert r.returncode == 0, r.stdout + r.stderr
    assert len(_vigentes(d)) == 1


def test_sin_reglas_no_se_pide_firma(tmp_path):
    """La firma cubre reglas; sin reglas no hay nada que firmar.

    Promover un incremento vacio ya era un error antes de todo esto —«no tiene
    artefactos promovibles»— y esta bien que lo sea. Lo que este test vigila es que
    la exigencia de firma no se dispare por el motivo equivocado: el problema es que
    no hay nada que promover, no que falte una aprobacion.
    """
    d = tmp_path / "vacio"
    d.mkdir()
    correr("--mode", "init", "--project-dir", str(d), "--preset", "research",
           "--layout", "flat", "--initiative-name", "M")
    correr("--mode", "new-increment", "--project-dir", str(d),
           "--type", "exploration", "--name", "Sin reglas")
    r = correr("--mode", "merge-increment", "--project-dir", str(d))
    assert "promovibles" in r.stderr
    assert "--by" not in r.stderr, "no se pide firma cuando no hay reglas que aprobar"
