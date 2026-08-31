"""Rows against columns, with the stopwatch on this machine. Module 7.

CSV stores one row after another, so a question about one column still has to
walk past all the others. Parquet stores each column apart, so it can read one
and ignore the rest. That is the whole idea, and it is repeated everywhere
without a number.

Three experiments:

  1. **The same three questions in both formats.** Counting rows, averaging one
     column, averaging seven. On CSV the three cost about the same, because the
     file gets parsed whole either way. On Parquet they should not.
  2. **What each column weighs inside the file.** Parquet writes its own
     inventory and DuckDB exposes it through `parquet_metadata()`, so the weight
     per column is read from the file rather than guessed. Next to it, how many
     distinct values that column holds, which is the explanation.
  3. **The same rows with fewer columns.** Cutting columns from the file, to see
     that the weight of a Parquet has very little to do with how many rows it
     has.

Every timing is the median of seven runs with its range, and two layouts whose
ranges overlap are reported as indistinguishable rather than ranked
(src/medir.py).

Run:  .venv\\Scripts\\python.exe src\\transform\\benchmark_formats.py
"""

from __future__ import annotations

import io
import json
import shutil
import sys
from pathlib import Path

import duckdb

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from medir import RUNS, distinguishable, measure  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")

PROJECT = Path(__file__).resolve().parents[2]
RAW_CSV = PROJECT / "data" / "MetroPT3(AirCompressor).csv"
BRONZE = PROJECT / "lake" / "bronze" / "telemetry"
SCRATCH = PROJECT / "lake" / "_formatos"
RESULTS = PROJECT / "results" / "m07_formats.json"

# The seven analogue signals, which is what "read many columns" means here.
ANALOGUE = ["TP2", "TP3", "H1", "DV_pressure", "Reservoirs",
            "Oil_temperature", "Motor_current"]


def mb(path: Path) -> float:
    return path.stat().st_size / 1024 / 1024


def questions(source: str) -> dict[str, str]:
    """The same three questions, phrased against whichever source."""
    many = ", ".join(f"avg({c})" for c in ANALOGUE)
    return {
        "contar_filas": f"SELECT count(*) FROM {source}",
        "una_columna": f"SELECT avg(TP2) FROM {source}",
        "siete_columnas": f"SELECT {many} FROM {source}",
    }


def column_weights(con: duckdb.DuckDBPyConnection, parquet: Path) -> list[dict]:
    """What each column weighs, read from the file's own inventory.

    Parquet stores the compressed size of every column of every row group. This
    is not an estimate: it is the file describing itself.
    """
    rows = con.sql(f"""
        SELECT path_in_schema AS columna,
               sum(total_compressed_size)   AS comprimido,
               sum(total_uncompressed_size) AS sin_comprimir
        FROM parquet_metadata('{parquet.as_posix()}')
        GROUP BY columna
        ORDER BY comprimido DESC
    """).fetchall()

    total = sum(r[1] for r in rows)
    out = []
    for name, packed, raw in rows:
        distinct = con.sql(
            f'SELECT count(DISTINCT "{name}") FROM read_parquet(\'{parquet.as_posix()}\')'
        ).fetchone()[0]
        out.append({
            "columna": name,
            "kb": round(packed / 1024, 1),
            "por_ciento_del_fichero": round(packed / total * 100, 1),
            "valores_distintos": distinct,
            "veces_comprimida": round(raw / packed, 1) if packed else None,
        })
    return out


