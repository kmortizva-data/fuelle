"""Las dos figuras del módulo 9: el igual que falla y la regla que acierta.

La primera hace un zoom brutal alrededor de 8,2 bar. A esa escala se ve que ahí
no hay «un valor», hay una nube de valores parecidos, y que preguntar por el
número exacto cae en una sola rendija de esa nube.

La segunda dibuja la corriente del motor con los dos cortes de la regla encima.
Los cortes no se eligen a ojo: están donde la distribución tiene sus valles, y
el dibujo tiene que enseñar eso o la regla parecería arbitraria.

Correr:  .venv\\Scripts\\python.exe src\\figures_module9.py
"""

from __future__ import annotations

import io
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import duckdb  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from figures_theme import (FIGURES, _style, colours, es, fingerprint,  # noqa: E402
                            guardar_huellas)

sys.stdout.reconfigure(encoding="utf-8")

PROJECT = Path(__file__).resolve().parents[1]
DATOS = PROJECT / "results" / "m09_tipos.json"
SAMPLE = PROJECT / "assets" / "muestras" / "sql.parquet"


def coma_flotante(d: dict, con) -> str:
    """El zoom alrededor del umbral: una nube, no un valor."""
    name = "fig_m09_coma_flotante"
    umbral = d["umbral_de_la_ficha"]
    valores = [r[0] for r in con.sql(f"""
        SELECT TP2 FROM t WHERE TP2 BETWEEN {umbral} - 0.06 AND {umbral} + 0.06
    """).fetchall()]

    for theme in ("claro", "oscuro"):
        c = colours(theme, module=9)
        with plt.rc_context(_style(theme, c)):
            fig, ax = plt.subplots(figsize=(9.0, 2.9))
            bordes = np.linspace(umbral - 0.06, umbral + 0.06, 61)
            ax.hist(valores, bins=bordes, color=c["ink_faint"], zorder=3)

            caja = {"facecolor": c["ground"], "edgecolor": "none", "pad": 2.0}

            # Lo que el lector quería decir: toda la banda.
            ax.axvspan(umbral - 0.05, umbral + 0.05, color=c["accent"], alpha=0.10, zorder=1)
            ax.annotate("lo que querías decir: toda esta banda, "
                        f"{es(d['filas_redondeando'])} lecturas",
                        xy=(umbral - 0.049, 0.93), xycoords=("data", "axes fraction"),
                        fontsize=8.5, color=c["ink_soft"], zorder=6, bbox=caja)

            # La rendija que encuentra el igual exacto. Las dos anotaciones van
            # dentro del área de dibujo: fuera chocaban con el título del eje.
            ax.axvline(umbral, color=c["accent"], linewidth=2, zorder=5)
            ax.annotate(f"lo que encuentra  TP2 = {umbral}:\n"
                        f"{d['filas_con_igual_exacto']} lecturas, esta raya",
                        xy=(umbral, 0.52), xycoords=("data", "axes fraction"),
                        xytext=(9, 0), textcoords="offset points",
                        fontsize=8.5, color=c["accent"], zorder=6, bbox=caja)

            ax.set_xlabel("presión del compresor TP2, en bar")
            ax.set_ylabel("lecturas")
            ax.grid(axis="y", zorder=0)
            ax.margins(y=0.34)

            fig.tight_layout(pad=0.6)
            target = FIGURES / f"{name}.{theme}.png"
            fig.savefig(target, bbox_inches="tight", pad_inches=0.12)
            plt.close(fig)
            print(f"  {target.name:<44} {target.stat().st_size / 1024:>7.1f} KB  "
                  f"{fingerprint(target)}")
    return name


def tres_estados(d: dict, con) -> str:
    """La corriente, con los dos cortes puestos donde la distribución los pide."""
    name = "fig_m09_tres_estados"
    valores = [r[0] for r in con.sql("SELECT Motor_current FROM t").fetchall()]
    parado, carga = d["corte_parado"], d["corte_carga"]
    estados = {x["estado"]: x for x in d["estados"]}

    for theme in ("claro", "oscuro"):
        c = colours(theme, module=9)
        with plt.rc_context(_style(theme, c)):
            fig, ax = plt.subplots(figsize=(9.0, 3.2))
            ax.hist(valores, bins=np.linspace(0, 10, 121), color=c["ink_faint"], zorder=3)
            ax.set_yscale("log")

            for corte in (parado, carga):
                ax.axvline(corte, color=c["accent"], linewidth=1.6,
                           linestyle="--", zorder=5)

            etiquetas = [("parado", 0, parado), ("en vacio", parado, carga),
                         ("en carga", carga, 10)]
            for clave, izq, der in etiquetas:
                x = (izq + der) / 2
                e = estados[clave]
                ax.annotate(f"{clave}\n{es(e['por_ciento'], 1)} %",
                            xy=(x, 1), xycoords=("data", "axes fraction"),
                            xytext=(0, -22), textcoords="offset points",
                            ha="center", fontsize=9, color=c["ink"], zorder=6)

            # Lo que dice la ficha, que no es donde está el dato.
            ficha = d["amperios_que_dice_la_ficha_en_carga"]
            ax.axvline(ficha, color=c["ink_soft"], linewidth=1.2,
                       linestyle=":", zorder=4)
            # Anclada en fracción de eje y no en y=0: el eje es logarítmico y
            # el cero no existe ahí, así que la etiqueta se iba de la figura.
            ax.annotate(f"la ficha dice {ficha} A en carga",
                        xy=(ficha, 0.40), xycoords=("data", "axes fraction"),
                        xytext=(7, 0), textcoords="offset points",
                        fontsize=8, color=c["ink_soft"], zorder=6,
                        bbox={"facecolor": c["ground"], "edgecolor": "none", "pad": 1.6})

            ax.set_xlabel("corriente del motor, en amperios "
                          "(los cortes en trazo discontinuo)")
            ax.set_ylabel("lecturas (escala logarítmica)")
            ax.grid(axis="y", zorder=0)
            ax.set_xlim(-0.2, 10)

            fig.tight_layout(pad=0.6)
            target = FIGURES / f"{name}.{theme}.png"
            fig.savefig(target, bbox_inches="tight", pad_inches=0.12)
            plt.close(fig)
            print(f"  {target.name:<44} {target.stat().st_size / 1024:>7.1f} KB  "
                  f"{fingerprint(target)}")
    return name


def main() -> None:
    if not DATOS.exists():
        raise SystemExit("Falta results/m09_tipos.json. Corre src/transform/queries_m09.py")

    d = json.loads(io.open(DATOS, encoding="utf-8").read())
    con = duckdb.connect()
    con.execute(f"CREATE VIEW t AS SELECT * FROM read_parquet('{SAMPLE.as_posix()}')")

    FIGURES.mkdir(exist_ok=True)
    guardar_huellas([coma_flotante(d, con), tres_estados(d, con)])
    print(f"  el igual encuentra {d['filas_con_igual_exacto']} de "
          f"{d['filas_redondeando']} lecturas")


if __name__ == "__main__":
    main()
