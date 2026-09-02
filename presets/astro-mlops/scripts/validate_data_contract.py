#!/usr/bin/env python3
"""
IEF V3 · preset astro-mlops
Validador de contratos de telemetria.

Convierte el artefacto del Paso 3 (data-contract.yml) en un test ejecutable sobre los
datos reales. Sin datos, valida la forma del contrato (--schema-only): sirve en CI.

    python core/scripts/validate_data_contract.py --contract data-contract.yml
    python core/scripts/validate_data_contract.py --contract c.yml --data datos.parquet
    python core/scripts/validate_data_contract.py --contract c.yml --schema-only

Codigos de salida
    0  sin errores (puede haber advertencias)
    1  al menos un ERROR, o una ADVERTENCIA con --strict
    2  fallo de uso (archivo inexistente, YAML invalido, falta pandas)

Filosofia: una violacion de `rango_valido` o la aparicion de un valor categorico no
declarado son ERRORES de contrato, no anomalias del equipo. Confundirlos es la forma
mas rapida de publicar un falso positivo.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

try:
    import yaml
except ImportError:  # pragma: no cover
    print("ERROR: falta PyYAML (pip install pyyaml)", file=sys.stderr)
    sys.exit(2)


# ─── Vocabulario del contrato ────────────────────────────────────────────────

CLASES_VALIDAS = {"medicion", "consigna", "comando", "ambiente", "derivada", "descartada"}
CLASES_MODELABLES = {"medicion", "derivada"}
TIPOS_VALIDOS = {"float", "int", "bool", "categorico", "datetime", "string"}

# Claves que no son canales aunque aparezcan al nivel de un canal.
CLAVES_DE_GRUPO = {"descripcion", "description", "nota", "advertencia"}

NIVEL_ERROR = "ERROR"
NIVEL_WARN = "WARN"
NIVEL_INFO = "INFO"

ICONO = {NIVEL_ERROR: "[X]", NIVEL_WARN: "[!]", NIVEL_INFO: "[i]"}


class Reporte:
    """Acumula hallazgos y decide el codigo de salida."""

    def __init__(self) -> None:
        self.items: List[Dict[str, Any]] = []

    def add(
        self,
        nivel: str,
        check: str,
        mensaje: str,
        canal: Optional[str] = None,
        evidencia: Any = None,
    ) -> None:
        self.items.append(
            {
                "nivel": nivel,
                "check": check,
                "canal": canal,
                "mensaje": mensaje,
                "evidencia": evidencia,
            }
        )

    def ok(self, check: str, mensaje: str, canal: Optional[str] = None) -> None:
        self.add(NIVEL_INFO, check, mensaje, canal)

    @property
    def errores(self) -> int:
        return sum(1 for i in self.items if i["nivel"] == NIVEL_ERROR)

    @property
    def advertencias(self) -> int:
        return sum(1 for i in self.items if i["nivel"] == NIVEL_WARN)

    def imprimir(self, solo_problemas: bool = False) -> None:
        for i in self.items:
            if solo_problemas and i["nivel"] == NIVEL_INFO:
                continue
            canal = f"[{i['canal']}] " if i["canal"] else ""
            print(f"  {ICONO[i['nivel']]} {canal}{i['mensaje']}")

    def a_json(self, contrato: str, datos: Optional[str]) -> Dict[str, Any]:
        return {
            "schema_version": "1.0",
            "kind": "contract_validation_report",
            "contract": contrato,
            "data": datos,
            "executed_at": datetime.now(timezone.utc).isoformat(),
            "summary": {
                "checks": len(self.items),
                "errors": self.errores,
                "warnings": self.advertencias,
                "status": "failed" if self.errores else "passed",
            },
            "findings": self.items,
        }


# ─── Lectura del contrato ────────────────────────────────────────────────────

def cargar_contrato(path: Path) -> Dict[str, Any]:
    if not path.exists():
        print(f"ERROR: no existe el contrato {path}", file=sys.stderr)
        sys.exit(2)
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as exc:
        print(f"ERROR: YAML invalido en {path}: {exc}", file=sys.stderr)
        sys.exit(2)
    if not isinstance(data, dict):
        print(f"ERROR: el contrato {path} no es un mapeo YAML", file=sys.stderr)
        sys.exit(2)
    return data


def iterar_canales(contrato: Dict[str, Any]) -> Iterable[Tuple[str, str, Dict[str, Any]]]:
    """Produce (grupo, nombre_canal, definicion).

    Acepta la forma agrupada por capa semantica:
        canales: {grupo: {canal: {...}}}
    y la forma plana:
        canales: {canal: {...}}
    """
    canales = contrato.get("canales") or contrato.get("channels") or {}
    if not isinstance(canales, dict):
        return
    for clave, valor in canales.items():
        if not isinstance(valor, dict):
            continue
        hijos = {
            k: v
            for k, v in valor.items()
            if isinstance(v, dict) and k not in CLAVES_DE_GRUPO
        }
        # Es un grupo si todos sus hijos-dict parecen definiciones de canal.
        es_grupo = bool(hijos) and any(
            ("clase" in v or "unidad" in v or "tipo" in v or "rol" in v) for v in hijos.values()
        )
        if es_grupo:
            for nombre, definicion in hijos.items():
                yield clave, nombre, definicion
        else:
            yield "", clave, valor


def columna_de(nombre: str, definicion: Dict[str, Any]) -> str:
    return str(definicion.get("columna") or definicion.get("column") or nombre)


# ─── Validacion de la forma del contrato ─────────────────────────────────────

def validar_esquema(contrato: Dict[str, Any], rep: Reporte) -> None:
    for clave in ("fuente", "canales"):
        if clave not in contrato:
            rep.add(NIVEL_ERROR, "schema.claves", f"falta la seccion obligatoria `{clave}`")

    if "tiempo" not in contrato:
        rep.add(
            NIVEL_WARN,
            "schema.tiempo",
            "sin seccion `tiempo`: no se podra auditar cadencia, huecos ni duplicados",
        )

    fuente = contrato.get("fuente") or {}
    if isinstance(fuente, dict):
        if not fuente.get("cadencia_nominal_s"):
            rep.add(NIVEL_WARN, "schema.cadencia", "`fuente.cadencia_nominal_s` sin declarar")
        if fuente.get("acceso") not in (None, "solo_lectura", "lectura_escritura"):
            rep.add(NIVEL_WARN, "schema.acceso", f"`fuente.acceso` inesperado: {fuente.get('acceso')}")

    canales = list(iterar_canales(contrato))
    if not canales:
        rep.add(NIVEL_ERROR, "schema.canales", "el contrato no declara ningun canal")
        return

    vistos: Dict[str, str] = {}
    n_modelables = 0

    for grupo, nombre, d in canales:
        etiqueta = f"{grupo}.{nombre}" if grupo else nombre

        clase = d.get("clase")
        if clase is None:
            rep.add(NIVEL_ERROR, "schema.clase", "sin `clase` declarada", canal=etiqueta)
        elif clase not in CLASES_VALIDAS:
            rep.add(
                NIVEL_ERROR,
                "schema.clase",
                f"clase invalida `{clase}` (validas: {sorted(CLASES_VALIDAS)})",
                canal=etiqueta,
            )
        elif clase in CLASES_MODELABLES:
            n_modelables += 1

        tipo = d.get("tipo")
        if tipo is not None and tipo not in TIPOS_VALIDOS:
            rep.add(
                NIVEL_ERROR,
                "schema.tipo",
                f"tipo invalido `{tipo}` (validos: {sorted(TIPOS_VALIDOS)})",
                canal=etiqueta,
            )

        if clase in {"medicion", "ambiente"} and not d.get("unidad"):
            rep.add(
                NIVEL_WARN,
                "schema.unidad",
                "canal fisico sin `unidad` declarada: el contrato queda incompleto",
                canal=etiqueta,
            )

        for clave_rango in ("rango_valido", "rango_observado"):
            r = d.get(clave_rango)
            if r is None:
                continue
            if not (isinstance(r, (list, tuple)) and len(r) == 2):
                rep.add(NIVEL_ERROR, "schema.rango", f"`{clave_rango}` debe ser [min, max]", canal=etiqueta)
            elif r[0] is not None and r[1] is not None and r[0] > r[1]:
                rep.add(NIVEL_ERROR, "schema.rango", f"`{clave_rango}` invertido: {r}", canal=etiqueta)

        if d.get("tipo") == "categorico" and not d.get("valores_observados"):
            rep.add(
                NIVEL_WARN,
                "schema.categorico",
                "canal categorico sin `valores_observados`: no se podra detectar un valor nuevo",
                canal=etiqueta,
            )

        if d.get("clase") == "descartada" and not d.get("motivo"):
            rep.add(NIVEL_WARN, "schema.descartada", "canal descartado sin `motivo`", canal=etiqueta)

        col = columna_de(nombre, d)
        if col in vistos:
            rep.add(
                NIVEL_ERROR,
                "schema.duplicado",
                f"la columna `{col}` ya la reclama `{vistos[col]}`",
                canal=etiqueta,
            )
        else:
            vistos[col] = etiqueta

    if n_modelables == 0:
        rep.add(
            NIVEL_ERROR,
            "schema.modelables",
            "ningun canal de clase `medicion` o `derivada`: no hay senal de salud que modelar",
        )
    else:
        rep.ok("schema.modelables", f"{n_modelables} canal(es) aptos para alimentar un modelo")

    if "dominio_de_validez" not in contrato:
        rep.add(
            NIVEL_WARN,
            "schema.dominio",
            "sin `dominio_de_validez`: el detector no sabra cuando abstenerse (regla BR-003)",
        )

    if "segmentacion" not in contrato:
        rep.add(
            NIVEL_WARN,
            "schema.segmentacion",
            "sin `segmentacion`: la unidad de analisis y de particion queda indefinida",
        )

    rep.ok("schema", f"{len(canales)} canal(es) declarados, forma del contrato revisada")


# ─── Validacion contra los datos ─────────────────────────────────────────────

def _es_numerico(serie) -> bool:
    import pandas as pd

    return pd.api.types.is_numeric_dtype(serie)


def validar_tiempo(df, contrato: Dict[str, Any], rep: Reporte) -> None:
    import numpy as np
    import pandas as pd

    tiempo = contrato.get("tiempo") or {}
    col = tiempo.get("columna") or tiempo.get("column")
    if not col:
        return
    if col not in df.columns:
        rep.add(NIVEL_ERROR, "tiempo.columna", f"la columna de tiempo `{col}` no existe en los datos")
        return

    serie = df[col]
    if not pd.api.types.is_datetime64_any_dtype(serie):
        try:
            serie = pd.to_datetime(serie, utc=True, errors="coerce")
        except Exception:  # pragma: no cover
            rep.add(NIVEL_ERROR, "tiempo.tipo", f"`{col}` no es convertible a datetime")
            return
        if serie.isna().all():
            rep.add(NIVEL_ERROR, "tiempo.tipo", f"`{col}` no es convertible a datetime")
            return

    n_nat = int(serie.isna().sum())
    if n_nat:
        rep.add(NIVEL_ERROR, "tiempo.nulos", f"{n_nat} timestamp(s) no parseables", evidencia=n_nat)

    diffs = serie.diff().dt.total_seconds().to_numpy()[1:]
    diffs = diffs[~np.isnan(diffs)]
    if diffs.size == 0:
        rep.add(NIVEL_WARN, "tiempo.cadencia", "no hay suficientes muestras para auditar la cadencia")
        return

    n_retrocesos = int((diffs < 0).sum())
    if tiempo.get("monotono", True) and n_retrocesos:
        rep.add(
            NIVEL_ERROR,
            "tiempo.monotono",
            f"{n_retrocesos} retroceso(s) temporal(es); el contrato declara monotono: true. "
            "Ordenar por timestamp ANTES de cualquier merge_asof",
            evidencia=n_retrocesos,
        )
    elif n_retrocesos:
        rep.add(NIVEL_WARN, "tiempo.monotono", f"{n_retrocesos} retroceso(s) temporal(es) declarados")
    else:
        rep.ok("tiempo.monotono", "eje temporal monotono")

    n_dup = int((diffs == 0).sum())
    if n_dup and not tiempo.get("duplicados_permitidos", False):
        rep.add(NIVEL_ERROR, "tiempo.duplicados", f"{n_dup} timestamp(s) duplicados", evidencia=n_dup)

    cadencia = (contrato.get("fuente") or {}).get("cadencia_nominal_s")
    positivos = diffs[diffs > 0]
    if cadencia and positivos.size:
        mediana = float(np.median(positivos))
        rep.ok("tiempo.cadencia", f"cadencia mediana observada {mediana:.3f} s (nominal {cadencia} s)")
        if abs(mediana - float(cadencia)) > 0.5 * float(cadencia):
            rep.add(
                NIVEL_ERROR,
                "tiempo.cadencia",
                f"la cadencia mediana {mediana:.3f} s se aleja mas de 50% de la nominal {cadencia} s",
                evidencia={"mediana_s": mediana, "nominal_s": cadencia},
            )

    umbral_hueco = tiempo.get("hueco_minimo_reportable_s")
    if umbral_hueco and positivos.size:
        huecos = positivos[positivos >= float(umbral_hueco)]
        horas = float(huecos.sum()) / 3600.0 if huecos.size else 0.0
        rep.ok(
            "tiempo.huecos",
            f"{huecos.size} hueco(s) sobre {umbral_hueco} s, {horas:.1f} h ausentes en total",
        )
        declarado = (contrato.get("huecos_conocidos") or {}).get("total_horas_ausentes")
        if declarado is not None:
            try:
                declarado_f = float(str(declarado).lstrip("~"))
            except (TypeError, ValueError):
                declarado_f = None
            if declarado_f is not None and declarado_f > 0 and horas > 1.5 * declarado_f:
                rep.add(
                    NIVEL_WARN,
                    "tiempo.huecos",
                    f"{horas:.1f} h ausentes frente a {declarado_f:.1f} h declaradas: "
                    "el archivado cambio o el contrato quedo obsoleto",
                    evidencia={"observado_h": horas, "declarado_h": declarado_f},
                )


def validar_canal(df, etiqueta: str, col: str, d: Dict[str, Any], rep: Reporte) -> None:
    import numpy as np
    import pandas as pd

    clase = d.get("clase")

    if col not in df.columns:
        nivel = NIVEL_INFO if clase == "descartada" else NIVEL_ERROR
        rep.add(nivel, "canal.ausente", f"la columna `{col}` no existe en los datos", canal=etiqueta)
        return

    serie = df[col]

    if clase == "descartada":
        rep.ok("canal.descartada", f"presente en los datos pero excluida por contrato ({col})", etiqueta)

    n_nulos = int(serie.isna().sum())
    if n_nulos and d.get("nullable") is False:
        rep.add(
            NIVEL_ERROR,
            "canal.nulos",
            f"{n_nulos} nulo(s) en un canal declarado `nullable: false`",
            canal=etiqueta,
            evidencia=n_nulos,
        )

    tipo = d.get("tipo")
    if tipo in {"float", "int"} and not _es_numerico(serie):
        rep.add(NIVEL_ERROR, "canal.tipo", f"declarado `{tipo}` pero el dtype es {serie.dtype}", canal=etiqueta)
        return

    centinela = d.get("centinela")
    if centinela is not None and _es_numerico(serie):
        valores = centinela if isinstance(centinela, (list, tuple)) else [centinela]
        n_cent = int(serie.isin(list(valores)).sum())
        if n_cent:
            rep.add(
                NIVEL_WARN,
                "canal.centinela",
                f"{n_cent} muestra(s) con valor centinela {valores}: convertir a NaN antes de modelar",
                canal=etiqueta,
                evidencia=n_cent,
            )

    limpia = serie.dropna()
    if centinela is not None and _es_numerico(serie) and not limpia.empty:
        valores = centinela if isinstance(centinela, (list, tuple)) else [centinela]
        limpia = limpia[~limpia.isin(list(valores))]

    if limpia.empty:
        rep.add(NIVEL_WARN, "canal.vacio", "sin muestras utiles tras descartar nulos y centinelas", canal=etiqueta)
        return

    if _es_numerico(limpia):
        vmin, vmax = float(limpia.min()), float(limpia.max())

        rango_valido = d.get("rango_valido")
        if rango_valido and len(rango_valido) == 2:
            lo, hi = rango_valido
            fuera = 0
            if lo is not None:
                fuera += int((limpia < float(lo)).sum())
            if hi is not None:
                fuera += int((limpia > float(hi)).sum())
            if fuera:
                rep.add(
                    NIVEL_ERROR,
                    "canal.rango_valido",
                    f"{fuera} muestra(s) fuera del dominio fisico {rango_valido}; "
                    f"observado [{vmin:.6g}, {vmax:.6g}]",
                    canal=etiqueta,
                    evidencia={"fuera": fuera, "min": vmin, "max": vmax},
                )
            else:
                rep.ok("canal.rango_valido", f"dentro del dominio fisico {rango_valido}", etiqueta)

        rango_obs = d.get("rango_observado")
        if rango_obs and len(rango_obs) == 2:
            lo, hi = rango_obs
            try:
                excede = (lo is not None and vmin < float(lo)) or (hi is not None and vmax > float(hi))
            except (TypeError, ValueError):
                excede = False
            if excede:
                rep.add(
                    NIVEL_WARN,
                    "canal.rango_observado",
                    f"observado [{vmin:.6g}, {vmax:.6g}] excede el rango de la auditoria {rango_obs}: "
                    "regimen nuevo o contrato desactualizado",
                    canal=etiqueta,
                    evidencia={"min": vmin, "max": vmax, "declarado": list(rango_obs)},
                )

    valores_decl = d.get("valores_observados")
    if valores_decl:
        try:
            presentes = set(pd.unique(limpia))
        except Exception:  # pragma: no cover
            presentes = set()
        declarados = set(valores_decl)
        nuevos = {v for v in presentes if v not in declarados and not _casi_igual(v, declarados)}
        if nuevos:
            muestra = [_escalar(v) for v in sorted(nuevos, key=str)[:12]]
            rep.add(
                NIVEL_ERROR,
                "canal.valores_nuevos",
                f"{len(nuevos)} valor(es) no declarados en `valores_observados`: {muestra}. "
                "Evento de CONTRATO (firmware, configuracion o archivador), no anomalia del equipo",
                canal=etiqueta,
                evidencia=[str(v) for v in muestra],
            )
        else:
            rep.ok("canal.valores", f"conjunto cerrado respetado ({len(declarados)} valores)", etiqueta)

    if clase in CLASES_MODELABLES and _es_numerico(limpia):
        std = float(np.std(limpia.to_numpy(dtype=float)))
        if std == 0.0:
            rep.add(
                NIVEL_ERROR,
                "canal.constante",
                "constante en todo el periodo: capacidad informativa nula, no puede alimentar un modelo",
                canal=etiqueta,
            )


def _escalar(valor: Any) -> Any:
    """Escalares de numpy a tipos de Python, para que el mensaje y el JSON sean legibles."""
    item = getattr(valor, "item", None)
    if callable(item):
        try:
            return item()
        except (TypeError, ValueError):
            pass
    return valor


def _casi_igual(valor: Any, declarados: set) -> bool:
    """Tolera 0 vs 0.0 y numpy scalars frente a los literales del YAML."""
    try:
        f = float(valor)
    except (TypeError, ValueError):
        return False
    for d in declarados:
        try:
            if abs(float(d) - f) < 1e-12:
                return True
        except (TypeError, ValueError):
            continue
    return False


def validar_datos(df, contrato: Dict[str, Any], rep: Reporte) -> None:
    validar_tiempo(df, contrato, rep)
    for grupo, nombre, d in iterar_canales(contrato):
        etiqueta = f"{grupo}.{nombre}" if grupo else nombre
        validar_canal(df, etiqueta, columna_de(nombre, d), d, rep)


def cargar_datos(path: Path, max_filas: Optional[int]):
    try:
        import pandas as pd
    except ImportError:
        print("ERROR: falta pandas para validar contra datos (usa --schema-only)", file=sys.stderr)
        sys.exit(2)

    if not path.exists():
        print(f"ERROR: no existen los datos {path}", file=sys.stderr)
        sys.exit(2)

    sufijo = path.suffix.lower()
    if sufijo in {".parquet", ".pq"}:
        df = pd.read_parquet(path)
    elif sufijo in {".csv", ".txt"}:
        df = pd.read_csv(path)
    elif sufijo in {".feather", ".ft"}:
        df = pd.read_feather(path)
    else:
        print(f"ERROR: formato no soportado: {sufijo}", file=sys.stderr)
        sys.exit(2)

    if max_filas and len(df) > max_filas:
        df = df.head(max_filas)
    return df


# ─── CLI ─────────────────────────────────────────────────────────────────────

def main() -> None:
    p = argparse.ArgumentParser(
        description="Valida un contrato de telemetria IEF contra su forma y contra los datos reales."
    )
    p.add_argument("--contract", required=True, help="ruta a data-contract.yml")
    p.add_argument("--data", help="parquet/csv/feather a validar")
    p.add_argument("--schema-only", action="store_true", help="valida solo la forma del contrato")
    p.add_argument("--report", help="ruta del reporte JSON de salida")
    p.add_argument("--strict", action="store_true", help="las advertencias tambien fallan")
    p.add_argument("--max-rows", type=int, help="limita las filas leidas (auditoria rapida)")
    p.add_argument("--quiet", action="store_true", help="imprime solo errores y advertencias")
    args = p.parse_args()

    contrato_path = Path(args.contract)
    contrato = cargar_contrato(contrato_path)
    rep = Reporte()

    print(f"CONTRATO: {contrato_path}")
    validar_esquema(contrato, rep)

    datos_path = None
    if args.data and not args.schema_only:
        datos_path = Path(args.data)
        df = cargar_datos(datos_path, args.max_rows)
        print(f"DATOS:    {datos_path}  ({len(df)} filas x {len(df.columns)} columnas)")
        validar_datos(df, contrato, rep)
    elif not args.schema_only:
        rep.add(
            NIVEL_WARN,
            "datos",
            "sin --data: el contrato quedo verificado en su forma, no contra la realidad",
        )

    print("-" * 78)
    rep.imprimir(solo_problemas=args.quiet)
    print("-" * 78)
    print(
        f"Resumen: {len(rep.items)} check(s) · "
        f"{rep.errores} error(es) · {rep.advertencias} advertencia(s)"
    )

    if args.report:
        salida = Path(args.report)
        salida.parent.mkdir(parents=True, exist_ok=True)
        with open(salida, "w", encoding="utf-8") as f:
            json.dump(
                rep.a_json(str(contrato_path), str(datos_path) if datos_path else None),
                f,
                indent=2,
                ensure_ascii=False,
            )
        print(f"Reporte: {salida}")

    if rep.errores or (args.strict and rep.advertencias):
        sys.exit(1)


if __name__ == "__main__":
    main()
