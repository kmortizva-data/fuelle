"""How big should a partition be? Measured, not copied from a blog post.

Module 6. Partitioning splits one table into folders so a question about one day
reads one folder instead of everything. The usual advice is "partition by day"
and it is repeated everywhere without a number attached.

This script writes the same data four ways and times all four, on this machine
and this filesystem, because that is what decides it here. On Windows, creating
many small files is not free, and the answer may well differ from the advice.

It also reports read time for a one-day question, which is the whole point of
partitioning: writing slower to read faster is a trade, and a trade needs both
numbers.

Every timing is the median of seven runs with its range (src/medir.py), and any
two layouts whose ranges overlap are reported as indistinguishable instead of
being ranked. The first version of this script timed each layout once, which is
enough to pick a winner and not enough to publish a factor.

Run:  .venv\\Scripts\\python.exe src\\transform\\choose_partition.py
"""

from __future__ import annotations

import io
import json
import shutil
import sys
from pathlib import Path

import duckdb

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from medir import RUNS, Measurement, distinguishable, measure  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")

PROJECT = Path(__file__).resolve().parents[2]
BRONZE = PROJECT / "lake" / "bronze" / "telemetry"
SCRATCH = PROJECT / "lake" / "_bench"
RESULTS = PROJECT / "results" / "m06_partition.json"

# The question every layout has to answer, so the comparison is fair.
ONE_DAY = "2020-06-05"


def source_glob() -> str:
    return f"{BRONZE.as_posix()}/**/*.parquet"


def write_layout(con: duckdb.DuckDBPyConnection, name: str,
                 partition_by: str | None) -> tuple[dict, Measurement]:
    target = SCRATCH / name

    if partition_by:
        select = f"SELECT *, {partition_by} AS part FROM read_parquet('{source_glob()}')"
        options = "FORMAT PARQUET, PARTITION_BY (part), OVERWRITE_OR_IGNORE, COMPRESSION ZSTD"
        destination = target.as_posix()
    else:
        select = f"SELECT * FROM read_parquet('{source_glob()}')"
        options = "FORMAT PARQUET, COMPRESSION ZSTD"
        destination = (target / "all.parquet").as_posix()

    def clean() -> None:
        """Untimed: each run must start from an empty folder."""
        if target.exists():
            shutil.rmtree(target)
        target.mkdir(parents=True, exist_ok=True)

    written = measure(
        lambda: con.execute(f"COPY ({select}) TO '{destination}' ({options})"),
        setup=clean,
    )

    files = list(target.rglob("*.parquet"))
    size = sum(f.stat().st_size for f in files)

    # The read that matters: one day out of seven months.
    glob = f"{target.as_posix()}/**/*.parquet" if partition_by else destination
    read = measure(lambda: con.sql(
        f"SELECT count(*) FROM read_parquet('{glob}') "
        f"WHERE CAST(timestamp AS DATE) = DATE '{ONE_DAY}'"
    ).fetchone()[0])

    row = {
        "layout": name,
        "files": len(files),
        "size_mb": round(size / 1024 / 1024, 2),
        "write_seconds": round(written.median, 2),
        "write_min_s": round(written.minimum, 2),
        "write_max_s": round(written.maximum, 2),
        "read_one_day_seconds": round(read.median, 3),
        "read_min_s": round(read.minimum, 3),
        "read_max_s": round(read.maximum, 3),
        "corridas": RUNS,
        "rows_that_day": read.result,
    }
    return row, read


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

    measured, reads = [], {}
    for name, expression in layouts:
        print(f"Writing {name}, {RUNS} times...", flush=True)
        row, read = write_layout(con, name, expression)
        measured.append(row)
        reads[name] = read
        print(
            f"  {row['files']:>4} files  {row['size_mb']:>7.2f} MB  "
            f"write {row['write_seconds']:>8.2f} s  "
            f"read one day {row['read_one_day_seconds']:.3f} s "
            f"({row['read_min_s']:.3f} to {row['read_max_s']:.3f})",
            flush=True,
        )

    # All layouts must agree on the answer, or the comparison is meaningless.
    answers = {row["rows_that_day"] for row in measured}
    consistent = len(answers) == 1

    # Ranking by median alone would invent differences. Two layouts whose read
    # ranges overlap are the same layout as far as this machine can tell, and
    # saying so is the honest result.
    fastest_name = min(measured, key=lambda r: r["read_one_day_seconds"])["layout"]
    for row in measured:
        other = reads[row["layout"]]
        row["read_distinguishable_from_fastest"] = (
            False if row["layout"] == fastest_name
            else distinguishable(reads[fastest_name], other))

    slowest = max(measured, key=lambda r: r["read_one_day_seconds"])
    fastest = min(measured, key=lambda r: r["read_one_day_seconds"])
    by_day = next(r for r in measured if r["layout"] == "by_day")
    single = next(r for r in measured if r["layout"] == "single_file")

    payload = {
        "one_day": ONE_DAY, "layouts": measured, "all_agree": consistent,
        "rows_that_day": measured[0]["rows_that_day"], "corridas": RUNS,
        "fastest_read": fastest["layout"], "slowest_read": slowest["layout"],
        # The headline of module 6, computed here and not by hand in the prose.
        "by_day_veces_mas_lento": round(
            by_day["read_one_day_seconds"] / single["read_one_day_seconds"], 1),
        "by_day_por_ciento_mas_grande": round(
            (by_day["size_mb"] / single["size_mb"] - 1) * 100),
        "by_day_ficheros": by_day["files"],
    }

    RESULTS.parent.mkdir(exist_ok=True)
    with io.open(RESULTS, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)

    print()
    print(f"  All layouts return the same {measured[0]['rows_that_day']:,} rows "
          f"for {ONE_DAY}: {consistent}")
    print(f"  fastest read: {fastest['layout']}")
    for row in measured:
        if row["layout"] != fastest_name and not row["read_distinguishable_from_fastest"]:
            print(f"  {row['layout']} reads the same as {fastest_name}: "
                  f"the ranges overlap, so there is no difference to report")
    print(f"Written to {RESULTS.relative_to(PROJECT)}")
    shutil.rmtree(SCRATCH, ignore_errors=True)

    if not consistent:
        raise SystemExit("Layouts disagree on the answer. The benchmark is invalid.")


if __name__ == "__main__":
    main()
