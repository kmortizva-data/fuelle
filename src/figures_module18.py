"""Las dos figuras del módulo 18.

1. `fig_m18_historial_de_versiones`: las horas de carga de cada día, en las dos
   versiones de la tabla. La vieja, calculada sobre la plata con el fallo, es una
   línea casi plana pegada al cero; la buena tiene los picos de las averías. Ese
   contraste es la razón de que el viaje en el tiempo sirva para algo.

2. `fig_m18_delta_contra_iceberg`: las cuatro medidas, con su rango de siete
   corridas. Las barras no se comparan a ojo: donde los rangos se solapan, la
   lección dice que no se distinguen.

Correr:  .venv\\Scripts\\python.exe src\\figures_module18.py
"""

from __future__ import annotations

import io
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import duckdb  # noqa: E402
import matplotlib.dates as mdates  # noqa: E402

from figures_theme import es, figura, guardar_huellas  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")

PROJECT = Path(__file__).resolve().parents[1]
SAMPLES = PROJECT / "assets" / "muestras"
DATOS = PROJECT / "results" / "m18_formatos.json"

# Las cuatro fechas de avería, para marcar en la figura de arriba lo que la
# versión vieja escondía. Son las del fichero oficial, no las de la web.
AVERIAS = ["2020-04-18", "2020-05-29", "2020-06-05", "2020-07-15"]


def versiones() -> tuple[list, list, list]:
    con = duckdb.connect()
    for n in ("antes", "ahora"):
        con.execute(f"CREATE VIEW {n} AS "
                    f"SELECT * FROM read_parquet('{(SAMPLES / f'{n}.parquet').as_posix()}')")
    filas = con.sql("""
        SELECT a.dia, a.horas_de_carga AS antes, b.horas_de_carga AS ahora
        FROM antes a JOIN ahora b ON b.dia = a.dia
        ORDER BY a.dia
    """).fetchall()
    return ([f[0] for f in filas], [f[1] for f in filas], [f[2] for f in filas])


def historial() -> None:
    dias, antes, ahora = versiones()

    def dibujar(fig, ax, c) -> None:
        for fecha in AVERIAS:
            ax.axvline(__import__("datetime").date.fromisoformat(fecha),
                       color=c["rule"], linewidth=1.0, zorder=1)
        ax.plot(dias, ahora, color=c["accent"], linewidth=1.1, zorder=3,
                label="versión 1, la plata arreglada")
        ax.plot(dias, antes, color=c["ink_faint"], linewidth=1.1, linestyle="--",
                zorder=4, label="versión 0, la plata con el fallo")
        ax.set_ylabel("horas de carga al día")
        ax.set_ylim(0, 25)
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%b"))
        ax.legend(frameon=False, fontsize=8, loc="upper left")
        # Las líneas verticales son las averías, y conviene decirlo.
        ax.text(0.995, 0.94, "las líneas verticales son las cuatro averías",
                transform=ax.transAxes, ha="right", va="top", fontsize=7.5,
                color=c["ink_faint"])

    figura("fig_m18_historial_de_versiones", dibujar, ancho=9.2, alto=3.4, module=18)


def comparacion() -> None:
    d = json.loads(io.open(DATOS, encoding="utf-8").read())
    medidas = d["medidas"]
    nombres = list(medidas)

    def dibujar(fig, ax, c) -> None:
        alto = 0.34
        for i, nombre in enumerate(nombres):
            for j, formato in enumerate(("delta", "iceberg")):
                m = medidas[nombre][formato]
                y = i + (j - 0.5) * alto * 1.15
                color = c["accent"] if formato == "delta" else c["ink_faint"]
                # La barra es la mediana y la línea es el rango de las siete
                # corridas. Sin el rango, dos medidas que se pisan parecerían
                # distintas solo porque sus medianas no coinciden.
                ax.barh(y, m["mediana"], height=alto, color=color, zorder=3)
                ax.plot([m["minimo"], m["maximo"]], [y, y], color=c["ink"],
                        linewidth=1.0, zorder=4)
                ax.text(m["maximo"] + 0.004, y, f"{es(m['mediana'], 3)} s",
                        va="center", fontsize=7.5, color=c["ink_soft"])

        ax.set_yticks(range(len(nombres)))
        ax.set_yticklabels(nombres, fontsize=8.5)
        ax.invert_yaxis()
        ax.set_xlabel("segundos, mediana de siete corridas y su rango")
        ax.set_xlim(0, max(m[f]["maximo"] for m in medidas.values()
                           for f in ("delta", "iceberg")) * 1.34)
        ax.legend(handles=[
            __import__("matplotlib").patches.Patch(color=c["accent"], label="Delta"),
            __import__("matplotlib").patches.Patch(color=c["ink_faint"], label="Iceberg"),
        ], frameon=False, fontsize=8, loc="lower right")

    figura("fig_m18_delta_contra_iceberg", dibujar, ancho=9.2, alto=3.4, module=18)


def main() -> None:
    if not DATOS.exists():
        raise SystemExit("Falta results/m18_formatos.json. "
                         "Corre src/transform/table_format.py")
    historial()
    comparacion()
    guardar_huellas(["fig_m18_historial_de_versiones", "fig_m18_delta_contra_iceberg"])


if __name__ == "__main__":
    main()
