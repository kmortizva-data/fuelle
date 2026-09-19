"""Bronze layer: the raw CSV, partitioned by day, with nothing else touched.

Two rules the bronze layer must obey:
  1. Nothing is cleaned, fixed or interpreted. Values land as they arrived.
  2. Running it twice must not duplicate a single row.

The only things added are a `day` column derived from the timestamp, because
that is what the partitioning needs, and a fingerprint manifest so a later run
can tell whether the source actually changed.

A warning about rule 2, and it is the reason module 5 exists as its own lesson:
this script gets rule 2 the cheap way, by deleting the folder and writing it
again. That really is idempotent, and at this size it is also the right choice,
but it proves nothing about the interesting case. A pipeline that appends
instead of replacing will happily duplicate everything on a rerun, and no
amount of rereading this file would show it. `fingerprint.py` runs that
experiment for real.

Every timing here is the median of seven runs (src/medir.py). The first version
reported a single run, and that run happened to be one where the antivirus was
scanning a freshly created 209 MB folder: it published 3.5 hours for a write
that takes seconds.

Run:  .venv\\Scripts\\python.exe src\\ingest\\bronze.py
"""

from __future__ import annotations

import hashlib
import io
import json
import shutil
import sys
from pathlib import Path

import duckdb

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from escritura import un_solo_hilo  # noqa: E402
from medir import RUNS, measure  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")

PROJECT = Path(__file__).resolve().parents[2]
RAW_CSV = PROJECT / "data" / "MetroPT3(AirCompressor).csv"
BRONZE = PROJECT / "lake" / "bronze" / "telemetry"
MANIFEST = PROJECT / "lake" / "bronze" / "_manifest.json"
RESULTS = PROJECT / "results" / "bronze.json"


def fingerprint(path: Path, chunk: int = 1 << 20) -> str:
    """SHA256 of the source file, so a rerun knows whether anything changed."""
    digest = hashlib.sha256()
    with io.open(path, "rb") as fh:
        while block := fh.read(chunk):
            digest.update(block)
    return digest.hexdigest()


def clear(days: tuple[str, str] | None = None) -> None:
    """Empty the layer, or only the days from `days[0]` to `days[1]`. Untimed.

    The range exists for module 29: the orchestrator backfills a stretch of days
    by clearing those folders and writing them again, and leaves the rest alone.
    """
    if days is None:
        if BRONZE.exists():
            shutil.rmtree(BRONZE)
    else:
        for folder in BRONZE.glob("day=*"):
            if days[0] <= folder.name.removeprefix("day=") <= days[1]:
                shutil.rmtree(folder)
    BRONZE.parent.mkdir(parents=True, exist_ok=True)


def write(con: duckdb.DuckDBPyConnection, days: tuple[str, str] | None = None) -> None:
    """Read the CSV and write it out as Parquet, one folder per day.

    With `days`, only that stretch is written. The CSV is still read whole, since
    it has no index to jump to a day, but only those folders are touched.
    """
    # The first column of the file has no name: it is the original 1 Hz row
    # number, and it is the evidence that the published CSV is one reading in
    # ten. It is kept, renamed, never renumbered.
    #
    # The name DuckDB invents for a headerless first column is an implementation
    # detail (it is "column00" today), so it is read back rather than hardcoded.
    source = f"read_csv_auto('{RAW_CSV.as_posix()}', header = true)"
    first = con.sql(f"SELECT * FROM {source} LIMIT 0").columns[0]
    only = ("" if days is None else
            f"WHERE CAST(timestamp AS DATE) BETWEEN DATE '{days[0]}' AND DATE '{days[1]}'")

    # One thread, so that two runs write the same bytes: module 29 found that
    # with several, the same rows land in different files. See src/escritura.py.
    with un_solo_hilo(con):
        con.execute(
            f"""
        COPY (
            SELECT
                "{first}" AS source_index,
                * EXCLUDE ("{first}"),
                CAST(timestamp AS DATE) AS day
            FROM {source}
            {only}
        )
        TO '{BRONZE.as_posix()}'
        (FORMAT PARQUET, PARTITION_BY (day), OVERWRITE_OR_IGNORE, COMPRESSION ZSTD)
        """
        )


