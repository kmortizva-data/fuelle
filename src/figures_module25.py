"""Las dos figuras del módulo 25.

1. `fig_m25_ciclo_carga_vacio`: el diente de sierra que hace la presión entre los
   dos umbrales del presostato. Es la única figura del curso que dibuja la
   presión, y se puede porque aquí **explica el mecanismo**: no está buscando una
   fuga en ella, que es lo que la regla del doble trazo prohíbe.

2. `fig_m25_paso_de_tiempo`: lo que cuesta avanzar a trancos. Los ciclos que la
   simulación pierde según crece el paso, y encima el error del ciclo de trabajo,
   que es el falso verde: con paso de 30 s la carga sale casi clavada y ya se han
   perdido dos ciclos de dieciséis.

Correr:  .venv\\Scripts\\python.exe src\\figures_module25.py
"""

from __future__ import annotations

import io
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from figures_theme import es, figura, guardar_huellas  # noqa: E402
from twin.model import mide  # noqa: E402
from twin.simulate import avanza  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")

PROJECT = Path(__file__).resolve().parents[1]
DATOS = PROJECT / "results" / "m25_simular.json"


def ciclo() -> None:
    dep, _ = mide()
    minutos = 90
    paso = 1 / 60
    r = avanza(dep, dep.consumo, minutos, paso)
    t = [i * paso for i in range(len(r["presiones"]))]

    def dibujar(fig, ax, c) -> None:
        ax.plot(t, r["presiones"], color=c["accent"], linewidth=1.6, zorder=4)
        for y, texto in ((dep.para, "para, {} bar"), (dep.arranca, "arranca, {} bar")):
            ax.axhline(y, color=c["ink_faint"], linewidth=1.1, linestyle="--", zorder=3)
            ax.annotate(texto.format(es(y, 2)), xy=(minutos * 0.985, y),
                        xytext=(0, 4 if y == dep.para else -13),
                        textcoords="offset points", ha="right",
                        fontsize=8.5, color=c["ink_soft"])
        ax.set_xlabel("minutos")
        ax.set_ylabel("presión del depósito, bar")
        ax.set_xlim(0, minutos)
        ax.set_ylim(dep.arranca - 0.5, dep.para + 0.5)
        ax.grid(axis="y", zorder=0)

    figura("fig_m25_ciclo_carga_vacio", dibujar, ancho=9.2, alto=3.0, module=25)


def paso_de_tiempo() -> None:
    d = json.loads(io.open(DATOS, encoding="utf-8").read())
    filas = [r for r in d["pasos"] if r["segundos"] != "patrón"]
    x = list(range(len(filas)))
    etiquetas = [str(r["segundos"]) for r in filas]
    perdidos = [r["ciclos_perdidos"] for r in filas]
    error = [r["error_de_carga"] * 100 for r in filas]
    patron = d["arranques_del_patron"]

    def dibujar(fig, ax, c) -> None:
        # Los pasos que aún valen pierden CERO ciclos, así que su barra no se ve.
        # Se marcan con una banda de fondo: si no, la figura es toda gris y el
        # lector no sabe dónde está la frontera, que es lo único que importa.
        buenos = [i for i, r in enumerate(filas) if r["se_parece"]]
        if buenos:
            ax.axvspan(-0.5, max(buenos) + 0.5, color=c["accent"], alpha=0.12, zorder=1)
            ax.annotate("aquí la simulación resuelve todos los ciclos",
                        xy=((max(buenos)) / 2, max(perdidos) + 0.95),
                        ha="center", fontsize=8.5, color=c["ink_soft"])

        ax.bar(x, perdidos, width=0.62, color=c["ink_faint"], zorder=3)
        ax.set_xticks(x)
        ax.set_xticklabels(etiquetas)
        for i, etiqueta in enumerate(ax.get_xticklabels()):
            etiqueta.set_color(c["accent"] if filas[i]["se_parece"] else c["ink_faint"])
        ax.set_xlabel("paso de la simulación, segundos")
        ax.set_ylabel(f"ciclos perdidos de {patron}")
        ax.set_xlim(-0.6, len(filas) - 0.4)
        ax.set_ylim(0, max(perdidos) + 1.4)
        ax.grid(axis="y", zorder=0)

        # El falso verde, encima y en su propio eje: el error del ciclo de
        # trabajo no crece con el paso, y con 30 s es el más pequeño de todos.
        der = ax.twinx()
        der.plot(x, error, color=c["ink_soft"], linewidth=1.4, linestyle=":",
                 marker="o", markersize=4, zorder=5)
        der.set_ylabel("error del ciclo de trabajo, puntos porcentuales")
        der.set_ylim(0, max(error) * 1.5)
        der.spines["top"].set_visible(False)
        i30 = etiquetas.index("30")
        der.annotate("mirando solo la línea,\n30 s parece el mejor de todos",
                     xy=(x[i30], error[i30]), xytext=(x[i30] - 2.6, max(error) * 0.62),
                     fontsize=8, color=c["ink_soft"],
                     arrowprops=dict(arrowstyle="->", color=c["ink_faint"],
                                     linewidth=1, shrinkB=4))

    figura("fig_m25_paso_de_tiempo", dibujar, ancho=9.2, alto=3.4, module=25)


def main() -> None:
    if not DATOS.exists():
        raise SystemExit("Falta results/m25_simular.json. Corre src/twin/simulate.py")
    ciclo()
    paso_de_tiempo()
    guardar_huellas(["fig_m25_ciclo_carga_vacio", "fig_m25_paso_de_tiempo"])


if __name__ == "__main__":
    main()
