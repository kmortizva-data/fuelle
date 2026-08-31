"""Crossing telemetry with the failure reports. Module 12.

A JOIN is where two tables meet, and it is also where row counts quietly go
wrong. This module measures both.

The good news for teaching is that the failure reports carry the errata module 1
documented, and one of them is exactly the trap this module is about: **`nr` is
not a unique key**. Two of the four rows are numbered `#1`. Anything that treats
that column as an identifier multiplies rows, and nothing errors.

So the module does not need an invented example of a bad JOIN. It has a real
one, sitting in the only ground truth this project has.

Three things get measured:

  1. **The dates are text.** `4/18/2020 0:00` is a string, so the join needs a
     conversion first. Module 9's lesson, cashed in.
  2. **The right join keeps the row count.** A LEFT JOIN over date ranges leaves
     1,516,948 readings as 1,516,948, and marks the ones inside a failure.
  3. **The wrong join multiplies.** Joining on `nr` turns 4 rows into 6.

Run:  .venv\\Scripts\\python.exe src\\transform\\queries_m12.py
"""

from __future__ import annotations

import io
import json
import sys
from pathlib import Path

import duckdb

sys.stdout.reconfigure(encoding="utf-8")

PROJECT = Path(__file__).resolve().parents[2]
SAMPLES = PROJECT / "assets" / "muestras"
RESULTS = PROJECT / "results" / "m12_join.json"

# El formato en que vienen escritas las fechas del parte, tal cual.
FORMATO = "%-m/%-d/%Y %-H:%M"

# Los partes con sus fechas ya convertidas a fecha de verdad. Se usa en varias
# consultas, así que se escribe una vez.
AVERIAS = f"""
    SELECT nr,
           CAST(strptime(start_time, '{FORMATO}') AS DATE) AS desde,
           CAST(strptime(end_time,   '{FORMATO}') AS DATE) AS hasta,
           failure, severity, report
    FROM averias
"""


