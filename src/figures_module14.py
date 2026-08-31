"""Las dos figuras del módulo 14: dónde están los huecos y cómo se ve la rejilla.

La primera reparte los 337.653 huecos por mes. En bronce esos huecos no existían
como filas y no había forma de dibujarlos; ponerlos en la rejilla es justo lo que
los convierte en algo que se puede contar y mirar.

La segunda hace zoom a unos minutos y enseña la diferencia entre el registro tal
como llega, con su reloj andando, y la misma media hora ajustada a casillas de
diez segundos. Es la operación entera del módulo en un dibujo.

Correr:  .venv\\Scripts\\python.exe src\\figures_module14.py
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
DATOS = PROJECT / "results" / "m14_plata.json"
SILVER = PROJECT / "lake" / "silver" / "telemetry"

# Un tramo elegido midiendo, no a ojo: cuarenta minutos con noventa casillas
# vacías Y con el compresor trabajando, para que se vean las dos cosas a la vez.
# El primero que probé caía dentro del corte de 48 horas del 25 de abril, donde
# la presión está plana en el suelo y no había nada que mirar.
DESDE, HASTA = "2020-06-12 00:40:00", "2020-06-12 01:20:00"

MESES = ["feb", "mar", "abr", "may", "jun", "jul", "ago", "sep"]


def huecos_por_mes(d: dict, con) -> str:
    name = "fig_m14_huecos"
    filas = con.sql("""
        SELECT strftime(day, '%Y-%m') AS mes,
               sum(CASE WHEN medido THEN 1 ELSE 0 END) AS con_dato,
               sum(CASE WHEN NOT medido THEN 1 ELSE 0 END) AS huecos
        FROM plata GROUP BY mes ORDER BY mes
    """).fetchall()
    etiquetas = [MESES[int(m.split("-")[1]) - 2] for m, _, _ in filas]
    con_dato = [c for _, c, _ in filas]
    huecos = [h for _, _, h in filas]
    x = range(len(filas))

    for theme in ("claro", "oscuro"):
        c = colours(theme, module=14)
        with plt.rc_context(_style(theme, c)):
            fig, ax = plt.subplots(figsize=(9.0, 3.0))
            ax.bar(x, con_dato, width=0.62, color=c["ink_faint"], zorder=3,
                   label="casillas con lectura")
            ax.bar(x, huecos, width=0.62, bottom=con_dato, color=c["accent"],
                   zorder=3, label="huecos")
            for i, (cd, h) in enumerate(zip(con_dato, huecos)):
                ax.annotate(f"{h * 100 / (cd + h):.0f} %", xy=(i, cd + h),
                            xytext=(0, 4), textcoords="offset points",
                            ha="center", fontsize=8.5, color=c["accent"])
            ax.set_xticks(list(x))
            ax.set_xticklabels(etiquetas)
            ax.set_ylabel("casillas de diez segundos")
            ax.grid(axis="y", zorder=0)
            ax.legend(frameon=False, fontsize=8.5, loc="upper right")
            ax.margins(y=0.16)

            fig.tight_layout(pad=0.6)
            target = FIGURES / f"{name}.{theme}.png"
            fig.savefig(target, bbox_inches="tight", pad_inches=0.12)
            plt.close(fig)
            print(f"  {target.name:<44} {target.stat().st_size / 1024:>7.1f} KB  "
                  f"{fingerprint(target)}")
    return name


def remuestreo(d: dict, con) -> str:
    name = "fig_m14_remuestreo"
    filas = con.sql(f"""
        SELECT timestamp, medido, TP2 FROM plata
        WHERE timestamp BETWEEN TIMESTAMP '{DESDE}' AND TIMESTAMP '{HASTA}'
        ORDER BY timestamp
    """).fetchall()
    horas = [f[0] for f in filas]
    hay = [f[1] for f in filas]
    presion = [f[2] for f in filas]

    # Los límites se calculan una vez, fuera del bucle de temas: no dependen del
    # color y la marca de los huecos necesita saber dónde está el suelo.
    medidas = [p for p in presion if p is not None]
    alto, bajo = max(medidas), min(medidas)
    margen = (alto - bajo) * 0.12
    vacias = [h for h, m in zip(horas, hay) if not m]

    for theme in ("claro", "oscuro"):
        c = colours(theme, module=14)
        with plt.rc_context(_style(theme, c)):
            fig, ax = plt.subplots(figsize=(9.2, 3.0))

            # La presión donde la hay. Los huecos quedan sin punto, que es lo
            # que se quiere ver: no se unen con una raya, porque unirlos sería
            # dibujar un dato que nadie midió.
            ax.plot([h for h, m in zip(horas, hay) if m],
                    [p for p, m in zip(presion, hay) if m],
                    marker="o", markersize=2.4, linestyle="none",
                    color=c["ink_faint"], zorder=4, label="casilla con lectura")

            # Y los huecos, marcados abajo para que se cuenten de un vistazo.
            ax.plot(vacias, [bajo - margen * 1.5] * len(vacias), marker="|",
                    markersize=9, linestyle="none", color=c["accent"], zorder=5,
                    label=f"casilla vacía: {es(len(vacias))} de {es(len(horas))}")

            ax.set_ylabel("presión TP2, bar")
            ax.set_ylim(bajo - margen * 2.4, alto + margen)
            ax.grid(axis="y", zorder=0)
            ax.legend(frameon=False, fontsize=8.5, loc="upper left")
            ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
            ax.set_xlabel("2020-06-12, cuarenta minutos con el compresor ciclando")

            fig.tight_layout(pad=0.6)
            target = FIGURES / f"{name}.{theme}.png"
            fig.savefig(target, bbox_inches="tight", pad_inches=0.12)
            plt.close(fig)
            print(f"  {target.name:<44} {target.stat().st_size / 1024:>7.1f} KB  "
                  f"{fingerprint(target)}")
    return name


def main() -> None:
    if not DATOS.exists() or not SILVER.exists():
        raise SystemExit("Falta la plata. Corre src/transform/silver.py primero.")

    d = json.loads(io.open(DATOS, encoding="utf-8").read())
    con = duckdb.connect()
    con.execute(f"CREATE VIEW plata AS "
                f"SELECT * FROM read_parquet('{SILVER.as_posix()}/**/*.parquet')")

    FIGURES.mkdir(exist_ok=True)
    guardar_huellas([huecos_por_mes(d, con), remuestreo(d, con)])
    print(f"  {es(d['huecos'])} huecos de {es(d['filas_plata'])} casillas")


if __name__ == "__main__":
    main()
