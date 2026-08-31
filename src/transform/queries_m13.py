"""Looking at the row next door: window functions. Module 13.

Everything so far collapsed rows into groups. A window function does the
opposite: it keeps every row and lets each one see its neighbours. Without it
there is no time series, and with it three things become measurable that were
invisible until now.

  1. **The gaps.** The distance between one reading and the next is not a column
     in the file. It only exists as the difference between two rows, so it took
     until module 13 to be able to ask for it.
  2. **The starts.** A compressor start is not a value either: it is the moment a
     row says loaded and the previous one did not.
  3. **The headline figure of this module**, 179,426 irregular gaps, which is the
     lake-wide count of readings that do not respect the ten seconds.

The lesson's live queries all run against one single day, because that is the
sample the reader downloads: carrying the exact clock for the whole lake would
cost 5.16 MB, and module 7 measured why.

Run:  .venv\\Scripts\\python.exe src\\transform\\queries_m13.py
"""

from __future__ import annotations

import io
import json
import sys
from pathlib import Path

import duckdb

sys.stdout.reconfigure(encoding="utf-8")

PROJECT = Path(__file__).resolve().parents[2]
SAMPLE = PROJECT / "assets" / "muestras" / "un_dia.parquet"
BRONZE = PROJECT / "lake" / "bronze" / "telemetry"
RESULTS = PROJECT / "results" / "m13_ventanas.json"

DIA = "2020-06-05"
NOMINAL = 10  # los segundos que la ficha promete entre lectura y lectura


