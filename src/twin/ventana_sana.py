"""Is the calibration window actually healthy? Module 26.

A twin gets calibrated on a stretch of record where the machine was well, and
this course picked that stretch **by date**: everything before the first
documented failure, 18 April. Picking by date protects you from one thing, which
is choosing the data that flatters the model. It does not protect you from the
machine having been broken in a way nobody wrote down.

It was. From 1 to 12 March 2020 the compressor works between two and eight times
harder, the oil runs ten degrees hotter, the motor draws twice the current, and
on the 11th the low pressure alarm fires for the first time in the whole record.
On the 13th everything goes back. There is no failure report for any of it.

So this asks the question the calibration should have asked first: **day by day,
does this window look like one machine in one condition?** It compares four
signals that come from four different instruments, because one signal drifting is
an argument and four drifting together is a fact.

Run:  .venv\\Scripts\\python.exe src\\twin\\ventana_sana.py
"""

from __future__ import annotations

import io
import json
import sys
from pathlib import Path

import duckdb

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from twin.model import MARZO, SANO  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")

PROJECT = Path(__file__).resolve().parents[2]
SILVER = PROJECT / "lake" / "silver" / "telemetry"
RESULTS = PROJECT / "results" / "m26_ventana.json"

# Lo que abarcaba la ventana vieja, más una semana a cada lado para poder ver
# que el evento empieza y termina en vez de tener que creérselo.
DESDE, HASTA = "2020-02-01", "2020-03-22"

# Un día se declara raro si carga más del doble que la mediana de febrero. No es
# un umbral fino ni hace falta: lo que separa a marzo de febrero no es sutil.
CUANTAS_VECES = 2.0


def por_dia() -> list[dict]:
    """Las cuatro señales, día a día, sin modelo ninguno de por medio."""
    con = duckdb.connect()
    filas = con.sql(f"""
        WITH t AS (
          SELECT *, lag(DV_eletric) OVER (ORDER BY timestamp) AS antes
          FROM read_parquet('{SILVER.as_posix()}/**/*.parquet')
          WHERE medido AND day BETWEEN DATE '{DESDE}' AND DATE '{HASTA}'
        )
        SELECT day,
               count(*)                                              AS lecturas,
               round(avg(DV_eletric), 4)                             AS carga,
               round(sum(CASE WHEN antes = 0 AND DV_eletric = 1 THEN 1 ELSE 0 END)
                         / (count(*) * 10 / 3600.0), 2)              AS arranques,
               round(avg(Oil_temperature), 1)                        AS aceite,
               round(avg(Motor_current), 2)                          AS corriente,
               round(avg(LPS), 4)                                    AS lps
        FROM t GROUP BY day ORDER BY day
    """).fetchall()
    con.close()
    return [{"dia": str(f[0]), "lecturas": int(f[1]), "carga": float(f[2]),
             "arranques": float(f[3]), "aceite": float(f[4]),
             "corriente": float(f[5]), "lps": float(f[6])} for f in filas]


def huecos(desde: str, hasta: str) -> dict:
    """Cuántos cortes largos tiene el registro en un tramo, y cuánto se llevan.

    Es lo que hacía que las duraciones se midieran mal: un tramo que salta un
    hueco se lleva las horas del hueco como si el compresor las hubiera pasado
    trabajando. Va aquí para poder citarlo, no para calcular nada.
    """
    con = duckdb.connect()
    fila = con.sql(f"""
        WITH h AS (
          SELECT date_diff('second', lag(timestamp) OVER (ORDER BY timestamp),
                           timestamp) AS s
          FROM read_parquet('{SILVER.as_posix()}/**/*.parquet')
          WHERE medido AND day BETWEEN DATE '{desde}' AND DATE '{hasta}'
        )
        SELECT count(*) FILTER (WHERE s > 3600),
               round(sum(s) FILTER (WHERE s > 15) / 60.0, 0)
        FROM h WHERE s IS NOT NULL
    """).fetchone()
    con.close()
    return {"de_mas_de_una_hora": int(fila[0]),
            "minutos_sin_registro": float(fila[1])}


