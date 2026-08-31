"""La figura del módulo 15: tres fuentes que no laten al mismo ritmo.

Un día entero con las tres, una encima de otra y compartiendo el eje del tiempo.
Arriba la telemetría, que da un punto cada diez segundos. En medio el clima, que
da uno cada hora. Abajo los partes de avería, que dan uno cuando se rompe algo.

Ese dibujo es el problema del módulo: cruzarlas obliga a decidir qué significa
«la temperatura de la calle a las 06:00:12», y la respuesta no es la misma para
las tres.

Correr:  .venv\\Scripts\\python.exe src\\figures_module15.py
"""

from __future__ import annotations

import io
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import duckdb  # noqa: E402
import matplotlib.dates as mdates  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402

from figures_theme import (FIGURES, _style, colours, es, fingerprint,  # noqa: E402
                            guardar_huellas)

sys.stdout.reconfigure(encoding="utf-8")

PROJECT = Path(__file__).resolve().parents[1]
DATOS = PROJECT / "results" / "m15_clima.json"
SILVER = PROJECT / "lake" / "silver" / "telemetry"
WEATHER = PROJECT / "lake" / "bronze" / "weather"
FAILURES = PROJECT / "lake" / "bronze" / "failures"

# El día de la avería #3, que es el único de los cuatro donde se pueden ver las
# tres fuentes a la vez: telemetría, clima y un parte que empieza a las 10:00.
DIA = "2020-06-05"


def main() -> None:
    if not DATOS.exists():
        raise SystemExit("Falta results/m15_clima.json. Corre src/ingest/weather.py")

    d = json.loads(io.open(DATOS, encoding="utf-8").read())
    con = duckdb.connect()
    con.execute(f"CREATE VIEW plata AS "
                f"SELECT * FROM read_parquet('{SILVER.as_posix()}/**/*.parquet')")
    con.execute(f"CREATE VIEW clima AS "
                f"SELECT * FROM read_parquet('{WEATHER.as_posix()}/**/*.parquet')")
    con.execute(f"CREATE VIEW partes AS "
                f"SELECT * FROM read_parquet('{(FAILURES / 'failures.parquet').as_posix()}')")

    aceite = con.sql(f"""
        SELECT timestamp, Oil_temperature FROM plata
        WHERE day = DATE '{DIA}' AND medido ORDER BY timestamp
    """).fetchall()
    calle = con.sql(f"""
        SELECT hora, temperatura FROM clima WHERE day = DATE '{DIA}' ORDER BY hora
    """).fetchall()
    averias = con.sql(f"""
        SELECT inicio, fin, nr FROM partes
        WHERE CAST(inicio AS DATE) <= DATE '{DIA}' AND CAST(fin AS DATE) >= DATE '{DIA}'
    """).fetchall()

    name = "fig_m15_tres_frecuencias"
    FIGURES.mkdir(exist_ok=True)
    for theme in ("claro", "oscuro"):
        c = colours(theme, module=15)
        with plt.rc_context(_style(theme, c)):
            fig, ejes = plt.subplots(3, 1, figsize=(9.2, 4.4), sharex=True,
                                     gridspec_kw={"height_ratios": [3, 3, 1],
                                                  "hspace": 0.18})

            ejes[0].plot([a[0] for a in aceite], [a[1] for a in aceite],
                         linewidth=1.0, color=c["ink_faint"], zorder=3)
            ejes[0].set_ylabel("aceite, °C")
            ejes[0].annotate(f"telemetría: {es(len(aceite))} puntos, uno cada 10 s",
                             xy=(0.01, 0.86), xycoords="axes fraction",
                             fontsize=8.5, color=c["ink_soft"])

            ejes[1].step([x[0] for x in calle], [x[1] for x in calle], where="post",
                         marker="o", markersize=3, linewidth=1.2,
                         color=c["accent"], zorder=3)
            ejes[1].set_ylabel("calle, °C")
            ejes[1].annotate(f"clima: {es(len(calle))} puntos, uno cada hora",
                             xy=(0.01, 0.86), xycoords="axes fraction",
                             fontsize=8.5, color=c["accent"])

            for inicio, fin, nr in averias:
                ejes[2].axvspan(max(inicio, aceite[0][0]), min(fin, aceite[-1][0]),
                                color=c["accent"], alpha=0.35, zorder=3)
                ejes[2].annotate(f"parte {nr}", xy=(inicio, 0.5),
                                 xytext=(6, 0), textcoords="offset points",
                                 va="center", fontsize=8.5, color=c["ink"])
            ejes[2].set_yticks([])
            ejes[2].set_ylim(0, 1)
            ejes[2].annotate(f"averías: {len(averias)} suceso en todo el día",
                             xy=(0.01, 0.62), xycoords="axes fraction",
                             fontsize=8.5, color=c["ink_soft"])

            for e in ejes[:2]:
                e.grid(axis="y", zorder=0)
            ejes[2].xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
            ejes[2].set_xlabel(f"{DIA}, el día que empieza la avería #3")

            fig.tight_layout(pad=0.6)
            target = FIGURES / f"{name}.{theme}.png"
            fig.savefig(target, bbox_inches="tight", pad_inches=0.12)
            plt.close(fig)
            print(f"  {target.name:<44} {target.stat().st_size / 1024:>7.1f} KB  "
                  f"{fingerprint(target)}")

    guardar_huellas([name])
    print(f"  {es(len(aceite))} puntos de telemetría, {es(len(calle))} de clima "
          f"y {len(averias)} parte en el mismo día")


if __name__ == "__main__":
    main()
