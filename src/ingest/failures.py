"""The four failure reports, into the lake with their errata intact. Module 15.

The third source, and the smallest: four rows written by hand from the dataset's
own documentation. It is also the only ground truth this project has, which is
why not one character of it gets corrected.

Three errata travel with it, all recorded in src/ingest/LEEME_failure_reports.md
and all left exactly as they arrived:

  - two reports numbered `#1`, and no `#2` at all. Module 12 turned that into a
    join returning 6 rows from 4.
  - `Air leak` and `Air Leak`, the same failure written two ways, which a
    GROUP BY would split into two groups.
  - the 29 May report declaring maintenance on 30 April, a month before its own
    failure.

What this script adds is types, not content: the text dates become real dates,
and the duration of each failure becomes a column. Both are derived from what is
there, which is what bronze is allowed to do.

Run:  .venv\\Scripts\\python.exe src\\ingest\\failures.py
"""

from __future__ import annotations

import io
import json
import shutil
import sys
from pathlib import Path

import duckdb

sys.stdout.reconfigure(encoding="utf-8")

PROJECT = Path(__file__).resolve().parents[2]
CSV = PROJECT / "src" / "ingest" / "failure_reports.csv"
BRONZE = PROJECT / "lake" / "bronze" / "failures"
RESULTS = PROJECT / "results" / "m15_averias.json"

FORMATO = "%-m/%-d/%Y %-H:%M"


def main() -> None:
    if not CSV.exists():
        raise SystemExit(f"Falta {CSV}")

    con = duckdb.connect()
    con.execute(f"""
        CREATE VIEW partes AS
        SELECT nr,
               strptime(start_time, '{FORMATO}') AS inicio,
               strptime(end_time,   '{FORMATO}') AS fin,
               date_diff('minute', strptime(start_time, '{FORMATO}'),
                                   strptime(end_time,   '{FORMATO}')) / 60.0 AS horas,
               failure, severity, report
        FROM read_csv_auto('{CSV.as_posix()}')
    """)

    filas = con.sql("SELECT * FROM partes ORDER BY inicio").fetchall()

    # Las erratas, contadas en vez de descritas.
    numeros_repetidos = con.sql(
        "SELECT count(*) FROM (SELECT nr FROM partes GROUP BY nr HAVING count(*) > 1)"
    ).fetchone()[0]
    formas_de_escribirlo = con.sql(
        "SELECT count(DISTINCT failure) FROM partes").fetchone()[0]
    formas_normalizando = con.sql(
        "SELECT count(DISTINCT lower(failure)) FROM partes").fetchone()[0]
    # El parte cuyo mantenimiento va fechado antes que su propia avería.
    mantenimiento_antes = con.sql("""
        SELECT count(*) FROM partes
        WHERE report LIKE '%30Apr%' AND inicio > TIMESTAMP '2020-05-01'
    """).fetchone()[0]

    if BRONZE.exists():
        shutil.rmtree(BRONZE)
    BRONZE.mkdir(parents=True, exist_ok=True)
    con.execute(f"COPY (SELECT * FROM partes) TO '{(BRONZE / 'failures.parquet').as_posix()}' "
                f"(FORMAT PARQUET, COMPRESSION ZSTD)")

    payload = {
        "partes": len(filas),
        "numeros_repetidos": numeros_repetidos,
        "formas_de_escribir_la_averia": formas_de_escribirlo,
        "formas_normalizando": formas_normalizando,
        "mantenimiento_fechado_antes": mantenimiento_antes,
        "horas_totales": round(sum(f[3] for f in filas), 1),
        "partes_detalle": [
            {"nr": f[0], "inicio": str(f[1]), "fin": str(f[2]),
             "horas": round(float(f[3]), 1), "averia": f[4]}
            for f in filas
        ],
    }
    RESULTS.parent.mkdir(exist_ok=True)
    with io.open(RESULTS, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)

    print(f"  {len(filas)} partes de avería, {payload['horas_totales']} horas en total")
    for f in payload["partes_detalle"]:
        print(f"    {f['nr']:<4} {f['inicio']}  a  {f['fin']}  {f['horas']:>6} h  {f['averia']}")
    print()
    print(f"  números de parte repetidos: {numeros_repetidos}")
    print(f"  formas de escribir la misma avería: {formas_de_escribirlo} "
          f"({formas_normalizando} normalizando mayúsculas)")
    print(f"  partes con el mantenimiento fechado antes de la avería: {mantenimiento_antes}")
    print(f"  escrito en {RESULTS.relative_to(PROJECT)}")

    # Las erratas son material del curso: si desaparecieran, alguien las habría
    # corregido y varias lecciones se quedarían sin ejemplo.
    if numeros_repetidos == 0 or formas_de_escribirlo == formas_normalizando:
        raise SystemExit("Las erratas del original han desaparecido. "
                         "El crudo se conserva literal, y los módulos 12 y 15 las usan.")


if __name__ == "__main__":
    main()
