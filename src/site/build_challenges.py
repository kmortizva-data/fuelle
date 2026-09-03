"""Resuelve cada reto y guarda su respuesta, para que la página pueda corregir.

Ninguna respuesta se teclea a mano. Cada reto declara aquí su solución en SQL,
el script la ejecuta **contra la misma muestra que descarga el navegador**, y
guarda el resultado en results/retos.json.

Que se ejecute contra la muestra y no contra el lago entero no es un detalle: si
la muestra y el lago no dieran lo mismo, el lector resolvería bien el reto y la
página le diría que no. Por eso make_sample.py comprueba antes que la muestra
reproduce la cifra publicada.

Correr:  .venv\\Scripts\\python.exe src\\site\\build_challenges.py
"""

from __future__ import annotations

import io
import json
import sys
from pathlib import Path

import duckdb

sys.stdout.reconfigure(encoding="utf-8")

PROJECT = Path(__file__).resolve().parents[2]
SAMPLES = PROJECT / "assets" / "muestras"
RESULTS = PROJECT / "results" / "retos.json"

# Cada reto se resuelve contra LA MUESTRA DE SU MODULO, que es la que se baja el
# lector. Desde la parte 3 no todos usan la misma: el modulo 13 necesita la hora
# exacta y los demas no. Resolver un reto contra otra muestra daria una respuesta
# que el lector no puede reproducir.
MUESTRA_DE = {
    "m08_alarma_con_presion": "sql",
    "m09_horas_por_estado": "sql",
    "m10_horas_por_mes": "sin_timestamp_ligera",
    "m11_con_with": "sin_timestamp_ligera",
    "m12_lecturas_por_averia": "sql",
    "m13_paradas_del_dia": "un_dia",
    "m15_aceite_por_tramo": "horas",
    "m17_oro_por_mes": "horas",
    "m18_donde_mentia": "antes",
    "m20_quien_la_rompe": "sql",
    "m24_la_banda": "un_dia",
    "m25_cuanto_dura": "un_dia",
}

SECONDS_PER_READING = 10
FULL_DAY_READINGS = 8640

