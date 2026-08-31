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
}


def plain(value):
    """Lo que JSON sabe escribir y JavaScript sabe comparar."""
    if hasattr(value, "isoformat"):
        return value.isoformat()[:10]
    if isinstance(value, (int, float, str)) or value is None:
        return value
    return str(value)


def connect_to(muestra: str) -> duckdb.DuckDBPyConnection:
    path = SAMPLES / f"{muestra}.parquet"
    if not path.exists():
        raise SystemExit(f"Falta {path.name}. Corre src/site/make_sample.py primero.")
    con = duckdb.connect()
    con.execute(f"CREATE VIEW telemetria AS SELECT * FROM read_parquet('{path.as_posix()}')")
    averias = SAMPLES / "averias.parquet"
    if averias.exists():
        con.execute(f"CREATE VIEW averias AS SELECT * FROM read_parquet('{averias.as_posix()}')")
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
