"""Las quince señales, clasificadas por lo que hacen y no por lo que dice la ficha.

Módulo 2. La ficha oficial dice que hay siete analógicas y ocho digitales, y
además dice cuál es cuál. Este script no lo cree: cuenta los valores distintos
de cada columna y deja que el dato se clasifique solo.

Una señal que solo toma dos valores es digital, diga lo que diga el papel. Una
que toma miles es analógica. Y si alguna cae en medio, eso es justo lo que hay
que mirar antes de seguir.

Correr:  .venv\\Scripts\\python.exe src\\ingest\\describe_signals.py
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
RESULTS = PROJECT / "results" / "m02_signals.json"

# Lo que la ficha oficial declara, para poder contrastarlo.
FICHA = {
    "TP2": "analógica", "TP3": "analógica", "H1": "analógica",
    "DV_pressure": "analógica", "Reservoirs": "analógica",
    "Oil_temperature": "analógica", "Motor_current": "analógica",
    "COMP": "digital", "DV_eletric": "digital", "Towers": "digital",
    "MPG": "digital", "LPS": "digital", "Pressure_switch": "digital",
    "Oil_level": "digital", "Caudal_impulses": "digital",
}


def main() -> None:
    if not BRONZE.exists():
        raise SystemExit("Falta la capa bronce. Corre src/ingest/bronze.py")

    con = duckdb.connect()
    con.execute(
        f"CREATE VIEW t AS SELECT * FROM read_parquet('{BRONZE.as_posix()}/**/*.parquet')"
    )

    filas = []
    for señal in FICHA:
        distintos, minimo, maximo = con.sql(
            f'SELECT count(DISTINCT "{señal}"), min("{señal}"), max("{señal}") FROM t'
        ).fetchone()
        # La regla, y es toda la clasificación: dos valores o menos es digital.
        medido = "digital" if distintos <= 2 else "analógica"
        filas.append({
            "señal": señal,
            "valores_distintos": distintos,
            "min": round(float(minimo), 3),
            "max": round(float(maximo), 3),
            "segun_la_ficha": FICHA[señal],
            "segun_el_dato": medido,
            "coinciden": medido == FICHA[señal],
        })

    print("  señal              distintos        min        max   ficha       dato")
    for f in filas:
        marca = "" if f["coinciden"] else "   <- no coinciden"
        print(f"  {f['señal']:<17} {f['valores_distintos']:>9,} {f['min']:>10.2f} "
              f"{f['max']:>10.2f}   {f['segun_la_ficha']:<10} {f['segun_el_dato']:<10}{marca}")

    analogicas = [f for f in filas if f["segun_el_dato"] == "analógica"]
    digitales = [f for f in filas if f["segun_el_dato"] == "digital"]
    discrepan = [f for f in filas if not f["coinciden"]]

    resultados = {
        "señales": filas,
        "n_analogicas_medidas": len(analogicas),
        "n_digitales_medidas": len(digitales),
        "n_discrepancias": len(discrepan),
        "discrepancias": [f["señal"] for f in discrepan],
    }
    RESULTS.parent.mkdir(exist_ok=True)
    with io.open(RESULTS, "w", encoding="utf-8") as fh:
        json.dump(resultados, fh, ensure_ascii=False, indent=2)

    print()
    print(f"  medidas: {len(analogicas)} analógicas, {len(digitales)} digitales")
    print(f"  la ficha dice: 7 analógicas, 8 digitales")
    if discrepan:
        print(f"  DISCREPAN {len(discrepan)}: {', '.join(f['señal'] for f in discrepan)}")
    else:
        print("  coinciden todas")
    print(f"  escrito en {RESULTS.relative_to(PROJECT)}")


if __name__ == "__main__":
    main()
