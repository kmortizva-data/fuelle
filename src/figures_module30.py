"""The figure of module 30: what the whole semester weighs in the reader's browser.

The same three curves per day, written three ways and at six resolutions, and
what each one costs over the network, compressed the way GitHub Pages sends it.

The finding is the gap between the lines, not their slope: **how the numbers are
written weighs more than how many there are**. A point every minute written as
whole minutes per slot still weighs less than a point every ten minutes written
as a running total in hours, and the dotted line across the figure is there to
make that comparison without reading any number.

Run:  .venv\\Scripts\\python.exe src\\figures_module30.py
"""

from __future__ import annotations

import io
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from figures_theme import es, figura, guardar_huellas  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")

PROJECT = Path(__file__).resolve().parents[1]
DATOS = PROJECT / "results" / "m30_panel.json"

NOMBRE = "fig_m30_peso_del_semestre"


def etiqueta_de_tramo(minutos: int) -> str:
    return "1 h" if minutos == 60 else f"{minutos} min"


def main() -> None:
    if not DATOS.exists():
        raise SystemExit("Faltan las cifras. Corre src/twin/panel.py primero.")
    d = json.load(io.open(DATOS, encoding="utf-8"))
    pesos = d["pesos"]
    xs = [p["puntos_por_dia"] for p in pesos]
    elegido = next(p for p in pesos if p["puntos_por_dia"] == d["puntos_por_dia"])

    def dibujar(fig, ax, c):
        acumulado = [p["acumulado"]["kb_red"] for p in pesos]
        tramos = [p["tramos"]["kb_red"] for p in pesos]
        caracteres = [(p["puntos_por_dia"], p["caracteres"]["kb_red"])
                      for p in pesos if p["caracteres"]]

        # La raya de la comparación: lo que pesa el acumulado a la resolución del
        # panel. La línea de los tramos no la cruza en ningún punto.
        ax.axhline(elegido["acumulado"]["kb_red"], color=c["ink_faint"],
                   linewidth=0.9, linestyle=":", zorder=1)
        ax.axvline(d["puntos_por_dia"], color=c["rule"], linewidth=1.0, zorder=1)

        # En el orden en que quedan de arriba abajo, para que la leyenda se lea
        # igual que el dibujo.
        ax.plot(xs, acumulado, color=c["ink_faint"], linewidth=1.6, linestyle="--",
                marker="o", markersize=4.5, zorder=3,
                label="el acumulado, en horas con dos decimales")
        ax.plot(xs, tramos, color=c["accent"], linewidth=2.2, marker="o",
                markersize=5, zorder=4, label="los minutos de cada tramo, enteros")
        ax.plot([x for x, _ in caracteres], [y for _, y in caracteres],
                color=c["ink_soft"], linewidth=1.3, linestyle=":", marker="s",
                markersize=4, zorder=3, label="un carácter por tramo")

        # Los dos números de la resolución elegida, encima de su punto: el del
        # acumulado a la izquierda y el de los tramos a la derecha, donde no hay
        # ninguna línea que pisar.
        for valor, color, dx, ha in ((elegido["acumulado"]["kb_red"], c["ink_soft"],
                                      -8, "right"),
                                     (elegido["tramos"]["kb_red"], c["accent"], 8,
                                      "left")):
            ax.annotate(f"{es(valor, 1)} KB", xy=(d["puntos_por_dia"], valor),
                        xytext=(dx, 9), textcoords="offset points", fontsize=8.5,
                        color=color, ha=ha, va="bottom")
        ax.annotate("lo que usa el panel", xy=(d["puntos_por_dia"], 1),
                    xycoords=("data", "axes fraction"), xytext=(4, -4),
                    textcoords="offset points", fontsize=8, color=c["ink_faint"],
                    ha="left", va="top")

        ax.set_xscale("log")
        ax.set_yscale("log")
        ax.set_xticks(xs)
        ax.set_xticklabels([f"{p['puntos_por_dia']}\n"
                            f"{etiqueta_de_tramo(p['minutos_por_punto'])}"
                            for p in pesos])
        ax.minorticks_off()
        ticks_y = [5, 10, 20, 50, 100, 200]
        ax.set_yticks(ticks_y)
        ax.set_yticklabels([str(t) for t in ticks_y])
        ax.set_ylim(4, max(acumulado) * 1.6)
        ax.set_xlabel("puntos por día, y cada cuánto va uno (escala logarítmica)")
        ax.set_ylabel("KB por la red (escala logarítmica)")
        ax.grid(axis="y", zorder=0)
        ax.legend(frameon=False, fontsize=8, loc="upper left")

    figura(NOMBRE, dibujar, ancho=9.0, alto=4.0, module=30)
    guardar_huellas([NOMBRE])


if __name__ == "__main__":
    main()