def inventory(con: duckdb.DuckDBPyConnection) -> dict:
    glob = f"{BRONZE.as_posix()}/**/*.parquet"
    rows = con.sql(f"SELECT count(*) FROM read_parquet('{glob}')").fetchone()[0]
    partitions = len(list(BRONZE.glob("day=*")))
    size = sum(f.stat().st_size for f in BRONZE.rglob("*.parquet"))
    return {
        "rows": rows,
        "partitions": partitions,
        "size_mb": round(size / 1024 / 1024, 2),
        "csv_mb": round(RAW_CSV.stat().st_size / 1024 / 1024, 2),
    }


def write_manifest(source_hash: str, stats: dict) -> dict:
    """What the layer was built from, so a later run can tell whether the source changed."""
    manifest = {
        "source_file": RAW_CSV.name,
        "source_sha256": source_hash,
        "source_bytes": RAW_CSV.stat().st_size,
        "rows": stats["rows"],
        "partitions": stats["partitions"],
    }
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    with io.open(MANIFEST, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, ensure_ascii=False, indent=2)
    return manifest


def main() -> None:
    if not RAW_CSV.exists():
        raise SystemExit(f"Raw CSV not found: {RAW_CSV}")

    con = duckdb.connect()

    print(f"Fingerprinting the source, {RUNS} times...")
    hashed = measure(lambda: fingerprint(RAW_CSV))
    source_hash = hashed.result
    speed = RAW_CSV.stat().st_size / 1024 / 1024 / hashed.median
    print(f"  sha256 {source_hash[:16]}...  {hashed}  ({speed:.0f} MB/s)")

    print(f"Writing bronze, {RUNS} times...")
    written = measure(lambda: write(con), setup=clear)
    stats = inventory(con)

    # Rule 2, tested rather than asserted in prose. Note what this does and does
    # not prove: `clear()` runs first, so this shows that replacing the layer
    # lands on the same count, not that an appending pipeline would be safe.
    print("Running it a second time, to check the count does not move...")
    clear()
    write(con)
    second = inventory(con)
    idempotent = second["rows"] == stats["rows"]

    write_manifest(source_hash, stats)

    results = {
        **stats,
        "write_seconds": round(written.median, 2),
        "write_min_s": round(written.minimum, 2),
        "write_max_s": round(written.maximum, 2),
        "fingerprint_seconds": round(hashed.median, 2),
        "fingerprint_mb_s": round(speed),
        "corridas": RUNS,
        "rows_after_second_run": second["rows"],
        "idempotent": idempotent,
        "compression_ratio": round(stats["csv_mb"] / stats["size_mb"], 2),
        "rows_per_partition": round(stats["rows"] / stats["partitions"]),
    }
    RESULTS.parent.mkdir(exist_ok=True)
    with io.open(RESULTS, "w", encoding="utf-8") as fh:
        json.dump(results, fh, ensure_ascii=False, indent=2)

    print()
    print(f"  Rows            {stats['rows']:,}")
    print(f"  Partitions      {stats['partitions']} (one per day)")
    print(f"  CSV             {stats['csv_mb']} MB")
    print(f"  Parquet         {stats['size_mb']} MB   ({results['compression_ratio']}x smaller)")
    print(f"  Write time      {written}")
    print(f"  Second run      {second['rows']:,} rows  ->  "
          f"{'same count' if idempotent else 'DUPLICATED, BUG'}")
    print()
    print(f"Written to {RESULTS.relative_to(PROJECT)} and {MANIFEST.relative_to(PROJECT)}")

    if not idempotent:
        raise SystemExit("Bronze is not idempotent. That is a bug, not a note.")


if __name__ == "__main__":
    main()
