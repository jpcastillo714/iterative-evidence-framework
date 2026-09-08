"""Un incremento no puede quedarse sin ninguna salida legitima.

Medido contra una memoria de titulo real. Su `data-contract.yml` —13 KB de contenido
bueno, organizado por capa semantica del dominio— cerraba las tres puertas a la vez:

    verify-step   -> FAIL  estructura valida (vacio)
    complete-step -> ERROR: el paso 2b no se puede dar por terminado
    advance       -> ERROR: el paso 2b esta IN_PROGRESS

La unica salida era editar `state.yml` a mano, que es justo lo que el framework prohibe.
Un framework que obliga a incumplir su propia regla central no se usa mal: se deja de
usar. Y el codigo ya prometia la solucion —«un preset puede aportar su propio
validador»— sin que ese mecanismo existiera en ninguna parte.

Ahora hay dos salidas, y son distintas a proposito:

  `structure: free`  el preset declara que la forma es del dominio. Es la limpia.
  `--force --reason` se acepta un artefacto que no valida, y queda registrado. Es la
                     de emergencia, y `doctor` no la olvida.
"""

from __future__ import annotations

import sys

import yaml

from conftest import BUNDLE, correr

CONTRATO_DEL_DOMINIO = """\
capas:
  telemetria_cruda:
    variables: [nMode, nStatus, lrPosActual]
    unidades: grados
  derivadas:
    variables: [q_paralactico, residuo]
"""


def _en_el_contrato(tmp_path):
    """Un `build` parado en el paso 3, con un contrato que el nucleo no reconoce.

    Se usa el ciclo `build` y no `exploration` a proposito: el 2b de una exploracion
    declara `structure: free`, asi que ahi ya no hay nada que forzar. El callejon sin
    salida solo puede darse donde el nucleo si valida la forma.
    """
    d = tmp_path / "proj"
    d.mkdir(parents=True, exist_ok=True)
    correr("--mode", "init", "--project-dir", str(d), "--preset", "research",
           "--layout", "flat", "--initiative-name", "M")
    correr("--mode", "new-increment", "--project-dir", str(d),
           "--type", "build", "--name", "Pipeline")
    dir_inc = d / "initiative" / "increments" / "001_pipeline"
    (dir_inc / "charter.md").write_text("# Charter\n", encoding="utf-8")
    (dir_inc / "inspection-report.md").write_text("# Inspeccion\n", encoding="utf-8")
    (dir_inc / "data-contract.yml").write_text(CONTRATO_DEL_DOMINIO, encoding="utf-8")
    return d


def _pasos(d):
    doc = yaml.safe_load((d / "initiative" / "state.yml").read_text(encoding="utf-8"))
    return doc["increments"][0]["steps"]


def _inc(d):
    doc = yaml.safe_load((d / "initiative" / "state.yml").read_text(encoding="utf-8"))
    return doc["increments"][0]


# ─── El mensaje ──────────────────────────────────────────────────────────────

def test_no_llama_vacio_a_un_archivo_que_tiene_contenido(tmp_path):
    """Decir `vacio` de un archivo de 13 KB manda a buscar el problema donde no esta."""
    d = _en_el_contrato(tmp_path)
    salida = correr("--mode", "verify-step", "--project-dir", str(d), "--step", "3").stdout
    assert "vacio" not in salida
    assert "no reconocida" in salida


def test_el_error_ensena_las_dos_salidas(tmp_path):
    """Un callejon sin salida documentado deja de ser un callejon sin salida."""
    d = _en_el_contrato(tmp_path)
    err = correr("--mode", "complete-step", "--project-dir", str(d), "--step", "3").stderr
    assert "structure: free" in err, "la salida limpia"
    assert "--force" in err, "la de emergencia"
    assert "saltarte trabajo que falta" in err, (
        "tiene que decir para que NO sirve, o --force se vuelve el camino facil"
    )


# ─── La salida limpia: structure: free ───────────────────────────────────────

def test_un_paso_puede_declarar_que_la_forma_es_del_dominio(tmp_path):
    """El punto de extension que el docstring prometia y no existia.

    Se prueba contra la ruta real —`verificar_artefacto`, la misma que usan
    `verify-step` y `complete-step`— y no contra una funcion auxiliar, porque lo que
    importa es que el motor cambie de opinion, no que exista un campo.
    """
    sys.path.insert(0, str(BUNDLE / "core" / "scripts"))
    from dataclasses import replace

    import ief_preset
    import verify_frame

    d = _en_el_contrato(tmp_path)
    preset = ief_preset.cargar_preset("research", BUNDLE)
    # El paso 3 del `build`, que conserva la validacion estricta: es donde se puede
    # comprobar que el motor cambia de opinion segun lo declarado.
    paso = next(x for x in preset.pasos("build") if x.clave == "3_data_contracts")
    assert paso.estructura == "core", "por defecto el nucleo si valida la forma"

    fallos = [n for _, n, ok in
              verify_frame.verificar_artefacto(preset, "001_pipeline", paso, d) if not ok]
    assert fallos, "sin declararlo, el nucleo sigue exigiendo su forma"

    libre = replace(paso, estructura="free")
    fallos_libre = [n for _, n, ok in
                    verify_frame.verificar_artefacto(preset, "001_pipeline", libre, d)
                    if not ok]
    assert not fallos_libre, "declarado `free`, el nucleo no opina de la forma"


