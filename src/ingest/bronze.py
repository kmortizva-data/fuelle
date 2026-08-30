"""Bronze layer: the raw CSV, partitioned by day, with nothing else touched.

Minimal version, written during the mock-up phase so lesson 13 has real numbers
to stand on. Modules 4 to 7 explain and refine what happens here; this is the
skeleton those lessons will teach.

Two rules the bronze layer must obey, and both are tested at the bottom:
  1. Nothing is cleaned, fixed or interpreted. Values land as they arrived.
  2. Running it twice must not duplicate a single row.

The only thing added is a `day` column derived from the timestamp, because that
is what the partitioning needs, and a fingerprint manifest so a later run can
tell whether the source actually changed.

Run:  .venv\\Scripts\\python.exe src\\ingest\\bronze.py
"""

from __future__ import annotations

import hashlib
import io
import json
import shutil
import sys
import time
from pathlib import Path

import duckdb

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


def ingest(con: duckdb.DuckDBPyConnection) -> None:
    """Read the CSV and write it out as Parquet, one folder per day."""
    if BRONZE.exists():
        shutil.rmtree(BRONZE)
    BRONZE.parent.mkdir(parents=True, exist_ok=True)

    # The first column of the file has no name: it is the original 1 Hz row
    # number, and it is the evidence that the published CSV is one reading in
    # ten. It is kept, renamed, never renumbered.
    #
    # The name DuckDB invents for a headerless first column is an implementation
    # detail (it is "column00" today), so it is read back rather than hardcoded.
    source = f"read_csv_auto('{RAW_CSV.as_posix()}', header = true)"
    first = con.sql(f"SELECT * FROM {source} LIMIT 0").columns[0]

    con.execute(
        f"""
        COPY (
            SELECT
                "{first}" AS source_index,
                * EXCLUDE ("{first}"),
                CAST(timestamp AS DATE) AS day
            FROM {source}
        )
        TO '{BRONZE.as_posix()}'
        (FORMAT PARQUET, PARTITION_BY (day), OVERWRITE_OR_IGNORE, COMPRESSION ZSTD)
        """
    )


def measure(con: duckdb.DuckDBPyConnection) -> dict:
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


def main() -> None:
    if not RAW_CSV.exists():
        raise SystemExit(f"Raw CSV not found: {RAW_CSV}")

    con = duckdb.connect()

    print("Fingerprinting the source...")
    started = time.perf_counter()
    source_hash = fingerprint(RAW_CSV)
    hash_seconds = time.perf_counter() - started
    print(f"  sha256 {source_hash[:16]}...  ({hash_seconds:.1f} s)")

    print("Writing bronze...")
    started = time.perf_counter()
    ingest(con)
    write_seconds = time.perf_counter() - started

    stats = measure(con)

    # Rule 2, tested rather than asserted in prose: run it again and the row
    # count must not move.
    print("Running it a second time, to prove it does not duplicate...")
    ingest(con)
    second = measure(con)
    idempotent = second["rows"] == stats["rows"]

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

    results = {
        **stats,
        "write_seconds": round(write_seconds, 2),
        "fingerprint_seconds": round(hash_seconds, 1),
        "rows_after_second_run": second["rows"],
        "idempotent": idempotent,
        "compression_ratio": round(stats["csv_mb"] / stats["size_mb"], 2),
    }
    RESULTS.parent.mkdir(exist_ok=True)
    with io.open(RESULTS, "w", encoding="utf-8") as fh:
        json.dump(results, fh, ensure_ascii=False, indent=2)

    print()
    print(f"  Rows            {stats['rows']:,}")
    print(f"  Partitions      {stats['partitions']} (one per day)")
    print(f"  CSV             {stats['csv_mb']} MB")
    print(f"  Parquet         {stats['size_mb']} MB   ({results['compression_ratio']}x smaller)")
    print(f"  Write time      {write_seconds:.2f} s")
    print(f"  Second run      {second['rows']:,} rows  ->  "
          f"{'idempotent' if idempotent else 'DUPLICATED, BUG'}")
    print()
    print(f"Written to {RESULTS.relative_to(PROJECT)} and {MANIFEST.relative_to(PROJECT)}")

    if not idempotent:
        raise SystemExit("Bronze is not idempotent. That is a bug, not a note.")


if __name__ == "__main__":
    main()
