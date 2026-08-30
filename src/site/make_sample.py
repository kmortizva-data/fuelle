"""The Parquet the browser downloads for the live queries, sized by measurement.

The live query block runs DuckDB inside the reader's browser, so it needs data
there. The lake is 1.5 million rows, which is fine on disk and not fine over a
phone connection, so the sample is a decision with a number behind it.

Three candidates are written and measured, and the one that gets picked is the
smallest that still lets the reader reproduce the lesson's own figure. A sample
that cannot reproduce the published number would make the challenge a lie.

Run:  .venv\\Scripts\\python.exe src\\site\\make_sample.py
"""

from __future__ import annotations

import gzip
import io
import json
import sys
from pathlib import Path

import duckdb

sys.stdout.reconfigure(encoding="utf-8")

PROJECT = Path(__file__).resolve().parents[2]
BRONZE = PROJECT / "lake" / "bronze" / "telemetry"
SAMPLES = PROJECT / "assets" / "muestras"
RESULTS = PROJECT / "results" / "sample.json"

# What module 10 actually asks of the data. Anything beyond this is weight the
# reader pays for and never uses.
NEEDED = ["timestamp", "day", "DV_eletric", "COMP", "Motor_current"]


def gzipped_size(path: Path) -> int:
    """What the reader really downloads: GitHub Pages serves this compressed."""
    return len(gzip.compress(path.read_bytes(), 6))


def write(con: duckdb.DuckDBPyConnection, name: str, columns: list[str],
          where: str = "") -> dict:
    target = SAMPLES / f"{name}.parquet"
    cols = ", ".join(f'"{c}"' for c in columns) if columns else "*"
    clause = f"WHERE {where}" if where else ""
    con.execute(
        f"""
        COPY (
            SELECT {cols}
            FROM read_parquet('{BRONZE.as_posix()}/**/*.parquet')
            {clause}
            ORDER BY timestamp
        )
        TO '{target.as_posix()}' (FORMAT PARQUET, COMPRESSION ZSTD)
        """
    )
    raw = target.stat().st_size
    gz = gzipped_size(target)
    rows = con.sql(f"SELECT count(*) FROM read_parquet('{target.as_posix()}')").fetchone()[0]
    return {
        "name": name,
        "rows": rows,
        "columns": len(columns) if columns else 17,
        "mb_on_disk": round(raw / 1024 / 1024, 2),
        "mb_downloaded": round(gz / 1024 / 1024, 2),
    }


def main() -> None:
    if not BRONZE.exists():
        raise SystemExit("Bronze layer missing. Run src/ingest/bronze.py first.")

    SAMPLES.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect()

    # The weight is not in the rows, it is in the columns that never repeat.
    # `timestamp` has 1.5 million distinct values and compresses badly; `day` has
    # 212 and compresses to almost nothing. Measuring that is the point here.
    candidates = [
        ("todo_todas_columnas", [], ""),
        ("todo_columnas_del_m10", NEEDED, ""),
        ("sin_timestamp", ["day", "DV_eletric", "COMP", "Motor_current"], ""),
        ("solo_lo_del_reto", ["day", "DV_eletric"], ""),
        ("un_mes_columnas_del_m10", NEEDED, "day >= DATE '2020-06-01' AND day < DATE '2020-07-01'"),
    ]

    measured = [write(con, name, cols, where) for name, cols, where in candidates]

    print("  candidato                      filas      cols   en disco   se descarga")
    for row in measured:
        print(f"  {row['name']:<28} {row['rows']:>9,}   {row['columns']:>4}   "
              f"{row['mb_on_disk']:>7.2f} MB   {row['mb_downloaded']:>8.2f} MB")

    # The test that decides: can the sample reproduce the lesson's own number?
    #
    # Chosen after the measurement above, which was the surprise of the day: the
    # weight is not the 1.5 million rows, it is the columns whose values never
    # repeat. Dropping `timestamp` and `Motor_current` takes the same rows from
    # 6.4 MB to under 60 KB, because `day` holds 212 distinct values and
    # `DV_eletric` holds two, and Parquet stores those with a dictionary.
    chosen = "sin_timestamp_ligera"
    path = SAMPLES / f"{chosen}.parquet"
    measured.append(write(con, chosen, ["day", "DV_eletric", "COMP"]))
    avg = con.sql(
        f"""
        SELECT round(avg(loaded_hours), 2) FROM (
            SELECT day,
                   count(*) AS readings,
                   sum(CASE WHEN DV_eletric = 1 THEN 1 ELSE 0 END) * 10 / 3600.0 AS loaded_hours
            FROM read_parquet('{path.as_posix()}')
            GROUP BY day
        ) WHERE readings > 0.9 * 8640
        """
    ).fetchone()[0]

    published = json.load(io.open(PROJECT / "results" / "m10_duty_cycle.json",
                                  encoding="utf-8"))["avg_loaded_hours"]
    reproduces = abs(avg - published) < 0.005

    print()
    print(f"  Elegido: {chosen}")
    print(f"  La muestra da {avg} h de media; el lago entero da {published} h  ->  "
          f"{'reproduce la cifra' if reproduces else 'NO REPRODUCE, no sirve'}")

    # The ones not chosen are deleted: they would ship as dead weight.
    for row in measured:
        if row["name"] != chosen:
            (SAMPLES / f"{row['name']}.parquet").unlink(missing_ok=True)

    RESULTS.parent.mkdir(exist_ok=True)
    with io.open(RESULTS, "w", encoding="utf-8") as fh:
        json.dump({"candidates": measured, "chosen": chosen,
                   "sample_avg_loaded_hours": avg, "lake_avg_loaded_hours": published,
                   "reproduces": reproduces}, fh, ensure_ascii=False, indent=2)
    print(f"Written to {RESULTS.relative_to(PROJECT)}")

    if not reproduces:
        raise SystemExit("The sample cannot reproduce the published figure.")


if __name__ == "__main__":
    main()
