"""La figura del módulo 24: la rampa, y por qué la mediana engaña.

Lo que hace la presión dentro de un tramo de carga, segundo a segundo. No es una
recta: los primeros diez segundos apenas sube porque el motor está arrancando, y
a partir de ahí decae según se llena el depósito y empuja hacia atrás.

Encima van las dos líneas que se pueden confundir, y confundirlas costó una
corrida: la **mediana instantánea**, que es lo que sale si se mide una pendiente
cualquiera, y la **media por minuto cargando**, que es lo que el compresor
consigue de verdad y lo que el gemelo necesita. Se llevan un 53 %.

Correr:  .venv\\Scripts\\python.exe src\\figures_module24.py
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
DATOS = PROJECT / "results" / "m24_fisica.json"


def main() -> None:
    if not DATOS.exists():
        raise SystemExit("Falta results/m24_fisica.json. Corre src/twin/model.py")

    d = json.loads(io.open(DATOS, encoding="utf-8").read())
    rampa = d["rampa"]
    x = [r["segundo"] for r in rampa]
    y = [r["bar_min"] for r in rampa]
    mediana = d["pendientes_tipicas"]["llenado_mediana"]
    media = d["llena"]

    def dibujar(fig, ax, c) -> None:
        ax.plot(x, y, marker="o", markersize=4.5, linewidth=1.8,
                color=c["accent"], zorder=4, label="lo que sube de verdad")
        ax.axhline(mediana, color=c["ink_faint"], linewidth=1.3, linestyle=":",
                   zorder=3, label="la mediana instantánea")
        ax.axhline(media, color=c["ink_soft"], linewidth=1.3, linestyle="--",
                   zorder=3, label="la media por minuto cargando")

        # La banda entre las dos, que es el error que se cuela si se toma la
        # mediana por buena.
        ax.fill_between([min(x), max(x)], media, mediana, color=c["accent"],
                        alpha=0.10, zorder=1)
        ax.annotate(f"{es((mediana / media - 1) * 100, 0)} % de más",
                    xy=(max(x) * 0.72, (media + mediana) / 2),
                    fontsize=8.5, color=c["ink_soft"], ha="center")
        ax.annotate("el motor arrancando", xy=(x[0], y[0]),
                    xytext=(x[1] * 1.2, y[0] - 0.12), fontsize=8,
                    color=c["ink_faint"])

        ax.set_xlabel("segundos desde que el presostato pide carga")
        ax.set_ylabel("sube, bar/min")
        ax.set_ylim(0, max(max(y), mediana) * 1.16)
        ax.set_xlim(min(x) - 3, max(x) + 3)
        ax.grid(axis="y", zorder=0)
        ax.legend(frameon=False, fontsize=8, loc="lower right")

    figura("fig_m24_balance_del_deposito", dibujar, ancho=9.2, alto=3.4, module=24)
    guardar_huellas(["fig_m24_balance_del_deposito"])
    print(f"  la mediana {mediana} contra la media {media}, "
          f"un {(mediana / media - 1):.0%} de más")


if __name__ == "__main__":
    main()
