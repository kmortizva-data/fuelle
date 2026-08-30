"""How many hours a day does the compressor actually run loaded?

Module 13, the GROUP BY lesson. This is the number the whole twin hangs from: a
leak does not move the pressure, because the control loop holds it. What moves
is how long the compressor has to work to hold it. So the duty cycle is the
signal, and this is where it first gets measured.

Before grouping anything, the script checks the rule it is about to group by.
The official datasheet says three different signals should all say "loaded":

  DV_eletric   active when the compressor is functioning under load
  COMP         active when there is NO air intake (so off, or offloaded)
  Motor_current  around 7 A under load, 4 A offloaded, 0 A off

Three sources for one fact is an invitation to check they agree, so step 1 does
exactly that instead of trusting the PDF.

Run:  .venv\\Scripts\\python.exe src\\transform\\m13_duty_cycle.py
"""

from __future__ import annotations

import io
import json
import sys
from pathlib import Path

import duckdb

sys.stdout.reconfigure(encoding="utf-8")

PROJECT = Path(__file__).resolve().parents[2]
BRONZE = PROJECT / "lake" / "bronze" / "telemetry"
RESULTS = PROJECT / "results" / "m13_duty_cycle.json"

SECONDS_PER_READING = 10  # measured in module 1, not assumed


