"""The Parquet files the browser downloads, each sized by measurement.

The live query block runs DuckDB inside the reader's browser, so it needs data
there. The lake is 1.5 million rows, which is fine on disk and not fine over a
phone connection, so every sample is a decision with a number behind it.

The rule that decides all of them, and it is not about size:

    ANY QUERY THE LESSON PUBLISHES MUST GIVE THE SAME ANSWER ON THE SAMPLE AS ON
    THE LAKE.

Otherwise the reader solves a challenge correctly and the page says no. That is
why the full-row samples drop columns and never rows: dropping a column cannot
change an aggregate that does not mention it, while dropping rows changes
almost every aggregate there is. The one sample that does drop rows, `un_dia`,
is only used by a module whose every query filters to that same day.

The weight itself is module 7's finding cashed in. `timestamp` holds 1,516,948
distinct values and costs 5.16 MB on its own; `day` holds 212 and costs 2 KB.
That is the whole reason `un_dia` exists rather than a lake-wide sample with the
clock in it.

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
REPORTS = PROJECT / "src" / "ingest" / "failure_reports.csv"
SAMPLES = PROJECT / "assets" / "muestras"
RESULTS = PROJECT / "results" / "sample.json"

# El día del módulo 13. Se elige el de la avería #3, que tiene el registro
# completo (8.716 lecturas) y arranques de sobra que contar.
ONE_DAY = "2020-06-05"

# Las muestras que se publican, con quién las usa y por qué llevan lo que llevan.
SHIPPED = {
    "sin_timestamp_ligera": {
        "columns": ["day", "DV_eletric", "COMP"],
        "where": "",
        "para": "módulos 10 y 11: agrupar y WITH",
        "por_que": "el ciclo de trabajo sale de DV_eletric y del día, y nada más",
    },
    "sql": {
        "columns": ["day", "LPS", "DV_eletric", "COMP", "Motor_current", "TP2"],
        "where": "",
        "para": "módulos 8, 9 y 12: filtrar, tipos y JOIN",
        "por_que": ("LPS para la alarma, Motor_current para los tres estados del motor, "
                    "TP2 para la presión. Sin TP3, que cuesta el doble que TP2"),
    },
    "un_dia": {
        "columns": ["timestamp", "day", "DV_eletric", "COMP", "Motor_current"],
        "where": f"day = DATE '{ONE_DAY}'",
        "para": "módulo 13: funciones de ventana",
        "por_que": ("comparar con la fila de al lado exige la hora exacta, y la hora "
                    "cuesta 5,16 MB si se lleva el lago entero. Un día son 43 KB"),
    },
}

# La tabla pequeña de los partes de avería, para el JOIN del módulo 12.
EXTRA = {"averias": REPORTS}


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
    rows = con.sql(f"SELECT count(*) FROM read_parquet('{target.as_posix()}')").fetchone()[0]
    return {
        "name": name,
        "rows": rows,
        "columns": len(columns) if columns else 17,
        "kb_on_disk": round(raw / 1024, 1),
        "kb_downloaded": round(gzipped_size(target) / 1024, 1),
    }


def agrees_with_lake(con: duckdb.DuckDBPyConnection, name: str, spec: dict) -> list[str]:
    """Every column kept has to hold exactly what the lake holds.

    Checked instead of trusted: the sum and the count of each numeric column are
    compared against the same query on the lake, over the same rows. A sample
    that quietly rounded, reordered or lost rows would fail here rather than in
    the reader's browser, where it would show up as a correct answer marked wrong.
    """
    path = SAMPLES / f"{name}.parquet"
    lake = f"read_parquet('{BRONZE.as_posix()}/**/*.parquet')"
    clause = f"WHERE {spec['where']}" if spec["where"] else ""
    problems = []

    for column in spec["columns"]:
        if column in ("day", "timestamp"):
            expr = f'count(DISTINCT "{column}")'
        else:
            expr = f'sum("{column}")'
        here = con.sql(
            f"SELECT {expr} FROM read_parquet('{path.as_posix()}')").fetchone()[0]
        there = con.sql(f"SELECT {expr} FROM {lake} {clause}").fetchone()[0]
        # Con tolerancia relativa y no con igualdad, porque sumar los mismos
        # decimales en otro orden no da exactamente lo mismo. La muestra va
        # ordenada por hora y el lago se agrega por particiones, así que TP2
        # salía 2.074.920,864001 aquí y 2.074.920,864 allí. Es la misma basura
        # de coma flotante que el módulo 1 documenta, no un dato distinto.
        if isinstance(here, float) or isinstance(there, float):
            iguales = abs(here - there) <= 1e-9 * max(abs(there), 1.0)
        else:
            iguales = here == there
        if not iguales:
            problems.append(f"{name}.{column}: la muestra da {here} y el lago {there}")

    n_here = con.sql(
        f"SELECT count(*) FROM read_parquet('{path.as_posix()}')").fetchone()[0]
    n_there = con.sql(f"SELECT count(*) FROM {lake} {clause}").fetchone()[0]
    if n_here != n_there:
        problems.append(f"{name}: {n_here:,} filas contra {n_there:,} en el lago")
    return problems


def write_reports(con: duckdb.DuckDBPyConnection) -> dict:
    """Los cuatro partes de avería, tal cual están escritos, para el JOIN."""
    target = SAMPLES / "averias.parquet"
    con.execute(
        f"COPY (SELECT * FROM read_csv_auto('{REPORTS.as_posix()}')) "
        f"TO '{target.as_posix()}' (FORMAT PARQUET, COMPRESSION ZSTD)")
    rows = con.sql(f"SELECT count(*) FROM read_parquet('{target.as_posix()}')").fetchone()[0]
    return {"name": "averias", "rows": rows,
            "columns": len(con.sql(
                f"SELECT * FROM read_parquet('{target.as_posix()}') LIMIT 0").columns),
            "kb_on_disk": round(target.stat().st_size / 1024, 1),
            "kb_downloaded": round(gzipped_size(target) / 1024, 1)}


def main() -> None:
    if not BRONZE.exists():
        raise SystemExit("Bronze layer missing. Run src/ingest/bronze.py first.")

    SAMPLES.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect()

    shipped, problems = [], []
    for name, spec in SHIPPED.items():
        row = write(con, name, spec["columns"], spec["where"])
        row["para"] = spec["para"]
        shipped.append(row)
        problems += agrees_with_lake(con, name, spec)
    shipped.append(write_reports(con))

    print("  muestra                     filas    cols   en disco   se descarga   para")
    for row in shipped:
        print(f"  {row['name']:<22} {row['rows']:>9,}   {row['columns']:>4}   "
              f"{row['kb_on_disk']:>8.1f} KB  {row['kb_downloaded']:>9.1f} KB   "
              f"{row.get('para', 'módulo 12: el JOIN')}")

    # El listón con el que se compara el peso: el motor, que se baja una vez.
    engine = sum(gzipped_size(f) for f in (PROJECT / "assets" / "duckdb-wasm").iterdir()
                 if f.is_file() and f.name.startswith("duckdb-eh"))
    mayor = max(shipped, key=lambda r: r["kb_downloaded"])
    print()
    print(f"  el motor pesa {engine / 1024 / 1024:.2f} MB comprimido y se baja una sola vez")
    print(f"  la muestra más pesada, {mayor['name']}, añade {mayor['kb_downloaded'] / 1024:.2f} MB "
          f"({mayor['kb_downloaded'] * 100 / (engine / 1024):.0f} % del motor)")

    # La comprobación que decide: la muestra tiene que reproducir la cifra del
    # módulo 10, que es la que cuelga de todo el proyecto.
    ligera = SAMPLES / "sin_timestamp_ligera.parquet"
    avg = con.sql(
        f"""
        SELECT round(avg(loaded_hours), 2) FROM (
            SELECT day,
                   count(*) AS readings,
                   sum(CASE WHEN DV_eletric = 1 THEN 1 ELSE 0 END) * 10 / 3600.0 AS loaded_hours
            FROM read_parquet('{ligera.as_posix()}')
            GROUP BY day
        ) WHERE readings > 0.9 * 8640
        """
    ).fetchone()[0]
    published = json.load(io.open(PROJECT / "results" / "m10_duty_cycle.json",
                                  encoding="utf-8"))["avg_loaded_hours"]
    reproduces = abs(avg - published) < 0.005
    print(f"  la muestra ligera da {avg} h de media y el lago {published} h  ->  "
          f"{'reproduce' if reproduces else 'NO REPRODUCE'}")

    RESULTS.parent.mkdir(exist_ok=True)
    with io.open(RESULTS, "w", encoding="utf-8") as fh:
        json.dump({"muestras": shipped, "un_dia": ONE_DAY,
                   "motor_mb": round(engine / 1024 / 1024, 2),
                   "sample_avg_loaded_hours": avg, "lake_avg_loaded_hours": published,
                   "reproduces": reproduces, "coinciden_con_el_lago": not problems},
                  fh, ensure_ascii=False, indent=2)
    print(f"Escrito en {RESULTS.relative_to(PROJECT)}")

    if problems:
        print()
        for p in problems:
            print(f"  {p}")
        raise SystemExit("Alguna muestra no dice lo mismo que el lago. No se puede publicar.")
    if not reproduces:
        raise SystemExit("The sample cannot reproduce the published figure.")


if __name__ == "__main__":
    main()
