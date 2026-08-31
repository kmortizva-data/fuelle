"""La figura del módulo 6: la curva de la partición, con sus rangos.

El consejo estándar dice «particiona por día» y esta figura es la respuesta
medida. Dos paneles con el mismo eje horizontal, que es el número de ficheros en
que se parte la tabla: a la izquierda lo que cuesta leer un día, a la derecha lo
que ocupa el total.

Los rangos van dibujados encima de cada punto porque sin ellos la figura miente
por omisión: las dos primeras disposiciones no se distinguen entre sí, y una
línea limpia uniendo medianas daría a entender que sí.

Correr:  .venv\\Scripts\\python.exe src\\figures_module6.py
"""

from __future__ import annotations

import io
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import matplotlib.pyplot as plt  # noqa: E402

from figures_theme import FIGURES, _style, colours, fingerprint, guardar_huellas  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")

PROJECT = Path(__file__).resolve().parents[1]
DATOS = PROJECT / "results" / "m06_partition.json"

NOMBRES = {
    "single_file": "un fichero",
    "by_month": "por mes",
    "by_week": "por semana",
    "by_day": "por día",
}


def main() -> None:
    if not DATOS.exists():
        raise SystemExit("Falta results/m06_partition.json. "
                         "Corre src/transform/choose_partition.py")

    datos = json.loads(io.open(DATOS, encoding="utf-8").read())
    capas = datos["layouts"]
    ficheros = [c["files"] for c in capas]
    lectura = [c["read_one_day_seconds"] for c in capas]
    bajos = [c["read_one_day_seconds"] - c["read_min_s"] for c in capas]
    altos = [c["read_max_s"] - c["read_one_day_seconds"] for c in capas]
    tamaños = [c["size_mb"] for c in capas]
    etiquetas = [NOMBRES[c["layout"]] for c in capas]

    name = "fig_m6_curva_de_particion"
    FIGURES.mkdir(exist_ok=True)
    for theme in ("claro", "oscuro"):
        c = colours(theme, module=6)
        with plt.rc_context(_style(theme, c)):
            fig, (izq, der) = plt.subplots(1, 2, figsize=(9.2, 3.1),
                                           gridspec_kw={"wspace": 0.28})

            izq.errorbar(ficheros, lectura, yerr=[bajos, altos], marker="o",
                         markersize=6, linewidth=1.6, color=c["accent"],
                         ecolor=c["ink_faint"], elinewidth=1, capsize=4, zorder=4)
            izq.set_xscale("log")
            izq.set_xlabel("ficheros en que se parte la tabla")
            izq.set_ylabel("segundos en leer un día")
            izq.grid(axis="y", zorder=0)
            izq.set_ylim(0, max(c2["read_max_s"] for c2 in capas) * 1.15)

            der.plot(ficheros, tamaños, marker="o", markersize=6, linewidth=1.6,
                     color=c["accent"], zorder=4)
            der.set_xscale("log")
            der.set_xlabel("ficheros en que se parte la tabla")
            der.set_ylabel("MB que ocupa el total")
            der.grid(axis="y", zorder=0)
            # A la izquierda de cada punto, porque la línea sube hacia la derecha
            # y una etiqueta centrada encima se le echa encima.
            for x, y in zip(ficheros, tamaños):
                der.annotate(f"{y:.2f}".replace(".", ","), xy=(x, y), xytext=(-8, 8),
                             textcoords="offset points", ha="right",
                             fontsize=8, color=c["ink_soft"])
            der.set_ylim(min(tamaños) * 0.94, max(tamaños) * 1.06)

            # Los nombres van en el eje y no flotando junto a los puntos: con
            # las barras de rango dibujadas no queda hueco libre donde ponerlos.
            for eje in (izq, der):
                eje.set_xticks(ficheros)
                eje.set_xticklabels([f"{f}\n{t}" for f, t in zip(ficheros, etiquetas)])
                eje.minorticks_off()

            fig.tight_layout(pad=0.6)
            target = FIGURES / f"{name}.{theme}.png"
            fig.savefig(target, bbox_inches="tight", pad_inches=0.12)
            plt.close(fig)
            print(f"  {target.name:<44} {target.stat().st_size / 1024:>7.1f} KB  "
                  f"{fingerprint(target)}")

    guardar_huellas([name])
    solapan = [NOMBRES[c["layout"]] for c in capas
               if c["layout"] != datos["fastest_read"]
               and not c["read_distinguishable_from_fastest"]]
    print(f"  no se distinguen de la más rápida: {', '.join(solapan) or 'ninguna'}")


if __name__ == "__main__":
    main()