def resume(dias: list[dict], desde: str, hasta: str) -> dict:
    """Las cuatro señales de un tramo, en su rango, para poder comparar tramos."""
    tramo = [d for d in dias if desde <= d["dia"] <= hasta]
    return {
        "dias": len(tramo),
        "carga": [min(d["carga"] for d in tramo), max(d["carga"] for d in tramo)],
        "arranques": [min(d["arranques"] for d in tramo),
                      max(d["arranques"] for d in tramo)],
        "aceite": [min(d["aceite"] for d in tramo), max(d["aceite"] for d in tramo)],
        "corriente": [min(d["corriente"] for d in tramo),
                      max(d["corriente"] for d in tramo)],
        "lps_maximo": max(d["lps"] for d in tramo),
    }


def main() -> None:
    if not SILVER.exists():
        raise SystemExit("Falta la plata. Corre src/transform/silver.py primero.")

    dias = por_dia()
    febrero = sorted(d["carga"] for d in dias if d["dia"] <= SANO[1])
    mediana = febrero[len(febrero) // 2]
    raros = [d for d in dias if d["carga"] > mediana * CUANTAS_VECES]

    tramos = {
        "febrero, la ventana nueva": resume(dias, SANO[0], SANO[1]),
        "del 1 al 12 de marzo": resume(dias, *MARZO),
        "del 13 al 22 de marzo": resume(dias, "2020-03-13", HASTA),
    }

    print(f"  la mediana de carga en febrero es {mediana}, y el listón de raro "
          f"está en {round(mediana * CUANTAS_VECES, 4)}")
    print()
    for nombre, r in tramos.items():
        print(f"  {nombre} ({r['dias']} días)")
        print(f"    carga      {r['carga'][0]} a {r['carga'][1]}")
        print(f"    arranques  {r['arranques'][0]} a {r['arranques'][1]} por hora")
        print(f"    aceite     {r['aceite'][0]} a {r['aceite'][1]} °C")
        print(f"    corriente  {r['corriente'][0]} a {r['corriente'][1]} A")
        print(f"    LPS máximo {r['lps_maximo']}")
    print()
    print(f"  días por encima del listón: {len(raros)}")
    print(f"    del {raros[0]['dia']} al {raros[-1]['dia']}, "
          f"y son {len(set(d['dia'] for d in raros))} seguidos "
          f"salvo los que no tienen registro")

    payload = {
        "desde": DESDE, "hasta": HASTA,
        "ventana_vieja": ["2020-02-01", "2020-03-15"],
        "ventana_nueva": list(SANO),
        "evento": list(MARZO),
        "mediana_de_febrero": mediana,
        "liston": round(mediana * CUANTAS_VECES, 4),
        "dias_raros": [d["dia"] for d in raros],
        "cuantos_dias_raros": len(raros),
        "tramos": tramos,
        "huecos_de_la_ventana_vieja": huecos("2020-02-01", "2020-03-15"),
        "huecos_de_la_ventana_nueva": huecos(*SANO),
        "dias": dias,
        # Cuánto de la ventana vieja era avería, que es la cifra del tropiezo.
        "dias_de_la_ventana_vieja": sum(
            1 for d in dias if d["dia"] <= "2020-03-15"),
    }
    RESULTS.parent.mkdir(exist_ok=True)
    with io.open(RESULTS, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)
    print()
    print(f"  escrito en {RESULTS.relative_to(PROJECT)}")

    # Lo que tiene que cumplirse para que la ventana nueva valga: ni un solo día
    # de febrero por encima del listón. Si algún día lo pasara, la ventana de
    # calibración volvería a estar sucia y habría que mirarla otra vez.
    sucios = [d["dia"] for d in raros if d["dia"] <= SANO[1]]
    if sucios:
        raise SystemExit(f"La ventana nueva tiene días raros dentro: {sucios}. "
                         "No se puede calibrar con ella.")


if __name__ == "__main__":
    main()