def main() -> None:
    if not BRONZE.exists():
        raise SystemExit("Bronze layer missing. Run src/ingest/bronze.py first.")

    con = duckdb.connect()
    con.execute(
        f"CREATE VIEW telemetry AS "
        f"SELECT * FROM read_parquet('{BRONZE.as_posix()}/**/*.parquet')"
    )

    # --- Step 1. Do the three signals agree on what "loaded" means? ----------
    agreement = con.sql(
        """
        SELECT
            DV_eletric,
            COMP,
            count(*)                          AS readings,
            round(min(Motor_current), 2)      AS current_min,
            round(avg(Motor_current), 2)      AS current_avg,
            round(max(Motor_current), 2)      AS current_max
        FROM telemetry
        GROUP BY DV_eletric, COMP
        ORDER BY readings DESC
        """
    ).fetchall()

    print("Step 1. Do the signals agree?")
    print("  DV_eletric  COMP    readings      current min / avg / max")
    for dv, comp, readings, lo, avg, hi in agreement:
        print(f"  {dv:>10.0f}  {comp:>4.0f}  {readings:>10,}      {lo:>5} / {avg:>5} / {hi:>5}")

    # --- Step 2. The duty cycle, per day -------------------------------------
    daily = con.sql(
        f"""
        SELECT
            day,
            count(*)                                                   AS readings,
            sum(CASE WHEN DV_eletric = 1 THEN 1 ELSE 0 END)            AS loaded_readings,
            round(sum(CASE WHEN DV_eletric = 1 THEN 1 ELSE 0 END)
                  * {SECONDS_PER_READING} / 3600.0, 2)                 AS loaded_hours,
            round(100.0 * sum(CASE WHEN DV_eletric = 1 THEN 1 ELSE 0 END)
                  / count(*), 1)                                       AS loaded_pct
        FROM telemetry
        GROUP BY day
        ORDER BY day
        """
    ).fetchall()

    hours = [row[3] for row in daily]
    complete = [row for row in daily if row[1] > 0.9 * 8640]  # a full day = 8640 readings

    summary = con.sql(
        f"""
        SELECT
            round(avg(loaded_hours), 2),
            round(min(loaded_hours), 2),
            round(max(loaded_hours), 2)
        FROM (
            SELECT day,
                   count(*) AS readings,
                   sum(CASE WHEN DV_eletric = 1 THEN 1 ELSE 0 END)
                       * {SECONDS_PER_READING} / 3600.0 AS loaded_hours
            FROM telemetry GROUP BY day
        )
        WHERE readings > 0.9 * 8640
        """
    ).fetchone()

    by_month = con.sql(
        f"""
        SELECT
            strftime(day, '%Y-%m')                                     AS month,
            count(*)                                                   AS days,
            round(avg(loaded_hours), 2)                                AS avg_loaded_hours
        FROM (
            SELECT day,
                   count(*) AS readings,
                   sum(CASE WHEN DV_eletric = 1 THEN 1 ELSE 0 END)
                       * {SECONDS_PER_READING} / 3600.0 AS loaded_hours
            FROM telemetry GROUP BY day
        )
        WHERE readings > 0.9 * 8640
        GROUP BY month
        ORDER BY month
        """
    ).fetchall()

    print()
    print("Step 2. Loaded hours per day")
    print(f"  Days in the file          {len(daily)}")
    print(f"  Complete days             {len(complete)}  (a full day is 8,640 readings)")
    print(f"  Average loaded hours      {summary[0]}")
    print(f"  Range                     {summary[1]} to {summary[2]}")
    print()
    print("  month     days   avg loaded hours")
    for month, days, avg in by_month:
        print(f"  {month}   {days:>4}   {avg:>16}")

    # --- Step 3. The days at the top, against the failure reports ------------
    # Module 13 only measures the duty cycle and points at the outliers; module
    # 16 does the JOIN properly. This runs here so the finding is recorded in
    # results/ from the start, and so the lesson never claims something the data
    # has not been asked.
    failures = {
        "2020-04-18": "#1",
        "2020-05-29": "#1 (second)", "2020-05-30": "#1 (second)",
        "2020-06-05": "#3", "2020-06-06": "#3", "2020-06-07": "#3",
        "2020-07-15": "#4",
    }
    complete_sorted = sorted(
        ({"day": str(d), "readings": r, "loaded_hours": lh, "loaded_pct": lp}
         for d, r, lr, lh, lp in daily if r > 0.9 * 8640),
        key=lambda row: -row["loaded_hours"],
    )
    top = complete_sorted[:10]
    for row in top:
        row["documented_failure"] = failures.get(row["day"])

    documented_days = [d for d in failures if any(x["day"] == d for x in complete_sorted)]
    caught = [d for d in documented_days
              if any(x["day"] == d for x in complete_sorted[:6])]

    print()
    print("Step 3. The busiest complete days, against the failure reports")
    print("  day           loaded hours   % of day   documented failure")
    for row in top:
        mark = row["documented_failure"] or ""
        print(f"  {row['day']}   {row['loaded_hours']:>12}   {row['loaded_pct']:>8}   {mark}")
    print()
    print(f"  Documented failure days present as complete days: {len(documented_days)}")
    print(f"  Of those, inside the top 6 by duty cycle:         {len(caught)}")

    results = {
        "seconds_per_reading": SECONDS_PER_READING,
        "top_days": top,
        "documented_failure_days_complete": documented_days,
        "documented_in_top_6": caught,
        "readings_in_a_full_day": 8640,
        "days_total": len(daily),
        "days_complete": len(complete),
        "avg_loaded_hours": summary[0],
        "min_loaded_hours": summary[1],
        "max_loaded_hours": summary[2],
        "by_month": [{"month": m, "days": d, "avg_loaded_hours": a} for m, d, a in by_month],
        "signal_agreement": [
            {"dv_eletric": dv, "comp": comp, "readings": n,
             "current_min": lo, "current_avg": avg, "current_max": hi}
            for dv, comp, n, lo, avg, hi in agreement
        ],
        "daily": [{"day": str(d), "readings": r, "loaded_readings": lr,
                   "loaded_hours": lh, "loaded_pct": lp} for d, r, lr, lh, lp in daily],
    }
    RESULTS.parent.mkdir(exist_ok=True)
    with io.open(RESULTS, "w", encoding="utf-8") as fh:
        json.dump(results, fh, ensure_ascii=False, indent=2)
    print()
    print(f"Written to {RESULTS.relative_to(PROJECT)}")


if __name__ == "__main__":
    main()
