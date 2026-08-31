"""The same question, four places to live. Module 3.

"File", "database", "lake" and "warehouse" get used as if they were synonyms and
they are not. The difference does not explain well in words, but it shows whole
when the same question gets timed in each of them.

The question is always the same and about as simple as they come: how many
readings there are for one given day. The only thing that changes is where the
data sits.

Size on disk gets measured too, because the trade is always speed against space,
and a place that answers fast while weighing three times more has not won
anything for free.

Run:  .venv\\Scripts\\python.exe src\\ingest\\donde_viven.py
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
CSV = PROJECT / "data" / "MetroPT3(AirCompressor).csv"
BRONZE = PROJECT / "lake" / "bronze" / "telemetry"
SCRATCH = PROJECT / "lake" / "_donde"
RESULTS = PROJECT / "results" / "m03_donde_viven.json"

DAY = "2020-06-05"


def size_mb(path: Path) -> float:
    if path.is_dir():
        return sum(f.stat().st_size for f in path.rglob("*") if f.is_file()) / 1024 / 1024
    return path.stat().st_size / 1024 / 1024


def time_query(con, sql: str):
    """Median of seven runs. One clock reading is not a measurement: see src/medir.py."""
    return measure(lambda: con.sql(sql).fetchone()[0])


def main() -> None:
    if not CSV.exists() or not BRONZE.exists():
        raise SystemExit("Data missing. Run src/ingest/bronze.py first.")

    SCRATCH.mkdir(parents=True, exist_ok=True)
    places, taken = [], []

    def record(name: str, fmt: str, path: Path, m) -> None:
        taken.append(m)
        places.append({"sitio": name, "formato": fmt, "mb": round(size_mb(path), 2),
                       **m.as_json(), "filas": m.result})

    # 1. A loose text file. It has to be read whole to answer.
    con = duckdb.connect()
    record("un fichero de texto", "CSV", CSV, time_query(con, (
        f"SELECT count(*) FROM read_csv_auto('{CSV.as_posix()}') "
        f"WHERE CAST(timestamp AS DATE) = DATE '{DAY}'")))
    con.close()

    # 2. The same data in columnar format, split into folders by day.
    con = duckdb.connect()
    record("un lago de ficheros", "Parquet particionado", BRONZE, time_query(con, (
        f"SELECT count(*) FROM read_parquet('{BRONZE.as_posix()}/**/*.parquet') "
        f"WHERE CAST(timestamp AS DATE) = DATE '{DAY}'")))
    con.close()

    # 3. A real database: the data inside, in its own format.
    db = SCRATCH / "compresor.duckdb"
    db.unlink(missing_ok=True)
    con = duckdb.connect(str(db))
    con.execute(f"CREATE TABLE telemetria AS "
                f"SELECT * FROM read_parquet('{BRONZE.as_posix()}/**/*.parquet')")
    con.close()
    con = duckdb.connect(str(db))
    record("una base de datos", "DuckDB", db, time_query(
        con, f"SELECT count(*) FROM telemetria WHERE CAST(timestamp AS DATE) = DATE '{DAY}'"))
    con.close()

    # 4. The same database with the day column precomputed and indexed, which is
    #    what a warehouse does: prepare the data for the questions that repeat.
    #
    #    In its OWN file, not alongside the previous table. The first version of
    #    this script put both in one, so the warehouse size included the table
    #    next door and came out twice as big. A number that misleads by accident
    #    still misleads.
    warehouse = SCRATCH / "almacen.duckdb"
    warehouse.unlink(missing_ok=True)
    con = duckdb.connect(str(warehouse))
    con.execute(f"CREATE TABLE almacen AS SELECT *, CAST(timestamp AS DATE) AS dia "
                f"FROM read_parquet('{BRONZE.as_posix()}/**/*.parquet')")
    con.execute("CREATE INDEX idx_dia ON almacen(dia)")
    con.close()
    con = duckdb.connect(str(warehouse))
    record("un almacén", "DuckDB con índice", warehouse, time_query(
        con, f"SELECT count(*) FROM almacen WHERE dia = DATE '{DAY}'"))
    con.close()

    print(f"  median of {RUNS} runs per place")
    print("  place                 format                   size  median     min     max")
    for p in places:
        print(f"  {p['sitio']:<21} {p['formato']:<22} {p['mb']:>7.2f} MB "
              f"{p['mediana_s']:>7.3f} {p['min_s']:>7.3f} {p['max_s']:>7.3f}")

    agree = len({p["filas"] for p in places}) == 1
    slowest = max(places, key=lambda p: p["mediana_s"])
    fastest = min(places, key=lambda p: p["mediana_s"])
    ratio = slowest["mediana_s"] / fastest["mediana_s"]

    # The index question, decided by the ranges and not by the medians. If the
    # two overlap there is nothing to report, and that IS the module 3 finding:
    # in a columnar engine an index over overlapping ranges buys nothing.
    plain, indexed = taken[2], taken[3]
    index_helps = distinguishable(plain, indexed)

    payload = {
        "dia": DAY, "sitios": places, "todos_coinciden": agree,
        "filas_ese_dia": places[0]["filas"], "repeticiones": RUNS,
        "veces_entre_extremos": round(ratio, 1),
        # The rounding to a whole number is stored here instead of being done
        # while writing the lesson: that way the published number comes out of a
        # run like every other one, and not out of anyone's hand.
        "veces_redondeadas": round(ratio),
        "mas_lento": slowest["sitio"], "mas_rapido": fastest["sitio"],
        # A derived number is a number too, so it gets computed here and not by
        # hand in the prose.
        "mb_de_mas_del_indice": round(places[3]["mb"] - places[2]["mb"], 1),
        "veces_indice_mas_lento": round(indexed.median / plain.median, 2),
        "el_indice_se_nota": index_helps,
    }
    RESULTS.parent.mkdir(exist_ok=True)
    with io.open(RESULTS, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)

    print()
    print(f"  all four return {places[0]['filas']:,} rows for {DAY}: {agree}")
    print(f"  slowest over fastest: {ratio:.1f}x")
    print(f"  index vs no index distinguishable: {index_helps} "
          f"(plain {plain}, indexed {indexed})")
    print(f"  written to {RESULTS.relative_to(PROJECT)}")

    shutil.rmtree(SCRATCH, ignore_errors=True)

    if not agree:
        raise SystemExit("The four places disagree. The comparison is void.")


if __name__ == "__main__":
    main()
