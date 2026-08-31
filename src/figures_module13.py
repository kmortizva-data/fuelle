"""La figura del módulo 13: lo que solo se ve mirando la fila de al lado.

Dos paneles sobre el mismo tramo de horas, porque las dos cosas que enseña el
módulo son la misma idea aplicada a dos columnas.

Arriba, la carga del compresor con sus arranques marcados. Un arranque no es un
valor que esté escrito en ninguna parte: es el instante en que una fila dice
carga y la anterior decía que no.

Abajo, el hueco entre cada lectura y la anterior. Tampoco es una columna del
fichero. Solo existe como diferencia entre dos filas, y por eso ha hecho falta
llegar hasta aquí para poder preguntarlo.

Correr:  .venv\\Scripts\\python.exe src\\figures_module13.py
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

from figures_theme import (FIGURES, _style, colours, fingerprint,  # noqa: E402
                            guardar_huellas)

sys.stdout.reconfigure(encoding="utf-8")

PROJECT = Path(__file__).resolve().parents[1]
DATOS = PROJECT / "results" / "m13_ventanas.json"
SAMPLE = PROJECT / "assets" / "muestras" / "un_dia.parquet"

# Un tramo corto, para que se vean las lecturas una a una.
DESDE, HASTA = "2020-06-05 08:00:00", "2020-06-05 10:00:00"


def main() -> None:
    if not DATOS.exists():
        raise SystemExit("Falta results/m13_ventanas.json. "
                         "Corre src/transform/queries_m13.py")

    d = json.loads(io.open(DATOS, encoding="utf-8").read())
    con = duckdb.connect()
    con.execute(f"CREATE VIEW dia AS SELECT * FROM read_parquet('{SAMPLE.as_posix()}')")

    filas = con.sql(f"""
        SELECT timestamp, DV_eletric, hueco, antes
        FROM (SELECT timestamp, DV_eletric,
                     date_diff('second', lag(timestamp) OVER (ORDER BY timestamp),
                               timestamp) AS hueco,
                     lag(DV_eletric) OVER (ORDER BY timestamp) AS antes
              FROM dia)
        WHERE timestamp BETWEEN TIMESTAMP '{DESDE}' AND TIMESTAMP '{HASTA}'
        ORDER BY timestamp
    """).fetchall()

    horas = [f[0] for f in filas]
    carga = [f[1] for f in filas]
    huecos = [f[2] for f in filas]
    arranques = [f[0] for f in filas if f[3] == 0 and f[1] == 1]

    name = "fig_m13_lag_y_hueco"
    FIGURES.mkdir(exist_ok=True)
    for theme in ("claro", "oscuro"):
        c = colours(theme, module=13)
        with plt.rc_context(_style(theme, c)):
            fig, (arriba, abajo) = plt.subplots(
                2, 1, figsize=(9.2, 3.8), sharex=True,
                gridspec_kw={"height_ratios": [2, 1], "hspace": 0.16})

            # Escalones y no una rampa: la señal salta, no pasa por el medio.
            arriba.step(horas, carga, where="post", color=c["ink_faint"],
                        linewidth=1.2, zorder=3)
            for x in arranques:
                arriba.axvline(x, color=c["accent"], linewidth=1.2, zorder=4)
            arriba.set_yticks([0, 1])
            arriba.set_yticklabels(["en vacío", "en carga"])
            arriba.set_ylim(-0.25, 1.35)
            arriba.annotate(f"cada línea es un arranque: {len(arranques)} en estas dos horas",
                            xy=(0.01, 0.90), xycoords="axes fraction",
                            fontsize=8.5, color=c["accent"])

            # Los huecos, con la referencia de los diez segundos que promete la ficha.
            abajo.plot(horas[1:], huecos[1:], marker="o", markersize=2.2,
                       linestyle="none", color=c["ink_faint"], zorder=3)
            abajo.axhline(d["segundos_nominales"], color=c["ink"], linestyle="--",
                          linewidth=1.0, zorder=4)
            abajo.set_ylabel("hueco, s")
            abajo.set_ylim(8.4, 10.8)
            abajo.set_yticks([9, 10])
            abajo.annotate(f"los {d['segundos_nominales']} s que promete la ficha",
                           xy=(0.01, 0.72), xycoords="axes fraction",
                           fontsize=8, color=c["ink"])
            abajo.grid(axis="y", zorder=0)

            abajo.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
            abajo.set_xlabel(f"{d['dia_de_la_muestra']}, de 08:00 a 10:00")

            fig.tight_layout(pad=0.6)
            target = FIGURES / f"{name}.{theme}.png"
            fig.savefig(target, bbox_inches="tight", pad_inches=0.12)
            plt.close(fig)
            print(f"  {target.name:<44} {target.stat().st_size / 1024:>7.1f} KB  "
                  f"{fingerprint(target)}")

    guardar_huellas([name])
    print(f"  {len(arranques)} arranques y {sum(1 for h in huecos[1:] if h != 10)} "
          f"huecos irregulares en el tramo dibujado")


if __name__ == "__main__":
    main()