def main() -> None:
    con = duckdb.connect()
    con.execute(f"CREATE VIEW telemetria AS "
                f"SELECT * FROM read_parquet('{(SAMPLES / 'sql.parquet').as_posix()}')")
    con.execute(f"CREATE VIEW averias AS "
                f"SELECT * FROM read_parquet('{(SAMPLES / 'averias.parquet').as_posix()}')")

    lecturas = con.sql("SELECT count(*) FROM telemetria").fetchone()[0]
    partes = con.sql("SELECT count(*) FROM averias").fetchone()[0]

    # --- 1. Las fechas vienen como texto ----------------------------------
    tipo_fecha = con.sql("SELECT typeof(start_time) FROM averias LIMIT 1").fetchone()[0]
    convertidas = con.sql(f"SELECT desde, hasta, nr FROM ({AVERIAS}) ORDER BY desde").fetchall()

    # --- 2. El cruce que respeta el recuento ------------------------------
    marcadas = con.sql(f"""
        SELECT count(*) AS filas,
               count(a.nr) AS dentro_de_una_averia
        FROM telemetria t
        LEFT JOIN ({AVERIAS}) a
               ON t.day BETWEEN a.desde AND a.hasta
    """).fetchone()

    por_averia = con.sql(f"""
        SELECT a.nr, a.desde, a.hasta, count(t.day) AS lecturas,
               round(sum(CASE WHEN t.DV_eletric = 1 THEN 1 ELSE 0 END)
                     * 10 / 3600.0, 1) AS horas_de_carga
        FROM ({AVERIAS}) a
        LEFT JOIN telemetria t ON t.day BETWEEN a.desde AND a.hasta
        GROUP BY a.nr, a.desde, a.hasta
        ORDER BY a.desde
    """).fetchall()

    # Los tres cruces posibles sobre los mismos datos, contados. Un diagrama de
    # conjuntos explica los tipos de JOIN; estos números los explican mejor.
    tipos = {}
    for nombre, sql in (
        ("INNER JOIN", f"""SELECT count(*) FROM telemetria t
                           JOIN ({AVERIAS}) a ON t.day BETWEEN a.desde AND a.hasta"""),
        ("LEFT JOIN", f"""SELECT count(*) FROM telemetria t
                          LEFT JOIN ({AVERIAS}) a ON t.day BETWEEN a.desde AND a.hasta"""),
        ("CROSS JOIN", "SELECT count(*) FROM telemetria t, averias a"),
    ):
        tipos[nombre] = con.sql(sql).fetchone()[0]

    # --- 3. El cruce que multiplica ---------------------------------------
    #
    #     `nr` parece un identificador y no lo es: dos partes son «#1». Cruzar
    #     por esa columna no da error, da filas de más.
    duplicadas = con.sql("""
        SELECT nr, count(*) AS veces FROM averias
        GROUP BY nr HAVING count(*) > 1
    """).fetchall()
    multiplicado = con.sql(
        "SELECT count(*) FROM averias a JOIN averias b ON a.nr = b.nr").fetchone()[0]

    # Y el mismo cruce hecho bien, con la pareja que sí identifica un parte.
    con_clave_buena = con.sql("""
        SELECT count(*) FROM averias a
        JOIN averias b ON a.nr = b.nr AND a.start_time = b.start_time
    """).fetchone()[0]

    payload = {
        "lecturas": lecturas,
        "partes": partes,
        "tipo_de_las_fechas": tipo_fecha,
        "fechas_convertidas": [[str(d), str(h), n] for d, h, n in convertidas],
        "filas_tras_el_cruce": marcadas[0],
        "el_cruce_respeta_el_recuento": marcadas[0] == lecturas,
        "lecturas_dentro_de_una_averia": marcadas[1],
        "por_ciento_dentro_de_una_averia": round(marcadas[1] * 100 / lecturas, 2),
        "por_averia": [{"nr": n, "desde": str(d), "hasta": str(h),
                        "lecturas": c, "horas_de_carga": float(hc)}
                       for n, d, h, c, hc in por_averia],
        "tipos_de_join": [{"tipo": k, "filas": v} for k, v in tipos.items()],
        "numeros_repetidos": [{"nr": n, "veces": v} for n, v in duplicadas],
        "filas_cruzando_por_nr": multiplicado,
        "filas_cruzando_por_la_clave_buena": con_clave_buena,
        "veces_que_multiplica": round(multiplicado / partes, 2),
    }
    RESULTS.parent.mkdir(exist_ok=True)
    with io.open(RESULTS, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)

    print(f"  {lecturas:,} lecturas y {partes} partes de avería")
    print(f"  las fechas del parte son de tipo {tipo_fecha}, así que hay que convertirlas")
    print()
    print(f"  tras el LEFT JOIN quedan {marcadas[0]:,} filas: "
          f"{'el recuento aguanta' if marcadas[0] == lecturas else 'SE MOVIO'}")
    print(f"  de ellas, {marcadas[1]:,} caen dentro de una avería "
          f"({payload['por_ciento_dentro_de_una_averia']} %)")
    print()
    print("  parte   desde        hasta        lecturas   horas de carga")
    for x in payload["por_averia"]:
        print(f"  {x['nr']:<7} {x['desde']}   {x['hasta']}   "
              f"{x['lecturas']:>8,}   {x['horas_de_carga']:>8}")
    print()
    print("  el mismo cruce, de tres formas:")
    for k, v in tipos.items():
        print(f"    {k:<12} {v:>14,} filas")
    print()
    for x in payload["numeros_repetidos"]:
        print(f"  el número de parte «{x['nr']}» aparece {x['veces']} veces: no es una clave")
    print(f"  cruzar los {partes} partes consigo mismos por nr da {multiplicado} filas")
    print(f"  cruzándolos por nr Y fecha de inicio da {con_clave_buena}, que es lo correcto")
    print(f"  escrito en {RESULTS.relative_to(PROJECT)}")

    if marcadas[0] != lecturas:
        raise SystemExit("El LEFT JOIN cambió el número de filas. Ese es el error que enseña.")
    if multiplicado <= partes:
        raise SystemExit("El cruce por nr no multiplica. El módulo se queda sin ejemplo real.")


if __name__ == "__main__":
    main()
