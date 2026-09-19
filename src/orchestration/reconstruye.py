"""Module 29's proof: set the whole lake aside, rebuild it with Dagster, compare.

Saying that a pipeline rebuilds the lake proves nothing. The test that counts is
the one this runs: move `lake/` out of the way, ask Dagster for everything, and
compare what comes back with what was there, table by table.

**Tables are compared by content, not by bytes.** Delta and Iceberg write uuids
and timestamps into their own logs, and PostgreSQL's files are not comparable at
all, so a byte comparison would fail on tables that are fine. Each table gets a
row count and a sum of a hash of every row: it does not care about row order,
and it does notice one changed value or one duplicated row.

**The files git tracks are compared by bytes**, which is stricter: every result
the twin writes and every knob series has to come back identical, and `git
status` decides.

**And so are the lake's own Parquet files**, bronze, weather, reports, silver
and module 7's single file. The first rebuild is why: the same rows came back in
other files and in another order, because DuckDB writes with several threads at
once, and that moved five hourly averages by a hundredth. Since then those
writes go through one thread (src/escritura.py), and this checks that it holds.

Then the ten gates run against the new lake. Only if all of that holds is
`lake_antes/` deleted. If anything fails, nothing is deleted, and the script
says how to put the old lake back.

After that, a second proof, the backfill: one day of bronze is deleted, as if it
had been corrupted, and Dagster rebuilds that day and only that day. It has to
come back identical, and the other days must not be touched.

Run:  .venv\\Scripts\\python.exe src\\orchestration\\reconstruye.py
"""

from __future__ import annotations

import hashlib
import io
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[2]
# Antes de importar dagster. Sin esto la telemetría va encendida: lo explica
# dagster_home/dagster.yaml.
os.environ["DAGSTER_HOME"] = str(PROJECT / "dagster_home")
sys.path.insert(0, str(PROJECT / "src"))
sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

import dagster as dg  # noqa: E402

from db import backup  # noqa: E402
from db.servidor import conecta, esta_vivo, para, servidor  # noqa: E402
from orchestration import definitions as d  # noqa: E402
from transform.table_format import conecta_con_extensiones  # noqa: E402

LAGO = PROJECT / "lake"
ANTES = PROJECT / "lake_antes"
RESULTS = PROJECT / "results" / "m29_reconstruir.json"
PYTHON = PROJECT / ".venv" / "Scripts" / "python.exe"

# El día que se estropea a propósito en la segunda prueba: el de la avería #3,
# que es también el del módulo 13.
DIA_A_RELLENAR = "2020-06-05"

# Lo que había en el lago y ningún activo construye, con el motivo. Si falta
# algo que no esté aquí, la reconstrucción está incompleta y no se borra nada.
RESTOS = {
    "_formatos_de_tabla/_prueba":
        "un catálogo SQLite de prueba del 1 de septiembre, de cuando se montó el "
        "módulo 18. No lo crea ningún script: estaba ahí por accidente",
}

TODO = [*d.defs.assets, *d.defs.asset_checks]


# --- Huellas ------------------------------------------------------------------

def _fuentes() -> dict[str, str]:
    b = LAGO.as_posix()
    f = f"{b}/_formatos_de_tabla"
    return {
        "lago/bronce": f"read_parquet('{b}/bronze/telemetry/**/*.parquet')",
        "lago/clima": f"read_parquet('{b}/bronze/weather/**/*.parquet')",
        "lago/averias": f"read_parquet('{b}/bronze/failures/failures.parquet')",
        "lago/plata": f"read_parquet('{b}/silver/telemetry/**/*.parquet')",
        "lago/historia, Delta, versión 0": f"delta_scan('{f}/delta', version = 0)",
        "lago/historia, Delta, versión 1": f"delta_scan('{f}/delta')",
        "lago/historia, Iceberg, versión 0": f"iceberg_scan('{f}/iceberg_primera.metadata.json')",
        "lago/historia, Iceberg, versión 1": f"iceberg_scan('{f}/iceberg_ultima.metadata.json')",
        "lecciones/todo_en_un_parquet": f"read_parquet('{b}/_formatos/todo.parquet')",
    }


