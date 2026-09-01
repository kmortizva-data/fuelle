"""Builds the gold layer with dbt, and reads the lineage out of dbt's manifest.

Module 17. Three things happen here, and the order matters:

  1. `dbt build` runs the whole project: three preparation views over the lake's
     three sources, three gold tables on top, and eleven data tests. If any test
     fails, dbt stops and the tables are not published.
  2. The dependency graph is read from `target/manifest.json`, which dbt writes
     by itself. Nobody lists the edges: they come from the `ref()` and `source()`
     calls inside the SQL. That file is what draws the module's figure.
  3. A test that SHOULD fail is added on purpose and run, then removed.

Step 3 is the same rule as module 16, and as every verifier in this course: a
check nobody has seen fail proves nothing. The deliberate failure is the `unique`
test on the failure report number, which module 12 already measured as a lie:
two of the four reports are called `#1`.

Run:  .venv\\Scripts\\python.exe src\\transform\\dbt_gold.py
"""

from __future__ import annotations

import io
import json
import subprocess
import sys
from pathlib import Path

import duckdb

sys.stdout.reconfigure(encoding="utf-8")

PROJECT = Path(__file__).resolve().parents[2]
DBT = PROJECT / "dbt"
DBT_EXE = PROJECT / ".venv" / "Scripts" / "dbt.exe"
MANIFEST = DBT / "target" / "manifest.json"
RUN_RESULTS = DBT / "target" / "run_results.json"
RESULTS = PROJECT / "results" / "m17_dbt.json"
BASE = PROJECT / "lake" / "gold" / "fuelle.duckdb"

# La prueba que tiene que fallar. `nr` no es clave y el modulo 12 lo midio.
#
# Se anade dentro del propio fichero de pruebas y no en uno aparte: dbt no deja
# describir un mismo modelo en dos sitios, asi que un fichero suelto ni llega a
# compilar. El original se restaura pase lo que pase.
ESQUEMA_DEL_ORO = DBT / "models" / "oro" / "_oro.yml"
SIN_LA_PRUEBA = """      - name: nr
        description: The report number, as it came. It repeats.
        data_tests: [not_null]"""
CON_LA_PRUEBA = """      - name: nr
        description: The report number, as it came. It repeats.
        data_tests: [not_null, unique]"""


def corre(*args: str) -> tuple[int, str]:
    """Runs dbt from the project directory and returns its code and output."""
    proceso = subprocess.run(
        [str(DBT_EXE), *args, "--profiles-dir", "."],
        cwd=str(DBT), capture_output=True, text=True, encoding="utf-8",
        errors="replace",
    )
    return proceso.returncode, proceso.stdout + proceso.stderr


def sin_color(texto: str) -> str:
    """dbt colours its output with escape codes that do not belong in a file."""
    fuera, dentro = [], False
    for ch in texto:
        if ch == "\x1b":
            dentro = True
        elif dentro:
            if ch.isalpha():
                dentro = False
        else:
            fuera.append(ch)
    return "".join(fuera)


def linaje() -> dict:
    """Reads the graph out of dbt's manifest. No edge is written by hand."""
    m = json.loads(io.open(MANIFEST, encoding="utf-8").read())

    nodos, aristas = {}, []
    for uid, fuente in m["sources"].items():
        nodos[uid] = {"nombre": fuente["name"], "capa": "fuente"}
    for uid, modelo in m["nodes"].items():
        if modelo["resource_type"] != "model":
            continue
        # La carpeta manda: models/preparacion o models/oro.
        capa = modelo["fqn"][1]
        nodos[uid] = {"nombre": modelo["name"], "capa": capa}

    for uid, modelo in m["nodes"].items():
        if modelo["resource_type"] != "model":
            continue
        for padre in modelo["depends_on"]["nodes"]:
            if padre in nodos:
                aristas.append([padre, uid])

    pruebas = [n for n, d in m["nodes"].items() if d["resource_type"] == "test"]
    return {"nodos": nodos, "aristas": aristas, "pruebas": len(pruebas)}


