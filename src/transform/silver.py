"""Silver: where the decisions get made, and written down. Module 14.

Bronze refused to decide anything. Silver has to decide, and the point of this
layer is that every decision leaves a trace: in code, in a column, and in a
number saying what it cost.

Three decisions, each measured rather than asserted:

  1. **Round the float noise away.** 85% of TP2's values carry more decimals
     than the sensor can possibly resolve. They get rounded to three, which is
     the precision the file actually shows, and the count of values touched gets
     recorded.
  2. **Flag the contradictions, do not delete them.** `DV_eletric` and `COMP`
     should be opposites and 16,762 readings have them equal. Deleting those
     rows would hide a sensor problem; a `dudoso` column keeps them visible.
  3. **Put everything on a regular ten second grid.** The record's clock skips:
     module 13 counted 179,426 irregular gaps. On a regular grid the holes stop
     being invisible and become rows with nothing in them, which is exactly what
     module 8 said a hole should look like.

That third one turned out to be harder than it reads, and the first attempt of
this script was wrong in an instructive way. It joined readings to the grid on
an exact timestamp match and kept 151,657 of 1,516,948, one in ten. The reason
is that **this clock does not sit on any fixed grid: it walks.** The readings
spread evenly across all ten possible second remainders, because every nine
second gap shifts the phase by one.

So each reading gets snapped to its slot, and then 12,841 of them land in a slot
already taken. Nothing gets thrown away: analogue signals in the same slot get
averaged, digital ones take the maximum (a valve open at any point in those ten
seconds was open), and a `lecturas` column records how many went in, so the
merge stays visible instead of hiding.

The assertion at the bottom is what caught the first version: silver must come
out holding every one of bronze's readings, or cleaning has become discarding.

Run:  .venv\\Scripts\\python.exe src\\transform\\silver.py
"""

from __future__ import annotations

import io
import json
import shutil
import sys
from pathlib import Path

import duckdb

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from escritura import un_solo_hilo  # noqa: E402
from medir import measure  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")

PROJECT = Path(__file__).resolve().parents[2]
BRONZE = PROJECT / "lake" / "bronze" / "telemetry"
SILVER = PROJECT / "lake" / "silver" / "telemetry"
RESULTS = PROJECT / "results" / "m14_plata.json"

# Los decimales que el sensor resuelve de verdad. Todo lo que hay por debajo es
# ruido de coma flotante, del que el módulo 9 midió el precio.
DECIMALES = 3
PASO = 10  # los segundos de la rejilla

# La ventana corta que dibuja la figura del remuestreo y cita la lección. Sus
# cuatro primeras lecturas tras el hueco son las que aparecen en el paso 8.
VENTANA = ("2020-06-12 00:55:00", "2020-06-12 00:55:30")

ANALOGICAS = ["TP2", "TP3", "H1", "DV_pressure", "Reservoirs",
              "Oil_temperature", "Motor_current"]
DIGITALES = ["COMP", "DV_eletric", "Towers", "MPG", "LPS",
             "Pressure_switch", "Oil_level", "Caudal_impulses"]


