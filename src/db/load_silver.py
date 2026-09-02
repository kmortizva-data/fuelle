"""Loads the silver layer into PostgreSQL, and measures what changed. Module 19.

Until now the database was a file: DuckDB opens it, answers, and closes. From
here it is a service, and the module's job is to make the difference concrete
rather than describe it.

Three things get measured, all with `medir.measure` and its median of seven:

  1. **Loading the same 1,841,760 rows into the server.** A file gets read where
     it lies; a server has to be handed every row over a connection. That is the
     cost of the thing that a file never charges you.
  2. **The same analytical question, asked of both.** Hours loaded per day, which
     is the number this whole project hangs from.
  3. **What each of them takes on disk** for the same data.

The table is deliberately naive: no primary key, no constraints, no indexes.
That is not an oversight, it is module 20's opening. Right now this database
would happily accept a duplicated timestamp or a negative pressure, exactly like
the Parquet did, and the next module is about telling it what is impossible.

Run:  .venv\\Scripts\\python.exe src\\db\\load_silver.py
"""

from __future__ import annotations

import io
import json
import shutil
import sys
from pathlib import Path

import duckdb

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from db.servidor import BASE, DATOS, PUERTO, conecta, servidor  # noqa: E402
from medir import distinguishable, measure, times_slower  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")

PROJECT = Path(__file__).resolve().parents[2]
SILVER = PROJECT / "lake" / "silver" / "telemetry"
TRABAJO = PROJECT / "lake" / "_pg"
CSV = TRABAJO / "plata.csv"
RESULTS = PROJECT / "results" / "m19_postgres.json"

# Las columnas de la plata, con el tipo que les toca en PostgreSQL. Aquí no hay
# ni clave ni restricciones a propósito: eso es el módulo 20.
COLUMNAS = [
    ("timestamp", "timestamptz"), ("lecturas", "integer"),
    ("medido", "boolean"), ("dudoso", "boolean"),
    ("tp2", "double precision"), ("tp3", "double precision"),
    ("h1", "double precision"), ("dv_pressure", "double precision"),
    ("reservoirs", "double precision"), ("oil_temperature", "double precision"),
    ("motor_current", "double precision"), ("comp", "double precision"),
    ("dv_eletric", "double precision"), ("towers", "double precision"),
    ("mpg", "double precision"), ("lps", "double precision"),
    ("pressure_switch", "double precision"), ("oil_level", "double precision"),
    ("caudal_impulses", "double precision"), ("day", "date"),
]

# La pregunta del proyecto, escrita igual para los dos motores.
PREGUNTA = """
    SELECT day,
           count(*) AS lecturas,
           sum(CASE WHEN dv_eletric = 1 THEN 1 ELSE 0 END) * 10 / 3600.0 AS horas
    FROM {tabla}
    WHERE medido
    GROUP BY day
    ORDER BY day
"""


def exporta_csv() -> int:
    """Saca la plata a un CSV. No se cronometra: es la preparación."""
    TRABAJO.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect()
    columnas = ", ".join(f'"{c}"' for c, _ in COLUMNAS)
    con.execute(f"""
        COPY (SELECT {columnas}
              FROM read_parquet('{SILVER.as_posix()}/**/*.parquet')
              ORDER BY timestamp)
        TO '{CSV.as_posix()}' (FORMAT CSV, HEADER)
    """)
    filas = con.sql(f"SELECT count(*) FROM "
                    f"read_parquet('{SILVER.as_posix()}/**/*.parquet')").fetchone()[0]
    con.close()
    return filas


def crea_tabla(pg) -> None:
    columnas = ", ".join(f"{n} {t}" for n, t in COLUMNAS)
    pg.execute("DROP TABLE IF EXISTS lecturas")
    pg.execute(f"CREATE TABLE lecturas ({columnas})")
    pg.commit()


def carga(pg) -> None:
    """Le pasa el CSV al servidor por la conexión, que es como se hace de verdad.

    `COPY ... FROM STDIN` y no `FROM '/ruta'` a propósito: la segunda forma
    obliga a que el fichero esté en la máquina del servidor y a tener permiso
    para leer su disco. Aquí coinciden, pero en cuanto el servidor está en otro
    sitio deja de valer, y la lección enseña la que siempre vale.
    """
    with pg.cursor() as cur, cur.copy(
            "COPY lecturas FROM STDIN WITH (FORMAT csv, HEADER)") as copia:
        with io.open(CSV, "rb") as fh:
            while bloque := fh.read(1 << 20):
                copia.write(bloque)
    pg.commit()


def tamano_en_disco(carpeta: Path) -> float:
    return sum(f.stat().st_size for f in carpeta.rglob("*") if f.is_file()) / 1024 / 1024


