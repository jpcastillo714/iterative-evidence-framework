"""El ciclo de vida de una regla: propuesta -> activa -> superada.

Es la direccion que distingue al IEF de spec-kit. Alli la constitucion se escribe de
arriba abajo antes de empezar; aqui las reglas se DESCUBREN trabajando y suben.

Y era donde estaba el agujero: promover sin detectar conflictos deja que dos incrementos
contradictorios convivan en silencio. Ese es literalmente el problema que origino este
trabajo: "me dijiste que cambiaste el archivo y no veo el cambio".
"""

from __future__ import annotations

import yaml

from conftest import correr


def _proyecto(tmp_path):
    d = tmp_path / "proj"
    d.mkdir(exist_ok=True)
    correr("--mode", "init", "--project-dir", str(d), "--preset", "product",
           "--layout", "flat", "--initiative-name", "P")
    return d


def _incremento_listo(d, nombre, reglas):
    """Abre un incremento, le escribe sus reglas y lo deja promovible."""
    correr("--mode", "new-increment", "--project-dir", str(d), "--type", "build",
           "--name", nombre)
    st = yaml.safe_load((d / "initiative" / "state.yml").read_text(encoding="utf-8"))
    inc = st["increments"][-1]
    slug = inc["slug"]

    dir_inc = d / "initiative" / "increments" / slug
    dir_inc.mkdir(parents=True, exist_ok=True)
    (dir_inc / "rules.yml").write_text(
        yaml.safe_dump({"rules": reglas}, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )

    inc["status"] = "COMPLETED"
    for k in inc["steps"]:
        inc["steps"][k] = "APPROVED"
    (d / "initiative" / "state.yml").write_text(
        yaml.safe_dump(st, sort_keys=False, allow_unicode=True), encoding="utf-8"
    )
    return slug


def _vigentes(d):
    ruta = d / "initiative" / "specs" / "rules.yml"
    if not ruta.exists():
        return {}
    doc = yaml.safe_load(ruta.read_text(encoding="utf-8")) or {}
    return {r["id"]: r for r in doc.get("rules", [])}


REGLA_A = [{
    "id": "RUL-001-001",
    "statement": "Un pedido sin cliente se descarta",
    "rationale": "El 3% del historico no tiene cliente y son pruebas del ERP",
    "applies_to": "pedidos.validacion",
    "scope": "increment",
    "status": "proposed",
}]


# ─── Promocion ───────────────────────────────────────────────────────────────

def test_promover_sube_la_regla_al_proyecto(tmp_path):
    d = _proyecto(tmp_path)
    slug = _incremento_listo(d, "Ingesta", REGLA_A)

    r = correr("--mode", "merge-increment", "--project-dir", str(d), "--increment", slug)
    assert r.returncode == 0, r.stdout + r.stderr

    regla = _vigentes(d)["RUL-001-001"]
    assert regla["scope"] == "project", "al promoverse deja de regir solo su incremento"
    assert regla["status"] == "active"
    assert regla["_origen"]["increment"] == slug, "la procedencia se conserva"


def test_no_se_promueve_con_compuertas_sin_aprobar(tmp_path):
    d = _proyecto(tmp_path)
    correr("--mode", "new-increment", "--project-dir", str(d), "--type", "build",
           "--name", "Sin aprobar")
    r = correr("--mode", "merge-increment", "--project-dir", str(d),
               "--increment", "001_sin_aprobar")
    assert r.returncode != 0
    assert "compuertas sin aprobar" in r.stderr


def test_dry_run_no_escribe(tmp_path):
    d = _proyecto(tmp_path)
    slug = _incremento_listo(d, "Ingesta", REGLA_A)
    r = correr("--mode", "merge-increment", "--project-dir", str(d),
               "--increment", slug, "--dry-run")
    assert r.returncode == 0
    assert "DRY-RUN" in r.stdout
    assert not (d / "initiative" / "specs" / "rules.yml").exists()


# ─── Conflictos ──────────────────────────────────────────────────────────────

REGLA_B_CONTRADICE = [{
    "id": "RUL-002-001",
    "statement": "Un pedido sin cliente se asigna al cliente generico",
    "rationale": "Descartarlos perdia 3% de facturacion real: eran ventas de mostrador",
    "applies_to": "pedidos.validacion",      # el MISMO ambito que RUL-001-001
    "scope": "increment",
    "status": "proposed",
}]


def test_una_contradiccion_sin_declarar_detiene_la_promocion(tmp_path):
    """El agujero que cerraba este trabajo."""
    d = _proyecto(tmp_path)
    correr("--mode", "merge-increment", "--project-dir", str(d),
           "--increment", _incremento_listo(d, "Ingesta", REGLA_A))

    slug = _incremento_listo(d, "Limpieza", REGLA_B_CONTRADICE)
    r = correr("--mode", "merge-increment", "--project-dir", str(d), "--increment", slug)

    assert r.returncode != 0, "dos reglas contradictorias no pueden convivir en silencio"
    assert "CONFLICTO" in r.stdout
    assert "supersedes: RUL-001-001" in r.stdout, "y debe decir como resolverlo"
    assert _vigentes(d)["RUL-001-001"]["status"] == "active", "nada cambio"


def test_con_supersedes_declarado_se_acepta(tmp_path):
    d = _proyecto(tmp_path)
    correr("--mode", "merge-increment", "--project-dir", str(d),
           "--increment", _incremento_listo(d, "Ingesta", REGLA_A))

    regla = [dict(REGLA_B_CONTRADICE[0], supersedes="RUL-001-001")]
    slug = _incremento_listo(d, "Limpieza", regla)
    r = correr("--mode", "merge-increment", "--project-dir", str(d), "--increment", slug)
    assert r.returncode == 0, r.stdout + r.stderr


def test_la_regla_superada_no_se_borra(tmp_path):
    """El proyecto necesita recordar que un dia penso lo contrario, y por que."""
    d = _proyecto(tmp_path)
    correr("--mode", "merge-increment", "--project-dir", str(d),
           "--increment", _incremento_listo(d, "Ingesta", REGLA_A))
    regla = [dict(REGLA_B_CONTRADICE[0], supersedes="RUL-001-001")]
    correr("--mode", "merge-increment", "--project-dir", str(d),
           "--increment", _incremento_listo(d, "Limpieza", regla))

    vig = _vigentes(d)
    assert set(vig) == {"RUL-001-001", "RUL-002-001"}, "las dos siguen ahi"
    vieja = vig["RUL-001-001"]
    assert vieja["status"] == "superseded"
    assert vieja["superseded_by"] == "RUL-002-001"
    assert vieja["superseded_at"], "con fecha: importa cuando dejo de regir"
    assert vieja["rationale"], "y conserva por que se penso en su momento"


def test_supersedes_a_una_regla_inexistente_se_rechaza(tmp_path):
    d = _proyecto(tmp_path)
    regla = [dict(REGLA_A[0], supersedes="RUL-999-999")]
    slug = _incremento_listo(d, "Ingesta", regla)
    r = correr("--mode", "merge-increment", "--project-dir", str(d), "--increment", slug)
    assert r.returncode != 0
    assert "no existe en la especificacion viva" in r.stdout


def test_ambitos_distintos_no_chocan(tmp_path):
    """Solo es conflicto si gobiernan lo mismo. Si no, el motor estorbaria."""
    d = _proyecto(tmp_path)
    correr("--mode", "merge-increment", "--project-dir", str(d),
           "--increment", _incremento_listo(d, "Ingesta", REGLA_A))

    otra = [dict(REGLA_B_CONTRADICE[0], applies_to="facturas.validacion")]
    slug = _incremento_listo(d, "Facturas", otra)
    r = correr("--mode", "merge-increment", "--project-dir", str(d), "--increment", slug)
    assert r.returncode == 0, r.stdout + r.stderr
    assert len(_vigentes(d)) == 2


# ─── Constitucion ────────────────────────────────────────────────────────────

def test_init_crea_la_constitucion(tmp_path):
    d = _proyecto(tmp_path)
    const = d / "initiative" / "specs" / "constitution.md"
    assert const.exists(), "la capa de arriba abajo debe existir desde el principio"
    texto = const.read_text(encoding="utf-8")
    assert "{{PROYECTO}}" not in texto, "la plantilla se rellena al crearla"
    assert "rules.yml" in texto, "debe explicar como se distingue de las reglas promovidas"


def test_la_constitucion_no_se_pisa_al_reiniciar(tmp_path):
    d = _proyecto(tmp_path)
    const = d / "initiative" / "specs" / "constitution.md"
    const.write_text("# Mis principios propios\n", encoding="utf-8")
    correr("--mode", "init", "--project-dir", str(d), "--preset", "product",
           "--initiative-name", "P", "--force-overwrite")
    assert const.read_text(encoding="utf-8") == "# Mis principios propios\n"
