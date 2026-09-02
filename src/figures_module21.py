"""La figura del módulo 21: el trato entero, no la mitad buena.

A la izquierda lo que el índice da, en escala logarítmica porque si no la barra
con índice no se vería. A la derecha lo que cobra: la escritura, que se pone al
doble.

Las dos mitades juntas y a la misma altura es todo el argumento. Publicar solo
la izquierda sería vender el índice en vez de medirlo.

Correr:  .venv\\Scripts\\python.exe src\\figures_module21.py
"""

from __future__ import annotations

import io
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import matplotlib.pyplot as plt  # noqa: E402

from figures_theme import (FIGURES, _style, colours, es, fingerprint,  # noqa: E402
                           guardar_huellas)

sys.stdout.reconfigure(encoding="utf-8")

PROJECT = Path(__file__).resolve().parents[1]
DATOS = PROJECT / "results" / "m21_indices.json"


def main() -> None:
    if not DATOS.exists():
        raise SystemExit("Falta results/m21_indices.json. Corre src/db/indexes.py")

    d = json.loads(io.open(DATOS, encoding="utf-8").read())
    leer, escribir = d["leer"], d["escribir"]

    name = "fig_m21_indice_antes_despues"
    FIGURES.mkdir(exist_ok=True)
    for theme in ("claro", "oscuro"):
        c = colours(theme, module=21)
        with plt.rc_context(_style(theme, c)):
            fig, (izq, der) = plt.subplots(1, 2, figsize=(9.2, 3.0),
                                           gridspec_kw={"wspace": 0.34})

            etiquetas = ["sin índice", "con índice"]
            for ax, medida, titulo, log in (
                    (izq, leer, "leer un día", True),
                    (der, escribir, f"escribir {es(escribir['filas'])} filas", False)):
                for i, clave in enumerate(("sin_indice", "con_indice")):
                    m = medida[clave]
                    color = c["ink_faint"] if clave == "sin_indice" else c["accent"]
                    ax.barh(i, m["mediana"], height=0.5, color=color, zorder=3)
                    ax.plot([m["minimo"], m["maximo"]], [i, i], color=c["ink"],
                            linewidth=1.1, zorder=4)
                    ax.text(m["maximo"] * (1.35 if log else 1.04), i,
                            f"{es(m['mediana'], 4 if log else 3)} s",
                            va="center", fontsize=8, color=c["ink_soft"])
                if log:
                    ax.set_xscale("log")
                    ax.set_xlim(medida["con_indice"]["minimo"] / 3,
                                medida["sin_indice"]["maximo"] * 12)
                else:
                    ax.set_xlim(0, medida["con_indice"]["maximo"] * 1.4)
                ax.set_yticks(range(2))
                ax.set_yticklabels(etiquetas, fontsize=9)
                ax.invert_yaxis()
                ax.set_title(titulo, fontsize=9, color=c["ink_soft"], pad=8)
                ax.tick_params(length=0)
                ax.spines["left"].set_visible(False)
                ax.grid(axis="x", zorder=0)

            izq.set_xlabel("segundos, escala logarítmica")
            der.set_xlabel("segundos")

            fig.tight_layout(pad=0.6)
            target = FIGURES / f"{name}.{theme}.png"
            fig.savefig(target, bbox_inches="tight", pad_inches=0.12)
            plt.close(fig)
            print(f"  {target.name:<47} {target.stat().st_size / 1024:>7.1f} KB  "
                  f"{fingerprint(target)}")

    guardar_huellas([name])
    print(f"  el índice ocupa {d['mb_del_indice']} MB")


if __name__ == "__main__":
    main()
