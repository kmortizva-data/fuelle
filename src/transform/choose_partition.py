"""How big should a partition be? Measured, not copied from a blog post.

Module 6. Partitioning splits one table into folders so a question about one day
reads one folder instead of everything. The usual advice is "partition by day"
and it is repeated everywhere without a number attached.

This script writes the same data three ways and times all three, on this machine
and this filesystem, because that is what decides it here. On Windows, creating
many small files is not free, and the answer may well differ from the advice.

It also reports read time for a one-day question, which is the whole point of
partitioning: writing slower to read faster is a trade, and a trade needs both
numbers.

Run:  .venv\\Scripts\\python.exe src\\transform\\choose_partition.py
"""

from __future__ import annotations

import io
import json
import shutil
import sys
import time
from pathlib import Path

import duckdb

sys.stdout.reconfigure(encoding="utf-8")

PROJECT = Path(__file__).resolve().parents[2]
BRONZE = PROJECT / "lake" / "bronze" / "telemetry"
SCRATCH = PROJECT / "lake" / "_bench"
RESULTS = PROJECT / "results" / "m06_partition.json"

# The question every layout has to answer, so the comparison is fair.
ONE_DAY = "2020-06-05"


def source_glob() -> str:
    return f"{BRONZE.as_posix()}/**/*.parquet"


def write_layout(con: duckdb.DuckDBPyConnection, name: str, partition_by: str | None) -> dict:
    target = SCRATCH / name
    if target.exists():
        shutil.rmtree(target)
    target.mkdir(parents=True, exist_ok=True)

    if partition_by:
        select = f"SELECT *, {partition_by} AS part FROM read_parquet('{source_glob()}')"
        options = "FORMAT PARQUET, PARTITION_BY (part), OVERWRITE_OR_IGNORE, COMPRESSION ZSTD"
        destination = target.as_posix()
    else:
        select = f"SELECT * FROM read_parquet('{source_glob()}')"
        options = "FORMAT PARQUET, COMPRESSION ZSTD"
        destination = (target / "all.parquet").as_posix()

    started = time.perf_counter()
    con.execute(f"COPY ({select}) TO '{destination}' ({options})")
    write_seconds = time.perf_counter() - started

    files = list(target.rglob("*.parquet"))
    size = sum(f.stat().st_size for f in files)

    # The read that matters: one day out of seven months.
    glob = f"{target.as_posix()}/**/*.parquet" if partition_by else destination
    started = time.perf_counter()
    rows = con.sql(
        f"SELECT count(*) FROM read_parquet('{glob}') "
        f"WHERE CAST(timestamp AS DATE) = DATE '{ONE_DAY}'"
    ).fetchone()[0]
    read_seconds = time.perf_counter() - started

    return {
        "layout": name,
        "files": len(files),
        "size_mb": round(size / 1024 / 1024, 2),
        "write_seconds": round(write_seconds, 2),
        "read_one_day_seconds": round(read_seconds, 3),
        "rows_that_day": rows,
    }


def main() -> None:
    if not BRONZE.exists():
        raise SystemExit("Bronze layer missing. Run src/ingest/bronze.py first.")

    con = duckdb.connect()
    layouts = [
        ("single_file", None),
        ("by_month", "date_trunc('month', timestamp)"),
        ("by_week", "date_trunc('week', timestamp)"),
        ("by_day", "CAST(timestamp AS DATE)"),
    ]

    measured = []
    for name, expression in layouts:
        print(f"Writing {name}...", flush=True)
        row = write_layout(con, name, expression)
        measured.append(row)
        print(
            f"  {row['files']:>4} files  {row['size_mb']:>7.2f} MB  "
            f"write {row['write_seconds']:>8.2f} s  "
            f"read one day {row['read_one_day_seconds']:.3f} s",
            flush=True,
        )

    # All layouts must agree on the answer, or the comparison is meaningless.
    answers = {row["rows_that_day"] for row in measured}
    consistent = len(answers) == 1

    RESULTS.parent.mkdir(exist_ok=True)
    with io.open(RESULTS, "w", encoding="utf-8") as fh:
        json.dump(
            {"one_day": ONE_DAY, "layouts": measured, "all_agree": consistent,
             "rows_that_day": measured[0]["rows_that_day"]},
            fh, ensure_ascii=False, indent=2,
        )

    print()
    print(f"  All layouts return the same {measured[0]['rows_that_day']:,} rows "
          f"for {ONE_DAY}: {consistent}")
    print(f"Written to {RESULTS.relative_to(PROJECT)}")
    shutil.rmtree(SCRATCH, ignore_errors=True)

    if not consistent:
        raise SystemExit("Layouts disagree on the answer. The benchmark is invalid.")


if __name__ == "__main__":
    main()
