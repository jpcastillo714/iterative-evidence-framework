"""
Suite de aceptacion del preset `astro-mlops`.

Cubre las cuatro herramientas ejecutables y la coherencia del preset con el resto del
bundle. Se ejecuta con `pytest tests/ -q` y no necesita datos reales: la serie nominal
se genera en memoria.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np
import pytest
import yaml

BUNDLE = Path(__file__).resolve().parent.parent
SCRIPTS = BUNDLE / "presets" / "astro-mlops" / "scripts"
CORE = BUNDLE / "core" / "scripts"


def _cargar(nombre: str, base=None):
    """Importa un script por ruta: los del preset viven fuera del nucleo."""
    base = base or SCRIPTS
    spec = importlib.util.spec_from_file_location(nombre, base / f"{nombre}.py")
    modulo = importlib.util.module_from_spec(spec)
    sys.modules[nombre] = modulo
    spec.loader.exec_module(modulo)
    return modulo


inject = _cargar("inject_faults")
evalmod = _cargar("eval_anomaly")
contrato = _cargar("validate_data_contract")
frame = _cargar("verify_frame", CORE)


# ─────────────────────────────────────────────────────────────────────────────
# Preset
# ─────────────────────────────────────────────────────────────────────────────

def test_preset_existe_y_extiende_academic():
    crudo = yaml.safe_load((BUNDLE / "presets/astro-mlops/preset.yml").read_text(encoding="utf-8"))
    assert crudo["id"] == "astro-mlops"
    assert crudo["extends"] == "academic", "debe heredar la numeracion 00-08 para migrar sin mover archivos"

    preset_mod = _cargar("ief_preset", CORE)
    p = preset_mod.cargar_preset("astro-mlops", BUNDLE)
    assert set(p.tipos_de_ciclo()) == {"build", "exploration"}
    assert [s.ref for s in p.pasos("build") if s.human_gate] == ["1", "4", "5"]


def test_preset_declara_sus_herramientas_y_existen():
    preset_mod = _cargar("ief_preset", CORE)
    p = preset_mod.cargar_preset("astro-mlops", BUNDLE)
    for _, cfg in p.herramientas.items():
        assert (BUNDLE / cfg["script"]).exists(), f"falta {cfg['script']}"
    for tipo in p.tipos_de_ciclo():
        for paso in p.pasos(tipo):
            if paso.plantilla:
                assert (BUNDLE / paso.plantilla).exists(), f"falta {paso.plantilla}"


def test_preset_tiene_convencion_y_fragmento():
    conv = yaml.safe_load(
        (BUNDLE / "presets/astro-mlops/directory-convention.yml").read_text(encoding="utf-8")
    )
    rutas = {d["path"] for d in conv["directories"]}
    # La numeracion heredada de `academic` debe seguir presente.
    assert "00_admin" in rutas and "07_documento" in rutas
    # Y lo que anade el preset.
    assert "05_datos/benchmark_sintetico" in rutas
    assert "06_resultados/experimentos" in rutas
    assert (BUNDLE / "presets/astro-mlops/agents-fragment.md").exists()


def test_bundle_registra_el_preset():
    b = yaml.safe_load((BUNDLE / "bundle.yml").read_text(encoding="utf-8"))
    ids = {p["id"] for p in b["provides"]["presets"]}
    assert "astro-mlops" in ids


def test_extension_registra_el_comando_evidence():
    e = yaml.safe_load((BUNDLE / "extension/extension.yml").read_text(encoding="utf-8"))
    nombres = {c["name"] for c in e["provides"]["commands"]}
    assert "speckit.ief.evidence" in nombres
    assert (BUNDLE / "extension/commands/ief.evidence.md").exists()


# ─────────────────────────────────────────────────────────────────────────────
# Plantillas: deben pasar el validador estructural del propio framework
# ─────────────────────────────────────────────────────────────────────────────

def test_plantilla_telemetria_es_reconocida_por_verify_frame():
    d = yaml.safe_load(
        (BUNDLE / "presets/astro-mlops/templates/data-contract.telemetry.yml").read_text(encoding="utf-8")
    )
    valido, forma = frame.validate_data_contract_shape(d)
    assert valido and forma == "telemetria"


def test_verify_frame_acepta_las_tres_formas_de_contrato():
    assert frame.validate_data_contract_shape(
        {"sources": [{"name": "s", "format": "parquet", "columns": [{"name": "c", "type": "float"}]}]}
    ) == (True, "sources")
    assert frame.validate_data_contract_shape(
        {"schemas": [{"name": "e", "fields": [{"name": "c", "type": "int"}]}]}
    ) == (True, "schemas")
    assert frame.validate_data_contract_shape({}) == (False, "vacio")


def test_plantilla_reglas_detector_cumple_el_vocabulario():
    d = yaml.safe_load(
        (BUNDLE / "presets/astro-mlops/templates/business-rules.detector.yml").read_text(encoding="utf-8")
    )
    ids = [r["id"] for r in d["rules"]]
    assert len(ids) == len(set(ids)), "ids de reglas duplicados"
    for r in d["rules"]:
        assert r["id"].startswith("BR-")
        assert r["description"]
        assert r["priority"].lower() in {"critical", "high", "medium", "low"}
        assert r["status"].lower() in {"draft", "validated", "approved", "deprecated"}


def test_plantilla_criterios_anomalia_es_trazable():
    d = yaml.safe_load(
        (BUNDLE / "presets/astro-mlops/templates/acceptance-tests.anomaly.yml").read_text(encoding="utf-8")
    )
    reglas = {
        r["id"]
        for r in yaml.safe_load(
            (BUNDLE / "presets/astro-mlops/templates/business-rules.detector.yml").read_text(encoding="utf-8")
        )["rules"]
    }
    ids = [t["test_id"] for t in d["tests"]]
    assert len(ids) == len(set(ids))
    for t in d["tests"]:
        assert t["test_id"].startswith("TST-ACC-")
        assert t["given"] and t["when"] and t["then"]
        assert t["linked_rule"] in reglas, f"{t['test_id']} apunta a una regla inexistente"


def test_criterios_incluyen_las_metricas_no_negociables():
    texto = (BUNDLE / "presets/astro-mlops/templates/acceptance-tests.anomaly.yml").read_text(encoding="utf-8")
    for clave in ("falsas_alarmas_max_por_noche", "cobertura_minima", "lead_time_minimo_h"):
        assert clave in texto


# ─────────────────────────────────────────────────────────────────────────────
# inject_faults
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def serie_nominal():
    rng = np.random.default_rng(0)
    return rng.normal(0.0, 1.0, 2000)


def test_sigma_robusto_se_aproxima_a_la_desviacion(serie_nominal):
    assert 0.9 < inject.sigma_robusto(serie_nominal) < 1.1


def test_sigma_robusto_ignora_una_cola_pesada(serie_nominal):
    contaminada = serie_nominal.copy()
    contaminada[:20] = 500.0          # 1% de valores extremos
    robusto = inject.sigma_robusto(contaminada)
    assert robusto < 1.2, "el MAD no deberia arrastrarse por los extremos"
    assert np.std(contaminada) > 10, "la desviacion clasica si se arrastra (por eso usamos MAD)"


@pytest.mark.parametrize("tipo", sorted(inject.MODOS))
def test_cada_modo_solo_toca_su_ventana(serie_nominal, tipo):
    modificada, meta = inject.inyectar(
        serie_nominal, tipo, inicio=500, largo=300, severidad=3.0,
        rng=np.random.default_rng(1),
    )
    assert np.array_equal(modificada[:500], serie_nominal[:500])
    assert np.array_equal(modificada[800:], serie_nominal[800:])
    assert meta["inicio_idx"] == 500 and meta["fin_idx"] == 800
    assert meta["tipo"] == tipo and meta["severidad_sigma"] == 3.0


@pytest.mark.parametrize("tipo", sorted(set(inject.MODOS) - {"dropout"}))
def test_cada_modo_deja_huella_medible(serie_nominal, tipo):
    modificada, _ = inject.inyectar(
        serie_nominal, tipo, inicio=500, largo=300, severidad=4.0,
        rng=np.random.default_rng(1),
    )
    tramo_antes = serie_nominal[500:800]
    tramo_despues = modificada[500:800]
    assert not np.allclose(tramo_antes, tramo_despues), f"{tipo} no modifico nada"


def test_deriva_lenta_corre_la_media_sin_inflar_la_varianza(serie_nominal):
    modificada, _ = inject.inyectar(serie_nominal, "deriva_lenta", 500, 400, 5.0,
                                    rng=np.random.default_rng(2))
    media_antes = float(np.mean(serie_nominal[500:900]))
    media_despues = float(np.mean(modificada[500:900]))
    assert media_despues - media_antes > 1.0


def test_valor_congelado_hunde_la_varianza(serie_nominal):
    """El fallo que los detectores basados en desviacion suelen no ver."""
    modificada, _ = inject.inyectar(serie_nominal, "valor_congelado", 500, 300, 1.0,
                                    rng=np.random.default_rng(3))
    assert float(np.std(modificada[500:800])) < 1e-12
    assert float(np.std(serie_nominal[500:800])) > 0.5


def test_dropout_introduce_nan_solo_dentro_de_la_ventana(serie_nominal):
    modificada, _ = inject.inyectar(serie_nominal, "dropout", 500, 300, 3.0,
                                    rng=np.random.default_rng(4))
    assert np.isnan(modificada[500:800]).any()
    assert not np.isnan(modificada[:500]).any()
    assert not np.isnan(modificada[800:]).any()


def test_inyeccion_es_determinista_con_la_misma_semilla(serie_nominal):
    a, _ = inject.inyectar(serie_nominal, "ruido_creciente", 100, 200, 2.0,
                           rng=np.random.default_rng(7))
    b, _ = inject.inyectar(serie_nominal, "ruido_creciente", 100, 200, 2.0,
                           rng=np.random.default_rng(7))
    assert np.array_equal(a, b), "sin determinismo no hay evidencia reproducible"


def test_tipo_desconocido_es_error_explicito(serie_nominal):
    with pytest.raises(ValueError):
        inject.inyectar(serie_nominal, "falla_inventada", 10, 50, 1.0)


def test_ventanas_disjuntas_no_se_solapan():
    rng = np.random.default_rng(11)
    inicios = inject.ventanas_disjuntas(10000, largo=200, cantidad=10, separacion=50, rng=rng)
    for a, b in zip(inicios, inicios[1:]):
        assert b - (a + 200) >= 50


# ─────────────────────────────────────────────────────────────────────────────
# eval_anomaly
# ─────────────────────────────────────────────────────────────────────────────

def test_tramos_agrupa_runs_contiguos():
    m = np.array([0, 1, 1, 0, 0, 1, 0], dtype=bool)
    assert evalmod.tramos(m) == [(1, 3), (5, 6)]


def test_confirmacion_k_de_n_filtra_excedencias_aisladas():
    excede = np.array([1, 0, 1, 0, 1, 1, 1, 0], dtype=bool)
    conf = evalmod.confirmar_k_de_n(excede, k=3, n=3)
    assert not conf[:6].any(), "tres excedencias salteadas no son una alarma"
    assert conf[6], "tres consecutivas si lo son"


def test_average_precision_perfecta_y_aleatoria():
    y = np.array([0, 0, 1, 1])
    assert evalmod.average_precision(y, np.array([0.1, 0.2, 0.8, 0.9])) == pytest.approx(1.0)
    assert evalmod.average_precision(y, np.array([0.9, 0.8, 0.2, 0.1])) < 0.6


def test_roc_auc_conocido():
    y = np.array([0, 0, 1, 1])
    assert evalmod.roc_auc(y, np.array([0.1, 0.2, 0.8, 0.9])) == pytest.approx(1.0)
    assert evalmod.roc_auc(y, np.array([0.9, 0.8, 0.2, 0.1])) == pytest.approx(0.0)
    assert evalmod.roc_auc(y, np.array([0.5, 0.5, 0.5, 0.5])) == pytest.approx(0.5)


def _escenario(n=1000):
    eventos = [
        {"id": "INJ-001", "tipo": "deriva_lenta", "severidad_sigma": 2.0,
         "inicio": 200, "fin": 260, "inicio_efectivo": 210},
        {"id": "INJ-002", "tipo": "salto_encoder", "severidad_sigma": 4.0,
         "inicio": 600, "fin": 660, "inicio_efectivo": 600},
    ]
    etiqueta = np.zeros(n, dtype=int)
    for e in eventos:
        etiqueta[e["inicio"]:e["fin"]] = 1
    return eventos, etiqueta


def test_detector_perfecto_recall_uno_y_cero_falsas():
    eventos, etiqueta = _escenario()
    scores = etiqueta.astype(float)
    rep = evalmod.evaluar(scores, etiqueta, eventos, np.ones(1000, bool),
                          umbral=0.5, k=1, n_conf=1, cadencia_s=20, horas_por_unidad=10)
    assert rep["por_evento"]["recall"] == 1.0
    assert rep["por_evento"]["alarmas_falsas"] == 0
    assert rep["falsas_alarmas"]["por_unidad"] == 0.0


def test_alarma_fuera_de_evento_cuenta_como_falsa():
    eventos, etiqueta = _escenario()
    scores = etiqueta.astype(float)
    scores[900:910] = 1.0                      # alarma sin evento detras
    rep = evalmod.evaluar(scores, etiqueta, eventos, np.ones(1000, bool),
                          umbral=0.5, k=1, n_conf=1, cadencia_s=20, horas_por_unidad=10)
    assert rep["por_evento"]["alarmas_falsas"] == 1
    assert rep["falsas_alarmas"]["por_unidad"] > 0


def test_abstencion_no_genera_falsas_alarmas():
    """Lo marcado `no_evaluable` no cuenta ni a favor ni en contra (regla BR-003)."""
    eventos, etiqueta = _escenario()
    scores = etiqueta.astype(float)
    scores[900:910] = 1.0
    evaluable = np.ones(1000, bool)
    evaluable[880:930] = False                 # zona fuera del dominio de validez
    rep = evalmod.evaluar(scores, etiqueta, eventos, evaluable,
                          umbral=0.5, k=1, n_conf=1, cadencia_s=20, horas_por_unidad=10)
    assert rep["por_evento"]["alarmas_falsas"] == 0
    assert rep["cobertura"]["fraccion_evaluable"] == pytest.approx(0.95)


def test_point_adjust_infla_y_el_reporte_lo_exhibe():
    """Una sola muestra detectada dentro de un evento largo: el sesgo en accion."""
    eventos, etiqueta = _escenario()
    scores = np.zeros(1000)
    scores[205] = 1.0                          # un unico punto dentro del primer evento
    rep = evalmod.evaluar(scores, etiqueta, eventos, np.ones(1000, bool),
                          umbral=0.5, k=1, n_conf=1, cadencia_s=20, horas_por_unidad=10)
    assert rep["por_punto"]["recall"] < 0.02
    assert rep["point_adjust"]["recall"] == pytest.approx(0.5)
    # La inflacion se mide contra la metrica puntual honesta: una muestra detectada
    # pasa a valer 60. El reporte tiene que exhibir ese salto.
    assert rep["point_adjust"]["f1"] > 10 * rep["por_punto"]["f1"]
    assert rep["point_adjust"]["delta_f1_vs_puntual"] > 0.5
    assert "advertencia" in rep["point_adjust"]


def test_desglose_por_tipo_y_severidad_presente():
    eventos, etiqueta = _escenario()
    rep = evalmod.evaluar(etiqueta.astype(float), etiqueta, eventos, np.ones(1000, bool),
                          umbral=0.5, k=1, n_conf=1, cadencia_s=20, horas_por_unidad=10)
    claves = {(d["tipo"], d["severidad_sigma"]) for d in rep["desglose_por_tipo"]}
    assert ("deriva_lenta", 2.0) in claves and ("salto_encoder", 4.0) in claves


def test_retraso_se_mide_desde_el_inicio_efectivo():
    eventos, etiqueta = _escenario()
    scores = np.zeros(1000)
    scores[220:240] = 1.0                      # alarma 10 muestras tras el inicio efectivo
    rep = evalmod.evaluar(scores, etiqueta, eventos, np.ones(1000, bool),
                          umbral=0.5, k=1, n_conf=1, cadencia_s=20, horas_por_unidad=10)
    assert rep["por_evento"]["retraso_mediano_min"] == pytest.approx(10 * 20 / 60.0, abs=0.01)


# ─────────────────────────────────────────────────────────────────────────────
# validate_data_contract
# ─────────────────────────────────────────────────────────────────────────────

def _contrato_minimo():
    return {
        "fuente": {"cadencia_nominal_s": 20, "acceso": "solo_lectura"},
        "tiempo": {"columna": "timestamp", "monotono": True, "hueco_minimo_reportable_s": 120},
        "canales": {
            "mecanico": {
                "descripcion": "x",
                "residuo": {"clase": "medicion", "tipo": "float", "unidad": "grados",
                            "rango_valido": [-1.0, 1.0]},
            },
            "estado": {
                "modo": {"clase": "comando", "tipo": "categorico", "valores_observados": [0, 1]},
            },
        },
        "dominio_de_validez": {"modelo_base": "x", "condiciones": ["y"]},
        "segmentacion": {"nivel_2_episodio": {"criterio": "z"}},
    }


def test_contrato_valido_no_produce_errores():
    rep = contrato.Reporte()
    contrato.validar_esquema(_contrato_minimo(), rep)
    assert rep.errores == 0


def test_canal_sin_clase_es_error():
    c = _contrato_minimo()
    del c["canales"]["mecanico"]["residuo"]["clase"]
    rep = contrato.Reporte()
    contrato.validar_esquema(c, rep)
    assert rep.errores >= 1


def test_clase_inventada_es_error():
    c = _contrato_minimo()
    c["canales"]["mecanico"]["residuo"]["clase"] = "magica"
    rep = contrato.Reporte()
    contrato.validar_esquema(c, rep)
    assert any(i["check"] == "schema.clase" for i in rep.items if i["nivel"] == "ERROR")


def test_contrato_sin_canal_modelable_es_error():
    """Solo consignas y comandos: no hay senal de salud que modelar."""
    c = _contrato_minimo()
    c["canales"]["mecanico"]["residuo"]["clase"] = "consigna"
    rep = contrato.Reporte()
    contrato.validar_esquema(c, rep)
    assert any(i["check"] == "schema.modelables" for i in rep.items if i["nivel"] == "ERROR")


def test_rango_invertido_es_error():
    c = _contrato_minimo()
    c["canales"]["mecanico"]["residuo"]["rango_valido"] = [1.0, -1.0]
    rep = contrato.Reporte()
    contrato.validar_esquema(c, rep)
    assert any(i["check"] == "schema.rango" for i in rep.items if i["nivel"] == "ERROR")


def test_dos_canales_reclamando_la_misma_columna_es_error():
    c = _contrato_minimo()
    c["canales"]["estado"]["duplicado"] = {"clase": "comando", "columna": "residuo"}
    rep = contrato.Reporte()
    contrato.validar_esquema(c, rep)
    assert any(i["check"] == "schema.duplicado" for i in rep.items if i["nivel"] == "ERROR")


def test_falta_dominio_de_validez_es_advertencia():
    c = _contrato_minimo()
    del c["dominio_de_validez"]
    rep = contrato.Reporte()
    contrato.validar_esquema(c, rep)
    assert any(i["check"] == "schema.dominio" for i in rep.items if i["nivel"] == "WARN")


@pytest.fixture
def frame_datos():
    pd = pytest.importorskip("pandas")
    n = 300
    ts = pd.date_range("2026-01-01", periods=n, freq="20s", tz="UTC")
    return pd.DataFrame({
        "timestamp": ts,
        "residuo": np.linspace(-0.5, 0.5, n),
        "modo": np.zeros(n, dtype=int),
    })


def test_datos_conformes_pasan(frame_datos):
    rep = contrato.Reporte()
    contrato.validar_datos(frame_datos, _contrato_minimo(), rep)
    assert rep.errores == 0


def test_valor_categorico_nuevo_es_error_de_contrato(frame_datos):
    """Un valor de estado no declarado es cambio de firmware o de configuracion,
    no una anomalia del equipo. La distincion es el punto del check."""
    df = frame_datos.copy()
    df.loc[10, "modo"] = 7
    rep = contrato.Reporte()
    contrato.validar_datos(df, _contrato_minimo(), rep)
    assert any(i["check"] == "canal.valores_nuevos" for i in rep.items if i["nivel"] == "ERROR")


def test_fuera_de_rango_fisico_es_error(frame_datos):
    df = frame_datos.copy()
    df.loc[5, "residuo"] = 99.0
    rep = contrato.Reporte()
    contrato.validar_datos(df, _contrato_minimo(), rep)
    assert any(i["check"] == "canal.rango_valido" for i in rep.items if i["nivel"] == "ERROR")


def test_retroceso_temporal_es_error(frame_datos):
    df = frame_datos.copy()
    df.loc[100, "timestamp"] = df.loc[10, "timestamp"]
    rep = contrato.Reporte()
    contrato.validar_datos(df, _contrato_minimo(), rep)
    assert any(i["check"] == "tiempo.monotono" for i in rep.items if i["nivel"] == "ERROR")


def test_canal_constante_no_puede_alimentar_un_modelo(frame_datos):
    df = frame_datos.copy()
    df["residuo"] = 0.0
    rep = contrato.Reporte()
    contrato.validar_datos(df, _contrato_minimo(), rep)
    assert any(i["check"] == "canal.constante" for i in rep.items if i["nivel"] == "ERROR")


def test_columna_ausente_es_error(frame_datos):
    df = frame_datos.drop(columns=["residuo"])
    rep = contrato.Reporte()
    contrato.validar_datos(df, _contrato_minimo(), rep)
    assert any(i["check"] == "canal.ausente" for i in rep.items if i["nivel"] == "ERROR")


def test_canal_descartado_ausente_no_es_error(frame_datos):
    c = _contrato_minimo()
    c["canales"]["estado"]["viejo"] = {"clase": "descartada", "motivo": "constante en 0"}
    rep = contrato.Reporte()
    contrato.validar_datos(frame_datos, c, rep)
    assert not any(
        i["check"] == "canal.ausente" and i["nivel"] == "ERROR" and i["canal"] == "estado.viejo"
        for i in rep.items
    )


# ─────────────────────────────────────────────────────────────────────────────
# Documentacion viva: si el protocolo desaparece, el preset queda sin fundamento
# ─────────────────────────────────────────────────────────────────────────────

def test_documentacion_del_preset_existe():
    for doc in (
        "presets/astro-mlops/docs/anomaly_detection_evaluation_protocol.md",
        "presets/astro-mlops/docs/mlops_traceability_spec.md",
        "docs/astro-mlops-adopcion.md",
    ):
        assert (BUNDLE / doc).exists(), f"falta {doc}"
