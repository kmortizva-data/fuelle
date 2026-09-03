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

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "transform"))

from table_format import CICLO, PASO, PLATA_CON_EL_FALLO  # noqa: E402

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
        "columns": ["timestamp", "day", "DV_eletric", "COMP", "Motor_current", "TP3"],
        "where": f"day = DATE '{ONE_DAY}'",
        "para": "módulos 13, 24 y 25: ventanas, y la física del depósito",
        "por_que": ("comparar con la fila de al lado exige la hora exacta, y la hora "
                    "cuesta 5,16 MB si se lleva el lago entero. Un día son 43 KB. "
                    "TP3 se le añadió para la parte 6 en vez de publicar otra muestra: "
                    "un día de presión son unos 9 KB, y otro fichero repetiría el "
                    "timestamp, que es la columna cara"),
    },
}

# La tabla pequeña de los partes de avería, para el JOIN del módulo 12.
EXTRA = {"averias": REPORTS}

# El módulo 15 cruza fuentes de frecuencias distintas, así que se lleva las dos
# por separado: si llegaran ya cruzadas, su reto no tendría nada que hacer. Las
# dos van a la hora, que es el ritmo de la más lenta.
POR_HORA = {
    "clima": """
        SELECT hora, temperatura, humedad, lluvia
        FROM read_parquet('{weather}/**/*.parquet')
        ORDER BY hora
    """,
    "horas": """
        SELECT time_bucket(INTERVAL 1 HOUR, timestamp) AS hora,
               round(avg(Oil_temperature), 2) AS aceite,
               round(avg(CASE WHEN DV_eletric = 1 THEN 1.0 ELSE 0.0 END), 4) AS carga,
               count(*) AS lecturas
        FROM read_parquet('{silver}/**/*.parquet')
        WHERE medido
        GROUP BY hora ORDER BY hora
    """,
}


# Las dos versiones de la tabla de oro del módulo 18. El navegador del lector no
# tiene ni la extensión Delta ni la Iceberg, así que no puede viajar en el
# tiempo ahí. Lo que sí puede es tener las dos versiones delante y cruzarlas,
# que es la habilidad que importa. La lección lo declara.
#
# Las consultas se importan de table_format.py para que la muestra y el lago no
# se puedan separar: si allí cambia el agregado, aquí cambia solo.
VERSIONES = {
    "antes": CICLO.format(plata="{fallo}", paso=PASO),
    "ahora": CICLO.format(plata="plata WHERE medido", paso=PASO),
}


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
        # Explícito y no deducido del recuento: una muestra puede tener menos
        # filas que la telemetría por ser de otro grano, como las horarias del
        # módulo 15, sin recortar nada. Lo que obliga a filtrar por día es
        # recortar filas, no tener pocas.
        "recorta_filas": bool(where),
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


def write_por_hora(con: duckdb.DuckDBPyConnection) -> list[dict]:
    """Las dos tablas horarias del módulo 15, si el lago las tiene."""
    weather = PROJECT / "lake" / "bronze" / "weather"
    silver = PROJECT / "lake" / "silver" / "telemetry"
    if not (weather.exists() and silver.exists()):
        return []
    out = []
    for nombre, sql in POR_HORA.items():
        target = SAMPLES / f"{nombre}.parquet"
        con.execute(f"COPY ({sql.format(weather=weather.as_posix(), silver=silver.as_posix())}) "
                    f"TO '{target.as_posix()}' (FORMAT PARQUET, COMPRESSION ZSTD)")
        rows = con.sql(f"SELECT count(*) FROM read_parquet('{target.as_posix()}')").fetchone()[0]
        cols = len(con.sql(
            f"SELECT * FROM read_parquet('{target.as_posix()}') LIMIT 0").columns)
        out.append({"name": nombre, "rows": rows, "columns": cols,
                    "kb_on_disk": round(target.stat().st_size / 1024, 1),
                    "kb_downloaded": round(gzipped_size(target) / 1024, 1),
                    "recorta_filas": False,
                    "para": "módulo 15: cruzar fuentes de distinta frecuencia"})
    return out


_VERSIONES_SQL: dict[str, str] = {}


def versiones_sql(bronze: Path, silver: Path) -> dict[str, str]:
    """Las dos consultas de las versiones, con las rutas del lago ya puestas.

    El resultado se guarda porque averiguar los bordes del registro cuesta una
    pasada por el bronce entero, y `check_muestras` llama a esto una vez por
    lección. Sin la caché, la puerta pasaba de segundos a minutos.
    """
    if _VERSIONES_SQL:
        return dict(_VERSIONES_SQL)
    con = duckdb.connect()
    con.execute(f"CREATE VIEW bronce AS "
                f"SELECT * FROM read_parquet('{bronze.as_posix()}/**/*.parquet')")
    borde = con.sql("SELECT min(timestamp), max(timestamp) FROM bronce").fetchone()
    con.close()
    fallo = PLATA_CON_EL_FALLO.format(desde=borde[0], hasta=borde[1], paso=PASO)
    _VERSIONES_SQL.update({nombre: sql.format(fallo=fallo) if "{fallo}" in sql else sql
                           for nombre, sql in VERSIONES.items()})
    return dict(_VERSIONES_SQL)


def write_versiones(con: duckdb.DuckDBPyConnection) -> list[dict]:
    """Las dos versiones de la tabla de oro, para el reto del módulo 18."""
    silver = PROJECT / "lake" / "silver" / "telemetry"
    if not silver.exists():
        return []
    con.execute(f"CREATE OR REPLACE VIEW bronce AS "
                f"SELECT * FROM read_parquet('{BRONZE.as_posix()}/**/*.parquet')")
    con.execute(f"CREATE OR REPLACE VIEW plata AS "
                f"SELECT * FROM read_parquet('{silver.as_posix()}/**/*.parquet')")
    out = []
    for nombre, sql in versiones_sql(BRONZE, silver).items():
        target = SAMPLES / f"{nombre}.parquet"
        con.execute(f"COPY ({sql}) TO '{target.as_posix()}' "
                    f"(FORMAT PARQUET, COMPRESSION ZSTD)")
        rows = con.sql(f"SELECT count(*) FROM read_parquet('{target.as_posix()}')").fetchone()[0]
        cols = len(con.sql(
            f"SELECT * FROM read_parquet('{target.as_posix()}') LIMIT 0").columns)
        out.append({"name": nombre, "rows": rows, "columns": cols,
                    "kb_on_disk": round(target.stat().st_size / 1024, 1),
                    "kb_downloaded": round(gzipped_size(target) / 1024, 1),
                    "recorta_filas": False,
                    "para": "módulo 18: las dos versiones, para cruzarlas"})
    return out


def write_reports(con: duckdb.DuckDBPyConnection) -> dict:
    """Los cuatro partes de avería, tal cual están escritos, para el JOIN."""
    target = SAMPLES / "averias.parquet"
    con.execute(
        f"COPY (SELECT * FROM read_csv_auto('{REPORTS.as_posix()}')) "
        f"TO '{target.as_posix()}' (FORMAT PARQUET, COMPRESSION ZSTD)")
    rows = con.sql(f"SELECT count(*) FROM read_parquet('{target.as_posix()}')").fetchone()[0]
    return {"name": "averias", "rows": rows, "recorta_filas": False,
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
    shipped += write_por_hora(con)
    shipped += write_versiones(con)

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