def main() -> None:
    if not SILVER.exists():
        raise SystemExit("Falta la plata. Corre src/transform/silver.py primero.")

    print("  sacando la plata a CSV (esto no se cronometra)")
    filas = exporta_csv()
    print(f"    {filas:,} filas, {CSV.stat().st_size / 1024 / 1024:.1f} MB de CSV")

    with servidor():
        pg = conecta()

        def prepara() -> None:
            crea_tabla(pg)

        prepara()
        carga(pg)
        en_servidor = pg.execute("SELECT count(*) FROM lecturas").fetchone()[0]
        print(f"    {en_servidor:,} filas en el servidor")
        if en_servidor != filas:
            raise SystemExit(f"El servidor tiene {en_servidor:,} y la plata {filas:,}. "
                             "La carga ha perdido filas.")

        print()
        print("  midiendo, mediana de siete:")
        cargar = measure(lambda: carga(pg), setup=prepara)
        print(f"    cargar en el servidor      {cargar.median:.2f} s "
              f"({cargar.minimum:.2f} a {cargar.maximum:.2f})")

        # --- La misma pregunta a los dos motores -------------------------
        duck = duckdb.connect()
        duck.execute(f"CREATE VIEW lecturas AS SELECT * FROM "
                     f"read_parquet('{SILVER.as_posix()}/**/*.parquet')")

        def pregunta_duckdb():
            return duck.sql(PREGUNTA.format(tabla="lecturas")).fetchall()

        def pregunta_postgres():
            with pg.cursor() as cur:
                return cur.execute(PREGUNTA.format(tabla="lecturas")).fetchall()

        en_fichero, en_servicio = pregunta_duckdb(), pregunta_postgres()
        if len(en_fichero) != len(en_servicio):
            raise SystemExit(f"DuckDB devuelve {len(en_fichero)} días y PostgreSQL "
                             f"{len(en_servicio)}. No es la misma pregunta.")

        fichero = measure(pregunta_duckdb)
        servicio = measure(pregunta_postgres)
        se_distinguen = distinguishable(fichero, servicio)
        factor = times_slower(servicio, fichero) if se_distinguen else None
        print(f"    la pregunta en el fichero  {fichero.median:.3f} s "
              f"({fichero.minimum:.3f} a {fichero.maximum:.3f})")
        print(f"    la pregunta en el servicio {servicio.median:.3f} s "
              f"({servicio.minimum:.3f} a {servicio.maximum:.3f})")
        print(f"    {'el fichero gana por ' + format(factor, '.1f') + ' veces'
                    if factor else 'no se distinguen'}")

        # --- Lo que ocupa cada uno ---------------------------------------
        # `float()` porque PostgreSQL devuelve numeric y llega como Decimal, que
        # no se divide contra un float. Es el mismo tropiezo que en `check_sql`.
        mb_tabla = float(pg.execute(
            "SELECT pg_total_relation_size('lecturas') / 1024.0 / 1024.0").fetchone()[0])
        mb_parquet = tamano_en_disco(SILVER)
        mb_base = tamano_en_disco(DATOS)
        print()
        print(f"    la plata en Parquet        {mb_parquet:>7.1f} MB")
        print(f"    la misma tabla en el server{mb_tabla:>7.1f} MB")
        print(f"    la base entera             {mb_base:>7.1f} MB")

        payload = {
            "filas": filas,
            "dias": len(en_fichero),
            "mb_del_csv_intermedio": round(CSV.stat().st_size / 1024 / 1024, 1),
            "segundos_en_cargar": round(cargar.median, 2),
            "carga_minimo": round(cargar.minimum, 2),
            "carga_maximo": round(cargar.maximum, 2),
            "mb_en_parquet": round(mb_parquet, 1),
            "mb_en_el_servidor": round(mb_tabla, 1),
            "mb_de_la_base_entera": round(mb_base, 1),
            "veces_mas_disco_el_servidor": round(mb_tabla / mb_parquet, 1),
            "pregunta": {
                "fichero": {"mediana": round(fichero.median, 4),
                            "minimo": round(fichero.minimum, 4),
                            "maximo": round(fichero.maximum, 4)},
                "servicio": {"mediana": round(servicio.median, 4),
                             "minimo": round(servicio.minimum, 4),
                             "maximo": round(servicio.maximum, 4)},
                "se_distinguen": se_distinguen,
                "veces": round(factor, 1) if factor else None,
            },
        }
        RESULTS.parent.mkdir(exist_ok=True)
        with io.open(RESULTS, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, ensure_ascii=False, indent=2)
        pg.close()

    # El CSV era un intermedio y no tiene por qué quedarse ocupando disco.
    shutil.rmtree(TRABAJO, ignore_errors=True)
    print(f"  escrito en {RESULTS.relative_to(PROJECT)}")


if __name__ == "__main__":
    main()