CHALLENGES = {
    # Modulo 8: la primera consulta. Dos condiciones a la vez y un orden
    # descendente, que es todo lo que la leccion ha ensenado hasta aqui.
    "m08_alarma_con_presion": """
        SELECT day, TP2, LPS
        FROM telemetria
        WHERE LPS = 1 AND TP2 > 6
        ORDER BY TP2 DESC
        LIMIT 10
    """,
    # Módulo 10: agrupar. El reto pide el promedio mes a mes, que obliga a
    # agrupar dos veces: primero por día para tener las horas, y luego por mes.
    # Modulo 9: la regla de los tres estados, pero contando horas en vez de
    # lecturas. El CASE viene dado; lo que se practica es la conversion.
    "m09_horas_por_estado": f"""
        SELECT CASE WHEN Motor_current < 1 THEN 'parado'
                    WHEN Motor_current < 5 THEN 'en vacio'
                    ELSE 'en carga' END        AS estado,
               round(count(*) * {SECONDS_PER_READING} / 3600.0, 1) AS horas
        FROM telemetria
        GROUP BY estado
        ORDER BY horas DESC
    """,
    "m10_horas_por_mes": f"""
        SELECT strftime(day, '%Y-%m')      AS mes,
               round(avg(horas), 2)        AS horas_de_carga
        FROM (
            SELECT day,
                   count(*) AS lecturas,
                   sum(CASE WHEN DV_eletric = 1 THEN 1 ELSE 0 END)
                       * {SECONDS_PER_READING} / 3600.0 AS horas
            FROM telemetria
            GROUP BY day
        )
        WHERE lecturas > 0.9 * {FULL_DAY_READINGS}
        GROUP BY mes
        ORDER BY mes
    """,
    # Modulo 11: la misma respuesta que el reto del modulo 10, pero escrita por
    # pasos. Que el resultado esperado sea identico no es casualidad: el reto
    # consiste justamente en que la reescritura no cambie nada.
    "m11_con_with": f"""
        WITH por_dia AS (
            SELECT day,
                   count(*) AS lecturas,
                   sum(CASE WHEN DV_eletric = 1 THEN 1 ELSE 0 END)
                       * {SECONDS_PER_READING} / 3600.0 AS horas
            FROM telemetria
            GROUP BY day
        ),
        dias_completos AS (
            SELECT * FROM por_dia WHERE lecturas > 0.9 * {FULL_DAY_READINGS}
        )
        SELECT strftime(day, '%Y-%m')  AS mes,
               round(avg(horas), 2)    AS horas_de_carga
        FROM dias_completos
        GROUP BY mes
        ORDER BY mes
    """,
    # Modulo 12: una fila por parte de averia, con las lecturas que caen dentro.
    # Los partes van a la IZQUIERDA del LEFT JOIN, que es lo que garantiza las
    # cuatro filas aunque alguno no tuviera ninguna lectura.
    "m12_lecturas_por_averia": """
        SELECT a.nr, a.desde, count(t.day) AS lecturas
        FROM (
            SELECT nr,
                   CAST(strptime(start_time, '%-m/%-d/%Y %-H:%M') AS DATE) AS desde,
                   CAST(strptime(end_time,   '%-m/%-d/%Y %-H:%M') AS DATE) AS hasta
            FROM averias
        ) a
        LEFT JOIN telemetria t ON t.day BETWEEN a.desde AND a.hasta
        GROUP BY a.nr, a.desde
        ORDER BY a.desde
    """,
    # Modulo 13: el cambio de estado al reves. Filtrado al dia de la muestra,
    # porque esa muestra es de un solo dia y sin el filtro la pagina diria una
    # cosa y el lago otra.
    "m13_paradas_del_dia": """
        SELECT count(*) AS paradas
        FROM (
            SELECT DV_eletric,
                   lag(DV_eletric) OVER (ORDER BY timestamp) AS antes
            FROM telemetria
            WHERE day = DATE '2020-06-05'
        )
        WHERE antes = 1 AND DV_eletric = 0
    """,
    # Modulo 15: el reto cruza las dos tablas horarias, asi que su muestra no es
    # telemetria cruda. connect_to registra las dos por su nombre.
    "m15_aceite_por_tramo": """
        SELECT CASE WHEN c.temperatura < 10 THEN 'a. menos de 10'
                    WHEN c.temperatura < 20 THEN 'b. de 10 a 20'
                    ELSE 'c. mas de 20' END AS calle,
               count(*) AS horas,
               round(avg(h.aceite), 1) AS aceite_medio
        FROM horas h
        JOIN clima c ON c.hora = h.hora
        GROUP BY calle
        ORDER BY calle
    """,
    # Modulo 17: un modelo de oro es un SELECT y nada mas. Este da un mes por
    # fila, que es otro grano distinto del de las dos tablas que cruza, y por eso
    # merece ser una tabla de oro propia en vez de una consulta suelta.
    "m17_oro_por_mes": """
        SELECT strftime(h.hora, '%Y-%m')     AS mes,
               count(*)                      AS horas,
               round(avg(h.aceite), 1)       AS aceite,
               round(avg(c.temperatura), 1)  AS calle
        FROM horas h
        JOIN clima c ON c.hora = h.hora
        GROUP BY mes
        ORDER BY mes
    """,
    # Modulo 18: las dos versiones de la misma tabla, una al lado de la otra.
    # El navegador no tiene ni la extension Delta ni la Iceberg, asi que el
    # viaje en el tiempo ya esta hecho y lo que se practica es compararlas.
    "m18_donde_mentia": """
        SELECT a.dia,
               a.horas_de_carga                               AS antes,
               b.horas_de_carga                               AS ahora,
               round(b.horas_de_carga - a.horas_de_carga, 2)  AS diferencia
        FROM antes a
        JOIN ahora b ON b.dia = a.dia
        ORDER BY diferencia DESC
        LIMIT 5
    """,
    # Modulo 20: lo que hay que hacer ANTES de anadir una restriccion, que es
    # contar quien la rompe. Si sale mas de cero, la base se niega a ponerla y
    # el problema no es la restriccion: son los datos.
    "m20_quien_la_rompe": """
        SELECT day, count(*) AS lecturas
        FROM telemetria
        WHERE DV_eletric = COMP
        GROUP BY day
        ORDER BY lecturas DESC
        LIMIT 5
    """,
    # Modulo 24: medir la banda del presostato con las propias manos. Es la
    # misma cuenta que hace src/twin/model.py sobre el lago entero, aqui sobre
    # un solo dia, y sale practicamente lo mismo.
    "m24_la_banda": """
        SELECT CASE WHEN antes = 0 THEN 'arranca' ELSE 'para' END AS momento,
               count(*)              AS veces,
               round(median(TP3), 2) AS presion
        FROM (SELECT TP3, DV_eletric,
                     lag(DV_eletric) OVER (ORDER BY timestamp) AS antes
              FROM telemetria WHERE day = DATE '2020-06-05')
        WHERE antes IS NOT NULL AND antes <> DV_eletric
        GROUP BY momento
        ORDER BY momento
    """,
    # Modulo 25: cuanto dura cada carga y cada vacio. Es lo que la simulacion
    # tiene que reproducir, y contarlo a mano da la vara de medir.
    "m25_cuanto_dura": """
        SELECT CASE WHEN cargando = 1 THEN 'carga' ELSE 'vacio' END AS estado,
               count(*)                  AS tramos,
               round(median(minutos), 2) AS minutos
        FROM (SELECT any_value(DV_eletric) AS cargando,
                     date_diff('second', min(timestamp), max(timestamp)) / 60.0 AS minutos
              FROM (SELECT timestamp, DV_eletric,
                           sum(CASE WHEN antes IS DISTINCT FROM DV_eletric THEN 1 ELSE 0 END)
                               OVER (ORDER BY timestamp) AS tramo
                    FROM (SELECT timestamp, DV_eletric,
                                 lag(DV_eletric) OVER (ORDER BY timestamp) AS antes
                          FROM telemetria WHERE day = DATE '2020-06-05'))
              GROUP BY tramo)
        GROUP BY estado
        ORDER BY estado
    """,
}


