"""Nested against WITH: does writing it readably cost anything? Module 11.

The module is about readability, which sounds like the one thing in this course
with no number behind it. It has two.

  1. **The same answer.** The nested query and the WITH version get compared row
     by row, not eyeballed. A rewrite that changes the result is not a rewrite.

  2. **The same time.** Both get timed with the median of seven, and then the
     ranges get compared. If they overlap, the honest statement is that writing
     it readably costs nothing measurable, and that is the point of the module.

The second is the one worth measuring, because the reason people give for not
using WITH is always that it must be slower.

Run:  .venv\\Scripts\\python.exe src\\transform\\queries_m11.py
"""

from __future__ import annotations

import io
import json
import sys
from pathlib import Path

import duckdb

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from medir import RUNS, distinguishable, measure  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")

PROJECT = Path(__file__).resolve().parents[2]
SAMPLE = PROJECT / "assets" / "muestras" / "sin_timestamp_ligera.parquet"
RESULTS = PROJECT / "results" / "m11_por_pasos.json"

FULL_DAY = 8640

# La consulta del módulo 10, tal cual quedó: una subconsulta dentro de otra.
ANIDADA = f"""
SELECT strftime(day, '%Y-%m') AS mes,
       round(avg(horas), 2)   AS horas_de_carga
FROM (
    SELECT day,
           count(*) AS lecturas,
           sum(CASE WHEN DV_eletric = 1 THEN 1 ELSE 0 END) * 10 / 3600.0 AS horas
    FROM telemetria
    GROUP BY day
)
WHERE lecturas > 0.9 * {FULL_DAY}
GROUP BY mes
ORDER BY mes
"""

# La misma pregunta, con cada paso con su nombre.
CON_WITH = f"""
WITH por_dia AS (
    SELECT day,
           count(*) AS lecturas,
           sum(CASE WHEN DV_eletric = 1 THEN 1 ELSE 0 END) * 10 / 3600.0 AS horas
    FROM telemetria
    GROUP BY day
),
dias_completos AS (
    SELECT * FROM por_dia WHERE lecturas > 0.9 * {FULL_DAY}
)
SELECT strftime(day, '%Y-%m') AS mes,
       round(avg(horas), 2)   AS horas_de_carga
FROM dias_completos
GROUP BY mes
ORDER BY mes
"""


def pasos_con_nombre(sql: str) -> int:
    """Cuántos bloques con nombre define un WITH."""
    return sum(1 for line in sql.splitlines() if line.strip().endswith("AS ("))


def main() -> None:
    if not SAMPLE.exists():
        raise SystemExit("Falta la muestra. Corre src/site/make_sample.py primero.")

    con = duckdb.connect()
    con.execute(f"CREATE VIEW telemetria AS SELECT * FROM read_parquet('{SAMPLE.as_posix()}')")

    # 1. ¿Dicen lo mismo? Fila por fila, no a ojo.
    filas_anidada = con.sql(ANIDADA).fetchall()
    filas_with = con.sql(CON_WITH).fetchall()
    iguales = filas_anidada == filas_with

    # 2. ¿Cuesta algo escribirlo claro?
    t_anidada = measure(lambda: con.sql(ANIDADA).fetchall())
    t_with = measure(lambda: con.sql(CON_WITH).fetchall())
    hay_diferencia = distinguishable(t_anidada, t_with)

    payload = {
        "filas_del_resultado": len(filas_with),
        "dan_lo_mismo": iguales,
        "corridas": RUNS,
        "anidada": t_anidada.as_json(4),
        "con_with": t_with.as_json(4),
        "hay_diferencia_de_tiempo": hay_diferencia,
        "pasos_con_nombre": pasos_con_nombre(CON_WITH),
        "lineas_anidada": len([x for x in ANIDADA.strip().splitlines() if x.strip()]),
        "lineas_con_with": len([x for x in CON_WITH.strip().splitlines() if x.strip()]),
        "resultado": [[str(m), float(h)] for m, h in filas_with],
    }
    RESULTS.parent.mkdir(exist_ok=True)
    with io.open(RESULTS, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)

    print(f"  las dos devuelven {len(filas_with)} filas y son iguales: {iguales}")
    print(f"  anidada:   {t_anidada}")
    print(f"  con WITH:  {t_with}")
    print(f"  ¿se distinguen en tiempo? {hay_diferencia}")
    print(f"  la version con WITH define {payload['pasos_con_nombre']} pasos con nombre")
    print(f"  lineas: {payload['lineas_anidada']} anidada contra "
          f"{payload['lineas_con_with']} con WITH")
    print(f"  escrito en {RESULTS.relative_to(PROJECT)}")

    if not iguales:
        raise SystemExit("Las dos versiones no dan lo mismo. La reescritura está mal.")


if __name__ == "__main__":
    main()
