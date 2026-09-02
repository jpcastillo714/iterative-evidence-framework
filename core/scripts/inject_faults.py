#!/usr/bin/env python3
"""
IEF V3 · preset astro-mlops
Banco de fallas sinteticas para telemetria de instrumentacion.

Por que existe
--------------
En instrumentacion bien mantenida la telemetria historica suele ser enteramente
nominal: no hay fallas etiquetadas con que validar un detector. Sin ground truth no
hay metrica, y sin metrica no hay memoria defendible.

Este modulo fabrica el ground truth de forma explicita, parametrizada y declarada:
inyecta modos de degradacion sobre una serie nominal, con severidad expresada en
unidades de sigma nominal, y emite un manifiesto que es un artefacto de evidencia.

Limitacion que hay que declarar en el informe
---------------------------------------------
Una falla inyectada es un MODELO de degradacion, no una falla real. El banco acota la
sensibilidad del detector (que detecta, desde que severidad, que no detecta nunca).
No demuestra que detectara la proxima falla del equipo. Es la antesala de la
validacion contra mantenimiento real, no su reemplazo.

Uso
---
    # Generar una serie nominal de juguete (para probar la herramienta)
    python core/scripts/inject_faults.py demo --out /tmp/nominal.parquet

    # Inyeccion unica
    python core/scripts/inject_faults.py inject --data nominal.parquet --column residuo \\
        --tipo deriva_lenta --severidad 2.0 --duracion-min 60 --out corrupto.parquet

    # Banco completo (tipos x severidades x repeticiones), ventanas disjuntas
    python core/scripts/inject_faults.py bench --data nominal.parquet --column residuo \\
        --out 05_datos/benchmark_sintetico --params params.yaml

Salidas del modo `bench`
------------------------
    benchmark.parquet   copia de la serie con las inyecciones aplicadas, mas las
                        columnas `label` (0/1) e `injection_id`
    injections.yml      manifiesto: tipo, severidad, ventana, parametros y semilla
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

try:
    import yaml
except ImportError:  # pragma: no cover
    print("ERROR: falta PyYAML (pip install pyyaml)", file=sys.stderr)
    sys.exit(2)


# ─── Modos de degradacion ────────────────────────────────────────────────────
#
# Convencion comun a todos: `severidad` esta en unidades de sigma nominal de la
# serie. Severidad 1.0 significa "el efecto es del tamano del ruido nominal".
# Cada funcion recibe una copia del tramo y devuelve el tramo modificado.

def _deriva_lenta(x: np.ndarray, sigma: float, sev: float, rng, **kw) -> np.ndarray:
    """Rampa monotona. El modo canonico de desgaste: lento, acumulativo, sin evento."""
    rampa = np.linspace(0.0, sev * sigma, x.size)
    return x + rampa


def _stiction(x: np.ndarray, sigma: float, sev: float, rng, **kw) -> np.ndarray:
    """Friccion estatica creciente: la senal se pega y se libera a saltos.

    Modela el mecanismo que deja de responder a correcciones pequenas hasta que el
    error acumulado supera el umbral de desprendimiento.
    """
    umbral = max(sev * sigma, 1e-12)
    salida = np.empty_like(x)
    pegado = x[0]
    for i, v in enumerate(x):
        if abs(v - pegado) < umbral:
            salida[i] = pegado          # se queda pegado
        else:
            pegado = v                  # se desprende y alcanza
            salida[i] = v
    return salida


def _juego_mecanico(x: np.ndarray, sigma: float, sev: float, rng, **kw) -> np.ndarray:
    """Backlash: perdida de movimiento en cada inversion de sentido."""
    d = np.diff(x, prepend=x[0])
    signo = np.sign(d)
    inversiones = np.diff(signo, prepend=signo[0]) != 0
    offset = np.where(inversiones, -signo * sev * sigma, 0.0)
    return x + np.cumsum(offset) * 0.5


def _perdida_ganancia(x: np.ndarray, sigma: float, sev: float, rng, **kw) -> np.ndarray:
    """El lazo de control pierde ganancia: la misma dinamica con mas amplitud de error."""
    media = float(np.nanmean(x))
    desv = float(np.nanstd(x))
    if desv <= 0:
        return x + rng.normal(0.0, sev * sigma, x.size)
    factor = 1.0 + (sev * sigma) / desv
    return media + (x - media) * factor


def _salto_encoder(x: np.ndarray, sigma: float, sev: float, rng, **kw) -> np.ndarray:
    """Perdida de cuentas del encoder: escalon permanente dentro de la ventana."""
    salto = sev * sigma * (1.0 if rng.random() > 0.5 else -1.0)
    return x + salto


def _ruido_creciente(x: np.ndarray, sigma: float, sev: float, rng, **kw) -> np.ndarray:
    """Degradacion del sensor o del contacto: la varianza crece, la media no se mueve."""
    escala = np.linspace(0.0, sev * sigma, x.size)
    return x + rng.normal(0.0, 1.0, x.size) * escala


def _cuantizacion(x: np.ndarray, sigma: float, sev: float, rng, **kw) -> np.ndarray:
    """Perdida de resolucion efectiva del encoder."""
    paso = max(sev * sigma, 1e-12)
    return np.round(x / paso) * paso


def _valor_congelado(x: np.ndarray, sigma: float, sev: float, rng, **kw) -> np.ndarray:
    """Canal congelado: el archivador repite el ultimo valor.

    No depende de la severidad. Es el fallo mas comun de una cadena de adquisicion y
    el que mas detectores pasan por alto, porque la varianza cae a cero en vez de subir.
    """
    return np.full_like(x, x[0])


def _dropout(x: np.ndarray, sigma: float, sev: float, rng, **kw) -> np.ndarray:
    """Perdida intermitente de muestras: NaN en rafagas."""
    salida = x.copy()
    fraccion = min(0.05 * max(sev, 0.1), 0.9)
    n_rafagas = max(1, int(x.size * fraccion / 10))
    for _ in range(n_rafagas):
        largo = int(rng.integers(3, max(4, x.size // 20)))
        ini = int(rng.integers(0, max(1, x.size - largo)))
        salida[ini : ini + largo] = np.nan
    return salida


MODOS = {
    "deriva_lenta": _deriva_lenta,
    "stiction": _stiction,
    "juego_mecanico": _juego_mecanico,
    "perdida_ganancia": _perdida_ganancia,
    "salto_encoder": _salto_encoder,
    "ruido_creciente": _ruido_creciente,
    "cuantizacion": _cuantizacion,
    "valor_congelado": _valor_congelado,
    "dropout": _dropout,
}

DESCRIPCION = {
    "deriva_lenta": "rampa monotona; desgaste acumulativo sin evento",
    "stiction": "friccion estatica: se pega y se libera a saltos",
    "juego_mecanico": "backlash en cada inversion de sentido",
    "perdida_ganancia": "el lazo pierde ganancia; mas amplitud de error",
    "salto_encoder": "escalon permanente por perdida de cuentas",
    "ruido_creciente": "la varianza crece, la media no se mueve",
    "cuantizacion": "perdida de resolucion efectiva",
    "valor_congelado": "canal congelado; la varianza CAE a cero",
    "dropout": "perdida intermitente de muestras (NaN en rafagas)",
}


# ─── Utilidades ──────────────────────────────────────────────────────────────

def sigma_robusto(x: np.ndarray) -> float:
    """Desviacion robusta (1.4826 x MAD). No la arrastra una cola pesada."""
    limpio = x[np.isfinite(x)]
    if limpio.size == 0:
        return 0.0
    mad = float(np.median(np.abs(limpio - np.median(limpio))))
    s = 1.4826 * mad
    if s <= 0:
        s = float(np.std(limpio))
    return s


def inyectar(
    serie: np.ndarray,
    tipo: str,
    inicio: int,
    largo: int,
    severidad: float,
    sigma: Optional[float] = None,
    rng: Optional[np.random.Generator] = None,
) -> Tuple[np.ndarray, Dict[str, Any]]:
    """Aplica una falla al tramo [inicio, inicio+largo) y devuelve (serie, metadatos)."""
    if tipo not in MODOS:
        raise ValueError(f"tipo de falla desconocido: {tipo} (validos: {sorted(MODOS)})")
    if rng is None:
        rng = np.random.default_rng()
    if sigma is None:
        sigma = sigma_robusto(serie)

    salida = serie.astype(float).copy()
    fin = min(inicio + largo, serie.size)
    tramo = salida[inicio:fin]
    if tramo.size < 2:
        raise ValueError("el tramo a inyectar necesita al menos 2 muestras")

    modificado = MODOS[tipo](tramo.copy(), sigma, severidad, rng)
    salida[inicio:fin] = modificado

    delta = np.abs(np.nan_to_num(modificado) - np.nan_to_num(tramo))
    supera = np.nonzero(delta >= sigma)[0]
    # Instante en que el efecto alcanza 1 sigma: referencia honesta para el lead time.
    inicio_efectivo = int(inicio + supera[0]) if supera.size else None

    meta = {
        "tipo": tipo,
        "descripcion": DESCRIPCION[tipo],
        "severidad_sigma": float(severidad),
        "sigma_nominal": float(sigma),
        "inicio_idx": int(inicio),
        "fin_idx": int(fin),
        "n_muestras": int(fin - inicio),
        "inicio_efectivo_idx": inicio_efectivo,
        "desviacion_max": float(np.nanmax(delta)) if delta.size else 0.0,
    }
    return salida, meta


def ventanas_disjuntas(
    n: int, largo: int, cantidad: int, separacion: int, rng: np.random.Generator
) -> List[int]:
    """Elige inicios de ventana que no se solapan ni se tocan."""
    ocupados: List[Tuple[int, int]] = []
    inicios: List[int] = []
    intentos = 0
    limite = cantidad * 200
    while len(inicios) < cantidad and intentos < limite:
        intentos += 1
        ini = int(rng.integers(0, max(1, n - largo)))
        fin = ini + largo
        if any(not (fin + separacion <= a or ini - separacion >= b) for a, b in ocupados):
            continue
        ocupados.append((ini, fin))
        inicios.append(ini)
    return sorted(inicios)


def _cargar_frame(path: Path):
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


def _guardar_frame(df, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.suffix.lower() in {".parquet", ".pq"}:
        df.to_parquet(path, index=False)
    else:
        df.to_csv(path, index=False)


# ─── Subcomando: demo ────────────────────────────────────────────────────────

def cmd_demo(args) -> None:
    """Serie nominal de juguete: residuo de un lazo de control con ciclo termico."""
    import pandas as pd

    rng = np.random.default_rng(args.seed)
    n = args.n
    t = np.arange(n)
    ciclo = 0.02 * np.sin(2 * np.pi * t / (n / 6.0))       # respiracion termica diaria
    ruido = rng.normal(0.0, 0.01, n)
    residuo = ciclo + ruido

    inicio = datetime(2026, 1, 1, tzinfo=timezone.utc)
    ts = [inicio + timedelta(seconds=args.cadencia * i) for i in range(n)]

    df = pd.DataFrame({"timestamp": ts, "residuo": residuo, "episodio": t // 200})
    _guardar_frame(df, Path(args.out))
    print(f"Serie nominal de {n} muestras -> {args.out}")
    print(f"sigma robusto = {sigma_robusto(residuo):.6g}")


# ─── Subcomando: inject ──────────────────────────────────────────────────────

def cmd_inject(args) -> None:
    df = _cargar_frame(Path(args.data))
    if args.column not in df.columns:
        print(f"ERROR: la columna `{args.column}` no existe. Hay: {list(df.columns)[:20]}", file=sys.stderr)
        sys.exit(2)

    serie = df[args.column].to_numpy(dtype=float)
    rng = np.random.default_rng(args.seed)
    largo = int(args.duracion_min * 60 / args.cadencia)
    inicio = args.inicio if args.inicio is not None else int(rng.integers(0, max(1, serie.size - largo)))

    modificada, meta = inyectar(serie, args.tipo, inicio, largo, args.severidad, rng=rng)
    df = df.copy()
    df[args.column] = modificada
    etiqueta = np.zeros(serie.size, dtype=int)
    etiqueta[meta["inicio_idx"] : meta["fin_idx"]] = 1
    df["label"] = etiqueta
    df["injection_id"] = np.where(etiqueta == 1, "INJ-001", "")

    _guardar_frame(df, Path(args.out))
    print(json.dumps(meta, indent=2, ensure_ascii=False))
    print(f"-> {args.out}")


# ─── Subcomando: bench ───────────────────────────────────────────────────────

def cmd_bench(args) -> None:
    import pandas as pd

    cfg: Dict[str, Any] = {}
    if args.params:
        with open(args.params, "r", encoding="utf-8") as f:
            cfg = (yaml.safe_load(f) or {}).get("benchmark_sintetico", {}) or {}

    tipos = args.tipos.split(",") if args.tipos else cfg.get("tipos") or list(MODOS)
    severidades = cfg.get("severidades_sigma") or [0.5, 1.0, 2.0, 4.0]
    duraciones = cfg.get("duracion_min") or [60]
    repeticiones = int(cfg.get("repeticiones_por_celda") or args.repeticiones)
    semilla = int(cfg.get("semilla") or args.seed)
    cadencia = float(args.cadencia)

    desconocidos = [t for t in tipos if t not in MODOS]
    if desconocidos:
        print(f"ERROR: tipos desconocidos: {desconocidos}", file=sys.stderr)
        sys.exit(2)

    df = _cargar_frame(Path(args.data))
    if args.column not in df.columns:
        print(f"ERROR: la columna `{args.column}` no existe. Hay: {list(df.columns)[:20]}", file=sys.stderr)
        sys.exit(2)

    serie = df[args.column].to_numpy(dtype=float)
    sigma = sigma_robusto(serie)
    if sigma <= 0:
        print("ERROR: sigma nominal es cero; la serie es constante", file=sys.stderr)
        sys.exit(2)

    rng = np.random.default_rng(semilla)
    celdas = [(t, s, d) for t in tipos for s in severidades for d in duraciones]
    total = len(celdas) * repeticiones

    largo_max = int(max(duraciones) * 60 / cadencia)
    separacion = int(args.separacion_min * 60 / cadencia)
    inicios = ventanas_disjuntas(serie.size, largo_max, total, separacion, rng)

    if len(inicios) < total:
        print(
            f"AVISO: la serie solo admite {len(inicios)} ventanas disjuntas de {total} pedidas. "
            "Se reduce el banco: reportarlo como limitacion del conjunto de evaluacion.",
            file=sys.stderr,
        )

    modificada = serie.copy()
    etiqueta = np.zeros(serie.size, dtype=int)
    ids = np.array([""] * serie.size, dtype=object)
    manifiesto: List[Dict[str, Any]] = []

    plan = [(celdas[i % len(celdas)], i) for i in range(len(inicios))]
    for (tipo, sev, dur), idx in plan:
        largo = int(dur * 60 / cadencia)
        inicio = inicios[idx]
        if inicio + largo > serie.size:
            continue
        modificada, meta = inyectar(modificada, tipo, inicio, largo, float(sev), sigma=sigma, rng=rng)
        inj_id = f"INJ-{len(manifiesto) + 1:03d}"
        etiqueta[meta["inicio_idx"] : meta["fin_idx"]] = 1
        ids[meta["inicio_idx"] : meta["fin_idx"]] = inj_id
        meta["id"] = inj_id
        meta["duracion_min"] = float(dur)
        manifiesto.append(meta)

    col_ts = args.timestamp if args.timestamp in df.columns else None
    if col_ts:
        ts = pd.to_datetime(df[col_ts], utc=True, errors="coerce")
        for m in manifiesto:
            m["inicio_ts"] = str(ts.iloc[m["inicio_idx"]])
            m["fin_ts"] = str(ts.iloc[min(m["fin_idx"], len(ts) - 1)])
            if m["inicio_efectivo_idx"] is not None:
                m["inicio_efectivo_ts"] = str(ts.iloc[m["inicio_efectivo_idx"]])

    salida_dir = Path(args.out)
    salida_dir.mkdir(parents=True, exist_ok=True)

    out_df = df.copy()
    out_df[args.column] = modificada
    out_df["label"] = etiqueta
    out_df["injection_id"] = ids
    _guardar_frame(out_df, salida_dir / "benchmark.parquet")

    doc = {
        "schema_version": "1.0",
        "kind": "fault_injection_manifest",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source": str(args.data),
        "column": args.column,
        "timestamp_column": col_ts,
        "cadencia_s": cadencia,
        "sigma_nominal": float(sigma),
        "sigma_metodo": "1.4826 * MAD sobre la serie fuente",
        "seed": semilla,
        "n_injections": len(manifiesto),
        "fraccion_anomala": float(etiqueta.mean()),
        "limitacion_declarada": (
            "Fallas sinteticas: modelan degradacion, no la reemplazan. Acotan la sensibilidad "
            "del detector; no demuestran deteccion de una falla real futura."
        ),
        "injections": manifiesto,
    }
    with open(salida_dir / "injections.yml", "w", encoding="utf-8") as f:
        yaml.safe_dump(doc, f, sort_keys=False, allow_unicode=True)

    print(f"Banco sintetico: {len(manifiesto)} inyeccion(es) sobre {serie.size} muestras")
    print(f"  sigma nominal      : {sigma:.6g}")
    print(f"  fraccion anomala   : {etiqueta.mean() * 100:.2f} %")
    if etiqueta.mean() > 0.20:
        print(
            "  [!] Mas del 20% del banco esta corrompido. Con tan pocos negativos, la tasa de\n"
            "      falsas alarmas y la precision quedan mal estimadas, y un umbral calibrado\n"
            "      sobre este conjunto estara sesgado. Usa una serie mas larga, menos\n"
            "      repeticiones o ventanas mas cortas.",
            file=sys.stderr,
        )
    print(f"  tipos              : {', '.join(sorted(set(m['tipo'] for m in manifiesto)))}")
    print(f"  -> {salida_dir / 'benchmark.parquet'}")
    print(f"  -> {salida_dir / 'injections.yml'}")


# ─── CLI ─────────────────────────────────────────────────────────────────────

def main() -> None:
    p = argparse.ArgumentParser(description="Banco de fallas sinteticas para telemetria (IEF astro-mlops)")
    sub = p.add_subparsers(dest="cmd", required=True)

    d = sub.add_parser("demo", help="genera una serie nominal de juguete")
    d.add_argument("--out", default="nominal_demo.parquet")
    d.add_argument("--n", type=int, default=5000)
    d.add_argument("--cadencia", type=float, default=20.0)
    d.add_argument("--seed", type=int, default=42)
    d.set_defaults(func=cmd_demo)

    i = sub.add_parser("inject", help="inyecta una falla unica")
    i.add_argument("--data", required=True)
    i.add_argument("--column", required=True)
    i.add_argument("--tipo", required=True, choices=sorted(MODOS))
    i.add_argument("--severidad", type=float, default=2.0, help="en unidades de sigma nominal")
    i.add_argument("--duracion-min", type=float, default=60.0)
    i.add_argument("--cadencia", type=float, default=20.0)
    i.add_argument("--inicio", type=int, help="indice de inicio (por defecto, aleatorio)")
    i.add_argument("--out", required=True)
    i.add_argument("--seed", type=int, default=7)
    i.set_defaults(func=cmd_inject)

    b = sub.add_parser("bench", help="genera el banco completo con ventanas disjuntas")
    b.add_argument("--data", required=True)
    b.add_argument("--column", default="residuo")
    b.add_argument("--timestamp", default="timestamp")
    b.add_argument("--out", required=True)
    b.add_argument("--params", help="params.yaml con la seccion benchmark_sintetico")
    b.add_argument("--tipos", help="lista separada por comas (sobrescribe params.yaml)")
    b.add_argument("--repeticiones", type=int, default=3)
    b.add_argument("--cadencia", type=float, default=20.0)
    b.add_argument("--separacion-min", type=float, default=30.0)
    b.add_argument("--seed", type=int, default=7)
    b.set_defaults(func=cmd_bench)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