def main() -> None:
    if not SAMPLE.exists():
        raise SystemExit("Falta la muestra. Corre src/site/make_sample.py primero.")

    con = duckdb.connect()
    con.execute(f"CREATE VIEW dia AS SELECT * FROM read_parquet('{SAMPLE.as_posix()}')")
    con.execute(f"CREATE VIEW lago AS "
                f"SELECT * FROM read_parquet('{BRONZE.as_posix()}/**/*.parquet')")

    # --- 1. Los huecos, en el lago entero ---------------------------------
    huecos_lago = con.sql(f"""
        SELECT hueco, count(*) AS veces
        FROM (SELECT date_diff('second', lag(timestamp) OVER (ORDER BY timestamp),
                               timestamp) AS hueco
              FROM lago)
        WHERE hueco IS NOT NULL
        GROUP BY hueco ORDER BY veces DESC
    """).fetchall()

    total_huecos = sum(v for _, v in huecos_lago)
    regulares = next(v for h, v in huecos_lago if h == NOMINAL)
    irregulares = total_huecos - regulares
    mayor = max(h for h, _ in huecos_lago)

    # Cuándo fue el mayor, que es más informativo que su tamaño.
    cuando_el_mayor = con.sql(f"""
        SELECT antes, timestamp, hueco FROM (
            SELECT lag(timestamp) OVER (ORDER BY timestamp) AS antes,
                   timestamp,
                   date_diff('second', lag(timestamp) OVER (ORDER BY timestamp),
                             timestamp) AS hueco
            FROM lago)
        WHERE hueco = {mayor}
    """).fetchone()

    # Y cuántas horas de carga tuvo el día de la muestra, para poder decir si
    # arrancar poco significa trabajar poco. No lo significa.
    carga_del_dia = con.sql(f"""
        SELECT round(sum(CASE WHEN DV_eletric = 1 THEN 1 ELSE 0 END) * 10 / 3600.0, 2)
        FROM dia WHERE day = DATE '{DIA}'
    """).fetchone()[0]

    # --- 2. Lo mismo en el día que se lleva el navegador ------------------
    huecos_dia = con.sql(f"""
        SELECT hueco, count(*) AS veces
        FROM (SELECT date_diff('second', lag(timestamp) OVER (ORDER BY timestamp),
                               timestamp) AS hueco
              FROM dia WHERE day = DATE '{DIA}')
        WHERE hueco IS NOT NULL
        GROUP BY hueco ORDER BY veces DESC
    """).fetchall()
    lecturas_dia = con.sql(
        f"SELECT count(*) FROM dia WHERE day = DATE '{DIA}'").fetchone()[0]

    # --- 3. Los arranques, que tampoco son una columna --------------------
    #
    #     Un arranque no está escrito en ningún sitio: es el momento en que una
    #     fila dice carga y la anterior decía que no. Solo se ve mirando la fila
    #     de al lado.
    arranques_dia = con.sql(f"""
        SELECT count(*) FROM (
            SELECT DV_eletric,
                   lag(DV_eletric) OVER (ORDER BY timestamp) AS antes
            FROM dia WHERE day = DATE '{DIA}')
        WHERE antes = 0 AND DV_eletric = 1
    """).fetchone()[0]

    # Y en el lago, para poder decir si ese día fue raro.
    arranques_por_dia = con.sql("""
        SELECT day, count(*) AS arranques FROM (
            SELECT day, DV_eletric,
                   lag(DV_eletric) OVER (PARTITION BY day ORDER BY timestamp) AS antes
            FROM lago)
        WHERE antes = 0 AND DV_eletric = 1
        GROUP BY day ORDER BY arranques DESC
    """).fetchall()
    mediana_arranques = sorted(a for _, a in arranques_por_dia)[len(arranques_por_dia) // 2]

    payload = {
        "dia_de_la_muestra": DIA,
        "segundos_nominales": NOMINAL,
        "lecturas_del_dia": lecturas_dia,
        "huecos_del_lago": [{"hueco": h, "veces": v} for h, v in huecos_lago[:6]],
        "huecos_totales": total_huecos,
        "huecos_regulares": regulares,
        "huecos_irregulares": irregulares,
        "por_ciento_irregulares": round(irregulares * 100 / total_huecos, 1),
        "hueco_mayor_segundos": mayor,
        "hueco_mayor_horas": round(mayor / 3600, 1),
        "hueco_mayor_desde": str(cuando_el_mayor[0]),
        "hueco_mayor_hasta": str(cuando_el_mayor[1]),
        "horas_de_carga_del_dia": float(carga_del_dia),
        "huecos_del_dia": [{"hueco": h, "veces": v} for h, v in huecos_dia],
        "arranques_del_dia": arranques_dia,
        "arranques_mediana_del_lago": mediana_arranques,
        "dias_con_arranques": len(arranques_por_dia),
        "arranques_maximo": arranques_por_dia[0][1],
        "dia_con_mas_arranques": str(arranques_por_dia[0][0]),
    }
    RESULTS.parent.mkdir(exist_ok=True)
    with io.open(RESULTS, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)

    print(f"  en el lago hay {total_huecos:,} huecos entre lecturas")
    print(f"    de {NOMINAL} s exactos: {regulares:,}")
    print(f"    irregulares:         {irregulares:,} ({payload['por_ciento_irregulares']} %)")
    print(f"    el mayor mide {mayor:,} s, o sea {payload['hueco_mayor_horas']} horas,")
    print(f"    y va del {cuando_el_mayor[0]} al {cuando_el_mayor[1]}")
    print()
    print(f"  el {DIA} tiene {lecturas_dia:,} lecturas y sus huecos son:")
    for h, v in huecos_dia:
        print(f"    {h} s  ->  {v:,} veces")
    print()
    print(f"  ese día el compresor arrancó {arranques_dia} veces")
    print(f"  y estuvo {carga_del_dia} h en carga, así que arrancó poco y trabajó mucho")
    print(f"  la mediana de los {len(arranques_por_dia)} días es {mediana_arranques}, "
          f"y el máximo {payload['arranques_maximo']} el {payload['dia_con_mas_arranques']}")
    print(f"  escrito en {RESULTS.relative_to(PROJECT)}")

    if irregulares <= 0:
        raise SystemExit("No hay huecos irregulares. La cifra del módulo no existe.")


if __name__ == "__main__":
    main()