def escribe(con: duckdb.DuckDBPyConnection, borde: tuple, ordenada: bool = True) -> None:
    """La capa, escrita. `con` trae la vista `bronce`, y `borde` sus dos extremos.

    Nada se tira. Las lecturas que comparten casilla se promedian si son
    analógicas y se quedan con el máximo si son digitales, porque una válvula
    que estuvo abierta en algún momento de esos diez segundos estuvo abierta. Y
    `lecturas` guarda cuántas había, para que la fusión quede a la vista en vez
    de esconderse.

    En orden de tiempo y con un solo hilo, que es lo que el módulo 29 descubrió
    que hacía falta. Antes salía sin orden y con varios hilos: cada corrida
    revolvía las mismas filas de otra manera y en otros ficheros, eso movía medias
    en su último decimal, y la capa pesaba unos 24 MB en vez de 21,88. El orden
    arregla las medias y el tamaño; el hilo único, que los bytes se repitan.
    `ordenada=False` existe solo para que src/orchestration/hilos.py pueda medirlo.
    """
    señales = ", ".join(
        f'round(avg(b."{c}"), {DECIMALES}) AS "{c}"' for c in ANALOGICAS)
    digitales = ", ".join(f'max(b."{c}") AS "{c}"' for c in DIGITALES)

    if SILVER.exists():
        shutil.rmtree(SILVER)
    SILVER.parent.mkdir(parents=True, exist_ok=True)
    with un_solo_hilo(con):
        con.execute(f"""
        COPY (
            WITH ajustado AS (
                SELECT time_bucket(INTERVAL {PASO} SECOND, b.timestamp) AS casilla, b.*
                FROM bronce b
            ),
            fundido AS (
                SELECT casilla,
                       count(*) AS lecturas,
                       max(CASE WHEN b.DV_eletric = b.COMP THEN 1 ELSE 0 END) AS dudoso,
                       {señales},
                       {digitales}
                FROM ajustado b
                GROUP BY casilla
            ),
            rejilla AS (
                SELECT unnest(generate_series(
                    TIMESTAMP '{borde[0]}', TIMESTAMP '{borde[1]}',
                    INTERVAL {PASO} SECOND)) AS timestamp
            )
            SELECT r.timestamp,
                   CAST(r.timestamp AS DATE) AS day,
                   coalesce(f.lecturas, 0) AS lecturas,
                   f.casilla IS NOT NULL   AS medido,
                   coalesce(f.dudoso, 0) = 1 AS dudoso,
                   f.* EXCLUDE (casilla, lecturas, dudoso)
            FROM rejilla r
            LEFT JOIN fundido f ON f.casilla = r.timestamp
            {"ORDER BY r.timestamp" if ordenada else ""}
        )
        TO '{SILVER.as_posix()}'
        (FORMAT PARQUET, PARTITION_BY (day), OVERWRITE_OR_IGNORE, COMPRESSION ZSTD)
    """)


def construye() -> dict:
    """La capa escrita una sola vez y sin cronómetro, que es lo que orquesta el módulo 29.

    Comprueba lo mismo que `main()` al terminar: que no se pierde ni una lectura
    y que la rejilla tiene las casillas que debe. Lo demás que mide `main()` es
    material de la lección del módulo 14, y la regla del orquestador es que lo
    que corre dé lo mismo cada vez: un cronómetro nunca lo da.
    """
    con = duckdb.connect()
    con.execute(f"CREATE VIEW bronce AS "
                f"SELECT * FROM read_parquet('{BRONZE.as_posix()}/**/*.parquet')")
    borde = con.sql("SELECT min(timestamp), max(timestamp) FROM bronce").fetchone()
    escribe(con, borde)

    filas_bronce = con.sql("SELECT count(*) FROM bronce").fetchone()[0]
    casillas = con.sql(f"""
        SELECT CAST(date_diff('second', min(timestamp), max(timestamp)) / {PASO} + 1 AS BIGINT)
        FROM bronce
    """).fetchone()[0]
    filas, conservadas, huecos = con.sql(
        f"SELECT count(*), sum(lecturas), count(*) FILTER (WHERE NOT medido) "
        f"FROM read_parquet('{SILVER.as_posix()}/**/*.parquet')").fetchone()
    con.close()
    if conservadas != filas_bronce:
        raise SystemExit(f"La plata perdió lecturas: conserva {conservadas:,} de "
                         f"{filas_bronce:,}. Limpiar no es tirar.")
    if filas != casillas:
        raise SystemExit("La rejilla no tiene las casillas que debería.")
    return {"filas": filas, "lecturas": conservadas, "huecos": huecos}