def test_el_preset_puede_declararlo_en_su_yaml():
    """No basta con que el motor lo respete: hay que poder escribirlo en un preset.

    Se lee la clave inglesa y la castellana, como el resto de campos de un paso.
    """
    sys.path.insert(0, str(BUNDLE / "core" / "scripts"))
    from ief_preset import _paso_desde_dict

    base = {"key": "3_data_contracts", "ref": "2b", "name": "Contrato",
            "artifact": "data-contract.yml"}

    assert _paso_desde_dict(base, "test").estructura == "core", (
        "sin declarar nada, el nucleo valida: la excepcion se pide, no se hereda"
    )
    assert _paso_desde_dict({**base, "structure": "free"}, "test").estructura == "free"
    assert _paso_desde_dict({**base, "estructura": "FREE"}, "test").estructura == "free"


# ─── La salida de emergencia: --force ────────────────────────────────────────

def test_force_sin_motivo_se_rechaza(tmp_path):
    """Sin el motivo, `--force` seria una forma silenciosa de mentir."""
    d = _en_el_contrato(tmp_path)
    r = correr("--mode", "complete-step", "--project-dir", str(d), "--step", "3", "--force")
    assert r.returncode != 0
    assert "--reason" in r.stderr
    assert _pasos(d)["3_data_contracts"] != "COMPLETED"


def test_force_con_motivo_desatasca_el_incremento(tmp_path):
    d = _en_el_contrato(tmp_path)
    r = correr("--mode", "complete-step", "--project-dir", str(d), "--step", "3",
               "--force", "--reason", "el contrato va por capa semantica del dominio")
    assert r.returncode == 0, r.stdout + r.stderr
    assert _pasos(d)["3_data_contracts"] == "COMPLETED"
    assert "FORZADO" in r.stdout, "forzar no puede pasar desapercibido"


def test_lo_forzado_queda_escrito_con_su_motivo(tmp_path):
    d = _en_el_contrato(tmp_path)
    correr("--mode", "complete-step", "--project-dir", str(d), "--step", "3",
           "--force", "--reason", "forma del dominio")
    forzados = _inc(d).get("forced_steps") or {}
    assert "3_data_contracts" in forzados
    assert forzados["3_data_contracts"]["reason"] == "forma del dominio"
    assert forzados["3_data_contracts"]["failed"], "se guarda QUE fallo, no solo que se forzo"


def test_doctor_no_olvida_un_paso_forzado(tmp_path):
    """Un paso aceptado a la fuerza no puede volver a parecer un paso normal."""
    d = _en_el_contrato(tmp_path)
    correr("--mode", "complete-step", "--project-dir", str(d), "--step", "3",
           "--force", "--reason", "forma del dominio")
    salida = correr("--mode", "doctor", "--project-dir", str(d)).stdout
    assert "3_data_contracts" in salida
    assert "forma del dominio" in salida


def test_force_no_se_aplica_a_lo_que_si_valida(tmp_path):
    """`--force` cubre lo que falla; no es un modo alternativo de trabajar."""
    d = _en_el_contrato(tmp_path)
    r = correr("--mode", "complete-step", "--project-dir", str(d), "--step", "1",
               "--force", "--reason", "innecesario")
    assert r.returncode == 0
    assert "FORZADO" not in r.stdout
    assert not (_inc(d).get("forced_steps") or {}), "nada que forzar, nada que registrar"


# ─── Donde se aplica la excepcion, y donde no ────────────────────────────────

def test_la_exploracion_deja_libre_su_contrato_y_el_build_no():
    """La distincion no es cosmetica: los dos contratos sirven para cosas distintas.

    El 2b de una exploracion formaliza LO QUE SE ENCONTRO —capas semanticas, canales,
    huecos conocidos— y eso es del dominio. El paso 3 de un `build` gobierna un pipeline
    que alguien va a mantener, y ahi la forma generica es justo lo que permite
    comprobarlo. Aflojar los dos habria sido tirar la validacion entera por un caso.
    """
    sys.path.insert(0, str(BUNDLE / "core" / "scripts"))
    import ief_preset

    for pid in ("generic", "research", "analysis", "product"):
        p = ief_preset.cargar_preset(pid, BUNDLE)

        if "exploration" in p.tipos_de_ciclo():
            expl = next(x for x in p.pasos("exploration") if x.clave == "2b_data_contract")
            assert expl.estructura == "free", (
                "%s: el contrato de una exploracion es del dominio" % pid
            )

        build = next((x for x in p.pasos("build") if x.artefacto == "data-contract.yml"), None)
        if build is not None:
            assert build.estructura == "core", (
                "%s: el contrato de un `build` gobierna un pipeline y si se valida" % pid
            )
