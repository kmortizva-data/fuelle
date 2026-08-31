"""What the 212 daily partitions actually look like. Module 4.

`bronze.py` reports one number, 212 folders, and that number hides the thing
worth seeing: the folders are nowhere near the same size. A full day of readings
every ten seconds is 8,640 of them, and most days fall short of that.

This profiles the layer that already exists on disk instead of rebuilding it, so
it costs a second and can be rerun whenever.

Run:  .venv\\Scripts\\python.exe src\\ingest\\partition_profile.py
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
RESULTS = PROJECT / "results" / "m04_particiones.json"

# A full day at one reading every ten seconds: 6 per minute, 360 per hour.
READINGS_IN_A_FULL_DAY = 24 * 60 * 6


def main() -> None:
    if not BRONZE.exists():
        raise SystemExit("Bronze layer missing. Run src/ingest/bronze.py first.")

    con = duckdb.connect()
    rows = con.sql(f"""
        SELECT day, count(*) AS lecturas
        FROM read_parquet('{BRONZE.as_posix()}/**/*.parquet')
        GROUP BY day
        ORDER BY day
    """).fetchall()

    days = [{"dia": str(d), "lecturas": n,
             "por_ciento_del_dia": round(n / READINGS_IN_A_FULL_DAY * 100, 1)}
            for d, n in rows]
    counts = sorted(n for _, n in rows)

    sizes = []
    for folder in sorted(BRONZE.glob("day=*")):
        kb = sum(f.stat().st_size for f in folder.rglob("*.parquet")) / 1024
        sizes.append({"dia": folder.name.split("=", 1)[1], "kb": round(kb, 1)})

    # "Complete" has to mean the same thing here as in module 10, which averages
    # over days above 90 % and gets 91 of them. Two thresholds would put two
    # different numbers behind the same word in the same course.
    complete = [d for d in days if d["lecturas"] > READINGS_IN_A_FULL_DAY * 0.9]
    brimming = [d for d in days if d["lecturas"] >= READINGS_IN_A_FULL_DAY]
    nearly_empty = [d for d in days if d["por_ciento_del_dia"] < 10]

    payload = {
        "particiones": len(days),
        "lecturas_de_un_dia_lleno": READINGS_IN_A_FULL_DAY,
        "dias": days,
        "kb_por_particion": sizes,
        "lecturas_minimo": counts[0],
        "lecturas_maximo": counts[-1],
        "lecturas_mediana": counts[len(counts) // 2],
        "por_ciento_mediano_del_dia": round(
            counts[len(counts) // 2] / READINGS_IN_A_FULL_DAY * 100, 1),
        "dias_completos": len(complete),
        "dias_a_rebosar": len(brimming),
        "dias_casi_vacios": len(nearly_empty),
        "kb_minimo": min(s["kb"] for s in sizes),
        "kb_maximo": max(s["kb"] for s in sizes),
        "veces_entre_la_mayor_y_la_menor": round(
            max(s["kb"] for s in sizes) / min(s["kb"] for s in sizes)),
    }
    RESULTS.parent.mkdir(exist_ok=True)
    with io.open(RESULTS, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)

    print(f"  {payload['particiones']} particiones")
    print(f"  un día lleno son {READINGS_IN_A_FULL_DAY:,} lecturas")
    print(f"  mediana {payload['lecturas_mediana']:,} "
          f"({payload['por_ciento_mediano_del_dia']} % de un día)")
    print(f"  completos {payload['dias_completos']}, "
          f"casi vacíos {payload['dias_casi_vacios']}")
    print(f"  la partición mayor pesa {payload['veces_entre_la_mayor_y_la_menor']} veces "
          f"lo que la menor ({payload['kb_maximo']} KB contra {payload['kb_minimo']} KB)")
    print(f"  escrito en {RESULTS.relative_to(PROJECT)}")


if __name__ == "__main__":
    main()