def main() -> None:
    if not RAW_CSV.exists() or not BRONZE.exists():
        raise SystemExit("Data missing. Run src/ingest/bronze.py first.")

    shutil.rmtree(SCRATCH, ignore_errors=True)
    SCRATCH.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect()

    # One Parquet file holding exactly what the CSV holds, so the comparison is
    # about the format and nothing else.
    full = SCRATCH / "todo.parquet"
    con.execute(
        f"COPY (SELECT * EXCLUDE (day) FROM read_parquet('{BRONZE.as_posix()}/**/*.parquet')) "
        f"TO '{full.as_posix()}' (FORMAT PARQUET, COMPRESSION ZSTD)")

    csv_source = f"read_csv_auto('{RAW_CSV.as_posix()}')"
    parquet_source = f"read_parquet('{full.as_posix()}')"

    # --- 1. The same three questions in both formats ----------------------
    print(f"Three questions, two formats, median of {RUNS} runs each.")
    print(f"  {'question':<18}{'CSV':>10}{'Parquet':>10}{'factor':>10}")
    timings, taken = [], {}
    for label, csv_sql in questions(csv_source).items():
        parquet_sql = questions(parquet_source)[label]
        on_csv = measure(lambda q=csv_sql: con.sql(q).fetchone())
        on_parquet = measure(lambda q=parquet_sql: con.sql(q).fetchone())
        taken[label] = (on_csv, on_parquet)
        real = distinguishable(on_csv, on_parquet)
        timings.append({
            "pregunta": label,
            "csv_s": round(on_csv.median, 3),
            "csv_min_s": round(on_csv.minimum, 3),
            "csv_max_s": round(on_csv.maximum, 3),
            "parquet_s": round(on_parquet.median, 4),
            "parquet_min_s": round(on_parquet.minimum, 4),
            "parquet_max_s": round(on_parquet.maximum, 4),
            "veces": round(on_csv.median / on_parquet.median, 1) if real else None,
            "diferencia_real": real,
        })
        factor = f"{timings[-1]['veces']}x" if real else "se solapan"
        print(f"  {label:<18}{on_csv.median:>9.3f}s{on_parquet.median:>9.4f}s{factor:>10}")

    # Parquet against itself: one column or seven, out of the same file.
    one, seven = taken["una_columna"][1], taken["siete_columnas"][1]
    columns_matter = distinguishable(one, seven)
    print()
    print(f"  Parquet, one column {one} against seven {seven}")
    print(f"  reading fewer columns is measurably cheaper: {columns_matter}")

    # --- 2. What each column weighs ---------------------------------------
    weights = column_weights(con, full)
    print()
    print(f"  {'column':<18}{'KB':>10}{'% file':>9}{'distinct':>11}")
    for w in weights:
        print(f"  {w['columna']:<18}{w['kb']:>10.1f}{w['por_ciento_del_fichero']:>9.1f}"
              f"{w['valores_distintos']:>11,}")

    # --- 3. The same rows, fewer columns ----------------------------------
    ladders = [
        ("las 17", "*"),
        ("5", "timestamp, TP2, TP3, Motor_current, COMP"),
        ("4", "TP2, TP3, Motor_current, COMP"),
        ("2", "CAST(timestamp AS DATE) AS day, COMP"),
    ]
    ladder_rows = []
    for label, projection in ladders:
        target = SCRATCH / f"cols_{len(ladder_rows)}.parquet"
        con.execute(f"COPY (SELECT {projection} FROM {parquet_source}) "
                    f"TO '{target.as_posix()}' (FORMAT PARQUET, COMPRESSION ZSTD)")
        n = len(con.sql(f"SELECT * FROM read_parquet('{target.as_posix()}') LIMIT 0").columns)
        ladder_rows.append({"columnas": label, "cuantas": n, "mb": round(mb(target), 2)})
        print(f"  {label:>6} columns -> {ladder_rows[-1]['mb']:>6.2f} MB")

    rows = con.sql(f"SELECT count(*) FROM {parquet_source}").fetchone()[0]
    heaviest, lightest = ladder_rows[0], ladder_rows[-1]

    payload = {
        "filas": rows,
        "corridas": RUNS,
        "csv_mb": round(mb(RAW_CSV), 2),
        "parquet_mb": round(mb(full), 2),
        "veces_mas_pequeno": round(mb(RAW_CSV) / mb(full), 1),
        "preguntas": timings,
        "columnas_importan": columns_matter,
        "pesos_por_columna": weights,
        "columna_mas_pesada": weights[0]["columna"],
        "por_ciento_de_la_mas_pesada": weights[0]["por_ciento_del_fichero"],
        "escalera_de_columnas": ladder_rows,
        "veces_entre_17_y_2_columnas": round(heaviest["mb"] / lightest["mb"]),
    }
    RESULTS.parent.mkdir(exist_ok=True)
    with io.open(RESULTS, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)

    print()
    print(f"  CSV {payload['csv_mb']} MB against Parquet {payload['parquet_mb']} MB "
          f"({payload['veces_mas_pequeno']}x smaller)")
    print(f"  same {rows:,} rows, 17 columns {heaviest['mb']} MB against 2 columns "
          f"{lightest['mb']} MB: {payload['veces_entre_17_y_2_columnas']}x")
    print(f"Written to {RESULTS.relative_to(PROJECT)}")

    shutil.rmtree(SCRATCH, ignore_errors=True)

    if not columns_matter:
        raise SystemExit("Reading one column costs the same as seven. "
                         "That contradicts the module. Check the benchmark.")


if __name__ == "__main__":
    main()