def huellas() -> tuple[dict[str, list], dict]:
    """Recuento y suma de un hash de cada fila, tabla a tabla. Y la forma del servidor."""
    salida = {}
    con = conecta_con_extensiones()
    for nombre, fuente in _fuentes().items():
        n, suma = con.sql(f"SELECT count(*), sum(hash(t)::HUGEINT) FROM {fuente} t").fetchone()
        salida[nombre] = [n, str(suma)]

    # Del oro solo las tablas: las vistas de preparación apuntan al lago con
    # rutas relativas a la carpeta de dbt, y desde aquí no se pueden leer.
    con.execute(f"ATTACH '{(LAGO / 'gold' / 'fuelle.duckdb').as_posix()}' AS oro (READ_ONLY)")
    tablas = con.sql("""
        SELECT table_schema, table_name FROM information_schema.tables
        WHERE table_catalog = 'oro' AND table_type = 'BASE TABLE' ORDER BY table_name
    """).fetchall()
    for esquema, tabla in tablas:
        n, suma = con.sql(f'SELECT count(*), sum(hash(t)::HUGEINT) '
                          f'FROM oro."{esquema}"."{tabla}" t').fetchone()
        salida[f"lago/{tabla}"] = [n, str(suma)]
    con.execute("DETACH oro")
    con.close()

    with servidor():
        pg = conecta()
        for tabla in ("lecturas", "dias"):
            n, suma = pg.execute(f"SELECT count(*), sum(hashtext(t::text)::bigint) "
                                 f"FROM {tabla} t").fetchone()
            salida[f"servidor/{tabla}"] = [n, str(suma)]
        forma = {
            "guardas": backup.guardas_de(pg),
            "indices": sorted(r[0] for r in pg.execute(
                "SELECT indexname FROM pg_indexes WHERE schemaname = 'public'").fetchall()),
            "roles": sorted(r[0] for r in pg.execute(
                "SELECT rolname FROM pg_roles WHERE rolname !~ '^pg_'").fetchall()),
        }
        pg.close()
    return salida, forma


def inventario(raiz: Path) -> set[str]:
    """Lo que hay en un lago a dos niveles, sin mirar dentro de PostgreSQL."""
    return {p.relative_to(raiz).as_posix() for p in raiz.glob("*/*")
            if not p.relative_to(raiz).as_posix().startswith("pg/")}


def _sha(fichero: Path) -> str:
    return hashlib.sha256(fichero.read_bytes()).hexdigest()


# Los Parquet que escribe DuckDB y tienen que salir iguales byte a byte. Delta e
# Iceberg no entran: escriben uuids y fechas en su propio registro a propósito.
CAPAS_EN_PARQUET = ("bronze/telemetry", "bronze/weather", "bronze/failures",
                    "silver/telemetry", "_formatos")


def bytes_del_lago() -> dict[str, str]:
    return {f.relative_to(LAGO).as_posix(): _sha(f)
            for capa in CAPAS_EN_PARQUET for f in (LAGO / capa).rglob("*.parquet")}


def ficheros_versionados_cambiados() -> list[str]:
    r = subprocess.run(["git", "status", "--porcelain", "--", "results", "assets"],
                       cwd=PROJECT, capture_output=True, text=True, encoding="utf-8")
    return [linea[3:] for linea in r.stdout.splitlines() if linea.strip()]


# --- Materializar -------------------------------------------------------------

def materializa(seleccion, **kw) -> tuple[float, dg.ExecuteInProcessResult]:
    t0 = time.perf_counter()
    r = dg.materialize(TODO, selection=seleccion, instance=dg.DagsterInstance.get(),
                       resources=d.defs.resources, raise_on_error=False, **kw)
    return time.perf_counter() - t0, r


def comprobaciones(r: dg.ExecuteInProcessResult) -> list[tuple[str, bool]]:
    return [(e.asset_check_key.name, e.passed) for e in r.get_asset_check_evaluations()]


def como_volver() -> str:
    return (f"El lago de antes sigue entero en {ANTES.name}/. Para volver a él:\n"
            f"  borra {LAGO.name}/ y renombra {ANTES.name}/ a {LAGO.name}/")


