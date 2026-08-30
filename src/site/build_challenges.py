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
SAMPLE = PROJECT / "assets" / "muestras" / "sin_timestamp_ligera.parquet"
RESULTS = PROJECT / "results" / "retos.json"

SECONDS_PER_READING = 10
FULL_DAY_READINGS = 8640

CHALLENGES = {
    # Módulo 13: agrupar. El reto pide el promedio mes a mes, que obliga a
    # agrupar dos veces: primero por día para tener las horas, y luego por mes.
    "m13_horas_por_mes": f"""
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
}


def plain(value):
    """Lo que JSON sabe escribir y JavaScript sabe comparar."""
    if hasattr(value, "isoformat"):
        return value.isoformat()[:10]
    if isinstance(value, (int, float, str)) or value is None:
        return value
    return str(value)


def main() -> None:
    if not SAMPLE.exists():
        raise SystemExit("Falta la muestra. Corre src/site/make_sample.py primero.")

    con = duckdb.connect()
    con.execute(
        f"CREATE VIEW telemetria AS SELECT * FROM read_parquet('{SAMPLE.as_posix()}')"
    )

    answers = {}
    for key, sql in CHALLENGES.items():
        result = con.sql(sql)
        columns = list(result.columns)
        rows = [[plain(v) for v in row] for row in result.fetchall()]
        answers[key] = {"columns": columns, "rows": rows, "sql": " ".join(sql.split())}
        print(f"  {key:<24} {len(rows)} filas, {len(columns)} columnas")
        for row in rows[:3]:
            print(f"      {row}")
        if len(rows) > 3:
            print(f"      ... y {len(rows) - 3} más")

    RESULTS.parent.mkdir(exist_ok=True)
    with io.open(RESULTS, "w", encoding="utf-8") as fh:
        json.dump(answers, fh, ensure_ascii=False, indent=2)
    print()
    print(f"Escrito en {RESULTS.relative_to(PROJECT)}")


if __name__ == "__main__":
    main()