def main() -> None:
    if not BRONZE.exists():
        raise SystemExit("Falta el bronce. Corre src/ingest/bronze.py primero.")

    con = duckdb.connect()
    con.execute(f"CREATE VIEW bronce AS "
                f"SELECT * FROM read_parquet('{BRONZE.as_posix()}/**/*.parquet')")

    filas_bronce = con.sql("SELECT count(*) FROM bronce").fetchone()[0]

    # --- Lo que cada decisión va a costar, antes de tomarla ---------------
    redondeo = {c: con.sql(f'SELECT count(*) FROM bronce WHERE "{c}" <> round("{c}", {DECIMALES})'
                           ).fetchone()[0] for c in ANALOGICAS}
    contradictorias = con.sql(
        "SELECT count(*) FROM bronce WHERE DV_eletric = COMP").fetchone()[0]

    borde = con.sql("SELECT min(timestamp), max(timestamp) FROM bronce").fetchone()
    casillas = con.sql(f"""
        SELECT CAST(date_diff('second', min(timestamp), max(timestamp)) / {PASO} + 1 AS BIGINT)
        FROM bronce
    """).fetchone()[0]

    # El reloj del registro no cae en ninguna rejilla fija: camina. Las lecturas
    # se reparten por igual entre los diez restos posibles de segundo, así que
    # cruzar por marca de tiempo exacta solo casaría una de cada diez. Hay que
    # ajustar cada lectura a su casilla, y entonces algunas caen en la misma.
    colisiones = con.sql(f"""
        SELECT count(*) - count(DISTINCT casilla)
        FROM (SELECT time_bucket(INTERVAL {PASO} SECOND, timestamp) AS casilla FROM bronce)
    """).fetchone()[0]

    # --- La capa, escrita ------------------------------------------------
    escrito = measure(lambda: escribe(con, borde), runs=3)

    con.execute(f"CREATE VIEW plata AS "
                f"SELECT * FROM read_parquet('{SILVER.as_posix()}/**/*.parquet')")
    resumen = con.sql("""
        SELECT count(*) AS filas,
               sum(CASE WHEN medido THEN 1 ELSE 0 END) AS ocupadas,
               sum(CASE WHEN NOT medido THEN 1 ELSE 0 END) AS huecos,
               sum(CASE WHEN dudoso THEN 1 ELSE 0 END) AS dudosas,
               sum(lecturas) AS lecturas_conservadas
        FROM plata
    """).fetchone()

    mb_bronce = sum(f.stat().st_size for f in BRONZE.rglob("*.parquet")) / 1024 / 1024
    mb_plata = sum(f.stat().st_size for f in SILVER.rglob("*.parquet")) / 1024 / 1024

    # Lo que cuestan de verdad los huecos: la misma plata sin sus casillas vacías,
    # escrita igual y en una carpeta aparte que se borra al terminar. Hasta el
    # módulo 29 esta lección restaba plata menos bronce y llamaba a eso el precio
    # de los huecos, y la resta mezclaba tres cosas: los huecos, el redondeo y
    # cómo troceaba los ficheros el escritor en paralelo.
    sin_huecos = PROJECT / "lake" / "_plata_sin_huecos"
    shutil.rmtree(sin_huecos, ignore_errors=True)
    with un_solo_hilo(con):
        con.execute(f"""
            COPY (SELECT * FROM plata WHERE medido ORDER BY timestamp)
            TO '{sin_huecos.as_posix()}'
            (FORMAT PARQUET, PARTITION_BY (day), OVERWRITE_OR_IGNORE, COMPRESSION ZSTD)
        """)
    mb_sin_huecos = sum(f.stat().st_size for f in sin_huecos.rglob("*.parquet")) / 1024 / 1024
    shutil.rmtree(sin_huecos)

    # La ventana que dibuja la figura y cita la lección, medida aquí para que
    # sus números tengan una corrida detrás como todos los demás. Leerlos del
    # gráfico sería justo lo que este curso no hace.
    ventana = con.sql(f"""
        SELECT min(TP2) AS primera, max(TP2) AS ultima, count(*) AS casillas
        FROM plata
        WHERE medido
          AND timestamp BETWEEN TIMESTAMP '{VENTANA[0]}' AND TIMESTAMP '{VENTANA[1]}'
    """).fetchone()

    payload = {
        "filas_bronce": filas_bronce,
        "decimales": DECIMALES,
        "paso_segundos": PASO,
        "valores_redondeados": redondeo,
        "valores_redondeados_TP2": redondeo["TP2"],
        "por_ciento_TP2_con_ruido": round(redondeo["TP2"] * 100 / filas_bronce, 1),
        "lecturas_contradictorias": contradictorias,
        "colisiones_al_ajustar": colisiones,
        "por_ciento_contradictorias": round(contradictorias * 100 / filas_bronce, 2),
        "casillas_de_la_rejilla": casillas,
        "filas_plata": resumen[0],
        "casillas_ocupadas": resumen[1],
        "lecturas_conservadas": resumen[4],
        "huecos": resumen[2],
        "por_ciento_de_huecos": round(resumen[2] * 100 / resumen[0], 1),
        "filas_dudosas": resumen[3],
        "mb_bronce": round(mb_bronce, 2),
        "mb_plata": round(mb_plata, 2),
        "mb_plata_sin_huecos": round(mb_sin_huecos, 2),
        "mb_que_cuestan_los_huecos": round(mb_plata - mb_sin_huecos, 2),
        "mb_de_la_plata_menos_el_bronce": round(mb_plata - mb_bronce, 2),
        "escribir": escrito.as_json(2),
        "ventana_desde": VENTANA[0],
        "ventana_hasta": VENTANA[1],
        "ventana_presion_primera": ventana[0],
        "ventana_presion_ultima": ventana[1],
        "ventana_casillas_con_dato": ventana[2],
    }
    RESULTS.parent.mkdir(exist_ok=True)
    with io.open(RESULTS, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)

    print(f"  el bronce trae {filas_bronce:,} lecturas")
    print()
    print(f"  1. redondear a {DECIMALES} decimales toca:")
    for c, n in sorted(redondeo.items(), key=lambda x: -x[1]):
        print(f"       {c:<18} {n:>9,} valores ({n * 100 / filas_bronce:.1f} %)")
    print(f"  2. marcar las contradictorias: {contradictorias:,} "
          f"({payload['por_ciento_contradictorias']} %)")
    print(f"  3. la rejilla de {PASO} s tiene {casillas:,} casillas, y al ajustar")
    print(f"     las lecturas a ellas hay {colisiones:,} que caen en una ya ocupada")
    print()
    print(f"  la plata queda con {resumen[0]:,} filas:")
    print(f"       ocupadas {resumen[1]:>9,}  (con {resumen[4]:,} lecturas dentro)")
    print(f"       huecos   {resumen[2]:>9,}  ({payload['por_ciento_de_huecos']} %)")
    print(f"       dudosas  {resumen[3]:>9,}")
    print(f"  y ocupa {mb_plata:.2f} MB contra los {mb_bronce:.2f} del bronce")
    print(f"  sin sus casillas vacías ocuparía {mb_sin_huecos:.2f}: los huecos cuestan "
          f"{mb_plata - mb_sin_huecos:.2f} MB")
    print(f"  la ventana de la figura sube de {ventana[0]} a {ventana[1]} bar "
          f"en {ventana[2]} casillas")
    print(f"  escrito en {RESULTS.relative_to(PROJECT)}")

    # Lo que la capa promete, comprobado.
    if resumen[4] != filas_bronce:
        raise SystemExit(f"La plata perdió lecturas: conserva {resumen[4]:,} de "
                         f"{filas_bronce:,}. Limpiar no es tirar.")
    if resumen[0] != casillas:
        raise SystemExit("La rejilla no tiene las casillas que debería.")


if __name__ == "__main__":
    main()
