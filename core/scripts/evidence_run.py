#!/usr/bin/env python3
"""
IEF V3 · preset astro-mlops
Puente de evidencia: ejecucion -> carpeta VRN -> run de MLflow.

Que resuelve
------------
MLflow registra QUE se ejecuto y con que parametros. El IEF registra POR QUE se
ejecuto y contra que criterio. Ninguno de los dos, solo, permite ir desde una
afirmacion del informe hasta el dato, el commit y la figura.

Este script ejecuta un comando, captura su evidencia cruda segun
`core/docs/verification_contract_spec.md` y, si MLflow esta disponible, crea o
etiqueta el run correspondiente con las claves `ief.*`. El `run_id` queda escrito
en el `artifacts.yml` del VRN, cerrando la cadena en ambos sentidos:

    CLM -> CRT -> TST -> VRN -> EVI            (IEF)
                          |
                          +-> mlflow run_id     (parametros, metricas, modelo)

Uso
---
    python core/scripts/evidence_run.py \\
        --test TST-ACC-007 --claim CLM-003-001 --criterion CRT-003-002 \\
        --name "Tasa de falsas alarmas en operacion nominal" \\
        -- python 04_codigo/pipelines/evaluar.py --config conf/config.yaml

Todo lo que vaya despues de `--` es el comando. El codigo de salida del script es
el del comando, salvo con --allow-failure (util para registrar un fallo esperado).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import yaml
except ImportError:  # pragma: no cover
    print("ERROR: falta PyYAML (pip install pyyaml)", file=sys.stderr)
    sys.exit(2)


# Se descubren desde el preset activo; esta lista es solo el respaldo cuando no
# hay preset o el proyecto no declara convencion de directorios.
DIRS_POR_DEFECTO = ["06_resultados", "05_datos/processed", "outputs", "artifacts", "results"]


def sha256(path: Path, tope_bytes: int = 2_000_000_000) -> Optional[str]:
    """Huella del CONTENIDO. Una ruta apunta a lo que haya hoy; un hash, a esto.

    Es lo que el invariante P7 exige y lo que permite que una cifra citada en el
    informe siga senalando el archivo con el que se calculo, aunque el pipeline se
    haya vuelto a ejecutar encima.
    """
    try:
        if path.stat().st_size > tope_bytes:
            return None
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for bloque in iter(lambda: f.read(1024 * 1024), b""):
                h.update(bloque)
        return h.hexdigest()
    except OSError:
        return None


def huella_entorno(project_dir: Path) -> Dict[str, Any]:
    """Sin las versiones de las librerias, `python 3.11` no reproduce nada."""
    info: Dict[str, Any] = {
        "python": platform.python_version(),
        "platform": platform.platform(),
        "cwd": str(project_dir),
    }
    for nombre in ("requirements.txt", "pyproject.toml", "uv.lock", "poetry.lock",
                   "environment.yml", "conda-lock.yml"):
        f = project_dir / nombre
        if f.exists():
            info.setdefault("lockfiles", {})[nombre] = sha256(f)
    try:
        out = subprocess.run(
            [sys.executable, "-m", "pip", "freeze", "--disable-pip-version-check"],
            capture_output=True, text=True, timeout=60,
        )
        if out.returncode == 0 and out.stdout.strip():
            info["pip_freeze_sha256"] = hashlib.sha256(out.stdout.encode()).hexdigest()
            info["pip_freeze_n_paquetes"] = len(out.stdout.strip().splitlines())
    except (OSError, subprocess.SubprocessError):
        pass
    return info


# ─── Estado IEF ──────────────────────────────────────────────────────────────

def cargar_state(project_dir: Path) -> Dict[str, Any]:
    path = project_dir / "initiative" / "state.yml"
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def resolver_incremento(state: Dict[str, Any], pedido: Optional[str]) -> str:
    if pedido:
        return pedido
    activo = state.get("active_increment")
    if activo:
        return str(activo)
    return "sin_incremento"


def id_incremento(slug: str) -> str:
    """De `003_pipeline_segmentacion` saca `003`."""
    cabeza = slug.split("_", 1)[0]
    return cabeza if cabeza.isdigit() else slug[:12]


def siguiente_vrn(dir_runs: Path, inc_id: str, test_id: str) -> str:
    sufijo_test = test_id.replace("TST-", "").replace("ACC-", "")
    prefijo = f"VRN-{inc_id}-{sufijo_test}-"
    existentes = [d.name for d in dir_runs.glob(f"{prefijo}*")] if dir_runs.exists() else []
    numeros = []
    for nombre in existentes:
        cola = nombre[len(prefijo) :]
        if cola.isdigit():
            numeros.append(int(cola))
    return f"{prefijo}{max(numeros) + 1 if numeros else 1:03d}"


# ─── Contexto de reproducibilidad ────────────────────────────────────────────

def git_info(project_dir: Path) -> Dict[str, Optional[str]]:
    def _git(*args: str) -> Optional[str]:
        try:
            out = subprocess.run(
                ["git", *args], cwd=project_dir, capture_output=True, text=True, timeout=10
            )
            return out.stdout.strip() if out.returncode == 0 else None
        except (OSError, subprocess.SubprocessError):
            return None

    estado = _git("status", "--porcelain")
    return {
        "commit": _git("rev-parse", "HEAD"),
        "branch": _git("rev-parse", "--abbrev-ref", "HEAD"),
        "dirty": None if estado is None else bool(estado),
    }


def snapshot_mtimes(project_dir: Path, dirs: List[str]) -> Dict[str, float]:
    vistos: Dict[str, float] = {}
    for d in dirs:
        base = project_dir / d
        if not base.exists():
            continue
        for p in base.rglob("*"):
            if p.is_file():
                try:
                    vistos[str(p)] = p.stat().st_mtime
                except OSError:
                    continue
    return vistos


def artefactos_nuevos(project_dir: Path, dirs: List[str], antes: Dict[str, float], t0: float) -> List[str]:
    salida: List[str] = []
    for d in dirs:
        base = project_dir / d
        if not base.exists():
            continue
        for p in base.rglob("*"):
            if not p.is_file():
                continue
            try:
                m = p.stat().st_mtime
            except OSError:
                continue
            if m >= t0 - 1.0 and antes.get(str(p)) != m:
                salida.append(str(p.relative_to(project_dir)))
    return sorted(salida)


# ─── MLflow (opcional) ───────────────────────────────────────────────────────

def registrar_en_mlflow(args, meta: Dict[str, Any], metricas: Dict[str, float]) -> Optional[Dict[str, str]]:
    if args.no_mlflow:
        return None
    try:
        import mlflow
    except ImportError:
        return None

    try:
        if args.mlflow_uri:
            mlflow.set_tracking_uri(args.mlflow_uri)
        mlflow.set_experiment(args.mlflow_experiment or meta["increment"])
        with mlflow.start_run(run_name=meta["vrn_id"]) as run:
            mlflow.set_tags(
                {
                    "ief.increment": meta["increment"],
                    "ief.claim": meta.get("claim_id") or "PENDING",
                    "ief.criterion": meta.get("criterion_id") or "PENDING",
                    "ief.test": meta["test_id"],
                    "ief.vrn": meta["vrn_id"],
                    "ief.verification_level": meta["verification_level"],
                    "ief.requirement": meta["requirement"],
                    "ief.status": meta["status"],
                    "git.commit": str(meta.get("git", {}).get("commit")),
                    "git.dirty": str(meta.get("git", {}).get("dirty")),
                }
            )
            mlflow.log_param("command", meta["command"][:500])
            mlflow.log_param("seed", args.seed)
            for k, v in metricas.items():
                try:
                    mlflow.log_metric(k, float(v))
                except (TypeError, ValueError):
                    continue
            return {"run_id": run.info.run_id, "tracking_uri": mlflow.get_tracking_uri()}
    except Exception as exc:  # pragma: no cover
        print(f"[MLflow] no se pudo registrar el run: {exc}", file=sys.stderr)
        return None


def _metricas_desde(path: Optional[str]) -> Dict[str, float]:
    """Extrae metricas escalares de un JSON plano o anidado (p. ej. evaluacion.json)."""
    if not path or not Path(path).exists():
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            doc = json.load(f)
    except (OSError, json.JSONDecodeError):
        return {}

    salida: Dict[str, float] = {}

    def _walk(nodo: Any, prefijo: str = "") -> None:
        if isinstance(nodo, dict):
            for k, v in nodo.items():
                _walk(v, f"{prefijo}{k}.")
        elif isinstance(nodo, (int, float)) and not isinstance(nodo, bool):
            salida[prefijo.rstrip(".").replace("-", "_")] = float(nodo)

    _walk(doc)
    return {k: v for k, v in salida.items() if len(k) < 120}


# ─── Programa principal ──────────────────────────────────────────────────────

def main() -> None:
    p = argparse.ArgumentParser(
        description="Ejecuta un comando y emite su carpeta VRN de evidencia (IEF V3)."
    )
    p.add_argument("--project-dir", default=os.getcwd())
    p.add_argument("--increment", help="slug del incremento (por defecto, el activo en state.yml)")
    p.add_argument("--test", required=True, help="TST-XXX que este run ejecuta")
    p.add_argument("--claim", help="CLM-XXX que el test sustenta")
    p.add_argument("--criterion", help="CRT-XXX que el test mide")
    p.add_argument("--name", default="", help="nombre legible del test")
    p.add_argument("--kind", default="integration",
                   choices=["unit", "static", "integration", "end-to-end", "negative", "manual"])
    p.add_argument("--level", default="executed",
                   choices=["asserted", "inspected", "executed", "reproduced", "independently-reviewed"])
    p.add_argument("--requirement", default="required", choices=["required", "optional"])
    p.add_argument("--expected-exit-code", type=int, default=0)
    p.add_argument("--allow-failure", action="store_true",
                   help="registra el fallo y sale con 0 (para verificaciones negativas)")
    p.add_argument("--seed", type=int, default=None)
    p.add_argument("--metrics-from", help="JSON del que extraer metricas escalares para MLflow")
    p.add_argument("--watch", action="append", help="directorio adicional a vigilar por artefactos")
    p.add_argument("--input", action="append",
                   help="archivo de entrada del que registrar el hash (repetible)")
    p.add_argument("--timeout", type=float, default=None,
                   help="segundos maximos de ejecucion; sin esto un pipeline colgado bloquea la CI")
    p.add_argument("--require-clean", action="store_true",
                   help="rechaza ejecutar si el arbol git tiene cambios sin commitear")
    p.add_argument("--shell", action="store_true", help="ejecuta el comando en el shell")
    p.add_argument("--no-mlflow", action="store_true")
    p.add_argument("--mlflow-uri")
    p.add_argument("--mlflow-experiment")
    p.add_argument("cmd", nargs=argparse.REMAINDER, help="-- comando a ejecutar")
    args = p.parse_args()

    comando = args.cmd[1:] if args.cmd and args.cmd[0] == "--" else args.cmd
    if not comando:
        print("ERROR: falta el comando. Usa: evidence_run.py [opciones] -- <comando>", file=sys.stderr)
        sys.exit(2)

    project_dir = Path(args.project_dir).resolve()
    state = cargar_state(project_dir)
    slug = resolver_incremento(state, args.increment)
    inc_id = id_incremento(slug)

    dir_runs = project_dir / "initiative" / "increments" / slug / "verification" / "runs"
    dir_runs.mkdir(parents=True, exist_ok=True)
    vrn_id = siguiente_vrn(dir_runs, inc_id, args.test)
    vrn_dir = dir_runs / vrn_id
    vrn_dir.mkdir(parents=True, exist_ok=True)

    if args.require_clean:
        estado = git_info(project_dir)
        if estado.get("dirty"):
            print(
                "ERROR: el arbol git tiene cambios sin commitear. Un run sobre un "
                "arbol sucio no es reproducible: commitea, o ejecuta sin "
                "--require-clean y el diff quedara guardado en el VRN.",
                file=sys.stderr,
            )
            sys.exit(2)

    dirs = list(DIRS_POR_DEFECTO) + list(args.watch or [])
    antes = snapshot_mtimes(project_dir, dirs)

    linea = " ".join(comando)
    print(f"[VRN] {vrn_id}  ({slug})")
    print(f"[CMD] {linea}")

    entorno = os.environ.copy()
    if args.seed is not None:
        # Registrar una semilla que no se inyecto es teatro de reproducibilidad.
        entorno["PYTHONHASHSEED"] = str(args.seed)
        entorno["IEF_SEED"] = str(args.seed)

    t0 = time.time()
    inicio = datetime.now(timezone.utc)
    try:
        proc = subprocess.run(
            linea if args.shell else comando,
            cwd=project_dir,
            capture_output=True,
            text=True,
            shell=args.shell,
            env=entorno,
            timeout=args.timeout,
        )
        exit_code, stdout, stderr = proc.returncode, proc.stdout, proc.stderr
        runner_exit = 0
    except subprocess.TimeoutExpired as exc:
        exit_code, runner_exit = None, 1
        stdout = exc.stdout or ""
        stderr = (exc.stderr or "") + (
            f"\nTIMEOUT: el comando supero {args.timeout} s y fue abortado."
        )
    except (OSError, subprocess.SubprocessError) as exc:
        exit_code, stdout, stderr, runner_exit = None, "", f"{type(exc).__name__}: {exc}", 1
    duracion = round(time.time() - t0, 4)

    if runner_exit != 0:
        estado = "error"          # fallo del arnes, no del sistema bajo prueba
    elif exit_code == args.expected_exit_code:
        estado = "passed"
    else:
        estado = "failed"

    artefactos = artefactos_nuevos(project_dir, dirs, antes, t0)

    meta: Dict[str, Any] = {
        "vrn_id": vrn_id,
        "test_id": args.test,
        "claim_id": args.claim,
        "criterion_id": args.criterion,
        "name": args.name or args.test,
        "increment": slug,
        "test_type": args.kind,
        "verification_level": args.level,
        "requirement": args.requirement,
        "command": linea,
        "command_exit_code": exit_code,
        "expected_command_exit_code": args.expected_exit_code,
        "test_runner_exit_code": runner_exit,
        "status": estado,
        "duration_seconds": duracion,
        "executed_at": inicio.isoformat(),
        "environment": huella_entorno(project_dir),
        "git": git_info(project_dir),
        "seed": args.seed,
    }

    metricas = _metricas_desde(args.metrics_from)
    mlflow_info = registrar_en_mlflow(args, meta, metricas)

    (vrn_dir / "command.txt").write_text(linea + "\n", encoding="utf-8")
    (vrn_dir / "stdout.txt").write_text(stdout or "", encoding="utf-8")
    (vrn_dir / "stderr.txt").write_text(stderr or "", encoding="utf-8")

    with open(vrn_dir / "metadata.yml", "w", encoding="utf-8") as f:
        yaml.safe_dump(meta, f, sort_keys=False, allow_unicode=True)

    observaciones = [
        f"Comando finalizado con codigo {exit_code} en {duracion} s",
        f"{len(artefactos)} artefacto(s) nuevo(s) o modificado(s)",
    ]
    if estado == "failed":
        observaciones.append(
            "Distinguir antes de actuar: fallo de ejecucion, hipotesis rechazada o "
            "verificacion bloqueada por prerrequisito ausente."
        )
    with open(vrn_dir / "result.yml", "w", encoding="utf-8") as f:
        yaml.safe_dump(
            {"status": estado, "observations": observaciones, "metrics": metricas or None},
            f,
            sort_keys=False,
            allow_unicode=True,
        )

    doc_art: Dict[str, Any] = {
        "artifacts": [
            {
                "path": rel,
                "sha256": sha256(project_dir / rel),
                "bytes": (project_dir / rel).stat().st_size
                if (project_dir / rel).exists() else None,
            }
            for rel in artefactos
        ],
        "inputs": [
            {"path": str(Path(f)), "sha256": sha256(project_dir / f)}
            for f in (args.input or [])
        ],
    }
    if mlflow_info:
        doc_art["mlflow"] = mlflow_info
        print(f"[MLflow] run_id {mlflow_info['run_id']}")
    with open(vrn_dir / "artifacts.yml", "w", encoding="utf-8") as f:
        yaml.safe_dump(doc_art, f, sort_keys=False, allow_unicode=True)

    print(f"[{estado.upper()}] exit={exit_code} · {duracion}s · {len(artefactos)} artefacto(s)")
    print(f"[EVI] {vrn_dir.relative_to(project_dir)}")

    if estado != "passed" and not args.allow_failure:
        sys.exit(exit_code if isinstance(exit_code, int) and exit_code != 0 else 1)


if __name__ == "__main__":
    main()