def main() -> None:
    if not (PROJECT / "lake" / "silver" / "telemetry").exists():
        raise SystemExit("Falta la plata. Corre src/transform/silver.py primero.")

    # 1. La construccion entera.
    print("  dbt build")
    codigo, salida = corre("build")
    salida = sin_color(salida)
    if codigo != 0:
        print(salida)
        raise SystemExit("dbt build fallo. La capa de oro no se publica.")

    resumen = [l for l in salida.splitlines() if "Done. PASS=" in l]
    print(f"    {resumen[-1].split(chr(32) * 2)[-1] if resumen else chr(63)}")

    corridas = json.loads(io.open(RUN_RESULTS, encoding="utf-8").read())
    g = linaje()

    modelos = [n for n in g["nodos"].values() if n["capa"] != "fuente"]
    fuentes = [n for n in g["nodos"].values() if n["capa"] == "fuente"]
    print(f"    {len(fuentes)} fuentes, {len(modelos)} modelos, "
          f"{g['pruebas']} pruebas, {len(g['aristas'])} dependencias")

    # 2. La prueba que tiene que fallar.
    #
    #    Sin esto, once pruebas en verde no dicen nada: podrian estar todas
    #    comprobando cosas incapaces de fallar. Es la regla del modulo 16.
    print()
    print("  y ahora, una prueba que tiene que fallar:")
    original = ESQUEMA_DEL_ORO.read_text(encoding="utf-8")
    if SIN_LA_PRUEBA not in original:
        raise SystemExit("El fichero _oro.yml ha cambiado de forma y este "
                         "experimento ya no sabe donde meter la prueba rota.")
    try:
        ESQUEMA_DEL_ORO.write_text(
            original.replace(SIN_LA_PRUEBA, CON_LA_PRUEBA), encoding="utf-8")
        codigo_roto, salida_rota = corre("test", "--select", "oro_averias")
        salida_rota = sin_color(salida_rota)
    finally:
        ESQUEMA_DEL_ORO.write_text(original, encoding="utf-8")

    fallo = [l.strip() for l in salida_rota.splitlines()
             if "unique_oro_averias_nr" in l and ("FAIL" in l or "ERROR" in l)]
    la_caza = codigo_roto != 0 and bool(fallo)
    print(f"    {'la caza' if la_caza else 'SE ESCAPA'}  "
          f"«nr es unico», que el modulo 12 ya sabia que era mentira")
    for l in fallo:
        print(f"      {l}")

    # Cuantas filas la incumplen, para poder citarlo en la leccion.
    culpables = 0
    for l in salida_rota.splitlines():
        if "Got" in l and "result" in l:
            trozos = l.split("Got")[1].split()
            if trozos and trozos[0].isdigit():
                culpables = int(trozos[0])

    # Lo que ha quedado escrito, para poder citarlo sin mirar por encima.
    con = duckdb.connect(str(BASE), read_only=True)
    tablas = {}
    for n in sorted(x["nombre"] for x in modelos if x["capa"] == "oro"):
        filas = con.sql(f"SELECT count(*) FROM {n}").fetchone()[0]
        columnas = len(con.sql(f"SELECT * FROM {n} LIMIT 0").columns)
        tablas[n] = {"filas": filas, "columnas": columnas}
        print(f"    {n:<20} {filas:>7,} filas  {columnas} columnas")
    con.close()

    payload = {
        "nodos_del_grafo": len(g["nodos"]),
        "tablas_de_oro": tablas,
        "kb_de_la_base": round(BASE.stat().st_size / 1024, 1),
        "fuentes": len(fuentes),
        "modelos": len(modelos),
        "modelos_de_preparacion": sum(1 for n in modelos if n["capa"] == "preparacion"),
        "modelos_de_oro": sum(1 for n in modelos if n["capa"] == "oro"),
        "pruebas": g["pruebas"],
        "dependencias": len(g["aristas"]),
        "pasos_de_la_construccion": len(corridas["results"]),
        "todo_en_verde": all(r["status"] in ("success", "pass")
                             for r in corridas["results"]),
        "la_prueba_rota_se_caza": la_caza,
        "filas_que_incumplen_la_prueba_rota": culpables,
        "grafo": g,
    }
    RESULTS.parent.mkdir(exist_ok=True)
    with io.open(RESULTS, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)

    print()
    print(f"  el grafo tiene {len(g['nodos'])} nodos y {len(g['aristas'])} "
          f"dependencias, ninguna escrita a mano")
    print(f"  escrito en {RESULTS.relative_to(PROJECT)}")

    if not la_caza:
        raise SystemExit("La prueba que tenia que fallar ha pasado. "
                         "Once pruebas en verde no valen nada si ninguna puede fallar.")


if __name__ == "__main__":
    main()