def plain(value):
    """Lo que JSON sabe escribir y JavaScript sabe comparar."""
    if hasattr(value, "isoformat"):
        return value.isoformat()[:10]
    if isinstance(value, (int, float, str)) or value is None:
        return value
    return str(value)


# Las muestras que no son telemetria cruda se registran con su propio nombre: el
# modulo 15 trabaja con `horas` y `clima`, y llamar `telemetria` a una tabla
# horaria haria ilegible cada consulta de su leccion.
POR_SU_NOMBRE = {"horas", "clima", "antes", "ahora"}


def connect_to(muestra: str) -> duckdb.DuckDBPyConnection:
    path = SAMPLES / f"{muestra}.parquet"
    if not path.exists():
        raise SystemExit(f"Falta {path.name}. Corre src/site/make_sample.py primero.")
    con = duckdb.connect()
    vista = muestra if muestra in POR_SU_NOMBRE else "telemetria"
    con.execute(f"CREATE VIEW {vista} AS SELECT * FROM read_parquet('{path.as_posix()}')")
    for extra in ("averias", "clima", "horas", "antes", "ahora"):
        otra = SAMPLES / f"{extra}.parquet"
        if extra != vista and otra.exists():
            con.execute(f"CREATE VIEW {extra} AS "
                        f"SELECT * FROM read_parquet('{otra.as_posix()}')")
    return con


def main() -> None:
    answers = {}
    for key, sql in CHALLENGES.items():
        muestra = MUESTRA_DE[key]
        con = connect_to(muestra)
        result = con.sql(sql)
        columns = list(result.columns)
        rows = [[plain(v) for v in row] for row in result.fetchall()]
        answers[key] = {"columns": columns, "rows": rows, "sql": " ".join(sql.split()),
                        "muestra": muestra}
        print(f"  {key:<26} {len(rows)} filas, {len(columns)} columnas  "
              f"(contra {muestra})")
        for row in rows[:3]:
            print(f"      {row}")
        if len(rows) > 3:
            print(f"      ... y {len(rows) - 3} más")
        con.close()

    RESULTS.parent.mkdir(exist_ok=True)
    with io.open(RESULTS, "w", encoding="utf-8") as fh:
        json.dump(answers, fh, ensure_ascii=False, indent=2)
    print()
    print(f"Escrito en {RESULTS.relative_to(PROJECT)}")


if __name__ == "__main__":
    main()
