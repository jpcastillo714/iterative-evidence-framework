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


def _en_el_paso_2b(tmp_path):
    """Un incremento de exploracion parado en el contrato de datos."""
    d = tmp_path / "proj"
    d.mkdir(parents=True, exist_ok=True)
    correr("--mode", "init", "--project-dir", str(d), "--preset", "research",
           "--layout", "flat", "--initiative-name", "M")
    correr("--mode", "new-increment", "--project-dir", str(d),
           "--type", "exploration", "--name", "EDA")
    dir_inc = d / "initiative" / "increments" / "001_eda"
    (dir_inc / "objective.md").write_text("# Objetivo\n", encoding="utf-8")
    (dir_inc / "analysis.md").write_text("# Analisis\n", encoding="utf-8")
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
    d = _en_el_paso_2b(tmp_path)
    salida = correr("--mode", "verify-step", "--project-dir", str(d), "--step", "2b").stdout
    assert "vacio" not in salida
    assert "no reconocida" in salida


def test_el_error_ensena_las_dos_salidas(tmp_path):
    """Un callejon sin salida documentado deja de ser un callejon sin salida."""
    d = _en_el_paso_2b(tmp_path)
    err = correr("--mode", "complete-step", "--project-dir", str(d), "--step", "2b").stderr
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

    d = _en_el_paso_2b(tmp_path)
    preset = ief_preset.cargar_preset("research", BUNDLE)
    paso = next(x for x in preset.pasos("exploration") if x.clave == "2b_data_contract")
    assert paso.estructura == "core", "por defecto el nucleo si valida la forma"

    fallos = [n for _, n, ok in
              verify_frame.verificar_artefacto(preset, "001_eda", paso, d) if not ok]
    assert fallos, "sin declararlo, el nucleo sigue exigiendo su forma"

    libre = replace(paso, estructura="free")
    fallos_libre = [n for _, n, ok in
                    verify_frame.verificar_artefacto(preset, "001_eda", libre, d)
                    if not ok]
    assert not fallos_libre, "declarado `free`, el nucleo no opina de la forma"


def test_el_preset_puede_declararlo_en_su_yaml():
    """No basta con que el motor lo respete: hay que poder escribirlo en un preset.

    Se lee la clave inglesa y la castellana, como el resto de campos de un paso.
    """
    sys.path.insert(0, str(BUNDLE / "core" / "scripts"))
    from ief_preset import _paso_desde_dict

    base = {"key": "2b_data_contract", "ref": "2b", "name": "Contrato",
            "artifact": "data-contract.yml"}

    assert _paso_desde_dict(base, "test").estructura == "core", (
        "sin declarar nada, el nucleo valida: la excepcion se pide, no se hereda"
    )
    assert _paso_desde_dict({**base, "structure": "free"}, "test").estructura == "free"
    assert _paso_desde_dict({**base, "estructura": "FREE"}, "test").estructura == "free"


# ─── La salida de emergencia: --force ────────────────────────────────────────

def test_force_sin_motivo_se_rechaza(tmp_path):
    """Sin el motivo, `--force` seria una forma silenciosa de mentir."""
    d = _en_el_paso_2b(tmp_path)
    r = correr("--mode", "complete-step", "--project-dir", str(d), "--step", "2b", "--force")
    assert r.returncode != 0
    assert "--reason" in r.stderr
    assert _pasos(d)["2b_data_contract"] != "COMPLETED"


def test_force_con_motivo_desatasca_el_incremento(tmp_path):
    d = _en_el_paso_2b(tmp_path)
    r = correr("--mode", "complete-step", "--project-dir", str(d), "--step", "2b",
               "--force", "--reason", "el contrato va por capa semantica del dominio")
    assert r.returncode == 0, r.stdout + r.stderr
    assert _pasos(d)["2b_data_contract"] == "COMPLETED"
    assert "FORZADO" in r.stdout, "forzar no puede pasar desapercibido"


def test_lo_forzado_queda_escrito_con_su_motivo(tmp_path):
    d = _en_el_paso_2b(tmp_path)
    correr("--mode", "complete-step", "--project-dir", str(d), "--step", "2b",
           "--force", "--reason", "forma del dominio")
    forzados = _inc(d).get("forced_steps") or {}
    assert "2b_data_contract" in forzados
    assert forzados["2b_data_contract"]["reason"] == "forma del dominio"
    assert forzados["2b_data_contract"]["failed"], "se guarda QUE fallo, no solo que se forzo"


def test_doctor_no_olvida_un_paso_forzado(tmp_path):
    """Un paso aceptado a la fuerza no puede volver a parecer un paso normal."""
    d = _en_el_paso_2b(tmp_path)
    correr("--mode", "complete-step", "--project-dir", str(d), "--step", "2b",
           "--force", "--reason", "forma del dominio")
    salida = correr("--mode", "doctor", "--project-dir", str(d)).stdout
    assert "2b_data_contract" in salida
    assert "forma del dominio" in salida


def test_force_no_se_aplica_a_lo_que_si_valida(tmp_path):
    """`--force` cubre lo que falla; no es un modo alternativo de trabajar."""
    d = _en_el_paso_2b(tmp_path)
    r = correr("--mode", "complete-step", "--project-dir", str(d), "--step", "1",
               "--force", "--reason", "innecesario")
    assert r.returncode == 0
    assert "FORZADO" not in r.stdout
    assert not (_inc(d).get("forced_steps") or {}), "nada que forzar, nada que registrar"