def main() -> None:
    if ANTES.exists():
        raise SystemExit(f"Ya existe {ANTES.name}/, de una corrida anterior que no terminó. "
                         f"Decide qué lago vale antes de seguir.\n{como_volver()}")
    if cambiados := ficheros_versionados_cambiados():
        raise SystemExit("Hay ficheros de results/ o assets/ sin guardar en git, y la "
                         "comparación por bytes no significaría nada:\n  "
                         + "\n  ".join(cambiados))

    grafo = d.defs.resolve_asset_graph()
    claves = list(grafo.get_all_asset_keys())
    materializables = [k for k in claves if grafo.get(k).is_materializable]
    dependencias = sum(len(grafo.get(k).parent_keys) for k in claves)
    print(f"  el grafo: {len(claves)} activos, {len(materializables)} que se pueden construir, "
          f"{dependencias} dependencias y {len(grafo.asset_check_keys)} comprobaciones")

    print("  1. las huellas del lago de ahora, tabla a tabla")
    antes, forma_antes = huellas()
    inventario_antes = inventario(LAGO)
    bytes_antes = bytes_del_lago()
    print(f"     {len(antes)} tablas y versiones, {len(bytes_antes)} ficheros Parquet")

    if esta_vivo():
        print("     el servidor estaba en marcha: se para, o su carpeta no se puede mover")
        para()
    print(f"  2. el lago entero pasa a {ANTES.name}/: desde aquí, no hay lago")
    LAGO.rename(ANTES)

    print("  3. Dagster lo construye todo")
    tramo = {"dagster/asset_partition_range_start": d.DIAS.get_first_partition_key(),
             "dagster/asset_partition_range_end": d.DIAS.get_last_partition_key()}
    pasos = [
        ("lago", "el bronce, los 214 días en una corrida",
         dg.AssetSelection.assets(d.bronce), {"tags": tramo}),
        ("lago", "el resto del lago, con el oro de dbt",
         dg.AssetSelection.groups("lago") - dg.AssetSelection.assets(d.bronce), {}),
        ("lecciones", "lo que consultan las lecciones", dg.AssetSelection.groups("lecciones"), {}),
        ("gemelo", "el gemelo, de la física al veredicto", dg.AssetSelection.groups("gemelo"), {}),
        ("servidor", "PostgreSQL, desde initdb", dg.AssetSelection.groups("servidor"), {}),
    ]
    segundos = {grupo: 0.0 for grupo, *_ in pasos}
    evaluadas = []
    for grupo, que, seleccion, extra in pasos:
        tardo, r = materializa(seleccion, **extra)
        segundos[grupo] += tardo
        evaluadas += comprobaciones(r)
        print(f"     {'bien ' if r.success else 'FALLA'} {que:<42} {tardo:6.1f} s")
        if not r.success:
            raise SystemExit(f"Un paso de Dagster ha fallado: {que}. Mira el registro de la "
                             f"corrida {r.run_id}.\n{como_volver()}")

    print("  4. las huellas del lago nuevo, y la comparación")
    despues, forma_despues = huellas()
    iguales = [t for t in antes if despues.get(t) == antes[t]]
    for tabla in antes:
        marca = "igual   " if tabla in iguales else "DISTINTA"
        print(f"     {marca} {tabla:<36} {antes[tabla][0]:>9,} filas")
    forma_igual = forma_antes == forma_despues
    print(f"     {'igual   ' if forma_igual else 'DISTINTA'} el servidor: "
          f"{forma_despues['guardas']} guardas, {len(forma_despues['indices'])} índices, "
          f"roles {', '.join(forma_despues['roles'])}")

    bytes_despues = bytes_del_lago()
    parquet_iguales = sum(1 for f, h in bytes_antes.items() if bytes_despues.get(f) == h)
    parquet_iguales_todos = parquet_iguales == len(bytes_antes) == len(bytes_despues)
    print(f"     {'iguales ' if parquet_iguales_todos else 'DISTINTOS'} {parquet_iguales} de "
          f"{len(bytes_antes)} ficheros Parquet byte a byte ({len(bytes_despues)} ahora)")

    faltan = sorted(inventario_antes - inventario(LAGO))
    sin_explicar = [f for f in faltan if f not in RESTOS]
    for f in faltan:
        print(f"     no vuelve   {f}: {RESTOS.get(f, 'SIN EXPLICAR')}")

    cambiados = ficheros_versionados_cambiados()
    print(f"     {len(cambiados)} ficheros versionados distintos en results/ y assets/")
    for f in cambiados:
        print(f"       {f}")

    en_verde = sum(1 for _, bien in evaluadas if bien)
    print(f"     {en_verde} de {len(evaluadas)} comprobaciones de Dagster en verde")

    print("  5. las diez puertas, contra el lago nuevo")
    puertas = subprocess.run([str(PYTHON), str(PROJECT / "src" / "site" / "check_all.py")],
                             cwd=PROJECT, capture_output=True, text=True, encoding="utf-8")
    verdes = sum(1 for linea in puertas.stdout.splitlines()
                 if linea.strip().startswith("check_") and linea.strip().endswith("verde"))
    print(f"     {verdes} en verde, salida {puertas.returncode}")

    print(f"  6. rellenar hacia atrás: se estropea el {DIA_A_RELLENAR} y se rehace solo ese día")
    telemetria = LAGO / "bronze" / "telemetry"
    carpeta = telemetria / f"day={DIA_A_RELLENAR}"
    ajenos = {f.relative_to(telemetria).as_posix(): (_sha(f), f.stat().st_mtime_ns)
              for f in telemetria.rglob("*.parquet") if f.parent != carpeta}
    del_dia = {f.name: _sha(f) for f in carpeta.glob("*.parquet")}
    shutil.rmtree(carpeta)
    tardo_el_dia, r = materializa(dg.AssetSelection.assets(d.bronce), partition_key=DIA_A_RELLENAR)
    vuelve = {f.name: _sha(f) for f in carpeta.glob("*.parquet")}
    intactos = sum(1 for rel, (sha, mtime) in ajenos.items()
                   if (telemetria / rel).exists()
                   and _sha(telemetria / rel) == sha
                   and (telemetria / rel).stat().st_mtime_ns == mtime)
    dia_igual = r.success and vuelve == del_dia
    print(f"     {'igual   ' if dia_igual else 'DISTINTO'} el día rehecho, byte a byte")
    print(f"     {intactos} de {len(ajenos)} ficheros de los otros días, sin tocar")
    print(f"     {tardo_el_dia:.1f} s para un día")

    todo_bien = (len(iguales) == len(antes) and forma_igual and not sin_explicar
                 and parquet_iguales_todos
                 and not cambiados and en_verde == len(evaluadas)
                 and puertas.returncode == 0 and dia_igual and intactos == len(ajenos))

    payload = {
        "activos": len(claves),
        "activos_que_se_construyen": len(materializables),
        "activos_externos": len(claves) - len(materializables),
        "dependencias": dependencias,
        "comprobaciones": len(evaluadas),
        "comprobaciones_en_verde": en_verde,
        "comprobaciones_de_dbt": sum(1 for n, _ in evaluadas
                                     if n not in ("el_contrato_se_cumple", "la_copia_restaura")),
        "dias_de_calendario": len(d.DIAS.get_partition_keys()),
        "tablas_comparadas": len(antes),
        "tablas_iguales": len(iguales),
        "parquet_comparados": len(bytes_antes),
        "parquet_iguales_byte_a_byte": parquet_iguales,
        "el_servidor_igual": forma_igual,
        "guardas_del_servidor": forma_despues["guardas"],
        "indices_del_servidor": len(forma_despues["indices"]),
        "lo_que_no_vuelve": {f: RESTOS.get(f, "sin explicar") for f in faltan},
        "ficheros_versionados_distintos": len(cambiados),
        "puertas_en_verde": verdes,
        "minutos": {g: round(s / 60, 1) for g, s in segundos.items()},
        "minutos_en_total": round(sum(segundos.values()) / 60, 1),
        "relleno": {
            "dia": DIA_A_RELLENAR,
            "igual_byte_a_byte": dia_igual,
            "ficheros_de_otros_dias": len(ajenos),
            "sin_tocar": intactos,
            "segundos": round(tardo_el_dia, 1),
        },
        "huellas": despues,
        "todo_bien": todo_bien,
    }
    RESULTS.parent.mkdir(exist_ok=True)
    with io.open(RESULTS, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)
    print(f"  escrito en {RESULTS.relative_to(PROJECT)}")

    if not todo_bien:
        raise SystemExit(f"La reconstrucción no ha salido igual. No se borra nada.\n{como_volver()}")
    shutil.rmtree(ANTES)
    print(f"  todo igual: {ANTES.name}/ borrado")
    print(f"  {payload['minutos_en_total']} minutos en total")


if __name__ == "__main__":
    main()
