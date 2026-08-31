"""The first whole query: pick columns, filter rows, order, cut. Module 8.

Four things the reader has never done, measured on the real compressor:

  1. What filtering 1.5 million rows actually costs. The lesson's figure.
  2. Where the low pressure alarm fires, and on which days most.
  3. The two days that are missing from the record entirely, which is where the
     difference between "zero" and "nothing" stops being a definition.
  4. What each of those two answers to a question about a day that is not there.

The third is the one worth the module. This file holds no NULL anywhere: every
column of every row has a value. So the emptiness cannot be taught by pointing
at a hole in the data, because there is none. It gets taught where the hole
really is, which is the calendar.

Run:  .venv\\Scripts\\python.exe src\\transform\\queries_m08.py
"""

from __future__ import annotations

import io
import json
import sys
from pathlib import Path

import duckdb

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from medir import RUNS, measure  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")

PROJECT = Path(__file__).resolve().parents[2]
SAMPLE = PROJECT / "assets" / "muestras" / "sql.parquet"
LAKE = (PROJECT / "lake" / "bronze" / "telemetry").as_posix()
RESULTS = PROJECT / "results" / "m08_primera_consulta.json"

FIRST_DAY, LAST_DAY = "2020-02-01", "2020-09-01"


def main() -> None:
    if not SAMPLE.exists():
        raise SystemExit("Falta la muestra. Corre src/site/make_sample.py primero.")

    con = duckdb.connect()
    con.execute(f"CREATE VIEW t AS SELECT * FROM read_parquet('{SAMPLE.as_posix()}')")

    rows = con.sql("SELECT count(*) FROM t").fetchone()[0]

    # 1. Lo que cuesta filtrar. Es la cifra del módulo, así que mediana de siete.
    filtrar = measure(lambda: con.sql("SELECT count(*) FROM t WHERE LPS = 1").fetchone()[0])
    contar_todo = measure(lambda: con.sql("SELECT count(*) FROM t").fetchone()[0])

    # 2. La alarma de baja presión.
    con_alarma = filtrar.result
    dias_con_alarma = con.sql("SELECT count(DISTINCT day) FROM t WHERE LPS = 1").fetchone()[0]
    dias_totales = con.sql("SELECT count(DISTINCT day) FROM t").fetchone()[0]
    peores = con.sql("""
        SELECT day, count(*) AS lecturas
        FROM t WHERE LPS = 1
        GROUP BY day ORDER BY lecturas DESC LIMIT 5
    """).fetchall()
    # Los 95 días, no solo los cinco peores. La figura pinta la intensidad de
    # cada día, y con solo cinco parecería que la alarma saltó cinco veces.
    por_dia = con.sql("""
        SELECT day, count(*) AS lecturas
        FROM t WHERE LPS = 1
        GROUP BY day ORDER BY day
    """).fetchall()

    # 3. Los días que no están. El registro tiene 212 días y el periodo 214.
    faltan = con.sql(f"""
        WITH calendario AS (
            SELECT unnest(generate_series(DATE '{FIRST_DAY}', DATE '{LAST_DAY}',
                                          INTERVAL 1 DAY))::DATE AS dia
        )
        SELECT dia FROM calendario
        WHERE dia NOT IN (SELECT DISTINCT day FROM t)
        ORDER BY dia
    """).fetchall()
    dias_calendario = con.sql(f"""
        SELECT count(*) FROM (
            SELECT unnest(generate_series(DATE '{FIRST_DAY}', DATE '{LAST_DAY}',
                                          INTERVAL 1 DAY)) AS d)
    """).fetchone()[0]

    # 4. Lo que contesta cada función cuando no hay ni una fila que mirar.
    #    count devuelve cero y avg devuelve nada, y esa diferencia es el módulo.
    ausente = str(faltan[0][0])
    vacio = con.sql(f"""
        SELECT count(*)      AS cuantas,
               avg(TP2)      AS presion_media,
               min(TP2)      AS presion_minima,
               sum(LPS)      AS alarmas
        FROM t WHERE day = DATE '{ausente}'
    """).fetchone()

    # Y la trampa que se sigue de ello: NULL no se compara con el igual.
    nulos_con_igual = con.sql(
        "SELECT count(*) FROM (SELECT NULL AS x) WHERE x = NULL").fetchone()[0]
    nulos_con_is = con.sql(
        "SELECT count(*) FROM (SELECT NULL AS x) WHERE x IS NULL").fetchone()[0]

    # 5. Un ORDER BY que empata no ordena del todo.
    #
    #    `ORDER BY day LIMIT 5` pide cinco filas de entre las miles que comparten
    #    día, y no dice cuáles. El motor devuelve las que le vienen bien, y eso
    #    cambia entre corridas. Se mide en vez de advertirlo, porque es la clase
    #    de fallo que uno no se cree hasta que lo ve.
    def corre(sql: str):
        aparte = duckdb.connect()
        aparte.execute(f"CREATE VIEW t AS SELECT * FROM read_parquet('{LAKE}/**/*.parquet')")
        filas = tuple(aparte.sql(sql).fetchall())
        aparte.close()
        return filas

    con_empates = "SELECT day, TP2, LPS FROM t WHERE LPS = 1 ORDER BY day LIMIT 5"
    sin_empates = "SELECT day, TP2, LPS FROM t WHERE LPS = 1 ORDER BY TP2 DESC LIMIT 5"
    vueltas = 8
    distintos_con = len({corre(con_empates) for _ in range(vueltas)})
    distintos_sin = len({corre(sin_empates) for _ in range(vueltas)})

    payload = {
        "filas": rows,
        "corridas": RUNS,
        "filtrar": filtrar.as_json(4),
        "contar_todo": contar_todo.as_json(4),
        "lecturas_con_alarma": con_alarma,
        "por_ciento_con_alarma": round(con_alarma / rows * 100, 3),
        "dias_con_alarma": dias_con_alarma,
        "dias_totales": dias_totales,
        "por_ciento_de_dias_con_alarma": round(dias_con_alarma / dias_totales * 100),
        "peores_dias": [{"dia": str(d), "lecturas": n} for d, n in peores],
        "alarmas_por_dia": [{"dia": str(d), "lecturas": n} for d, n in por_dia],
        "dias_del_calendario": dias_calendario,
        "dias_que_faltan": [str(d[0]) for d in faltan],
        "cuantos_faltan": len(faltan),
        "dia_ausente": ausente,
        "vacio_cuantas": vacio[0],
        "vacio_presion_media": vacio[1],
        "vacio_presion_minima": vacio[2],
        "vacio_alarmas": vacio[3],
        "filas_con_igual_null": nulos_con_igual,
        "filas_con_is_null": nulos_con_is,
        "corridas_del_orden": vueltas,
        "resultados_distintos_ordenando_por_dia": distintos_con,
        "resultados_distintos_ordenando_por_presion": distintos_sin,
    }
    RESULTS.parent.mkdir(exist_ok=True)
    with io.open(RESULTS, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)

    print(f"  {rows:,} filas en la muestra")
    print(f"  filtrar por la alarma: {filtrar}")
    print(f"  contar sin filtrar:    {contar_todo}")
    print()
    print(f"  la alarma salta en {con_alarma:,} lecturas, el "
          f"{payload['por_ciento_con_alarma']} % del registro")
    print(f"  repartidas en {dias_con_alarma} de los {dias_totales} días "
          f"({payload['por_ciento_de_dias_con_alarma']} %)")
    for d, n in peores:
        print(f"    {d}  {n:>4} lecturas con la alarma activa")
    print()
    print(f"  el periodo tiene {dias_calendario} días de calendario y el registro "
          f"{dias_totales}: faltan {len(faltan)}")
    print(f"    {', '.join(str(d[0]) for d in faltan)}")
    print(f"  preguntando por el {ausente}, que no está:")
    print(f"    count(*) devuelve {vacio[0]}, avg(TP2) devuelve {vacio[1]}, "
          f"sum(LPS) devuelve {vacio[3]}")
    print(f"  y una fila con NULL: con «= NULL» salen {nulos_con_igual}, "
          f"con «IS NULL» sale {nulos_con_is}")
    print()
    print(f"  la misma consulta, {vueltas} veces sobre los mismos datos:")
    print(f"    ordenando por día (hay empates):   {distintos_con} resultados distintos")
    print(f"    ordenando por presión (sin empates): {distintos_sin} resultado")
    print()
    print(f"  escrito en {RESULTS.relative_to(PROJECT)}")

    # Lo que el módulo afirma, comprobado en vez de supuesto.
    if vacio[0] != 0 or vacio[1] is not None:
        raise SystemExit("Un día ausente tendría que dar count 0 y avg NULL. No lo hace.")
    if nulos_con_igual != 0 or nulos_con_is != 1:
        raise SystemExit("La comparación con NULL no se comporta como dice la lección.")
    if distintos_sin != 1:
        raise SystemExit("La consulta que la lección publica no es reproducible. "
                         "Sin eso no se puede publicar su salida.")


if __name__ == "__main__":
    main()
