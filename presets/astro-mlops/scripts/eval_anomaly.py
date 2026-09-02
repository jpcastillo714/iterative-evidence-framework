#!/usr/bin/env python3
"""
IEF V3 · preset astro-mlops
Evaluacion de detectores de anomalias en series temporales.

Que hace distinto
-----------------
1. Evalua POR EVENTOS, no por punto. A quien opera el instrumento no le importa
   cuantas muestras marcaste dentro de una degradacion: le importa si la viste y
   cuantas veces lo despertaste sin motivo.
2. Reporta FALSAS ALARMAS POR NOCHE (o por unidad de tiempo). Es el numero que
   decide si el sistema se queda encendido.
3. Reporta point-adjust SIEMPRE junto a la metrica por eventos y al delta entre
   ambas. El point-adjust infla resultados de forma conocida; publicarlo solo es
   enganoso.
4. Exige que el umbral venga calibrado sobre datos nominales. Si se calibra sobre
   el propio conjunto de evaluacion, lo dice en el reporte.
5. Respeta la abstencion: las muestras `no_evaluable` no cuentan ni como acierto
   ni como falsa alarma, y la cobertura se reporta como metrica.

Uso
---
    python core/scripts/eval_anomaly.py \\
        --scores 06_resultados/experimentos/scores.parquet \\
        --labels 05_datos/benchmark_sintetico/injections.yml \\
        --calib  06_resultados/experimentos/scores_nominal.parquet \\
        --quantile 0.999 --k-de-n 3 5 \\
        --report 06_resultados/experimentos/evaluacion.json

Codigos de salida
    0  evaluacion completada
    1  la evaluacion no pudo realizarse con garantias (sin eventos, sin umbral)
    2  fallo de uso
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np

try:
    import yaml
except ImportError:  # pragma: no cover
    print("ERROR: falta PyYAML (pip install pyyaml)", file=sys.stderr)
    sys.exit(2)


# ─── Primitivas ──────────────────────────────────────────────────────────────

def tramos(mask: np.ndarray) -> List[Tuple[int, int]]:
    """Runs contiguos de True como [(inicio, fin_exclusivo), ...]."""
    if mask.size == 0:
        return []
    m = mask.astype(np.int8)
    bordes = np.diff(m, prepend=0, append=0)
    inicios = np.nonzero(bordes == 1)[0]
    finales = np.nonzero(bordes == -1)[0]
    return list(zip(inicios.tolist(), finales.tolist()))


def confirmar_k_de_n(excede: np.ndarray, k: int, n: int) -> np.ndarray:
    """Alarma confirmada: k excedencias dentro de las ultimas n muestras.

    Convierte una tasa de falsas alarmas puntual en una tasa operacional, a cambio
    de un retraso acotado que este mismo reporte cuantifica.
    """
    if k <= 1 and n <= 1:
        return excede.copy()
    x = excede.astype(np.int32)
    acum = np.cumsum(np.concatenate([[0], x]))
    salida = np.zeros_like(x, dtype=bool)
    for i in range(x.size):
        ini = max(0, i - n + 1)
        salida[i] = (acum[i + 1] - acum[ini]) >= k
    return salida


def average_precision(y: np.ndarray, s: np.ndarray) -> float:
    """Area bajo precision-recall por el metodo de precision promedio."""
    if y.sum() == 0 or y.size == 0:
        return float("nan")
    orden = np.argsort(-s, kind="mergesort")
    y_ord = y[orden]
    tp = np.cumsum(y_ord)
    fp = np.cumsum(1 - y_ord)
    precision = tp / np.maximum(tp + fp, 1)
    recall = tp / y.sum()
    d_recall = np.diff(np.concatenate([[0.0], recall]))
    return float(np.sum(precision * d_recall))


def roc_auc(y: np.ndarray, s: np.ndarray) -> float:
    """AUC por el estadistico de Mann-Whitney, con empates promediados."""
    pos, neg = int(y.sum()), int((1 - y).sum())
    if pos == 0 or neg == 0:
        return float("nan")
    orden = np.argsort(s, kind="mergesort")
    rangos = np.empty(s.size, dtype=float)
    rangos[orden] = np.arange(1, s.size + 1, dtype=float)
    s_ord = s[orden]
    i = 0
    while i < s_ord.size:
        j = i
        while j + 1 < s_ord.size and s_ord[j + 1] == s_ord[i]:
            j += 1
        if j > i:
            promedio = (i + j + 2) / 2.0
            rangos[orden[i : j + 1]] = promedio
        i = j + 1
    suma_pos = float(rangos[y == 1].sum())
    return (suma_pos - pos * (pos + 1) / 2.0) / (pos * neg)


def _prf(tp: int, fp: int, fn: int) -> Dict[str, float]:
    p = tp / (tp + fp) if (tp + fp) else 0.0
    r = tp / (tp + fn) if (tp + fn) else 0.0
    f = 2 * p * r / (p + r) if (p + r) else 0.0
    return {"precision": round(p, 4), "recall": round(r, 4), "f1": round(f, 4)}


# ─── Carga de entradas ───────────────────────────────────────────────────────

def _leer_tabla(path: Path):
    try:
        import pandas as pd
    except ImportError:
        print("ERROR: falta pandas (pip install pandas pyarrow)", file=sys.stderr)
        sys.exit(2)
    if not path.exists():
        print(f"ERROR: no existe {path}", file=sys.stderr)
        sys.exit(2)
    if path.suffix.lower() in {".parquet", ".pq"}:
        return pd.read_parquet(path)
    return pd.read_csv(path)


def cargar_scores(path: Path, col_score: str, col_evaluable: Optional[str], col_ts: str):
    df = _leer_tabla(path)
    if col_score not in df.columns:
        print(f"ERROR: falta la columna de score `{col_score}`. Hay: {list(df.columns)[:20]}", file=sys.stderr)
        sys.exit(2)
    scores = df[col_score].to_numpy(dtype=float)

    evaluable = np.ones(scores.size, dtype=bool)
    if col_evaluable and col_evaluable in df.columns:
        evaluable = df[col_evaluable].to_numpy().astype(bool)
    evaluable &= np.isfinite(scores)

    ts = None
    if col_ts in df.columns:
        import pandas as pd

        ts = pd.to_datetime(df[col_ts], utc=True, errors="coerce")
    return df, scores, evaluable, ts


def cargar_eventos(path: Path, n: int) -> Tuple[np.ndarray, List[Dict[str, Any]], Dict[str, Any]]:
    """Devuelve (etiqueta_puntual, eventos, metadatos del manifiesto)."""
    etiqueta = np.zeros(n, dtype=int)
    eventos: List[Dict[str, Any]] = []
    meta: Dict[str, Any] = {}

    if path.suffix.lower() in {".yml", ".yaml"}:
        with open(path, "r", encoding="utf-8") as f:
            doc = yaml.safe_load(f) or {}
        meta = {k: v for k, v in doc.items() if k != "injections"}
        for inj in doc.get("injections", []):
            ini, fin = int(inj["inicio_idx"]), int(inj["fin_idx"])
            ini, fin = max(0, ini), min(n, fin)
            if fin <= ini:
                continue
            etiqueta[ini:fin] = 1
            eventos.append(
                {
                    "id": inj.get("id"),
                    "tipo": inj.get("tipo"),
                    "severidad_sigma": inj.get("severidad_sigma"),
                    "inicio": ini,
                    "fin": fin,
                    "inicio_efectivo": inj.get("inicio_efectivo_idx"),
                }
            )
    else:
        df = _leer_tabla(path)
        col = "label" if "label" in df.columns else df.columns[-1]
        vals = df[col].to_numpy().astype(int)[:n]
        etiqueta[: vals.size] = vals
        for idx, (ini, fin) in enumerate(tramos(etiqueta.astype(bool)), start=1):
            eventos.append(
                {
                    "id": f"EVT-{idx:03d}",
                    "tipo": None,
                    "severidad_sigma": None,
                    "inicio": ini,
                    "fin": fin,
                    "inicio_efectivo": None,
                }
            )
    return etiqueta, eventos, meta


# ─── Evaluacion ──────────────────────────────────────────────────────────────

def evaluar(
    scores: np.ndarray,
    etiqueta: np.ndarray,
    eventos: List[Dict[str, Any]],
    evaluable: np.ndarray,
    umbral: float,
    k: int,
    n_conf: int,
    cadencia_s: float,
    horas_por_unidad: float,
) -> Dict[str, Any]:
    excede = (scores >= umbral) & evaluable
    alarma = confirmar_k_de_n(excede, k, n_conf) & evaluable

    y = etiqueta[evaluable].astype(int)
    s = scores[evaluable]

    # ── Por punto ────────────────────────────────────────────────────────────
    pred = alarma[evaluable].astype(int)
    tp = int(((pred == 1) & (y == 1)).sum())
    fp = int(((pred == 1) & (y == 0)).sum())
    fn = int(((pred == 0) & (y == 1)).sum())
    por_punto = _prf(tp, fp, fn)
    por_punto["pr_auc"] = round(average_precision(y, s), 4)
    por_punto["roc_auc"] = round(roc_auc(y, s), 4)

    # ── Por evento ───────────────────────────────────────────────────────────
    detectados, retrasos, anticipaciones = 0, [], []
    por_evento_detalle = []
    for ev in eventos:
        seg = alarma[ev["inicio"] : ev["fin"]]
        hit = bool(seg.any())
        detectados += int(hit)
        primer = int(np.nonzero(seg)[0][0]) + ev["inicio"] if hit else None
        ref = ev.get("inicio_efectivo") or ev["inicio"]
        if hit:
            retrasos.append((primer - ref) * cadencia_s / 60.0)
            anticipaciones.append((ev["fin"] - primer) * cadencia_s / 60.0)
        por_evento_detalle.append(
            {
                "id": ev["id"],
                "tipo": ev["tipo"],
                "severidad_sigma": ev["severidad_sigma"],
                "detectado": hit,
                "retraso_min": round((primer - ref) * cadencia_s / 60.0, 2) if hit else None,
            }
        )

    alarmas = tramos(alarma)
    intervalos = [(e["inicio"], e["fin"]) for e in eventos]
    verdaderas = sum(1 for a, b in alarmas if any(not (b <= i or a >= j) for i, j in intervalos))
    falsas = len(alarmas) - verdaderas

    recall_ev = detectados / len(eventos) if eventos else float("nan")
    precision_ev = verdaderas / len(alarmas) if alarmas else 0.0
    f1_ev = (
        2 * precision_ev * recall_ev / (precision_ev + recall_ev)
        if eventos and (precision_ev + recall_ev)
        else 0.0
    )

    # ── Falsas alarmas por unidad operacional ────────────────────────────────
    horas_evaluables = float(evaluable.sum()) * cadencia_s / 3600.0
    unidades = horas_evaluables / horas_por_unidad if horas_por_unidad > 0 else float("nan")
    far = falsas / unidades if unidades and unidades > 0 else float("nan")

    # ── Point-adjust, solo para exhibir su sesgo ─────────────────────────────
    ajustada = alarma.copy()
    for ev in eventos:
        if alarma[ev["inicio"] : ev["fin"]].any():
            ajustada[ev["inicio"] : ev["fin"]] = True
    pa = ajustada[evaluable].astype(int)
    pa_metrica = _prf(
        int(((pa == 1) & (y == 1)).sum()),
        int(((pa == 1) & (y == 0)).sum()),
        int(((pa == 0) & (y == 1)).sum()),
    )

    # ── Desglose por tipo y severidad: la tabla que se publica ───────────────
    desglose: Dict[str, Dict[str, Any]] = {}
    for ev, det in zip(eventos, por_evento_detalle):
        if ev["tipo"] is None:
            continue
        clave = f"{ev['tipo']}@{ev['severidad_sigma']}"
        d = desglose.setdefault(clave, {"tipo": ev["tipo"], "severidad_sigma": ev["severidad_sigma"], "n": 0, "detectados": 0})
        d["n"] += 1
        d["detectados"] += int(det["detectado"])
    for d in desglose.values():
        d["recall"] = round(d["detectados"] / d["n"], 4) if d["n"] else 0.0

    return {
        "umbral": float(umbral),
        "confirmacion_k_de_n": [k, n_conf],
        "cobertura": {
            "muestras_totales": int(evaluable.size),
            "muestras_evaluables": int(evaluable.sum()),
            "fraccion_evaluable": round(float(evaluable.mean()), 4),
            "horas_evaluables": round(horas_evaluables, 2),
        },
        "por_punto": por_punto,
        "por_evento": {
            "n_eventos": len(eventos),
            "detectados": detectados,
            "recall": round(recall_ev, 4) if eventos else None,
            "precision": round(precision_ev, 4),
            "f1": round(f1_ev, 4),
            "n_alarmas": len(alarmas),
            "alarmas_verdaderas": verdaderas,
            "alarmas_falsas": falsas,
            "retraso_mediano_min": round(float(np.median(retrasos)), 2) if retrasos else None,
            "anticipacion_mediana_min": round(float(np.median(anticipaciones)), 2) if anticipaciones else None,
        },
        "falsas_alarmas": {
            "por_unidad": round(far, 3) if np.isfinite(far) else None,
            "horas_por_unidad": horas_por_unidad,
            "unidades_evaluadas": round(unidades, 2) if np.isfinite(unidades) else None,
        },
        "point_adjust": {
            "f1": pa_metrica["f1"],
            "precision": pa_metrica["precision"],
            "recall": pa_metrica["recall"],
            "delta_f1_vs_eventos": round(pa_metrica["f1"] - f1_ev, 4),
            "delta_f1_vs_puntual": round(pa_metrica["f1"] - por_punto["f1"], 4),
            "advertencia": (
                "El point-adjust marca como acierto el evento completo si se detecto una sola "
                "muestra. `delta_f1_vs_puntual` mide cuanto de la cifra viene de la convencion "
                "y no del detector. Publicarlo sin la metrica por eventos sobreestima el desempeno."
            ),
        },
        "desglose_por_tipo": sorted(desglose.values(), key=lambda d: (d["tipo"], d["severidad_sigma"] or 0)),
        "eventos": por_evento_detalle,
    }


# ─── Umbral ──────────────────────────────────────────────────────────────────

def calibrar_umbral(args, scores: np.ndarray, etiqueta: np.ndarray, evaluable: np.ndarray):
    if args.threshold is not None:
        return float(args.threshold), "explicito", None

    if args.calib:
        df = _leer_tabla(Path(args.calib))
        col = args.score_col if args.score_col in df.columns else df.columns[-1]
        base = df[col].to_numpy(dtype=float)
        base = base[np.isfinite(base)]
        if base.size == 0:
            print("ERROR: el conjunto de calibracion no tiene scores finitos", file=sys.stderr)
            sys.exit(1)
        return float(np.quantile(base, args.quantile)), "nominal_externo", None

    negativos = scores[(etiqueta == 0) & evaluable]
    negativos = negativos[np.isfinite(negativos)]
    if negativos.size == 0:
        print("ERROR: no hay muestras nominales para calibrar el umbral", file=sys.stderr)
        sys.exit(1)
    aviso = (
        "Umbral calibrado sobre los negativos del PROPIO conjunto de evaluacion. "
        "Es optimista y no reproduce el desempeno en operacion. Usa --calib con un "
        "conjunto nominal independiente antes de citar este numero (invariante P5)."
    )
    return float(np.quantile(negativos, args.quantile)), "negativos_del_test", aviso


# ─── Impresion ───────────────────────────────────────────────────────────────

def imprimir(rep: Dict[str, Any]) -> None:
    ev, pt, fa, pa = rep["por_evento"], rep["por_punto"], rep["falsas_alarmas"], rep["point_adjust"]
    cob = rep["cobertura"]

    print("=" * 74)
    print("EVALUACION DE DETECCION DE ANOMALIAS")
    print("=" * 74)
    print(f"  Umbral                : {rep['umbral']:.6g}  (calibrado: {rep['umbral_origen']})")
    print(f"  Confirmacion          : {rep['confirmacion_k_de_n'][0]} de {rep['confirmacion_k_de_n'][1]}")
    print(f"  Cobertura evaluable   : {cob['fraccion_evaluable'] * 100:.1f} %  ({cob['horas_evaluables']:.1f} h)")
    print("-" * 74)
    print("  POR EVENTO   (lo que le importa a quien opera)")
    print(f"    eventos             : {ev['n_eventos']}   detectados: {ev['detectados']}")
    print(f"    recall / precision  : {ev['recall']} / {ev['precision']}      F1: {ev['f1']}")
    print(f"    alarmas falsas      : {ev['alarmas_falsas']} de {ev['n_alarmas']}")
    print(f"    FALSAS ALARMAS/unid : {fa['por_unidad']}   (unidad = {fa['horas_por_unidad']} h)")
    print(f"    retraso mediano     : {ev['retraso_mediano_min']} min")
    print(f"    anticipacion median : {ev['anticipacion_mediana_min']} min")
    print("-" * 74)
    print("  POR PUNTO")
    print(f"    precision/recall/F1 : {pt['precision']} / {pt['recall']} / {pt['f1']}")
    print(f"    PR-AUC / ROC-AUC    : {pt['pr_auc']} / {pt['roc_auc']}")
    print("-" * 74)
    print("  POINT-ADJUST (referencia, NO metrica principal)")
    print(f"    F1                  : {pa['f1']}")
    print(f"    delta vs eventos    : {pa['delta_f1_vs_eventos']:+.4f}")
    print(f"    delta vs puntual    : {pa['delta_f1_vs_puntual']:+.4f}   <- lo que aporta la convencion")
    if rep["desglose_por_tipo"]:
        print("-" * 74)
        print("  RECALL POR TIPO Y SEVERIDAD")
        print(f"    {'tipo':<20} {'sigma':>7} {'n':>5} {'recall':>8}")
        for d in rep["desglose_por_tipo"]:
            print(f"    {d['tipo']:<20} {str(d['severidad_sigma']):>7} {d['n']:>5} {d['recall']:>8.3f}")
    if rep.get("advertencias"):
        print("-" * 74)
        for a in rep["advertencias"]:
            print(f"  [!] {a}")
    print("=" * 74)


# ─── CLI ─────────────────────────────────────────────────────────────────────

def main() -> None:
    p = argparse.ArgumentParser(description="Evaluacion por eventos de un detector de anomalias (IEF astro-mlops)")
    p.add_argument("--scores", required=True, help="parquet/csv con la columna de score")
    p.add_argument("--labels", required=True, help="injections.yml o tabla con columna label")
    p.add_argument("--score-col", default="score")
    p.add_argument("--evaluable-col", default="evaluable", help="columna booleana de abstencion")
    p.add_argument("--timestamp-col", default="timestamp")
    p.add_argument("--threshold", type=float, help="umbral explicito")
    p.add_argument("--calib", help="scores de un conjunto NOMINAL independiente")
    p.add_argument("--quantile", type=float, default=0.999)
    p.add_argument("--k-de-n", nargs=2, type=int, default=[1, 1], metavar=("K", "N"))
    p.add_argument("--cadencia", type=float, default=20.0, help="segundos entre muestras")
    p.add_argument("--horas-por-unidad", type=float, default=10.0, help="duracion de la unidad operacional (noche)")
    p.add_argument("--report", help="ruta del reporte JSON")
    args = p.parse_args()

    _, scores, evaluable, _ = cargar_scores(
        Path(args.scores), args.score_col, args.evaluable_col, args.timestamp_col
    )
    etiqueta, eventos, meta = cargar_eventos(Path(args.labels), scores.size)

    if not eventos:
        print("ERROR: no hay eventos etiquetados. Sin ground truth no hay evaluacion.", file=sys.stderr)
        sys.exit(1)

    umbral, origen, aviso = calibrar_umbral(args, scores, etiqueta, evaluable)
    k, n_conf = args.k_de_n

    rep = evaluar(
        scores, etiqueta, eventos, evaluable, umbral, k, n_conf, args.cadencia, args.horas_por_unidad
    )
    rep["schema_version"] = "1.0"
    rep["kind"] = "anomaly_evaluation_report"
    rep["executed_at"] = datetime.now(timezone.utc).isoformat()
    rep["scores"] = str(args.scores)
    rep["labels"] = str(args.labels)
    rep["umbral_origen"] = origen
    rep["quantile"] = args.quantile
    rep["advertencias"] = [a for a in [aviso] if a]
    if meta.get("limitacion_declarada"):
        rep["advertencias"].append(meta["limitacion_declarada"])
    if meta:
        rep["manifiesto"] = {
            k2: meta.get(k2) for k2 in ("sigma_nominal", "seed", "n_injections", "fraccion_anomala")
        }

    imprimir(rep)

    if args.report:
        salida = Path(args.report)
        salida.parent.mkdir(parents=True, exist_ok=True)
        with open(salida, "w", encoding="utf-8") as f:
            json.dump(rep, f, indent=2, ensure_ascii=False)
        print(f"Reporte: {salida}")


if __name__ == "__main__":
    main()
