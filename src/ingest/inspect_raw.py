"""X-ray of the raw MetroPT-3 file, before anything touches it.

Module 1. Answers three questions the lesson needs:
  1. What is actually inside the file (rows, columns, time span, sampling period)?
  2. Does the official datasheet agree with the file?
  3. How long does one honest question take against the raw CSV?

Every number this script prints is written to results/m01_raw.json, which is the
only place check_numbers.py will look when validating the lesson prose.
"""

from __future__ import annotations

import io
import json
import sys
import time
from pathlib import Path

import duckdb

# The console on this machine is cp1252; without this, accented output dies.
sys.stdout.reconfigure(encoding="utf-8")

PROJECT = Path(__file__).resolve().parents[2]
RAW_CSV = PROJECT / "data" / "MetroPT3(AirCompressor).csv"
RESULTS = PROJECT / "results" / "m01_raw.json"

# Claimed by the official PDF that ships inside the UCI zip.
DATASHEET_CLAIMED_POINTS = 15_169_480
DATASHEET_CLAIMED_HZ = 1.0


def main() -> None:
    if not RAW_CSV.exists():
        raise SystemExit(f"Raw CSV not found: {RAW_CSV}\nRun the download step first.")

    con = duckdb.connect()
    src = f"read_csv_auto('{RAW_CSV.as_posix()}')"

    columns = con.sql(f"SELECT * FROM {src} LIMIT 0").columns
    size_mb = RAW_CSV.stat().st_size / 1024 / 1024

    started = time.perf_counter()
    rows, first_ts, last_ts = con.sql(
        f"SELECT count(*), min(timestamp), max(timestamp) FROM {src}"
    ).fetchone()
    scan_seconds = time.perf_counter() - started

    # The sampling period, measured rather than assumed: the gap between
    # consecutive readings, taken as the most frequent gap in the file.
    period_seconds, period_count = con.sql(
        f"""
        SELECT gap, count(*) AS n
        FROM (
            SELECT date_diff('second', lag(timestamp) OVER (ORDER BY timestamp),
                             timestamp) AS gap
            FROM {src}
        )
        WHERE gap IS NOT NULL
        GROUP BY gap
        ORDER BY n DESC
        LIMIT 1
        """
    ).fetchone()

    irregular = con.sql(
        f"""
        SELECT count(*)
        FROM (
            SELECT date_diff('second', lag(timestamp) OVER (ORDER BY timestamp),
                             timestamp) AS gap
            FROM {src}
        )
        WHERE gap IS NOT NULL AND gap <> {period_seconds}
        """
    ).fetchone()[0]

    implied_ratio = DATASHEET_CLAIMED_POINTS / rows

    results = {
        "rows": rows,
        "columns": list(columns),
        "n_signals": len(columns) - 2,  # minus the unnamed index and timestamp
        "first_timestamp": str(first_ts),
        "last_timestamp": str(last_ts),
        "period_seconds_measured": period_seconds,
        "readings_at_that_period": period_count,
        "irregular_gaps": irregular,
        "irregular_gaps_pct": round(100 * irregular / (rows - 1), 3),
        "size_mb": round(size_mb, 1),
        "scan_seconds": round(scan_seconds, 2),
        "datasheet_claimed_points": DATASHEET_CLAIMED_POINTS,
        "datasheet_claimed_hz": DATASHEET_CLAIMED_HZ,
        "datasheet_over_file_ratio": round(implied_ratio, 4),
    }

    RESULTS.parent.mkdir(exist_ok=True)
    with io.open(RESULTS, "w", encoding="utf-8") as fh:
        json.dump(results, fh, ensure_ascii=False, indent=2)

    print(f"Rows                  {rows:,}")
    print(f"Signals               {results['n_signals']}")
    print(f"Span                  {first_ts}  ->  {last_ts}")
    print(f"Sampling period       {period_seconds} s  ({period_count:,} readings)")
    print(f"Irregular gaps        {irregular:,}  ({results['irregular_gaps_pct']} %)")
    print(f"Size on disk          {size_mb:.1f} MB")
    print(f"Full scan             {scan_seconds:.2f} s")
    print()
    print(f"Datasheet claims      {DATASHEET_CLAIMED_POINTS:,} points at 1 Hz")
    print(f"File delivers         {rows:,} rows every {period_seconds} s")
    print(f"Ratio                 {implied_ratio:.4f}")
    print()
    print(f"Written to {RESULTS.relative_to(PROJECT)}")


if __name__ == "__main__":
    main()
